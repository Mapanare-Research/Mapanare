# Mapanare v3.22.0 — "Puare" (Performance + Codegen Quality + Tensor PoC)

> Address the deeper code quality issues: _coerce_arg reduction phase 2,
> replace Any annotations, improve monomorphization, reduce alloca density,
> and deliver a tensor proof-of-concept that validates the "AI-native" claim.

**Status:** PLANNED
**Estimated scope:** Medium-Large (2-3 sessions)
**Breaking:** No
**Prerequisite:** v3.21.0

---

## Items

### 1. `_coerce_arg` reduction — phase 2 [HIGH]

**File:** `mapanare/emit_llvm_mir.py:180-301`
**Reporter:** Cobra (H1, present since v1.0.0)

Continue from v3.20.0 phase 1 (~20 remaining call sites). Fix MIR type propagation
for the remaining patterns. Target: reduce to <10 call sites (truly unavoidable
coercions only, e.g., varargs, FFI boundaries).

### 2. 200 `Any` annotations in LLVM emitter [MEDIUM]

**File:** `mapanare/emit_llvm_mir.py`
**Reporter:** Viper (M12)

Replace `Any` with proper llvmlite types:
- `ir.Value` for SSA values
- `ir.Type` for types
- `ir.Function` for functions
- `ir.IRBuilder` for builders
- `ir.Block` for basic blocks

Start with hottest paths: `_emit_binop`, `_emit_call`, `_emit_struct_init`.
Target: reduce from 200 to <50 `Any` annotations. MyPy should catch real errors.

### 3. Monomorphization uses `deepcopy` [MEDIUM]

**Files:** `mapanare/lower.py:476`, `mapanare/optimizer.py:290,337`
**Reporter:** Cobra (M4)

`deepcopy` traverses entire AST subtree. O(n) per monomorphization.

**Fix:** Implement structural sharing via fresh-name substitution walk:
- Walk AST, only copy nodes that contain type parameters
- Unmodified subtrees share references with original
- Substitute type variables during the walk
- Result: O(k) where k = nodes containing type params, not n = total nodes

### 4. Alloca density reduction [MEDIUM]

**Files:** `mapanare/emit_llvm_mir.py`, `mapanare/emit_llvm_text.py`
**Reporter:** Rattler (M6)

~37 allocas per function. Single-block functions (constructors, accessors, wrappers)
don't need allocas at all — they have no cross-block control flow.

**Fix:** Heuristic: if function has exactly 1 basic block + no mutable variables,
emit pure SSA without allocas. `version()` goes from 10 instructions to 4.

### 5. Tensor proof-of-concept [MEDIUM]

**Files:** New + `mapanare/lower.py`, `mapanare/emit_llvm_mir.py`, `mapanare/semantic.py`
**Reporter:** Coral (L11, "AI-native" gap)

Implement one end-to-end tensor operation:
```mn
let a: Tensor<Float>[3] = tensor([1.0, 2.0, 3.0])
let b: Tensor<Float>[3] = tensor([4.0, 5.0, 6.0])
let c = a + b  // elementwise add via Add trait
print(c)       // [5.0, 7.0, 9.0]
```

Pipeline: parse -> semantic (shape check: both `[3]`) -> MIR -> LLVM IR
(loop over elements, fadd) -> run.

One operation, one element type, one shape. Proof the design works.

---

## Verification

- [ ] `_coerce_arg` call sites < 10
- [ ] MyPy on `emit_llvm_mir.py` with `--strict` catches more errors than before
- [ ] Monomorphization of large generic function: measurable speedup
- [ ] `version()` function in golden IR: 4 instructions, 0 allocas
- [ ] `tensor_add.mn` compiles and runs natively, correct result
- [ ] `/golden` — all pass
- [ ] Benchmark suite shows improvement across the board
