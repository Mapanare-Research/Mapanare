# Rattler — v4.136.0 LLVM IR correctness review

**Score: 8.9/10**
**Grade: MEETS**
**Prior (v4.120.0): 8.3/10 PASS**
**Delta: +0.6**

## Executive summary

The v4.121.0 → v4.135.0 closeout arc landed three IR-layer fixes I have
been tracking since v4.114.0 (Sh.2 LIST, Sh.2 STRING, Rt.1 enum
unboxing) and shipped a strict 3-stage byte-identical fixed point at
v4.134.0 that holds at v4.135.0 (`stage2.ll == stage3.ll`, md5
`0c00ad07fee94f98bb350b359395843b`, both files `llvm-as`-clean). All
three Sh.2 frames I named at v4.114.0 / v4.120.0 are gone from the
valgrind top-frame table. ASan ASAN_ERROR is at zero across 65 goldens.
This is genuine IR-correctness progress, not panel polish. I am not
going above 9.0 because (a) byte-identity ≠ semantic-correctness proof,
(b) 5 valgrind ERRORS remain (Ge.1, generics monomorphization
uninit-reads), and (c) the Sh.2 fix shape is correct but narrow — it
mitigates the symptom in the Python emitter only and leaves the
self-hosted `emit_llvm.mn` without equivalent move-tracking
infrastructure (Sh.4–7 carry-forwards live there).

## What improved since v4.120.0

- **Sh.2 LIST closure (v4.131.0)** at
  `mapanare/emit_llvm_text.py:2566-2591` (`_do_copy`). The fix shape is
  correct: only mark `i.dest.name` as a tracked owner when `i.src.name`
  was already a tracked owner (lines 2584-2587 — pop src, insert dest);
  if src is an alias (field-get / enum-payload / param), explicitly
  untrack dest if it was previously an owner (lines 2589-2591). This
  inverts the v4.101.0 default-track-everything stance that produced
  the v4.105.0 baseline of 12× `__mn_list_free` and 11×
  `emit_llvm__emit_mir_call` valgrind frames. Net valgrind effect:
  ERRORS 31 → 14 (`docs/roadmap/v4/v4.135.0/VALGRIND_REPORT.md:166-178`).
