# v4.52.0 Semantic Audit — semantic.mn vs semantic.py

> Side-by-side comparison of the self-hosted semantic pass (`mapanare/self/semantic.mn`, 1,974 lines)
> against the Python bootstrap (`mapanare/semantic.py`, 2,336 lines).
> Performed 2026-04-12 as Phase 0 of v4.52.0 (A7 closure).

## Architecture parity

Both sides use the same two-pass architecture:
- **Pass 1**: Register all top-level definitions (functions, structs, enums, agents, traits, imports, type aliases)
- **Pass 2**: Check function/agent/impl bodies (type inference, scope resolution, operator validation)

Both use state-threading (Python via mutable `self`, self-hosted via `SemState` struct passing).

## Wiring status

**The self-hosted semantic pass IS wired into `compile()`.** At `main.mn:297`:
```mapanare
let errors: List<SemanticError> = check(resolved, filename)
```
Verified working: broken files produce exit 1 + `filename:line:column: error: message`.

## Check-by-check comparison

### Parity (both sides perform equivalent checks)

| # | Check | Python | Self-hosted | Notes |
|---|-------|--------|-------------|-------|
| 1 | Undefined variable | `_infer_expr` Identifier | `infer_expr` ident | Same message |
| 2 | Undefined function | `_check_call` | `check_call_resolved` | Same message |
| 3 | Argument count mismatch | `_check_call` | `check_call_resolved` | SH only checks when params registered |
| 4 | Assignment to undefined var | `_check_assign` | `check_assign_expr` | Same |
| 5 | Assignment to immutable var | `_check_assign` | `check_assign_expr` | Same |
| 6 | Assignment type mismatch | `_check_assign` | `check_assign_expr` | SH: "Type mismatch in assignment" |
| 7 | Let type annotation mismatch | `_check_let` | `check_let_stmt` | Same pattern |
| 8 | If condition not Bool | `_check_if` | `check_if_expr` | Same |
| 9 | Arithmetic on non-numeric | `_check_binary` | `check_arithmetic_binary` | Same logic |
| 10 | Tensor arithmetic type | `_check_binary` | `check_arithmetic_binary` | Same |
| 11 | Logical op non-Bool | `_check_binary` | `check_logical_binary` | Same |
| 12 | Matmul non-Tensor | `_check_binary` | `check_matmul_binary` | Same |
| 13 | Unary `-` non-numeric | `_check_unary` | `check_unary_expr` | Same |
| 14 | Unary `!` non-Bool | `_check_unary` | `check_unary_expr` | Same |
| 15 | Undefined agent in spawn | `_check_spawn` | `check_spawn_callee` | Same |
| 16 | Spawn non-agent | `_check_spawn` | `check_spawn_callee` | Same |
| 17 | Pipe RHS undefined fn | `_check_pipe_expr` | `check_pipe_expr` | Same |
| 18 | Pipe type mismatch | `_check_pipe_expr` | `check_pipe_expr` | SH less detailed |
| 19 | Impl undefined type | `_check_impl` | `check_impl_body` | Same |
| 20 | Impl undefined trait | `_check_impl` | `check_impl_body` | Same |
| 21 | Impl trait-is-not-trait | `_check_impl` | `check_impl_body` | Same |
| 22 | Missing trait method | `_check_impl` | `validate_trait_methods` | Same |
| 23 | Pipe def undefined stage | `_check_pipe_def` | `check_pipe_stage_err` | Same |

### Divergent-breaking (self-hosted accepts what Python rejects)

