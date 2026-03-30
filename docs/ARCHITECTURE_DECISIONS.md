# Mapanare Architecture Decisions -- v2.1.0 Self-Hosted Compiler

This document records the key architectural decisions made during the v2.1.0
self-hosted compiler work. Each decision captures the problem, the chosen
solution, and any trade-offs or limitations that remain.

---

## Context

The self-hosted compiler (mnc-stage1) compiles itself to produce stage2 IR.
All 15/15 golden tests pass. Self-compilation works (0.8s, 200MB, 53K lines
of LLVM IR). One stage2 `llvm-as` error remains -- see Decision 8 below.

---

## Decision 1: Byref Pass-by-Reference (`_BYREF_BYTES=64`)

**Problem.** `LowerState` (240B), `EmitState` (240B), and `LowerResult` (248B)
were passed by value through 632 call sites. Every struct copy triggered
`_clone_list_fields`, which recursively duplicated list backing arrays. The
combined allocation pressure reached 57GB, causing immediate OOM.

**Solution.** Structs larger than 64 bytes are passed by pointer with
pre-zeroed `sret` return buffers. The threshold is controlled by
`_BYREF_BYTES` (default 64). Callers allocate an `alloca` for the return
value and pass it as the first argument; callees write through the pointer
instead of returning by value.

**Impact.** Eliminated the entire class of large-struct corruption bugs.
Self-compilation went from OOM to 0.8s / 200MB -- a reduction of roughly
two orders of magnitude in peak memory.

---

## Decision 2: Selective COW Cloning

**Problem.** Two extremes both failed:

- Full `_clone_list_fields` on every `Copy` produced the 57GB OOM described
  above.
- No cloning at all caused nested list corruption: `module.functions` data
  was silently lost because multiple references shared the same backing
  array.

**Solution.** Clone list fields on struct `Copy` *except* for append-only
lists (`EmitState.lines`, `EmitState.str_globals`) which only grow and are
never shared across independent scopes. These are excluded from cloning
because their usage pattern guarantees no aliased mutation.

**Trade-off.** 95% of clones are eliminated. The remaining 5% -- lists that
are mutation-prone or shared across scopes -- correctly maintain COW
refcounts and are cloned on write.

---

## Decision 3: Type Erasure for `Option<Struct/Enum>`

**Problem.** `Option<TypeExpr>` was lowered as `{i1, %enum.TypeExpr}`, but
`WrapNone` produced `{i1, i8*}`. The type mismatch cascaded through every
Phi node and store that touched an Option-wrapped struct or enum.

**Solution.** Option payloads of struct or enum type use `ptr` (opaque
pointer). `WrapSome` stores the inner value to an `alloca` and takes its
address as `ptr`. `WrapNone` uses `{i1, ptr}` with a null payload.

**Limitation.** `Option<List>` still uses the inline representation
`{i1, {ptr, i64, i64, i64}}`. `WrapNone` for list options falls back to
the function return type because the list layout is small enough to pass
by value and the opaque-pointer path has not been extended to cover it.

---

## Decision 4: Opaque Pointer Migration (partial)

**Done.** The self-hosted emitter (`emit_llvm_ir.mn`, `emit_llvm.mn`) fully
uses `ptr` instead of `i8*`. All `GEP`, `store`, and `load` instructions
use opaque pointers.

**Not done.** The Python text emitter (`emit_llvm_text.py`) still uses typed
pointers (`i8*`, `TYPE*`). This is Phase 2 work.

**Why it matters.** The Python emitter compiles the self-hosted source code.
The resulting `main.ll` contains a mix of typed and opaque pointers. LLVM 18
accepts both, so the compiler works today. However, the mixed representation
prevents full consistency between stage1 and stage2 output and complicates
debugging type mismatches.

---

## Decision 5: Per-Module Function Resolution

**Problem.** The global function map (`global_fn_map`) used last-wins
semantics. Functions with the same name in different modules -- notably
`fresh_tmp` in both `lower_state` and `emit_llvm` -- collided silently,
causing the wrong function signature to be used at call sites.

**Solution.** Per-module cumulative function maps, built in topological
dependency order. Each module resolves calls only against functions from
itself and its earlier dependencies. Later modules cannot shadow earlier
ones within a given module's resolution scope.

**Known collisions avoided:** `fresh_tmp`, `is_comparison_op`, `new_param`.

---

## Decision 6: The Last Stage2 Error -- Why It Exists

**The error.** A nested if-expression Phi produces `i64` (both arms have
unknown MIR type) but a downstream match-Phi expects `%struct.TypeInfo`.

**Root cause.** The MIR loses generic type information. Function calls return
`mir_unknown()` when the function-return-type lookup via `lambda_vars` fails.
This happens because the list holding return-by-value entries loses data --
the same list corruption class described in Decision 2, manifesting at the
type-inference level rather than the data level.

**Why it cannot be fixed in the `.mn` emitter.** The fix requires multi-pass
type inference (backward propagation from consumers to producers). The
single-pass string-based emitter in the self-hosted compiler cannot look
ahead to determine what type a consumer expects.

**Fix path.** Phase 2 Python text emitter opaque pointer migration, or adding
a type inference pass to the Python lowerer. Either approach eliminates the
typed-pointer surface where the mismatch manifests.

---

## Decision 7: Python Lowerer Control Flow Bug

The Python Stage 0 compiler has a known bug: `return` inside `if` blocks
drops all subsequent code in the enclosing function. Similarly, `break`
inside `if` inside `for` loops is swallowed -- the break never executes.

**Workaround.** Use boolean flags instead of early returns and breaks:

```mn
// BAD -- return inside if is dropped by Stage 0
fn example(x: int) -> int {
    if x > 0 {
        return x
    }
    return -x
}

// GOOD -- boolean flag pattern
fn example(x: int) -> int {
    let result: int = 0
    let done: bool = false
    if x > 0 {
        result = x
        done = true
    }
    if !done {
        result = -x
    }
    return result
}
```

This bug affects how the self-hosted `.mn` code is compiled. Any new code
in `lower.mn` or `emit_llvm.mn` must avoid early return and break patterns.

---

## Next Steps

1. **Phase 2:** Migrate the Python text emitter to opaque pointers. This
   removes all typed-pointer type mismatches from `main.ll` and eliminates
   the last stage2 error (Decision 6).

2. **Phase 4:** Fixed-point verification (`stage2 == stage3`). Once Phase 2
   is complete, the self-hosted compiler should produce identical IR when
   compiling itself twice in succession.

The remaining `llvm-as` error will be eliminated by Phase 2, since opaque
pointers remove the entire class of typed-pointer type mismatches that
cause the Phi node conflict.
