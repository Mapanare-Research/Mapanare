# Mapanare v5.6.5 — "Ve.1 Fix — parser list-growth surgery, stage3 restored"

> **Close Ve.1 — the stage2 segfault that has been open since v5.4.4.**
> `parse_fn_body` writes 8 B past a 256-byte malloc'd block, causing
> `mnc-stage2` to SIGSEGV before emitting any stage3.ll. v5.5.7's
> valgrind investigation localised the root cause; v5.6.5 does the
> surgery.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.6.4 shipped (Rt.06 closed; all memory tracking
infrastructure in place)
**Estimated work:** 1–2 sessions (~3–4 hours). One surgical bug, but
the investigation phase could branch if the 256-byte allocation turns
out to be something unexpected.
**Owner docket:** Ve.1 (opened v5.4.4; root-caused v5.5.7;
remediation v5.6.5)

---

## Why this release exists

### The stuck state

```
[Stage 0] mnc-stage1: OK
[Stage 1] stage1 → stage2.ll: llvm-as OK
          mnc-stage2: builds
[Stage 2] mnc-stage2 mnc_all.mn → stage3.ll: 0 lines (SIGSEGV)
```

Persists unchanged across v5.4.4 → v5.6.4 (11 releases). Every
release's SESSION_REPORT carries the same "Ve.1 persists" footnote.
`verify_fixed_point.sh --keep` always fails at Stage 2.

v5.5.7's `VE1_INVESTIGATION.md` ruled out:

- Deep recursion (stack ulimit raised to 64 MB / unlimited — still
  crashes)
- Async work (reproduces on pre-async code paths)
- stage2.ll corruption (llvm-as clean)

And pinned the bug to:

```
Invalid write of size 8
  at 0x419DC6: parse_fn_body
  by 0x4197F7: parse_fn_params
 Address 0x7a3c980 is 0 bytes after a block of size 256 alloc'd
   at malloc
   by 0x419D42: parse_fn_body
```

`parse_fn_body` allocates a 256-byte block, then `parse_fn_body`
(8 bytes later in the compiled binary) writes 8 B immediately past
the end of it. 154,355 errors / 42 contexts — pervasive; fires on
every fn definition past the 32nd in any input ≥ ~3.6K LOC.

### Root-cause hypothesis

`256 = 32 × 8` strongly suggests a `List<ptr>` with 32-entry default
capacity that doesn't realloc before the 33rd push.

- Runtime `MN_LIST_INITIAL_CAP = 8` (confirmed in
  `mapanare_core.c:1031`)
- `mn_list_grow` doubles: 8 → 16 → 32 → 64 → …
- At capacity 32, `__mn_list_push`'s `len < cap` check should
  trigger `mn_list_grow` before the 33rd push

The `__mn_list_push` fast path (mapanare_core.c:1158–1172) and slow
path (1174–1210) both appear sound on paper. This suggests:

1. **Hypothesis A (most likely):** The 256-byte block is a
   self-hosted data structure (NOT a runtime `MnList` — those are
   allocated via `mn_list_alloc_buf` which prepends a 16-byte
   header, so a "pure" 256 B is atypical). Look for a hand-rolled
   buffer in `parser.mn` or one of the structs it builds.
2. **Hypothesis B:** A `MnList` that bypasses `__mn_list_push`
   somewhere — direct write via a pre-capacity-grow pointer.
3. **Hypothesis C:** The default-capacity path used by the LLVM
   emitter (rather than the C runtime) starts at 32 for some
   reason.

v5.6.5 Phase 1 resolves the hypothesis with an ASan symbolic
backtrace.

### Reproducer

Smallest crashing input: `mapanare/self/lower.mn` (3.6K LOC).
`mapanare/self/mir.mn` (1.0K LOC) does NOT crash — confirms the
trigger is scale-related (≥32 fn definitions in one file past some
ordering threshold).

---

## Scope

### What ships

#### Ve.1a — ASan-instrumented investigation

Build `mnc-stage1-asan` via `scripts/build_asan.sh`, run it on
`lower.mn`, capture the symbolic backtrace. Expected output:

```
==XXXXX==ERROR: AddressSanitizer: heap-buffer-overflow
WRITE of size 8 at 0x60800000dfa0
    #0 0x... parse_fn_body mapanare/self/parser.mn:<line>
    #1 0x... parse_fn_params mapanare/self/parser.mn:<line>
...
allocated by thread T0 here:
    #0 0x... malloc
    #1 0x... <alloc site> mapanare/self/parser.mn:<line>
    ...
```

