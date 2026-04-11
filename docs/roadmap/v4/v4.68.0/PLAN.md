# Mapanare v4.68.0 — `async` / `await` Grammar + AST + Parser

> **Arc 8 release 2.** Syntax only. `async fn` / `await expr` return
> to the grammar for real this time. Delta review is mandatory — this
> is exactly the scenario `REVIEW_CADENCE.md` was written for.
> Compiling an `async fn` at v4.68.0 produces a "not yet lowered"
> error; semantics and lowering come in v4.69.0-v4.70.0.

**Status:** PLANNED
**Breaking:** No (additive; `async` and `await` become reserved words again)
**Prerequisite:** v4.67.0 (DESIGN.md approved)
**Delta review:** **YES — mandatory.** Rattler primary, Anaconda + Coral cross-check.
**Full panel:** No (v4.71.0)
**Estimated work:** 1 sprint
**Theme:** The tombstone comments in `mapanare.lark` from v4.30.0 get replaced with real productions. The v4.19.0 hollow-feature ghost finally gets a body.

---

## Scope

### Grammar

```
async_fn_def: "async" fn_def_body
await_expr: "await" expr
```

- `async fn foo() -> Int { ... }` — an async function
- `await some_future` — suspend until the future resolves

### AST

```python
@dataclass
class AsyncFnDef(Definition):
    """
    `async fn foo() -> T` — lowered to `fn foo() -> Future<T>` with
    a coroutine frame. See docs/roadmap/v4/v4.67.0/DESIGN.md §4.
    """
    name: str
    params: list[Param]
    return_type: TypeExpr  # the user-written return type (NOT wrapped in Future<>)
    body: Block
    span: Span

@dataclass
class AwaitExpr(Expr):
    """
    `await expr` — suspends the enclosing async fn until `expr` resolves.
    `expr` must be Future<T>; the result type is T.
    """
    expr: Expr
    span: Span
```

### Interim behavior

v4.68.0 does NOT emit any coroutine lowering. Attempting to compile an `async fn`:

1. Parser accepts it
2. Semantic check accepts it (v4.69.0 tightens)
3. Lowerer fails with a rustc-quality error:

```
error: async fn is under construction — semantic and lowering arrive in v4.69.0-v4.70.0
  --> src/foo.mn:5:1
   |
 5 | async fn foo() -> Int {
   | ^^^^^^^^^^^^^^^^^^^^^^
   |
   = note: this will compile in v4.70.0+; see docs/roadmap/v4/POST_RECOVERY_ROADMAP.md §Arc 8
```

This is the **honest interim state** pattern — the grammar is real, the semantics aren't yet, and we say so loudly.

---

## Phase 1 — Grammar

- [ ] `mapanare/mapanare.lark` — add productions. Replace the v4.30.0 tombstone comments with real rules:
  ```
  async_fn_def: "async" "fn" NAME ("<" type_param_list ">")? "(" param_list? ")" ("->" type_expr)? block
  await_expr: "await" expression
  KW_ASYNC: "async"
  KW_AWAIT: "await"
  ```
- [ ] Reintroduce the `KW_ASYNC` and `KW_AWAIT` terminals (deleted in v4.30.0)
- [ ] Add `async_fn_def` to the `module_item` / `definition` alternative list
- [ ] Add `await_expr` to the unary-expression level (tighter than binary ops, looser than postfix)

## Phase 2 — AST

- [ ] `mapanare/ast_nodes.py`:
  - `AsyncFnDef` dataclass (as above)
  - `AwaitExpr` dataclass (as above)
- [ ] These are **new, real** nodes — not aliases. The v4.30.0 deletion is reverted at the AST level.

## Phase 3 — Parser transformer

- [ ] `mapanare/parser.py`:
  - `async_fn_def` transformer: constructs `AsyncFnDef` from grammar children
  - `await_expr` transformer: constructs `AwaitExpr`
- [ ] Span computation for both
- [ ] `AwaitExpr` precedence: binds tighter than binary ops, looser than postfix (so `await foo.bar` means `await (foo.bar)`, not `(await foo).bar`)

## Phase 4 — AST walker registration

- [ ] `mapanare/semantic.py` — add `isinstance(node, AsyncFnDef)` / `AwaitExpr` branches. v4.69.0 implements the actual checking; v4.68.0 just routes to a stub that accepts and continues.
- [ ] `mapanare/lower.py` — add `isinstance(node, AsyncFnDef)` / `AwaitExpr` branches. Both raise a rustc-quality error with the "under construction" message. This is the honest interim.
- [ ] `mapanare/optimizer.py` — walker registration (for tree traversal — the nodes just need to be traversable)

## Phase 5 — Self-hosted mirror

