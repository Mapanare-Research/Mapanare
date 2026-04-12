# v4.42.0 Session Report — 2026-04-12

**Scope:** Arc 3 release 1 — Tensor literals + runtime wiring
**Breaking:** No (additive syntax)
**Delta review:** YES (Rattler + Coral)

---

## Verdict
- Self-graded: 9.2/10 (clean implementation, self-hosted mirror stub-only for emission)
- CARRY_FORWARD.md rows closed: P1, P4
- New LOW items: 0

## Completed

### Phase 1: Grammar (`mapanare/mapanare.lark:293–362`)
- `tensor_literal` production: `KW_TENSOR LT type_expr GT LBRACKET tensor_body RBRACKET`
- `tensor_body`, `?tensor_elem`, `tensor_nested`, `?tensor_atom` rules
- `tensor_atom` excludes `list_lit` to avoid LALR ambiguity with nested `[`

### Phase 2: AST + Parser (`mapanare/ast_nodes.py:283–293`, `mapanare/parser.py:838–895`)
- `TensorLiteral` dataclass: `element_type`, `shape`, `elements` (flat row-major)
- Parser walks nested body, flattens elements, infers shape from nesting depth
- Jagged arrays detected at parse time with per-depth count validation

### Phase 3: Semantic (`mapanare/semantic.py:1233–1270`)
- `_check_tensor_literal`: element type checking, int-to-float promotion
- Returns `TypeInfo(kind=TENSOR, args=[elem_ti], tensor_shape=tuple)`

### Phase 4: Lowering (`mapanare/lower.py:1409–1411`, `2595–2622`)
- `TensorInit` MIR instruction in `mapanare/mir.py:287–300`
- `_lower_tensor_literal` dispatches to TensorInit

### Phase 5: Runtime (`runtime/native/mapanare_gpu_builtins.c:267–358`)
- 10 new `__mn_tensor_*` functions wrapping `mapanare_tensor_alloc` et al.
- CPU-only — no GPU dependency for construction
- Bounds-checked store/get functions

### Phase 6: LLVM Emitter (`mapanare/emit_llvm_text.py:339–348`, `3136–3175`, `1497–1531`)
- `_do_tensor_init`: shape alloca → `__mn_tensor_alloc` → element store loop
- `_emit_drop_glue_tensors`: free non-returned tensor pointers at return
- All tensor runtime functions in `_RUNTIME_FN_ATTRS`
- Tensor builtins dispatched: `tensor_rank`, `tensor_size`, `tensor_get_f64`, etc.

### Phase 7: Self-hosted mirror
- `ast.mn`: `TensorLit(List<Expr>, List<Int>)` variant + accessors
- `mir.mn`: `TensorInit(Value, MIRType, List<Int>, List<Value>)` + accessors
- `parser.mn`: `parse_tensor_lit` (delegates to `parse_list_lit` for 1D)
- `semantic.mn`: tensor_lit inference block
- `lower.mn`: `lower_tensor` function
- `emit_llvm.mn`: `emit_tensor_init` stub (null ptr — full emission deferred to v4.43.0)
- mnc-stage1 builds, 48/50 golden pass (49_tensor_literal stub, 51 pre-existing)

### Phase 8: Tests
- `tests/parser/test_tensor_literal.py`: 13 tests (1D/2D/3D, jagged, negation, vars)
- `tests/semantic/test_tensor_literal.py`: 7 tests (type checking, promotion)
- `tests/llvm/test_tensor_literal.py`: 12 tests (compilation, builtins, drop glue)
- `tests/golden/49_tensor_literal.mn`: golden program with element access
- Total: 32 new tests, 738 pass (0 regressions in parser/semantic/LLVM)

### Phase 10: LOW sweep
- P1: `__mn_list_get` readonly+willreturn removed (calls abort on OOB)
- P4: SPEC §5.6 "compatible types" → "name-set equality" (matches implementation)

## Carry-forward closed
- P1: `__mn_list_get` attrs — `emit_llvm_text.py:253–254` — readonly+willreturn removed
- P4: SPEC §5.6 wording — `docs/SPEC.md:906` — corrected to name-set-only

## Carry-forward still open
- P2: `pattern_matching.py` zero unit tests — v4.43.0
- P3: Self-hosted guard fall-through divergence — v4.43.0
- P5: `examples/` showcase gap — v4.43.0+
- P6: Unreachable-arm warning path zero test coverage — v4.43.0

## Measurements
- IR line count: 188,962 (main.ll)
- Golden test count: 50 (49_tensor_literal new)
- Stage1 golden: 48/50
- Pytest: 738 pass (parser/semantic/LLVM dirs), 32 new
- Fixed-point: not yet verified (self-hosted emitter is stub)

## Decisions Made
- Decision 1: Jagged arrays → parse error at parse time (not semantic). Shape mismatch message includes depth + expected/got counts.
- Decision 2: `Tensor<Float>[]` → parse error. `Tensor<Float>[0]` via annotation is allowed.
- Decision 3: No 0-D tensors in v4.42.0. Scalars are scalars.
- Self-hosted emitter: stub (null ptr) for v4.42.0, full implementation deferred to v4.43.0 when tensor indexing makes it testable end-to-end.

## Verification Results
- 32/32 tensor-specific tests pass
- 738/738 parser+semantic+LLVM tests pass (0 regressions)
- 48/50 golden through mnc-stage1 (49_tensor_literal stub, 51 pre-existing)
- Delta review: Rattler + Coral (in progress)

## Next Session Should Start With
- Read `docs/roadmap/v4/v4.43.0/PLAN.md`
- Read `docs/roadmap/v4/v4.43.0/PROMPT.md`
- Implement tensor indexing `t[i, j]` with runtime bounds checking