Outcome: one specific `.mn` line for the allocation, one specific
line for the invalid write. From these, the 256-byte container is
identified (a `List<X>` with known element type, a fixed buffer, a
struct).

#### Ve.1b — Fix the root cause

Three possible surgical paths depending on what Phase 1 reveals:

**Path 1 — runtime bug in `__mn_list_push`:** A missing
`mn_list_grow` call before the memcpy. Fix in
`runtime/native/mapanare_core.c`. Requires `make build-rt` to pick
up.

**Path 2 — parser writes directly into a list's backing store:**
Replace the direct-write pattern with a call to `__mn_list_push`.
Fix in `mapanare/self/parser.mn`.

**Path 3 — hand-rolled buffer with off-by-one:** Either replace
with a `List<X>` (preferred) or fix the bounds check. Fix in
`parser.mn`.

All three paths lead to the same gate: after the fix,
`mnc-stage1-asan lower.mn` produces zero heap-buffer-overflow
warnings.

#### Ve.1c — Fixed-point validation

`bash scripts/verify_fixed_point.sh --keep` should now produce a
non-empty `stage3.ll`. Two outcomes:

- **STRICT fixed-point** — `stage3.ll == stage2.ll` modulo the
  VERSION placeholder. Celebrated as historic; first STRICT hit
  since v4.134.0.
- **NEAR fixed-point** — `stage3.ll != stage2.ll` but both
  `llvm-as` clean and both compile to a working binary. Also a win
  (v5.3.2 state).

Either outcome closes Ve.1. The line count / define count of
stage3.ll becomes a new metric we can track for regression.

#### Ve.1d — Asan golden sweep + valgrind sweep regression check

Confirm the fix doesn't introduce new UAF/overflow elsewhere:

```bash
ASAN_OUTDIR=/tmp/asan-v5.6.5 bash scripts/run_asan_goldens.sh
VG_OUTDIR=/tmp/vg-v5.6.5    bash scripts/valgrind_all_goldens.sh
```

Expected: 60 CLEAN / 6 CRASH_NO_ASAN / 0 ASAN_ERROR (same as
v5.6.4); 66 WARNINGS_ONLY / 0 ERRORS.

If valgrind drops an error: the fix regressed something. Investigate
before shipping.

### What does NOT ship

- **Any Rt.04 / guard-lift work.** v5.6.6 scope.
- **General parser robustness pass.** If other hand-rolled buffers
  exist, they stay until triggered.
- **`MN_LIST_INITIAL_CAP` tuning.** The cap of 8 is fine; the bug is
  elsewhere.
- **Python bootstrap changes.** Self-hosted emitter only.

---

## Exit criteria

1. `mnc-stage1-asan lower.mn > /dev/null` produces **zero**
   AddressSanitizer findings.
2. `mnc-stage1-asan mnc_all.mn > /dev/null` produces zero ASan
   findings (full corpus, not just lower.mn).
3. `bash scripts/verify_fixed_point.sh --keep` exits 0 with
   `stage3.ll` non-empty and `llvm-as`-clean.
4. ASan UAF sweep: 60 CLEAN / 6 CRASH_NO_ASAN / 0 ASAN_ERROR
   preserved.
5. Valgrind sweep: 66 WARNINGS_ONLY / 0 ERRORS preserved.
6. LSan sweep: no regressions (baseline gate PASSES).
7. Harness 64/66 preserved.
8. stage2.ll line count within ±1% of v5.6.4's 205,446.
9. Non-bootstrap pytest 0 failures.
10. `make lint` clean.
11. `docs/known_issues.md` Ve.1 row flipped to **CLOSED v5.6.5**.
12. `docs/roadmap/v5/PARITY_GAPS.md` Ve.1 entry (if present) marked
    closed.

---

## Design decisions

### D1 — ASan first, bisect second

The valgrind trace at v5.5.7 pinned the bug to `parse_fn_body`, but
valgrind's "0 bytes after a block of size 256" doesn't identify the
allocation site by source line. ASan does. Run ASan first; fall
back to `git bisect` only if ASan's trace is inconclusive.

### D2 — Don't refactor parser.mn

Even if the fix reveals questionable code in `parse_fn_body`, the
surgery should be minimal: change the one allocation/push pattern
that's broken, preserve the rest. Larger refactors go into a
dedicated parser-cleanup arc (potentially v5.7.x).

### D3 — Runtime vs parser fix — pick the one with narrower blast radius

