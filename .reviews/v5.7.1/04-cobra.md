# Panel v5.8.0 — Cobra (Bootstrap / Self-Hosted)

**Score:** 9.6 / 10
**Grade:** EXCEEDS
**Delta vs v5.2.0:** +0.8

## Summary

The fixed point is restored. La Culebra Se Muerde La Cola — across the
whole 66-test corpus.

At v5.2.0 I gave 8.8 MEETS with a -0.6 ceiling deduction because In.1
broke the fixed point from NEAR to BROKEN. The v4.134.0 strict fixed
point was the crown jewel of the self-hosted compiler, and I said
restoring it would return the score to 9.2+. It is restored. I verified
personally: `wc -l /tmp/stage2.ll /tmp/stage3.ll` returns
217,879 lines each; `diff` returns exactly 4 lines, all attributable
to the VERSION-metadata placeholder. `llvm-as /tmp/stage2.ll` and
`llvm-as /tmp/stage3.ll` both produce clean bitcode. The compiler
that compiled the compiler that compiled itself produces the same
text the source produces. Across 217,879 lines of IR. That is the
metric.

But this arc did more than restore. The 12 closed goldens (Sh.4 × 5
async, Sh.6 × 5 tensor, Sh.7 × 1 closure-typed, B × 1 or-pattern) are
verified individually — every per-feature claim checked out under
grep against HEAD. This is the first time in project history the
native goldens are 100% green; no caveats, no asterisks. The
PARITY_GAPS.md document I demanded at v4.154.0 has held up across
nine releases of feature work and memory-safety closeout. Every
docket I sampled appears in the inventory or the Historical section
with a closure release citation and a verifiable grep target. The
27% ledger undercount that was my benchmark complaint at v4.154.0 is
gone — when I cross-checked v5.6.x dockets (Ve.1 / Ve.2 / Ve.3 /
Ve.4 / Lk.1 / Rt.04) against the SESSION_REPORTs and the
PARITY_GAPS.md / known_issues.md tables, the numbers matched in both
directions.

This is the first EXCEEDS I have given since v4.154.0. The score
reflects three things: fixed-point restoration (the load-bearing
metric in my domain), the engineering discipline shown across the
v5.6.x bug closeout arc (Ve.1 → Ve.4, with one HONEST RESCOPE on
Rt.04 rather than a false closure), and the quality of the
PARITY_GAPS.md tracking. The 0.4 point I'm not awarding is
attributable to two things: Rt.04 remains OPEN as a v6.0 carry
(legitimate — multi-level alias analysis is the borrow checker's
job, not a v5.x patch), and the v5.6.4 → v5.6.10 transient
fixed-point break could have been gated more tightly in the
sanitizer matrix (see scoring section).

## Verification I performed personally

Following the v5.2.0 lesson — never trust SESSION_REPORTs on
fixed-point claims — every load-bearing metric was verified at HEAD.

### Fixed point (the crown jewel)

```
$ wc -l /tmp/stage2.ll /tmp/stage3.ll
  217879 /tmp/stage2.ll
  217879 /tmp/stage3.ll
  435758 total

$ diff /tmp/stage2.ll /tmp/stage3.ll
217879c217879
< !0 = !{!"5.8.0"}
---
> !0 = !{!"__MN_VERSION__"}

$ diff /tmp/stage2.ll /tmp/stage3.ll | wc -l
4

$ llvm-as /tmp/stage2.ll -o /tmp/stage2.bc
stage2 llvm-as OK

$ llvm-as /tmp/stage3.ll -o /tmp/stage3.bc
stage3 llvm-as OK
```

**Status: NEAR FIXED POINT.** stage2.ll == stage3.ll byte-identical
except the single VERSION metadata line. Both pass `llvm-as` cleanly.
The diff is the same shape Dr.1 produced at v4.134.0 — cosmetic, not
structural. This is the pattern I have always called acceptable
steady state.

