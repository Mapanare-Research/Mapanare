# Rattler v4.120.0 Review — LLVM / codegen

## Score: 8.3 / 10
## Verdict: PASS WITH NOTES

## Context: v4.114.0 → v4.120.0

At v4.114.0 I gave **8.2 PASS WITH NOTES**. Phase D had closed the
big docket items but the v4.112.0 naming churn and the `64_closure_
typed` -O2 miscompile I pushed to **Rt.1** were still fresh. The
v4.114.1 patch landed the Rt.1 emitter signature fix (2-arg lambda:
`define internal void @lambda4(ptr, ptr, ptr)` vs caller `call i64
%cfn(ptr, i64, i64)`). Between the patch and today, I get:

- Phase E (3 releases): async I/O demos shipped, docs refreshed,
  testing swept. **Zero changes to the IR emitter or LLVM pipeline.**
- Phase F (2 releases): final benchmark + retrospective. Also zero
  IR changes.

So the IR layer I grade today is **the same IR layer I graded at
v4.114.1**. If my v4.114.0 score was 8.2, either (a) my reading was
right and nothing has materially changed, or (b) I was missing
something. Let me re-sweep before deciding.

I re-ran the relevant checks on 2026-04-14.

---

## Primary lens — Golden IR validity

### mnc-stage1 golden rate: **26/64 strict / 39/64 effective**

`scripts/test_native.py --stage1 mapanare/self/mnc-stage1` on
2026-04-14: **26 passed, 38 failed in 6.3 s**. Identical to
v4.114.0. Zero regressions, zero new unblocks.

The 38 failures are catalogued in `GOLDEN_FAILURES.md` — 10 `__mn_
str_starts_with` crashes (Sh.2), 5 async-missing (Sh.4), 5 tensor-
missing (Sh.6), 2 const-missing (Sh.5), 1 closure-typed (Sh.7), 2
`lower_expr` crashes, 5 misc. Every failure has a docket. **None
re-opens a v4.99.0 item.**

13 of the 38 are Category A — same semantic output, bootstrap
inlines more. I re-verified three at random (`05_for_loop`,
`11_closure`, `24_enum_methods`) and accept the classification. 39/
64 effective is an honest number.

### Integration pipeline: 60/64 pass + 2 skip + 2 fail

`tests/integration/test_golden_pipeline.py` runs the full chain
emit → llvm-as → opt → llc → clang → run. 60/64 pass unchanged
since v4.104.0. The two FAILs (`51_match_guards_and_or`,
`47_try_operator`) are pre-existing; neither is a recovery-arc
regression.

### IR cleanliness

I re-sampled 5 emitted `.ll` files from `mnc-stage1` (`01_hello`,
`03_function`, `06_struct`, `10_result`, `11_closure`). All five
pass `llvm-as` + `opt -O2` + `llc -filetype=obj` + link. No
malformed metadata, no undefined types, no return-type mismatches.
The v4.101.0 use-after-free drop-glue saga is dead; the
`_move_resource` move-semantics at six emitter call sites is
holding.

`main.ll` is **854,572 lines** (the v4.104.0 claim of 857,645
predates v4.108.0 StringBuilder + v4.111.0 disabling of 4 zero-ROI
MIR passes; the 3,073-line shrink is expected and is documented in
`AUDIT_NOTES.md` §v4.104.0). File validates with `llvm-as`.

## Primary lens — `string_concat` Phase C fix

v4.108.0's auto-StringBuilder MIR pass is load-bearing. I pulled
the IR for the `string_concat` benchmark at -O2 and verified:

- `__mn_sb_new` hoisted into the loop preheader (was not there
  before v4.108.0 — `__mn_str_concat` was being called per-iter)
- `__mn_sb_append` in the loop body
- `__mn_sb_finish` in the single exit block

Result: v4.118.0 `string_concat` at 1.32 ms vs v4.82.0's 102.31 ms.
77× speedup. The geomean vs C gcc dropped from 9.5× (v4.107.0) to
5.46× (v4.118.0) on the strength of this one fix. That is real
engineering.

I complained in prior reviews that Arcs 11–12's optimiser work had
**zero** O2 impact. The v4.109.0 forensics published in
`OPT_ROI_ANALYSIS.md` agreed: TBAA metadata is 100% dead, inline
flags are redundant, only function attributes on runtime-call
declarations propagate through LLVM's module attribute table. The
forensics is honest and names the decay points (`emit_llvm_text.py
:910-926` for the dead TBAA). That honesty counts in my favour.

## Primary lens — Rt.1 lambda signature fix (v4.106.1)

The 2-arg lambda miscompile that I caught at v4.106.0 and named
**Rt.1** — `@lambda4(ptr, ptr, ptr)` called as `(ptr, i64, i64)` —
was patched in v4.106.1. I compiled `64_closure_typed.mn` through
`mnc-stage1` at -O2 fresh today:

- `mnc-stage1` still **fails** on `64_closure_typed.mn` (it's on
  the 38-failure list with docket Sh.7).
- The **Python bootstrap** compiles it correctly, including through
  -O2.

So the v4.106.1 patch fixed the Python-bootstrap emitter (the
`closure_typed` miscompile path I originally flagged). It did not
fix the self-hosted emitter — Sh.7 is the self-hosted side, tracked
for v5.x. This split is clean: the Python bootstrap is the
reference emitter, the self-hosted emitter is the parity target.

Rt.1 PY: **CLOSED**. Rt.1 SH: carries forward as Sh.7.

## Primary lens — IR pathologies (Culebra scans)

I ran `culebra scan` on a freshly-compiled `mnc-stage1` LLVM IR.
Results:

- 0 `ALLOCA_ALIAS` findings (down from 14× in v4.105.0 valgrind top
  frames; `mir_opt__block_successors` was the hot spot, and
  disabling 4 MIR passes in v4.111.0 removed it)
- 0 `RET_TYPE_MISMATCH`
- 0 `MISSING_PERCENT`
- 0 `DUPLICATE_CASE`
- 0 `PHI_UNDEF_REF` on main line (historical dead-block elim bug
  from v3.47.0 long closed)

Instr.1 (the v4.114.0 Culebra-scan-over-854K-IR issue) is still
open — the scan **completes** today in ~12 s on my 7950X, so it
may have been a v4.114.0-era transient. I am not going to close
the docket for somebody else; flag for v5.x.

## Secondary — Panel evidence quality

`benchmarks/FINAL_REPORT_v4.120.md` is 500 lines of genuine panel
evidence: methodology with hardware / toolchain versions, 7 tables
including the per-workload progress arc, 6 ASCII position charts,
reproducibility section with exact commands. I re-ran `run_
benchmarks.py --runs 3 --only fib_recursive` and the numbers
matched the report within ±5%.

`AUDIT_NOTES.md` (v4.119.0) catches every line-count drift I would
have caught myself and publishes them as cosmetic. The 3-item
discrepancy list is honest.

`V5_READINESS.md` is *neutral*. I was skeptical an assistant agent
could write a non-advocatory readiness assessment; the matrix
format with ✅/◐/⬜/✖ and the 8-itemised known gaps did the work.

## What I'd dock

- **`make test` red on `dev`** — the full pytest suite shows 73
  failures, up from the v4.117.0 flaky audit's 22. The extras are
  in bootstrap / wasm / lsp / transpiler subdirectories. Most are
  stale assertions or feature gaps already tracked by dockets; a
  handful (struct-literal syntax, CI meta-tests) are not. **0.3
  point deduction.** Runnable lint being red is unprofessional even
  if the errors are cosmetic.
- **`make lint` red** — 64 files need black, 204 ruff errors, 34
  mypy errors. Most auto-fixable. **0.2 point.**
- **`verify_fixed_point.sh` fails at Stage 1** — documented as
  Sh.8, but advertising "self-hosted compiler" without a
  reproducible fixed-point is overclaim territory. The Python
  bootstrap's `skip_check=True` bypass is the escape hatch; the
  self-hosted binary has no bypass. **0.2 point.**

## Final score

Last panel (v4.114.0): **8.2**
This panel: **8.3** (+0.1)

The small uptick reflects Phase E's async I/O landing + the
documentation + testing sweep being real work, offset by the lint
debt I would have dinged at v4.114.0 if I had checked. The IR layer
itself has not shifted — neither better nor worse — since v4.114.1.

## Verdict: PASS WITH NOTES

Three notes:

1. Lint debt must be cleared before v5 can be called stable. A new
   user running `make lint` and seeing 204 ruff errors will not
   trust the project.
2. Qs.1 (`List<Int>` indexing through native pipeline prints `<?>`)
   still reproduces today. I tested it fresh. Must close.
3. The v5 tag should wait until fixed-point convergence is
   achievable end-to-end — **or** until the SPEC explicitly states
   that "self-hosting" is defined as "golden IR matches" and not
   "stage1 compiles itself." Either is fine; the current state is
   ambiguous.

## Carry-forward items for v4.121.0+

- **Rt.1** — PY side CLOSED; SH side = Sh.7 (carry)
- **Qs.1** — `List<Int>` indexing in call position (I reproduced today)
- **TBAA.1** — wire or delete
- **Sh.8** — fixed-point blocker
- **Instr.1** — Culebra scan completes for me today; re-verify or close

## Reproducibility

```bash
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1
python scripts/ir_doctor.py audit mapanare/self/main.ll
llvm-as mapanare/self/main.ll -o /tmp/main.bc  # must succeed
culebra scan mapanare/self/main.ll
make test
make lint
```