If the root cause is in `__mn_list_push`, fixing the runtime is the
cleaner call (one fix covers all List users). If it's in
`parser.mn`'s use of a hand-rolled buffer, the parser fix is
narrower (one bug site). Check which has the lower risk of
regressing unrelated paths.

### D4 — No speculative "also grow earlier" optimizations

If the fix is in `__mn_list_push`, don't raise `MN_LIST_INITIAL_CAP`
or add speculative capacity preallocation. Those are perf changes
masquerading as safety fixes. Fix the bug; measure the baseline.

### D5 — STRICT vs NEAR fixed-point

v5.6.4 is NEAR (stage3 empty). Once v5.6.5 produces non-empty
stage3, compare to stage2:

- If they differ only in VERSION placeholder → STRICT. Celebrate.
- If they differ in more lines → diff the output. Common NEAR
  causes: non-determinism in iteration order, VERSION macro in
  more than one place, or a codegen quirk that stabilises on a
  second pass. NEAR is fine; Ve.1 is still CLOSED. A future release
  can chase STRICT if desired.

### D6 — How other languages handle list growth

- **C++ `std::vector`** — `size() < capacity()` invariant with
  `push_back` grow.
- **Rust `Vec<T>`** — `len < cap` with `push` → `grow_amortized`.
- **Go `slice`** — append rebuilds with `growslice` when
  `len == cap`.
- **Python `list`** — over-allocates per `list_resize`.

Mapanare's `MnList` follows the C++ pattern: `__mn_list_push` checks
`len < cap`, calls `mn_list_grow` when full. Standard; not the
place bugs usually hide — but worth confirming the fast-path grow
condition actually fires at the 32 → 33 boundary.

---

## Risks

- **R1 — Root cause is not what we think.** Valgrind says 256 B
  buffer at `parse_fn_body`, but the actual allocation may come
  from a called function (inlined or not). ASan's symbolic trace
  resolves this, but if ASan gives a different story from valgrind,
  we regroup. *Mitigation:* Phase 0 runs both valgrind and ASan on
  the same input; if they disagree, document and investigate before
  proceeding.
- **R2 — Fix introduces new memory behaviour.** Any change to
  `__mn_list_push` or a hot parser helper could affect every
  Mapanare program. *Mitigation:* full ASan + valgrind sweep gate
  before shipping; harness 64/66 gate; pytest 0-regression gate.
- **R3 — stage3 non-empty but diverges wildly from stage2.** If
  stage3 is 2× stage2's size or defines a different set of
  functions, the "fix" may have papered over the crash without
  actually fixing lower-layer state. *Mitigation:* diff stage2 vs
  stage3; if the diff is >1% non-VERSION lines, investigate before
  claiming closure.
- **R4 — Fix lands but Ve.1 reproduces elsewhere.** Another
  hand-rolled buffer with a similar off-by-one. *Mitigation:* Phase
  3 runs ASan on the full `mnc_all.mn`, not just `lower.mn`. If a
  second error pops, triage (this could become v5.6.5.1 or v5.6.7).
- **R5 — Python bootstrap has a similar latent bug.** Our Python
  emitter could write `parse_fn_body`-equivalent code into mnc-stage1
  that corrupts on parse. *Mitigation:* unlikely (Python uses
  `list.append`, not raw buffer writes), but worth spot-checking
  `parser.py` / `lower.py` for similar patterns after the fix.
- **R6 — v5.4.4 intended to fix Ve.1 and regressed it.** Our fix
  could similarly regress it further or make the stage2 segfault
  *worse* (silent miscompilation instead of crash). *Mitigation:*
  stage2.ll diff against v5.6.4; if lines grew by >10%, the fix is
  likely over-scoped.

---

## What NOT to do

- **Do not "fix" by raising `MN_LIST_INITIAL_CAP`.** That papers
  over the bug; the capacity-grow path still has the off-by-one
  and will fire at a higher threshold later.
- **Do not disable the fast-path in `__mn_list_push`.** The fast
  path is the hot-path performance optimization from v4.151.0;
  regressing it is a perf red flag.
- **Do not refactor `parse_fn_body`.** Minimal surgical fix only.
- **Do not ship without non-empty stage3.** If Phase 3 still fails,
  keep iterating or revert the fix and rescope.
- **Do not delete the v5.5.7 VE1_INVESTIGATION.md.** Keep it as
  reference; update `docs/known_issues.md` Ve.1 row to point to it
  and to v5.6.5/SESSION_REPORT.md.
- **Do not skip the full 66-golden ASan/valgrind sweep.** Ve.1's
  fix touches parsing code, which every compiled program exercises.
  A regression would be silent without the full sweep.