The line count (217,879) is also worth noting. At v5.2.0 stage2.ll
was 120,956 lines and `llvm-as`-rejected. At v5.3.0 panel baseline
stage2.ll grew but In.1 still produced invalid SSA. The current
217,879 lines reflects the v5.4.0 → v5.7.0 feature additions
(drop-glue infrastructure, coroutine emission, tensor surface,
closure-typed routing) compounded on a clean fixed-point base. Nearly
double the v5.2.0 line count, fully self-consistent.

### Goldens

```
$ python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
[...]
PASS 66_qualified_type_ref 21L->46L 4bb 33stk 8ms (1 fns) stg1:2fns 9ms
All 66 tests passed in 2.8s
```

**66/66.** First time in project history. The 12 closed since v5.3.0
break down as documented in MEASUREMENTS.md §2: 5 async (55–59), 5
tensor (49–53), 1 or-pattern (51_match_guards_and_or), 1 closure-typed
(64_closure_typed). Every one of these was a feature gap in my domain
at v5.2.0.

### Module growth

```
$ wc -l mapanare/self/*.mn | tail -1
  48269 total
```

Up from 41,195 at v5.2.0 baseline (+7,074, +17.2%). Breakdown:
- v5.4.0–v5.4.4 drop-glue infrastructure across emit_llvm.mn (+~600 LOC)
- v5.5.4–v5.5.7 LLVM-coroutine emission + scheduler integration (+~400 LOC)
- v5.6.0–v5.6.3 tensor surface (literals + indexing + broadcast +
  slicing + reductions) across parser.mn / lower.mn / emit_llvm.mn
  (+~1,800 LOC)
- v5.6.4 tensor drop-glue
- v5.6.5–v5.6.13 memory-safety closeout (Ve.1 / Ve.2 / Ve.3 / Ve.4 /
  Lk.1)
- v5.7.0 closure-typed parameter routing across parser / lower /
  emit / mir_opt (~150 LOC)

This is the pattern I want: feature work in `.mn`, not in Python.
The Python bootstrap stays the reference; the self-hosted compiler
catches up.

### Source drift v5.7.1 → HEAD

```
$ git log --oneline v5.7.0...HEAD | head -5
a6456a5 v5.7.1: SPEC + docs polish — pre-panel + culebra clean baseline

$ git diff a6456a5..HEAD -- mapanare/ runtime/ | wc -l
0
```

Zero source drift since v5.7.1 commit. v5.8.0 is honestly a docs/
polish release; the compiler I am reviewing is byte-identical to the
v5.7.1 release artifact at the source level. Only the embedded
VERSION string differs. This is the right release discipline — the
panel reviews what shipped, not what is being staged.

## What improved since v5.2.0

### Fixed-point regression closed (BROKEN → NEAR)

The narrative is worth recording for the project history:

1. **v5.3.2** — In.1-stage2 closure. The `clone_instr_for_inline`
   helper was extended from a partial set of instruction kinds to all
   30+ MIR variants, mirroring `replace_uses_in_instr`. I verified
   the helper at `mapanare/self/mir_opt.mn:864` and counted 36
   instruction-kind string-matches in the file — that's the
   clone+rename matrix. This was the right fix for my MEDIUM
   In.1-stage2 carry-forward from v5.2.0.

2. **v5.5.4–v5.5.7** — async coroutine emission (Sh.4). Real LLVM
   coroutines (`presplitcoroutine` + `@llvm.coro.id/begin/save/
   suspend/end` pipeline) require non-trivial cooperation between
   `mir_opt.mn::clone_instr_for_inline` (rename `await_suspend` /
   `block_on` operands when inlined into `block_on(...)`) and
   `emit_llvm.mn` (async-aware function prologue / `coro.final` /
   `coro.cleanup` / `coro.ret`). I verified 28 `llvm.coro`
   references in `emit_llvm.mn` and 2 `presplitcoroutine`
   attributes. The coroutine arc transiently broke fixed-point during
   v5.5.x but stabilized by v5.5.7.

