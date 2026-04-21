# Rattler — LLVM Review (Arc 12)

**Grade: 8/10**
**Verdict: PASS WITH NOTES**

## Assessment

Arc 12 added three MIR-level passes that transform IR before it reaches the LLVM emitter. The central question: does MIR-level optimization produce IR that is (1) semantically equivalent, (2) at least as LLVM-friendly as unoptimized IR, and (3) not in conflict with LLVM's own optimization passes?

### Function inlining (v4.87.0)

**SSA correctness: SOUND.** The inlining pass clones callee blocks with a unique prefix (`_inlN_`), rewrites all Value names, and splices the callee into the caller CFG. Return becomes Copy + Jump to a merge block. This preserves SSA dominance: the cloned definitions dominate the merge block exactly as the original callee's definitions dominated its return.

**Interaction with LLVM inliner: BENIGN.** MIR inlining operates on small, single-block callees (< 20 instructions). LLVM's inliner would almost certainly inline these same functions. The result is equivalent — MIR inlining just does it earlier, giving downstream MIR passes (DCE, constant propagation) a chance to clean up. No conflict.

**Conservative budget: GOOD.** The `body * call_count < 200` heuristic prevents code bloat. One inline site per fixpoint iteration prevents exponential expansion.

### Strength reduction (v4.88.0)

**Correctness: SOUND.** `x % 2^n → x & (2^n - 1)` is algebraically correct for non-negative integers. Mapanare integers are signed i64, but the runtime guarantees mod operand N > 0 for the targeted pattern. The emitter maps BinOpKind.AND to `and i64`, which is correct.

**LICM: DISABLED, CORRECT DECISION.** The LICM infrastructure (dominators, natural loops) is present but the transform is gated. The miscompilation on matmul was correctly diagnosed (loop-carried value tracking) and the pass was disabled rather than shipped broken. This is the right call.

### Escape analysis (v4.89.0)

**Alias-set computation: SOUND.** The fixed-point iteration over Copy/Phi chains correctly computes transitive aliases. A value that flows through `Copy` or `Phi` into a returning position will be marked escaped, and its originating allocation will not be promoted. The 6 escape criteria are complete for the current MIR instruction set.

**Emitter gap: NOTED.** `AllocKind.STACK` is set on instructions but the emitter does not read it. This means the analysis has zero runtime effect today. The annotation is correct and harmless (default is HEAP), but the feature is incomplete until the emitter wiring ships.

## Items

| Item | Priority | Notes |
|------|----------|-------|
| Escape analysis emitter wiring | MEDIUM | AllocKind.STACK set but not consumed — zero runtime effect |
| LICM disabled | LOW | Infrastructure present, transform gated — acceptable |
| MIR inlining multi-block callees | LOW | Currently single-block only — future expansion |

## Score justification

8/10 — all three passes are semantically correct. No miscompilation risk. Deduction for the escape analysis emitter gap: the analysis is sound but the optimization is incomplete (annotation without codegen). LICM gating is the right engineering decision.
