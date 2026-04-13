# Mapanare v4.97.0 — Self-Hosted Optimizer Propagation

> **Arc 14 release 1.** The Python bootstrap has had inlining, LICM,
> escape analysis, TBAA, `nsw`/`nuw`, and function attributes since
> Arcs 11-12 (v4.83.0-v4.91.0). The self-hosted compiler still emits
> the pre-optimization IR. This release ports every optimization from
> the Python pipeline to `mapanare/self/`, rebuilds mnc-stage1 with
> them, and verifies the fixed-point still holds. The self-hosted
> compiler compiling itself faster is the proof.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.96.0
**Delta review:** No
**Full panel:** No (v4.99.0)
**Estimated work:** 1 sprint
**Theme:** The self-hosted compiler deserves every optimization the Python bootstrap has. Port them all.

---

## Scope

Arc 14 is a short 3-release arc: Final Polish + v5 Gate. v4.97.0 is the
heavy lift -- porting four categories of optimization work to the
self-hosted compiler. v4.98.0 runs the final cross-language benchmarks.
v4.99.0 is the panel where the lead decides whether to tag v5.0.0.

The self-hosted `mir_opt.mn` currently has: constant folding, DCE, copy
propagation, block merging. Missing: inlining, LICM (loop-invariant
code motion), strength reduction, and escape analysis (heap-to-stack
promotion). These were added to the Python `mir_opt.py` in Arc 12
(v4.87.0-v4.91.0) and proved effective -- fib(35) dropped from 173ms
to ~45ms at O2 with the improved IR.

The self-hosted `emit_llvm.mn` currently emits correct but pessimistic
IR. Missing: `nsw`/`nuw` flags on integer arithmetic, TBAA metadata on
loads/stores, `inbounds` on GEPs, function attributes (`noalias`,
`nonnull`, `readonly`, `willreturn`, `nounwind`). These were added to
`emit_llvm_text.py` in Arc 11 (v4.83.0-v4.85.0).

The porting strategy is: **rewrite in idiomatic .mn, do not transliterate
Python.** The self-hosted compiler has different data structures, different
string handling, and different control flow patterns than the Python
bootstrap. The algorithm transfers; the code does not.

After v4.97.0, mnc-stage1 should produce measurably better IR than before,
and the fixed-point (stage1-from-Python == stage1-from-self) must still hold.

## Phase 1 -- LLVM IR quality improvements in `emit_llvm.mn`

- [ ] Add `nsw`/`nuw` flags to integer arithmetic instructions (`add`, `sub`, `mul`)
  - Read `mapanare/emit_llvm_text.py` for the Python implementation (flag emission logic)
  - In `emit_llvm.mn`, modify the instruction emitters for `MIRBinOp` to append flags when operand types are known-signed/unsigned
- [ ] Add `inbounds` keyword to all GEP instructions
  - Every `getelementptr` in `emit_llvm.mn` should emit `getelementptr inbounds`
  - Verify: golden tests still pass through `llvm-as` with the flag
- [ ] Add TBAA metadata emission
  - Emit TBAA type descriptors at module level (root, int, float, ptr, struct types)
  - Attach `!tbaa` metadata to load/store instructions
  - Verify: `opt -O2` can now reorder non-aliasing loads/stores
- [ ] Add function attributes: `nounwind`, `willreturn` on leaf functions; `noalias` on sret pointers; `nonnull` on reference parameters; `readonly` on pure functions
  - Read `emit_llvm_text.py` for the attribute inference logic
  - Port the inference to `emit_llvm.mn` using self-hosted type info
- [ ] Rebuild mnc-stage1: `bash scripts/rebuild.sh`
- [ ] Run golden tests: all 57 pass through `llvm-as` and `opt -O2`

## Phase 2 -- MIR inlining pass in `mir_opt.mn`

- [ ] Read `mapanare/mir_opt.py` inlining pass -- understand the heuristic:
  - Inline threshold: < 20 MIR instructions
  - Non-recursive (no self-calls)
  - Total inlined instruction budget per function: 200
  - Single call site preference (always inline if only one caller)
- [ ] Implement `inline_pass(module: MIRModule) -> MIRModule` in `mir_opt.mn`
  - Build a call graph (caller -> callee edges)
  - Identify inline candidates based on the heuristic
  - Clone callee instructions into call site, rewriting SSA names
  - Remove the call instruction, splice in the cloned body
  - Update the call graph after each inlining decision
- [ ] Add to the optimization pipeline in `mir_opt.mn` (runs after constant folding, before DCE)
- [ ] Test: rebuild mnc-stage1 with inlining enabled, run golden suite

## Phase 3 -- LICM + strength reduction in `mir_opt.mn`

- [ ] Read `mapanare/mir_opt.py` LICM implementation:
  - Identify natural loops via back-edge detection
  - Hoist instructions whose operands are all loop-invariant
  - Do not hoist instructions with side effects (stores, calls to non-pure functions)
- [ ] Implement `licm_pass(module: MIRModule) -> MIRModule` in `mir_opt.mn`
  - Loop detection: find back edges in the CFG, compute loop bodies
  - Invariant identification: instruction is invariant if all operands are defined outside the loop or are themselves invariant
  - Hoist invariant instructions to the loop preheader
- [ ] Implement basic strength reduction:
  - `x * 2` -> `x << 1` (shift left)
  - `x * (power-of-2)` -> `x << N`
  - `x / (power-of-2)` -> `x >> N` (unsigned) or arithmetic shift (signed)