3. **v5.6.5–v5.6.10** — Ve.1 / Ve.2 / Ve.3 closures and the
   memory-safety arc. v5.6.4 introduced tensor drop-glue plus
   `is_tensor_allocating_fn`; the resulting stage2.ll layout shift
   exposed two latent bugs (Ve.1 `parse_fn_body` overflow, Ve.3
   `clone_instr_for_inline`'s List<Instruction> drop-glue UAF on
   `List<Enum>` returns). Fixed-point was BROKEN across this window;
   the SESSION_REPORTs are honest about it. Critically, the bug
   diagnosis was real engineering — Ve.1 was traced to a 256-byte
   fallback in `llvm_type_size`, Ve.3 to a multi-level aliasing class
   in inliner-cloned Allocas, Ve.4 to an `elem_size` mismatch
   between `__mn_list_push` writes and inline-GEP-i64 reads. None of
   these are workarounds; they are root-cause closures.

4. **v5.6.11** — Ve.4 closure restores fixed-point. I verified the
   fix at `emit_llvm.mn:2585-2606` (read side) and 2689 (write side
   symmetric):

   ```
   v5.6.11 Ve.4 — use runtime elem_size for the offset, not a constant
   i64 stride. The 7 Ve.2 residual sites (`build_match_arms` and 5
   others) allocate `List<Int> = []` with elem_size=384 (Lk.1 floor);
   `__mn_list_push` writes at idx * 384 while a constant-stride GEP
   would read at idx * 8 — mismatch produces garbage reads of
   intra-buffer spillage. Loading elem_size from list field 3 makes
   the read consistent with the push regardless of allocator stride.
   ```

   The 14-LOC fix at the structural site is the kind of patch I
   want to see — it doesn't paper over the symptom (broken match
   arms in self-compiled lowerer), it doesn't blanket-disable a
   pass, it identifies the arithmetic invariant that was violated
   and restores it.

5. **v5.6.12** — Lk.1 closure via destination-passing in
   `lower_let`. Verified `lower_list_typed_into` and
   `lower_struct_new_into` helpers at `lower.mn:3522` and 3695, with
   call sites at 790 and 828. The pattern is rustc-style result
   location semantics — pre-compute the var's alloca name, lower
   `ListInit` directly into it, skip the post-emit Alloca + Store
   pair that would create the duplicate `%t<N>.addr` alloca. This is
   structurally the right answer; I would have accepted "leak stays,
   borrow checker fixes it in v6.0" but the team did better.

The In.1-stage2 closure I demanded at v5.2.0 holds, and was re-tested
through every v5.5.x async / v5.6.x memory release. NEAR is preserved
at HEAD.

### All four Sh.* feature gaps closed — 66/66

Per-feature verification:

**Sh.4 (async, v5.5.4–v5.5.7).** `grep -c "presplitcoroutine\|llvm.coro" mapanare/self/emit_llvm.mn` returns 30. The 5 async goldens (55_async_basic, 56_async_await, 57_real_await, 58_async_file_io, 59_async_fanout) all pass through `mnc-stage1`. MEASUREMENTS.md §5 documents valgrind / ASan / LSan / TSan all clean across the 5 goldens at HEAD. The TSan claim is the strongest one — async + multi-threading + zero races is the highest sanitizer bar in the corpus.