- **Sh.2 STRING closure (v4.132.0)** at
  `mapanare/emit_llvm_text.py:2592-2609`. Mirrors the LIST fix into the
  STRING branch: pop `_str_slots[src]` → install at dest on real
  ownership transfer (2604-2605); pop dest if it was an owner and src
  is an alias (2608-2609). Comment block at 2592-2599 is honest about
  scope ("a String extracted from a struct field or concat'd into a
  local then stored into an Instruction enum payload"). Net:
  ASAN_ERROR 23 → 0 (`docs/roadmap/v4/v4.135.0/ASAN_REPORT.md:13-17`),
  valgrind ERRORS 14 → 5 (same docket family, residual Ge.1 only).
- **Rt.1 enum unboxing (v4.124.0)** at
  `mapanare/emit_llvm_text.py:1098-1172` and emission sites
  `4380-4408` (insertvalue) + `4514-4527` (extractvalue). Eligibility
  predicate is sound: `_compute_enum_inline_slots` requires (a) no
  boxed self-reference fields, (b) every payload field across every
  variant fits in an i64 slot via `_type_fits_inline_slot`, (c)
  `max_fields ≤ _MAX_INLINE_SLOTS = 2` (line 1116). The
  per-type-fits predicate at 1121-1132 is conservative: only `i64`,
  `double`, `i1`, `i8`, `i16`, `i32`, opaque `ptr`, and legacy `T*`
  qualify; String (`{ptr, i64}`), List, Result wrappers, and user
  structs are rejected — so `Result<Int, String>` correctly stays
  boxed. Pack/unpack at 1134-1172 is bitwidth-correct (zext/trunc for
  smaller integer types, bitcast for double, ptrtoint/inttoptr for
  pointers). 83K mallocs/run → 0 on `enum_match` and CLEAN under both
  valgrind and ASan (`docs/roadmap/v4/v4.135.0/ASAN_REPORT.md:111-113`).
- **Qs.1 fix (v4.122.0)** at `mapanare/lower.py:1262-1267`. The
  one-line `val = Value(name=val.name, ty=declared)` rebinding lifts
  the empty-list literal's MIR type into the declared annotation so
  downstream IndexGet / ListPush / `len` lowering observes the element
  type. The fix is at the lowerer (which is the right layer); the
  emitter side was always correct given correct types. Regression
  guarded by `tests/golden/65_list_int_indexing.mn`.
- **Strict 3-stage fixed point (v4.134.0, holds v4.135.0)**.
  `scripts/verify_fixed_point.sh` (line 81 `llvm-as` on stage2.ll, line
  98 `clang -O2 -c`, line 146 `llvm-as` on stage3.ll) gates with
  teeth. Both stages parse, both stages survive `clang -O2 -c`. Diff
  is 0; md5 match. Cobra's v4.99.0 blocker is closed with a
  reproducible script (~90 s wall).
- **Goldens through `mnc-stage1`: 21 → 53 (+32)**, zero regressions
  across the arc (`MEASUREMENTS.md:62-77`). Integration pipeline
  (emit→llvm-as→opt→llc→clang→run) holds 60/64 from v4.104.0 baseline.
- **Top valgrind frames cleared.** The v4.105.0 hot list
  (`mir_opt__block_successors` 14×, `__mn_list_free` 12×,
  `emit_llvm__emit_mir_call` 11×) is **all zeros** at v4.135.0
  (`VALGRIND_REPORT.md:166-178`).

## What remains open / new concerns

- **Ge.1 (5 valgrind ERRORS, `mapanare/self/lower.mn` +
  `lower_state.mn`)** — opened v4.132.0 when Sh.2 closure unmasked the
  noise floor. Top frames `lower__try_monomorphize_struct` 4×,
  `lower_state__fresh_tmp` 4×, `lower__monomorphize_impl_methods` 2×,
  `emit_llvm__resolve_variant_index` 1× (all from `26_generics`,
  `29_generic_impl`, `30_nested_generics`, `31_generic_multi`,
  `32_generic_enum` — `VALGRIND_REPORT.md:79-103`). All five tests exit
  0 — silent-UB profile. ASan does not catch it (stack-uninit is not
  ASan-instrumented; `ASAN_REPORT.md:118-120`). This is the only
  open compiler-side memory-safety class on v4.x evidence. Severity is
  bounded — silent UB on the *compiler* only, not on emitted user code
  — but it is still UB, and a different allocator could turn it into
  miscompilation.
- **Byte-identity is weaker evidence than the framing implies.**
  `stage2.ll == stage3.ll` proves the compiler is a fixed point of its
  own emitter on its own source. It does not prove the emitter is
  correct; it proves the emitter is *deterministic and stable*. If
  there were a miscompile that the compiler reproduces in itself
  (e.g., a wrong tag layout that consistently round-trips because both
  the emit site and the read site agree on the wrong layout), the
  fixed-point check would not catch it. The orthogonal evidence I rely
  on for actual correctness is (a) `llvm-as` on stage2.ll + stage3.ll,
  (b) `clang -O2 -c` on stage2.ll producing a working stage2 binary
  that successfully recompiles `mnc_all.mn`, (c) the 53/65 golden pass
  through `mnc-stage1`. Together these are strong but not conclusive.
- **Sh.2 fix is correct but narrow.** The Python emitter's `_do_copy`
  now handles the alias-vs-owner distinction for LIST and STR. It
  does not handle MAP / SIGNAL / STREAM / boxed-enum-payload aliasing
  with the same shape — those paths still call `_track_container`
  unconditionally on Copy (lines 2611-2617). I have not been able to
  construct a failing testcase from the v4.135.0 surface, but the
  asymmetry is worth flagging. If a future MAP-of-Strings or
  Stream-of-Lists testcase trips the same alias-extraction pattern, the
  fix shape needs to be extended. **Carry as Sh.2-residual / SE.1 (new
  docket suggestion).**
- **Self-hosted emitter (`mapanare/self/emit_llvm.mn`) still has no
  move-tracking infrastructure.** v4.124.0 explicitly deferred the
  Rt.1 mirror and v4.131.0/v4.132.0 explicitly deferred the Sh.2
  mirror (`MEASUREMENTS.md:102-104`). Today the strict-fixed-point
  metric (stage2 == stage3) holds *because* `mnc_all.mn` does not
  trigger the Sh.2 alias-extraction pattern in its own self-compile —
  not because the self-hosted emitter has the equivalent fix. If a
  future self-hosted module starts using the pattern at scale, stage2
  could regress. Sh.4/5/6/7 carries forward.
- **`mnc-stage2` teardown exit 10** (`FIXEDPOINT_STATUS.md:128-135`).
  The script accepts this because the IR has been flushed before the
  crash. From an IR-correctness perspective this is benign — IR is
  written to stdout before cleanup. But it does mean the binary is not
  a clean-exiting tool, and panel reviewers should not present it as
  one. Tracked since v4.30.0; low-priority but should not be allowed
  to age out of the docket.
- **Dr.1 self-hosted version-string freeze**
  (`mapanare/self/emit_llvm.mn:3523` emits `!0 = !{!"4.127.0"}`)
  remains. Pre-PRE-PANEL audit caught it; deferred to v5.x metadata
  housekeeping. Cosmetic for IR correctness, not for IR provenance.

## Verdict + score rationale

The IR layer at v4.135.0 is materially better than at v4.120.0 by
every metric I track. Three named fixes (Sh.2 LIST, Sh.2 STR, Rt.1)
landed with audited diff shapes; the fixes are at the right layer
(emitter for sanitizer surface, lowerer for type propagation); the
post-fix evidence (valgrind 31 → 5, ASan 23 → 0, goldens 21 → 53,
strict fixed point reached + held) is reproducible and survives
re-sweep. The Sh.2 fix in particular addresses the exact extracted-
alias drop-glue pattern I identified in my v4.114.0 + v4.120.0
reviews, and the diff shape (only-track-on-real-ownership-transfer,
untrack-on-alias) is the inversion of the v4.101.0 default that I had
flagged as overly aggressive. I am moving from 8.3 to 8.9 on this
strength.

I am not at 9.0 because byte-identity is correctness-adjacent, not
correctness-equivalent. The fixed-point metric proves the emitter is a
deterministic stable function of its own source — it does not prove
the function is *the right* function. The overlapping evidence
(`llvm-as` on both stages, `clang -O2` on stage2, 53/65 goldens
through mnc-stage1, integration pipeline 60/64) is what gives me
confidence at 8.9; without the goldens + integration evidence I would
score lower. A 9.5+ would require either (a) a property-based or
semantic-equivalence check between Python-bootstrap output and
stage1 output on a non-trivial corpus (the proxy-divergence metric
from v4.127.0/v4.128.0 was retired without a replacement), or (b)
closure of the Ge.1 generics-init class so that the
compiler-under-valgrind sweep has zero ERRORS.

The grade is **MEETS**. There is no IR-level pathology that should
block v5; the named blockers from my prior reviews are closed; the
fixed-point milestone is real and reproducible. The carry-forwards
are all v5.x-track and none reproduces under the goldens or the
integration pipeline. Per the mechanical rule, this is a clean PASS.

## Carry-forward items

| Docket | Severity | Proposed release target |
|---|---|---|
| Ge.1 (generics monomorphization stack-uninit, 5 valgrind ERRORS in `try_monomorphize_struct` → `fresh_tmp`) | MEDIUM | v4.137.0–v4.140.0 (single-pass `_init_struct_fields` audit) |
| Sh.2-residual / SE.1 (apply alias-vs-owner shape to MAP / SIGNAL / STREAM / boxed-enum-payload Copy paths) | LOW | v4.137.0+ (defensive, no current failing testcase) |
| Self-hosted emitter mirror of Sh.2 + Rt.1 (`mapanare/self/emit_llvm.mn` move-tracking) | MEDIUM | v5.x (depends on self-hosted lowerer feature parity) |
| mnc-stage2 teardown exit 10 (cleanup-path; IR is flushed) | LOW | v5.x |
| Dr.1 self-hosted hardcoded version `!0 = !{!"4.127.0"}` | LOW (COSMETIC) | v5.x metadata sweep |
| Sh.4/5/6/7 (self-hosted async / const / tensor / closure-typed) | LOW | v5.x feature track |

## Comparison to v4.120.0 delta + reasons

v4.120.0: 8.3 PASS WITH NOTES. Three notes: lint debt (An.2),
List<Int> indexing (Qs.1), fixed-point convergence (Cobra/Sh.8/Sh.11).

- **Qs.1** — CLOSED v4.122.0 with audited 1-line lowerer fix +
  regression golden. **+0.2.**
- **Cobra fixed-point blocker** — CLOSED v4.134.0; HOLDS v4.135.0
  with reproducible md5. **+0.2.**
- **Sh.2 (LIST + STR) — the v4.114.0/v4.120.0 extracted-alias
  drop-glue I named** — CLOSED v4.131.0 + v4.132.0 with audited
  `_do_copy` diff. **+0.2.**
- **Lint debt (An.2)** — not closed; carried forward. v4.130.0
  PRE_PANEL_AUDIT confirms. Worth roughly **−0.0** to my IR score
  because lint is not in my domain (Anaconda owns it); my v4.120.0
  deduction was a generalist concern, withdrawn here.
- **New finding: Ge.1.** Opened v4.132.0 by Sh.2 noise-floor
  clearing. **−0.1** because it's net-new compiler-side memory
  unsafety, even if silent UB and out of scope for closeout.

Net: 8.3 → 8.9 (+0.6), grade upgrade NOTES → MEETS clean.