| # | Check | Python | Self-hosted | Severity | v4.52.0 action |
|---|-------|--------|-------------|----------|----------------|
| D1 | `?` on non-Result/Option | `_check_error_prop` (4 checks) | Returns `unknown_type()`, no validation | **HIGH** — produces garbage IR | **FIX** |
| D2 | Match guard must be Bool | `_check_match` guard check | Infers guard but no Bool check | MEDIUM | **FIX** |
| D3 | While condition must be Bool | `_check_while` (implicit in check_stmt) | Infers condition but no Bool check | MEDIUM | **FIX** |
| D4 | Match exhaustiveness | `_check_match_exhaustiveness` (Maranget) | Not checked | MEDIUM | **DEFER** — requires Maranget port |
| D5 | Unreachable match arm | `_check_match_exhaustiveness` (warning) | Not checked | LOW | DEFER |
| D6 | Or-pattern binding names | `_bind_pattern` OrPattern | Not checked | LOW | DEFER |
| D7 | Argument type mismatch (per-arg) | `_check_call` per-arg types | Only checks count, not types | MEDIUM | DEFER (v4.53.0) |
| D8 | `__struct_meta` validation | `_check_call` | Not checked | LOW | DEFER |
| D9 | `encode_struct` / `decode_to` validation | `_check_call` | Not checked | LOW | DEFER |
| D10 | Generic type arity mismatch | `_resolve_type_expr` | Not checked | LOW | DEFER |
| D11 | Tensor broadcast shape | `_check_binary` | Not checked | LOW | DEFER |
| D12 | Matmul shape mismatch | `_check_binary` | Not checked | LOW | DEFER |
| D13 | Tensor rank mismatch on index | `_infer_expr` IndexExpr | Not checked | LOW | DEFER |
| D14 | Tensor element type mismatch | `_check_tensor_literal` | Not checked | LOW | DEFER |
| D15 | Agent input/output unknown type | `_check_agent` | Not checked | LOW | DEFER |
| D16 | Impl extra method not in trait | `_check_impl` | Not checked | LOW | DEFER |
| D17 | Send type mismatch | `_check_send` | Not checked | LOW | DEFER |
| D18 | Namespace member not found | `_check_namespace_access` | Not checked | LOW | DEFER |
| D19 | `extern "Python"` ABI rejection | `_register_def` | Not checked | LOW | DEFER |
| D20 | Arithmetic on `any` type | `_check_binary` | Not checked | LOW | DEFER |
| D21 | Trait bounds at generic call | `_check_trait_bounds_at_call` | Not checked | LOW | DEFER |
| D22 | `println` deprecation warning | `_check_call` | Not checked | LOW | DEFER |
| D23 | Multi-index on non-Tensor | `_infer_expr` IndexExpr | Not checked | LOW | DEFER |
| D24 | Multiple device annotations | `_check_decorators` | Not checked | LOW | DEFER |

### Divergent-benign (different behavior, no correctness impact)

| # | Check | Difference | Notes |
|---|-------|-----------|-------|
| B1 | Error message formatting | Python: "Cannot assign X to variable 'y' of type Z" | SH: "Type mismatch in assignment to 'y'" — less specific but still useful |
| B2 | Field access type inference | Python: resolves struct fields | SH: returns `unknown_type()` — no false positive, just less precise |
| B3 | Method call return types | Python: resolves from impl | SH: returns `unknown_type()` — same as B2 |
| B4 | Import resolution errors | Python: via ModuleResolver | SH: handled by main.mn resolve_imports, not semantic |

### Not checked by either side

| Check | Notes |
|-------|-------|
| Return type vs body consistency | Neither checks declared return matches actual return |
| Struct field names in constructors | Neither validates field names or types |
| Duplicate parameter names | Neither checks |
| Duplicate struct field names | Neither checks |
| `break`/`continue` outside loop | Neither checks |
| Recursive type cycles | Neither checks |

## v4.52.0 scope decision

**In scope (3 fixes):**
- D1: `?` operator validation — highest priority, currently produces garbage IR
- D2: Match guard Bool check — easy, prevents type confusion
- D3: While condition Bool check — easy, parity with if-condition check

**Deferred (21 items):**
- D4-D24 deferred to v4.53.0+ — benign for currently-correct programs, would require significant new infrastructure (Maranget port, per-arg type matching, etc.)

## Evidence of working wiring

```
$ echo 'fn main() { let x: Int = "hello" }' | mnc-stage1
/tmp/test.mn:0:0: error: Type mismatch: declared type Int but initial value is String
(exit 1)

$ echo 'fn main() { foo() }' | mnc-stage1
/tmp/test.mn:0:0: error: Undefined function 'foo'
(exit 1)

$ echo 'fn main() { let x: Int = 42 }' | mnc-stage1
; ModuleID = ...  (valid LLVM IR)
(exit 0)
```
