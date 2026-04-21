# Cobra — C++/ABI Review (Arc 11)

**Grade: 9/10**
**Verdict: PASS**

## Assessment

**noalias on sret parameters:** Correct per the System V and Win64 ABIs. The sret pointer is a hidden first parameter that points to caller-allocated stack space. The callee writes the return value through it. No other pointer visible to the callee can alias it — the caller guarantees this by construction (it's a local alloca in the caller's frame). Safe on x86_64, aarch64, and all targets Mapanare supports.

**willreturn + nounwind on function definitions:** These do not affect the calling convention. They are optimization hints that LLVM uses for inlining and dead-store elimination. No ABI impact.

**Cross-function attribute consistency:** The runtime function declarations already had per-function attributes (noalias on allocators, readonly on queries). The user-defined function attributes (nounwind willreturn) are consistent — they don't promise anything the runtime functions don't also deliver.

## Score justification

9/10 — the ABI annotations are correct and consistent. No calling convention violations. The noalias sret annotation is exactly right for the struct-return pattern used by the emitter.
