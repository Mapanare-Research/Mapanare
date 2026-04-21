# Rattler — LLVM Review (Arc 11)

**Grade: 9/10**
**Verdict: PASS**

## Assessment

The IR annotation pass is semantically correct across all four changes:

**nsw on integer add/sub/mul:** Correct. Mapanare defines signed overflow as UB, matching C99/LLVM semantics. The `nsw` flag was already present before Arc 11 — good prior work.

**nounwind on all user functions:** Correct. Mapanare has no exception mechanism, no `throw`, no unwind paths. Every function is `nounwind` by construction. Eliminates `.eh_frame` and landing pads.

**willreturn on all user functions:** Correct but aggressive. Mapanare treats infinite recursion as UB (stack overflow). This is semantically defensible but means that a user who writes an infinite loop gets UB, not a hang. The right tradeoff for a compiled language.

**inbounds on all GEPs:** Correct. Every GEP in the emitter references a known struct field or array element within an allocated object. The 9 sites upgraded (Future type, array, agent) were all safe.

**TBAA tree:** Correct but incomplete. The coarse tree (int/float/ptr/bool) is emitted at module level, but loads/stores are not yet annotated with `!tbaa` references. The tree is available; the annotation work is future.

**noalias on sret:** Correct. The sret pointer is a caller-allocated slot passed exclusively to one function call. It does not alias any pointer the callee can observe through other arguments.

## Score justification

9/10 — every annotation is semantically correct. The TBAA tree is emitted but not yet wired to loads/stores (deferred, not a bug). The honest negative benchmark result is a feature of good methodology, not a failure of the IR work.
