# Cobra — C++/ABI Review (Arc 12)

**Grade: 9/10**
**Verdict: PASS**

## Assessment

### Inlining and ABI preservation

MIR inlining operates entirely within the MIR layer — it clones instructions and rewrites Value names. The LLVM emitter sees the post-inlining MIR and emits IR as usual. This means:

- **Calling convention: UNCHANGED.** Inlining eliminates the call entirely; the cloned body uses the same register/stack layout as if the code were written inline. No ABI boundary is crossed.
- **Sret handling: SAFE.** The inliner only targets single-block callees. Functions with sret returns (struct-returning) are typically multi-block (entry + return logic), so they are excluded by the cost model. Even if they were inlined, the Return→Copy rewrite produces a value copy, not a pointer alias.
- **Varargs / FFI: NOT AFFECTED.** ExternCall and ClosureCall are never candidates for MIR inlining (only Call with matching fn_lookup entries).

### Escape analysis and stack layout

The `AllocKind.STACK` annotation would instruct the emitter to use `alloca` instead of a runtime allocator call. The stack layout implications:

- **4KB cap: APPROPRIATE.** With the default 8MB Linux stack and typical recursion depth, 4KB per promoted allocation leaves ample headroom. The guard against loop-interior promotion prevents unbounded stack growth.
- **No alloca in loops: CORRECT.** LLVM places all `alloca` in the entry block (`_alloca` helper in the emitter does this), so even if the analysis promoted a loop allocation, the emitter would emit a single entry-block alloca. But the conservative guard is still valuable as documentation of intent.

### Struct identity through optimization

MIR optimization does not change struct layouts, field orders, or type representations. StructInit, FieldGet, FieldSet preserve their type metadata through all passes. The optimizer only adds/removes/rewrites instructions — it never modifies the struct registry (`MIRModule.structs`).

## Score justification

9/10 — no ABI concerns. Inlining is purely intraprocedural after clone. Escape analysis stack layout is well-guarded. No struct identity changes.