**Sh.6 (tensor, v5.6.0–v5.6.3).** `grep -c "__mn_tensor_\|tensor_reduction\|lower_tensor_slice" mapanare/self/lower.mn` returns 29. The reduction helpers (`is_tensor_reduction_method`, `tensor_reduction_ret_ty`, `lower_tensor_slice`) are present at the documented locations. `lower.mn` total: 4,814 lines (was 3,602 at the v5.2.0 baseline, +1,212 lines / +33% — entirely Sh.6 feature surface). The 5 tensor goldens (49_tensor_literal, 50_tensor_indexing, 51_tensor_broadcast, 52_tensor_slicing, 53_linear_regression) produce byte-identical output to the Python bootstrap. v5.6.0's MEASUREMENTS.md hero metric was `49_tensor_literal: 1 3 1 3 2 6 1 6 2 3 3 8 1 8 3 20 -1 -2.5` — that's the actual stdout from a self-hosted-compiled binary. Stepped slicing (`a[::2]`) and tensor reshape / mutable views remain out of scope, correctly tracked as separate v5.x / v6.0 feature work in PARITY_GAPS.md.

**Sh.7 (closure-typed parameters, v5.7.0).** `grep -n "lookup_var(fn_name)\|TK_FN()" mapanare/self/lower.mn` returns line 2468. I read the surrounding code at lines 2460–2477 — the indirect-call routing is exactly what the SESSION_REPORT describes:

```mn
let var_lookup: Option<Value> = lookup_var(st, fn_name)
match var_lookup {
    Some(addr_v) => {
        if addr_v.ty.kind == TK_FN() {
            let load_r: LowerResult = make_value(st, addr_v.ty, fn_name + "_val")
            let load_s: LowerState = emit_instr(load_r.state, Instruction::Load(load_r.value, addr_v))
            let dr_ind: LowerResult = make_value(load_s, mir_unknown(), "t")
            let s_ind: LowerState = emit_instr(dr_ind.state, Instruction::Call(dr_ind.value, load_r.value.name, args))
            return new_lower_result(dr_ind.value, s_ind)
        }
    },
    _ => {}
}
```

That's the indirect-call pattern: load the fn-typed local, call through the loaded SSA name. Verified the matching `emit_call_ir` recognition at `emit_llvm_ir.mn:236,243` (`if callee.starts_with("%")` — both `emit_call_ir` and `emit_call_void` paths). The four-layer fix described in the SESSION_REPORT (parser multi-param lambda, lower indirect-call, emit `%`-prefixed callee, mir_opt rename Call's fn_name) is all present at HEAD.

**B (or-pattern + None, v5.7.0).** `_is_enum_variant_name` at `mapanare/semantic.py:1296`:

```python
def _is_enum_variant_name(self, name: str) -> bool:
    """Check if a name refers to an enum variant in any visible enum."""
    # v5.7.0: built-in Option/Result variants are not user-defined
    # enum symbols; recognize them here so or-pattern binding-set
    # checks treat `None` (and `Some`/`Ok`/`Err` if ever nullary)
    # as variant references rather than fresh bindings.
    if name in ("None", "Some", "Ok", "Err"):
        return True
    # Walk all symbols looking for enums with a matching variant
```