- [ ] Add both passes to the pipeline in `mir_opt.mn` (LICM after inlining, strength reduction after LICM)
- [ ] Rebuild + golden suite

## Phase 4 -- Escape analysis (heap to stack promotion) in `mir_opt.mn`

- [ ] Read `mapanare/mir_opt.py` escape analysis:
  - Track allocations (heap alloc calls)
  - Determine if the allocated pointer escapes the function (stored to global, passed to unknown call, returned)
  - If non-escaping: replace heap alloc with stack alloc (alloca), remove free
- [ ] Implement `escape_analysis_pass(module: MIRModule) -> MIRModule` in `mir_opt.mn`
  - Walk each function, find all allocation sites
  - For each allocation: follow the pointer through all uses
  - If the pointer never escapes: rewrite to alloca + remove the corresponding free
- [ ] Add to the pipeline (after LICM, before final DCE)
- [ ] Rebuild + golden suite

## Phase 5 -- Rebuild with full optimizer + verification

- [ ] Full rebuild with all new passes enabled: `bash scripts/rebuild.sh full`
- [ ] Golden tests: 57/57 pass through both Python bootstrap and mnc-stage1
- [ ] Stage2 validation: `python scripts/ir_doctor.py stage2`
- [ ] Measure compile time: time mnc-stage1 compiling `mnc_all.mn` before vs after
  - Record: wall-clock time, peak RSS, emitted IR size
  - The self-hosted compiler compiling itself should be measurably faster with the optimizer
- [ ] Integration tests: no regressions

## Phase 6 -- Fixed-point verification

- [ ] Build mnc-stage1 from Python bootstrap: `python scripts/build_stage1.py`
- [ ] Build mnc-stage1 from self-hosted compiler: use the newly-built mnc-stage1 to compile itself
- [ ] Compare the two IR outputs: `culebra diff stage1-from-python.ll stage1-from-self.ll`
- [ ] Fixed-point must hold: both produce identical (or semantically equivalent) IR
- [ ] If divergence: investigate, fix, re-verify. Do not ship with a broken fixed-point.

## Phase 7 -- LOW sweep + closeout

- [ ] Grep for `TODO(v4.97)` or unfinished items
- [ ] Standard closeout: `VERSION`, `CHANGELOG.md`, `SESSION_REPORT.md`

---

## Exit criteria (12 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `nsw`/`nuw` flags emitted by `emit_llvm.mn` | diff of `emit_llvm.mn` + `llvm-as` validates |
| 2 | TBAA metadata emitted at module + instruction level | grep `!tbaa` in emitted IR |
| 3 | `inbounds` on all GEPs | grep `getelementptr inbounds` in emitted IR |
| 4 | Function attributes emitted (`nounwind`, `noalias`, etc.) | grep `nounwind` in emitted IR |
| 5 | Inlining pass implemented in `mir_opt.mn` | diff of `mir_opt.mn` |
| 6 | LICM pass implemented in `mir_opt.mn` | diff of `mir_opt.mn` |
| 7 | Strength reduction implemented in `mir_opt.mn` | diff of `mir_opt.mn` |
| 8 | Escape analysis implemented in `mir_opt.mn` | diff of `mir_opt.mn` |
| 9 | Golden tests: 57/57 pass | test log |
| 10 | Stage2 validates | `ir_doctor.py stage2` output |
| 11 | Fixed-point holds (stage1-from-Python matches stage1-from-self) | `culebra diff` output |
| 12 | Compile time measured and recorded (before vs after) | `SESSION_REPORT.md` metrics |

---

## What this release does NOT do

- **Run cross-language benchmarks** -- that is v4.98.0.
- **Add new MIR optimization passes** beyond what the Python bootstrap already has -- this is a port, not research.
- **Modify the Python bootstrap optimizer** -- `mir_opt.py` and `emit_llvm_text.py` are read-only in this release.
- **Change language semantics** -- pure compiler internals.
- **Modify the C runtime** -- no runtime changes.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Self-hosted Mapanare lacks Python stdlib features used in optimizer (e.g., sets, dicts with complex keys) | medium | high | Rewrite the algorithm in idiomatic .mn; do not transliterate Python. Use lists where Python uses sets if needed. |
| Inlining pass introduces infinite loop on recursive functions | low | high | The heuristic explicitly excludes recursive functions; add a test for mutual recursion too |
| LICM hoists a side-effectful instruction, causing miscompilation | medium | high | Conservative: only hoist if the instruction is provably pure (no stores, no calls to non-pure fns). Run full golden suite + integration tests. |
| Escape analysis promotes an escaping allocation to stack, causing UAF | low | critical | Conservative: if in doubt, do not promote. Valgrind on all golden tests that use heap allocation. |
| Fixed-point breaks because optimizer pass ordering differs between Python and self-hosted | medium | medium | If fixed-point diverges: compare the IR diff, identify which pass ordering causes the difference, align. Accept semantic equivalence if structural identity fails. |
| Self-hosted compiler too slow to compile itself with 4 new passes | low | low | Measure before/after. If the optimizer itself is slow, add pass-level timing and optimize the hot pass. |

---

## After v4.97.0

v4.98.0 runs the final comprehensive benchmark suite: all optimizer benchmarks, async benchmarks, and GPU benchmarks across Mapanare, Python, Go, and Rust. The self-hosted compiler from v4.97.0 -- now with all optimizations -- is what gets benchmarked.