- [ ] `mapanare/self/mapanare.lark` (if there's a copy for self-hosted bootstrap) — add the productions
- [ ] `mapanare/self/lexer.mn` — recognize `async` and `await` as keywords again
- [ ] `mapanare/self/parser.mn` — parse `async fn` and `await expr`
- [ ] `mapanare/self/ast.mn` — `AsyncFnDef` and `AwaitExpr` variants of the AST enums
- [ ] `mapanare/self/semantic.mn` — stub accept
- [ ] `mapanare/self/lower.mn` — error out with the same "under construction" message
- [ ] Fixed-point diff stays at 0 — the grammar changes don't affect `mnc_all.mn`'s content unless `mnc_all.mn` itself uses `async`/`await` (it shouldn't yet)

## Phase 6 — Delta review

- [ ] Prep `.reviews/deltas/v4.68.0-async-grammar.md`:
  - The story: v4.19.0 → v4.24.0 → v4.30.0 Path B → v4.68.0 Path A (with DESIGN.md)
  - The grammar diff
  - The AST diff
  - The parser test coverage
  - The intentionally-broken lower path (`under construction` error)
  - Pointer to DESIGN.md sections 1, 3, 4
- [ ] **Rattler (primary)** — LLVM lens; verifies the design doc supports the grammar shape
- [ ] **Anaconda (secondary)** — toolchain lens; verifies the error message is rustc-quality and the pass-pipeline implications are understood
- [ ] **Coral (secondary)** — language design lens; verifies the syntax matches DESIGN.md §3 user-visible semantics
- [ ] Delta review is BLOCKING. v4.68.0 does not merge until all three reviewers approve.

## Phase 7 — Tests

- [ ] `tests/parser/test_async_await.py`:
  - `test_async_fn_parses`
  - `test_async_fn_with_params_parses`
  - `test_async_fn_with_generic_type_params_parses`
  - `test_await_expression_parses`
  - `test_await_in_method_call_position` — `await foo.bar()`
  - `test_nested_await_parses` — `await (await inner())`
  - `test_await_outside_function_is_parse_error` — `await x` at module level
  - `test_async_keyword_is_reserved` — cannot use `async` as an identifier
  - `test_await_keyword_is_reserved`
- [ ] `tests/lower/test_async_interim_error.py`:
  - `test_compiling_async_fn_produces_under_construction_error`
  - `test_error_message_points_at_roadmap` — the error message includes the path to POST_RECOVERY_ROADMAP.md
  - `test_error_message_mentions_v4.70.0` — the error tells users when it'll work

## Phase 8 — LOW sweep

2 items.

## Phase 9 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.68.0
- [ ] `CHANGELOG.md [4.68.0]` — `async`/`await` grammar re-added, fully documented as "under construction pending v4.69.0-v4.70.0"
- [ ] SESSION_REPORT

---

## Exit criteria (13 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `async` and `await` are reserved keywords | `test_async_keyword_is_reserved` |
| 2 | Grammar accepts `async fn` definitions | `test_async_fn_parses` |
| 3 | Grammar accepts `await expr` | `test_await_expression_parses` |
| 4 | `AsyncFnDef` + `AwaitExpr` are real AST nodes | grep |
| 5 | Parser constructs both with correct spans | unit tests |
| 6 | Semantic walker registered | grep `isinstance(node, AsyncFnDef)` in `semantic.py` |
| 7 | Lowerer produces rustc-quality "under construction" error | `test_compiling_async_fn_produces_under_construction_error` |
| 8 | Error message points at POST_RECOVERY_ROADMAP.md | `test_error_message_points_at_roadmap` |
| 9 | Self-hosted lexer + parser + ast mirror the Python side | self-hosted parse tests |
| 10 | Fixed-point diff still 0 (mnc_all.mn doesn't use async yet) | `verify_fixed_point.sh` |
| 11 | Delta review PASS from all 3 reviewers | `.reviews/deltas/v4.68.0-async-grammar.md` |
| 12 | CHANGELOG explicit about "under construction" status | diff |
| 13 | Standard closeout clean | CI |

---

## What v4.68.0 does NOT do

- **Compile `async fn` to anything other than an error** — that's v4.69.0-v4.70.0
- **Emit any LLVM coroutine intrinsics** — v4.70.0+
- **Validate the semantic constraints** (`await` only inside `async fn`, `Future<T>` return type) — v4.69.0 adds these
- **Introduce `Future<T>` as a first-class type** — v4.69.0 adds the type constructor
- **Allow users to write async code in their programs** — any attempt errors at compile time. That's the point.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| `await` at expression level has precedence issues | medium | medium | Parser tests cover common cases; ambiguity resolved by explicit parens if needed |
| `async` conflicts with identifiers in existing code | very low | high | The tombstone comments from v4.30.0 say it was reserved; nobody's using it. Scan the self-hosted tree just to be sure |
| Delta review finds the DESIGN.md ambiguous | medium | low | Iterate; if DESIGN.md needs updates, do it before v4.69.0 |
| Honest "under construction" error is mistaken for a real compile failure | low | low | Error message is clear; CHANGELOG is explicit |

---

## Reference

- [`v4.67.0/DESIGN.md`](../v4.67.0/DESIGN.md) §3 (semantics) and §4 (lowering)
- [`v4.30.0/SESSION_REPORT.md`](../v4.30.0/SESSION_REPORT.md) — the deletion that v4.68.0 reverses

---

## After v4.68.0

v4.69.0 adds semantic analysis. `Future<T>` becomes a type constructor. The compile-time rules (`await` only inside `async fn`, return type must be `Future<_>`) get enforced. Lowering still fails — but at semantic time, not lower time.