Plus `lower.py:1647` carrying the matching v5.7.0 comment (`bare 'None' identifier — KW_NONE only matches`). This is the parity I want — when the Python bootstrap is patched, the self-hosted side gets the matching commit citation. The self-hosted side already had the right behavior (per SESSION_REPORT, `bind_pattern` doesn't have the over-strict check) so no mirror was needed; the right call.

### PARITY_GAPS.md tracking discipline holds

The 27% undercount finding from v4.154.0 was my benchmark for this
release. I cross-checked the v5.6.x docket sequence (Ve.1 / Ve.2 /
Ve.3 / Ve.4 / Lk.1 / Rt.04) against three sources:
SESSION_REPORTs, PARITY_GAPS.md, known_issues.md. The numbers match
in all three directions.

Specifically:

- **Ve.1**: PARITY_GAPS.md shows CLOSED v5.6.5 in known_issues.md "Closed since v5.4.0" block. ✓
- **Ve.2**: PARITY_GAPS.md "Closed since v5.4.0" block (v5.6.7 partial → v5.6.12 closed). ✓
- **Ve.3**: PARITY_GAPS.md row 90 CLOSED v5.6.9 (drop-glue UAF on List<Enum> returns). ✓
- **Ve.4**: PARITY_GAPS.md row 91 CLOSED v5.6.11 (elem_size mismatch). ✓
- **Lk.1**: PARITY_GAPS.md row 92 CLOSED v5.6.12 (destination-passing in lower_let). ✓
- **Rt.04**: known_issues.md row 47 OPEN, deferred v6.0 (multi-level alias analysis). ✓

Every closure has a verifying grep / pytest target documented. Every
deferral has a stated cost (e.g. Rt.04 → 62_list_output stays LEAK,
baseline-gated). The "Close policy" section that I demanded ("An item
does not close just because a SESSION_REPORT says it is done") is
still in the document at lines 198-212.

The historical entries are detailed — the Own.1 phase rows (lines
237-243) span six releases of progress with verification artifacts
preserved at each step. I did not have to chase the closure
breadcrumbs across SESSION_REPORTs; the inventory is the
single-source-of-truth I asked for.

This is exactly the tracking discipline that needs to live across
v6.0+. The pattern works.

### Sanitizer matrix preserved

MEASUREMENTS.md §5 documents:

- valgrind 63 CLEAN / 2 ERRORS (third-party Mesa/Vulkan, same class as v5.3.0) / 1 LINK_FAIL (Python bootstrap path, not native)
- ASan 74/74 C tests pass (Stream-C carry-forward closed at v5.3.1)
- TSan 74/74 C tests pass (same)
- LSan baseline: 0 regressions, all Mapanare-code classes leak-clean; only documented third-party + multi-level-alias carry-forwards remain

The valgrind +1 CLEAN delta vs v5.3.0 (62 → 63) reflects the
addition of new test programs in the corpus (66 vs ~62 pre-v5.5.4
era in some classes). Memory-safety parity is preserved across the
full v5.3.1 → v5.7.1 arc.

The ASan / TSan delta — from 3 fail at v5.3.0 to 0 fail at v5.7.1 —
closes the Stream-C carry-forward I deducted for at v5.3.0. This is
work that happened pre-v5.3.1 but it earns credit in this panel since
v5.2.0 was my last delta point.

## What held

- **Bootstrap pytest 225 passed / 0 failed** (per SESSION_REPORT, was
  13 baseline pre-v5.7.0 including 51_match_guards_and_or). Not
  re-run for v5.8.0 due to zero source drift; I accept this.

- **stage2.ll grew from 120,956 (v5.2.0, BROKEN) to 217,879 (NEAR)**
  — the growth is fully accounted for by v5.4.x drop-glue, v5.5.x
  coroutine emission, v5.6.x tensor surface, v5.7.0 closure-typed
  routing. Per-release line-count deltas in CLAUDE.md follow a
  monotonic pattern that I cross-checked against MEASUREMENTS.md
  Table 4.1.

- **Binary size 6,311,072 bytes** (was 3,648,672 at v5.2.0, +73%).
  Within expectations for the feature additions; not a concern.

- **`mnc-stage1 --version` reports `mapanare 5.8.0`**. The v5.2.0
  stale-binary deduction does not apply at v5.7.1 — the binary on
  disk reports the current VERSION.

## What concerns me

- **v5.6.x transient fixed-point break is documented but the gating
  could be tighter.** Across v5.6.4 → v5.6.10 (7 releases),
  `verify_fixed_point.sh` reported BROKEN or empty stage3.ll. The
  SESSION_REPORTs are honest about this — every release that broke
  fixed-point notes it explicitly, and v5.6.11 closes Ve.4 with the
  hero metric "first NEAR since v5.6.4". But the PROMPT 1% / 3%
  growth budgets that were enforced for stage2.ll line counts didn't
  have a corresponding fixed-point gate. A `verify_fixed_point.sh`
  invocation in the CI matrix that fails the merge if NEAR is lost
  would have made this easier to catch.

  This is the same class of concern I raised at v5.2.0 (In.1 closed
  without fixed-point gate). The v5.6.x team caught it themselves
  this time, and the closure was mechanically correct, so the
  deduction is small. But the gate is still worth adding for v6.0.

- **Rt.04 remains OPEN as v6.0 carry.** `62_list_output` still leaks
  at struct→list→string (depth 2) — 13 obj / 346 B per LSan, baseline
  -gated. The structural fix needs the v6.0 borrow checker to walk
  field aliases recursively. This is the right deferral; the v5.6.6
  RESCOPE explicitly chose UAF prevention over leak prevention when
  the one-level walk produced a real heap-use-after-free.

  No deduction for this — the engineering is honest. But Rt.04 is
  the single MEDIUM that will carry into v6.0, and the borrow
  checker design needs to land it as a first-class gate.

- **In.1-stage2 row in PARITY_GAPS.md is in "Optimizer" table, not
  expanded into v5.6.x docket family.** Minor: `In.1` shows CLOSED
  v5.1.2 in PARITY_GAPS.md and that's what closed at v5.1.2, but the
  v5.3.2 `clone_instr_for_inline` extension that re-closed
  In.1-stage2 isn't given its own row — it's folded into the In.1
  closure. The MEASUREMENTS.md §3 carry-forward tally correctly lists
  In.1-stage2 CLOSED v5.3.2, so the tracking exists; the
  PARITY_GAPS.md row could be more precise.

  Not load-bearing. The closure is real and verifiable.

- **The Sh.4 dual-namespace ambiguity** (PARITY_GAPS.md notes lines
  144-155): `Sh.4` historically referred to async self-hosted lowering
  in `known_issues.md`, but to tensor reshape in PARITY_GAPS.md
  feature-gap section. The v5.7.1 doc polish disambiguates it, but
  this is the kind of cross-doc ID collision that PARITY_GAPS.md
  exists to prevent. A monotonic increasing docket scheme (Sh.4a
  / Sh.4b or Sh.4-async / Sh.4-tensor) would be cleaner. Cosmetic;
  no deduction.

## Score breakdown

Prior: 8.8 (MEETS) at v5.2.0, with 0.4 ceiling deduction from BROKEN
fixed point.

### Positive deltas

- **+0.4** — Fixed-point restoration. The single biggest carry-forward
  from v5.2.0 is closed. NEAR is preserved at HEAD (verified
  personally: 217,879 == 217,879, 4-line VERSION-only diff,
  `llvm-as` clean both stages). This restores the v5.2.0 ceiling
  deduction.

- **+0.2** — Sh.4 closure (5 async goldens). LLVM-coroutine emission
  in self-hosted is the largest feature arc since the original v4.x
  enum-inline port. Real coroutines, real scheduler integration,
  TSan-clean. The v5.5.4 → v5.5.7 sequence treated this as a phased
  rollout (real coroutines first, scheduler-driven AwaitSuspend
  next, scheduler-driven BlockOn after, sanitizer hardening last) —
  exactly the staging discipline I praised at v5.2.0 for the E8
  audit.

- **+0.15** — Sh.6 closure (5 tensor goldens). Four phases (literals,
  indexing, broadcast, slicing+reductions) across v5.6.0 → v5.6.3,
  each closing a self-contained subset of the tensor surface. Per-
  phase verification (every phase has its golden checked).

- **+0.1** — Sh.7 + B closure → 66/66. First time in project
  history. The closure-typed routing fix is structurally elegant —
  load the fn-typed local, call through the loaded SSA name. The B
  fix mirrors v4.134.0 Sh.12 from the Python side. Both verified at
  HEAD.

- **+0.1** — PARITY_GAPS.md tracking discipline holds. The 27%
  undercount complaint is fully addressed. Every v5.6.x docket I
  cross-checked against three sources matched. Historical entries
  are detailed enough that I did not need to chase SESSION_REPORTs.
  This is process credit — earned by sustaining the discipline
  across 28 releases.

- **+0.05** — Honest RESCOPE on Rt.04. The v5.6.6 release attempted
  the one-level field walk, reproduced a UAF in `62_list_output`,
  and reverted to a leak-with-baseline-gate rather than shipping
  the broken fix. The SESSION_REPORT is explicit about the empirical
  verification at three growth thresholds. This is the engineering
  discipline I want; many projects would have shipped the partial
  fix and let UAF-into-prod become the next reviewer's problem.

- **+0.05** — Memory-safety closeout (Ve.1 → Ve.4 + Lk.1). Five
  separate root-cause closures across v5.6.5–v5.6.12, each at the
  structural site. Ve.1 (256-byte fallback in `llvm_type_size`),
  Ve.4 (`elem_size` stride mismatch), Lk.1 (destination-passing
  semantics) — all real engineering, none of them workarounds.

### Negative deltas

- **-0.05** — v5.6.x transient fixed-point break could have been
  gated tighter. The team self-caught it; deduction is small but
  the lesson is worth recording for v6.0 — `verify_fixed_point.sh`
  belongs in the merge gate.

- **-0.05** — Sh.4 dual-namespace ambiguity. Cosmetic but real.

- **-0.05** — Bootstrap pytest not re-run for v5.8.0. With zero
  source drift this is correct, but the SESSION_REPORT-only citation
  is the same shape as the v4.153.0 ledger pattern I flagged. A
  one-line CI gate ("if VERSION changed, bootstrap pytest re-runs")
  would close this.

### Arithmetic

- Base: 8.8
- Positives: +0.4 + 0.2 + 0.15 + 0.1 + 0.1 + 0.05 + 0.05 = +1.05
- Negatives: -0.05 - 0.05 - 0.05 = -0.15
- Raw: 8.8 + 1.05 - 0.15 = **9.7**

Adjustment: I am applying a -0.1 ceiling for the v5.6.x transient
fixed-point break. Even though it was self-caught and self-restored,
the principle from v5.2.0 still applies: fixed-point regressions cost
ceiling. The deduction is much smaller this time because the closure
was mechanically correct and the gate failure was caught internally,
not by an external panel.

Ceiling-adjusted: **9.6**.

This is the highest score I have given since v4.144.0 (when fixed-
point was strict). The 0.4 gap to a perfect 10 reflects: Rt.04 OPEN
(v6.0 deferred, legitimate); fixed-point still NEAR not STRICT (Dr.1
class drift, cosmetic); and the v5.6.x transient gate failure noted
above.

## Carry-forward (for v5.8.0+)

| ID | Severity | Scope |
|---|---|---|
| Rt.04 | MEDIUM (v6.0) | Multi-level alias analysis for drop-glue. Structural fix is the borrow checker. 62_list_output stays LEAK (baseline-gated). |
| Sh.5 | LOW | `const` in fn bodies; v5.x feature track |
| Sh.9a / 9b | LOW | Async emitter quirks; documented workarounds |
| Gr.1 | LOW | Multi-line literal parse-error |
| Li.1 | LOW | LICM live-golden regression; v6.0 |

That is 5 items, down from 4 + Sh.4-7 expansion at v5.2.0. The
Sh.* expansion bucket is gone — every Sh.* I tracked is closed. The
new MEDIUM (Rt.04) is honestly v6.0 borrow-checker work; it is not a
v5.x defer-and-forget pattern.

## The fixed-point lecture, revisited

At v5.2.0 I wrote: "La Culebra Se Muerde La Cola. The snake eats its
own tail. That phrase meant something — it meant the compiler had
reached the point where it could reproduce itself, byte for byte,
through three stages of self-compilation."

The snake's jaw is healed. The compiler now produces 217,879 lines
of LLVM IR; that text is byte-identical when the compiler compiles
itself a second time, modulo a single VERSION metadata line. Both
texts pass `llvm-as` cleanly. The closure-typed parameter routing
that produces `call %fn(...)` for fn-typed locals is the same on the
second self-compile as the first. The drop-glue for `List<Enum>`
returns is the same. The match-arm lowering with the elem_size-aware
GEP is the same. The async coroutine emission — `presplitcoroutine`
attribute, `@llvm.coro.id/begin/save/suspend/end` pipeline — is the
same.

This is what the metric measures: that the compiler is a fixed point
of itself across the full v5.4 / v5.5 / v5.6 / v5.7 surface. Every
feature I tracked at v5.2.0 (Sh.4–7, B, Own.1 P2, In.1-stage2, Rt.03
loop-reassignment, Rt.05 inner-coroutine handle) is either closed and
verified at HEAD, or correctly deferred to v6.0 with a structural
reason.

The v5.6.x bug-closeout arc was the highest engineering bar in this
domain since the original v4.x enum-inline port. Six separate root-
cause closures across nine releases (Ve.1, Ve.2, Ve.3, Ve.4, Lk.1
plus the Rt.04 RESCOPE). None of them shortcuts. None of them
"closed in SESSION_REPORT but not in code." Per-release per-docket
empirical evidence with sanitizer + golden + fixed-point gates.

This is the closeout discipline I have asked for since v4.144.0. It
is here. The fixed point is here. 66/66 is here. EXCEEDS is here.

Now ship v6.0 with the borrow checker.

---

## Reproducibility

```bash
# Fixed-point verification (verified 2026-04-26)
wc -l /tmp/stage2.ll /tmp/stage3.ll
# 217879 each
diff /tmp/stage2.ll /tmp/stage3.ll | wc -l
# 4 (VERSION-only)
llvm-as /tmp/stage2.ll && llvm-as /tmp/stage3.ll
# both OK

# Goldens
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
# All 66 tests passed in 2.8s

# Module sizes
wc -l mapanare/self/*.mn | tail -1
# 48269 total

# Sh.4 verification
grep -c "presplitcoroutine\|llvm.coro" mapanare/self/emit_llvm.mn
# 30

# Sh.6 verification
grep -c "__mn_tensor_\|tensor_reduction\|lower_tensor_slice" mapanare/self/lower.mn
# 29

# Sh.7 verification (closure-typed)
grep -n "lookup_var(fn_name)\|TK_FN()" mapanare/self/lower.mn
# 2468

# Sh.7 emit_call_ir % prefix
grep -n "starts_with(\"%\")" mapanare/self/emit_llvm_ir.mn
# 236, 243

# B verification (or-pattern + None)
grep -n "_is_enum_variant_name" mapanare/semantic.py
# 1286, 1296 — with v5.7.0 None/Some/Ok/Err short-circuit at 1302

# v5.6.11 Ve.4 fix
grep -n "elem_size" mapanare/self/emit_llvm.mn
# 933, 1470, 2281, 2590, 2592, 2595, 2597, 2689 (Ve.4 sites)

# v5.6.12/13 destination passing
grep -c "lower_list_typed_into\|lower_struct_new_into" mapanare/self/lower.mn
# 7

# Source drift v5.7.1 → HEAD
git diff a6456a5..HEAD -- mapanare/ runtime/ | wc -l
# 0

# Binary version
mapanare/self/mnc-stage1 --version
# mapanare 5.8.0

# PARITY_GAPS.md ledger discipline
grep -c "v5.7.0\|v5.6.\|v5.5.\|v5.4." docs/roadmap/v5/PARITY_GAPS.md
# 13+ — all closures cited with release
```

## Final score

**9.6 / 10 — EXCEEDS.** Delta vs v5.2.0: **+0.8**.
