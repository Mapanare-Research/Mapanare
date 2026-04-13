# Mapanare v4.69.0 — Semantic Analysis for `async` / `await`

> **Arc 8 release 3.** Adds type-level enforcement of the async
> constraints: `await` only inside `async fn`, `async fn` return type
> is sugar for `Future<T>`, `Future<T>` becomes a first-class type
> constructor. Lowering still errors — but the error moves from
> parse time to semantic time, which is progress.

**Status:** DONE (2026-04-13)
**Session log:** TypeKind.FUTURE added, async fn return type wrapped in Future<T>, await-outside-async error, await-on-non-Future error, forgot-to-await arithmetic error. 11 new tests.
**Decisions taken:** Error (not warning) for missing await; reject await inside non-async closures; Future<T> uses uniform {i8,ptr} representation per DESIGN.md §3.3.
**Breaking:** No
**Prerequisite:** v4.68.0
**Delta review:** No (no new syntax; type system extension)
**Full panel:** No (v4.71.0)
**Estimated work:** 1.5 sprints
**Theme:** `Future<T>` is real. The type checker catches async misuse.

---

## Scope

### New type constructor

- `Future<T>` — first-class type. A `Future<T>` resolves to a `T` at runtime. Can be awaited inside an `async fn`.
- `TypeKind.FUTURE` — added to the enum
- `Future<T>.t` — the inner type

### Semantic rules

1. **`async fn foo() -> T`** — the function's type in the symbol table is `fn () -> Future<T>`. Callers see `Future<T>`, not `T`.
2. **`await expr` — only inside `async fn`.** Not inside a regular `fn`, not at module level, not inside a non-async closure.
3. **`await expr` requires `expr: Future<T>`.** Anything else is a compile error with a rustc-quality message.
4. **`await expr` returns `T`** where `expr: Future<T>`.
5. **Calling an `async fn` returns a `Future<T>`, not `T`.** The caller must either `await` it (if inside another `async fn`) or handle the future differently (not yet — v5.x `.then` / `.block_on`).
6. **An `async fn` cannot recursively call itself without `await`.** The recursion would run synchronously and defeat the purpose. Warn (or error) on direct recursion without `await`.

---

## Phase 1 — Type system extension

### Phase 1.1: `TypeKind.FUTURE`

- [ ] `mapanare/types.py`:
  ```python
  class TypeKind(Enum):
      ...
      FUTURE = "future"
  ```
- [ ] `FutureType` dataclass or use the generic `Type(kind=FUTURE, args=[T])` pattern
- [ ] Display: `Future<T>`

### Phase 1.2: Type constructor registration

- [ ] `FUTURE` is a generic type constructor like `Option`, `Result`, `List`
- [ ] Parse `Future<T>` as a type expression — grammar already handles generic type parameters; just register `Future` as a builtin type name

### Phase 1.3: Async function type

- [ ] When the semantic checker visits an `AsyncFnDef`, it builds the function's type as `fn (params) -> Future<return_type>`. The user wrote `async fn foo() -> Int`; the type system sees `fn () -> Future<Int>`.
- [ ] The function is registered in the symbol table with this wrapped type.
- [ ] Inside the function body, the return expressions still have type `Int` (the user-written return type). The wrapping happens at the function boundary.

---

## Phase 2 — Semantic check for `AsyncFnDef`

- [ ] `mapanare/semantic.py` `check_async_fn_def(node: AsyncFnDef) -> None`:
  1. Check parameter types
  2. Check return type
  3. Compute the wrapped type: `fn (params) -> Future<return>`
  4. Register in symbol table with `is_async: True`
  5. Enter a new scope; set `scope.enclosing_async_fn = node`
  6. Type-check the body — the body's return type is the user-written `return_type`, not `Future<return_type>`
  7. Exit the scope
- [ ] The `is_async` flag on the symbol table entry is important for the `await` check below.

---

## Phase 3 — Semantic check for `AwaitExpr`

- [ ] `mapanare/semantic.py` `check_await_expr(node: AwaitExpr) -> Type`:
  ```python
  def check_await_expr(self, node: AwaitExpr) -> Type:
      # Rule 1: must be inside an async fn
      if not self._in_async_context():
          self._error(SemanticError(
              line=node.span.line,
              column=node.span.column,
              end_line=node.span.end_line,
              end_column=node.span.end_column,
              message="`await` can only be used inside an `async fn`",
              suggestion="mark the enclosing function with `async fn foo() -> T { ... }`",
          ))
          return Type.error()

      # Type-check the awaited expression
      inner_ty = self.check_expr(node.expr)
      if inner_ty.is_error():
          return Type.error()  # suppress cascade

      # Rule 2: must be Future<T>
      if inner_ty.kind != TypeKind.FUTURE:
          self._error(SemanticError(
              ...,
              message=f"`await` requires `Future<T>`, got `{inner_ty}`",
              suggestion="only async function calls or Stream methods return Future<T>",
          ))
          return Type.error()

      # Rule 3: return the inner type
      return inner_ty.args[0]  # Future<T>.t
  ```
- [ ] `_in_async_context()` walks the scope stack looking for an enclosing `AsyncFnDef`
- [ ] Inside a non-async closure (`|| { ... }`) nested in an async fn, `await` is NOT allowed — the closure is not itself async

---

## Phase 4 — Async function calls

- [ ] When a call site calls an `async fn`, the return type is `Future<T>`, not `T`.
- [ ] Typical pattern inside another async fn:
  ```mapanare
  async fn inner() -> Int { return 42 }
  async fn outer() -> Int {
      let x: Int = await inner()
      return x + 1
  }
  ```
- [ ] Without `await`:
  ```mapanare
  async fn outer() -> Int {
      let x: Future<Int> = inner()  // explicit Future<Int> annotation works
      // ... later
      return await x  // defer the await
  }
  ```
- [ ] At a non-async call site (`fn main() { let x = inner() }`), the returned `Future<Int>` is useless without a way to block on it. v4.69.0 accepts this — the programmer gets a `Future<Int>` they can't do anything with. v4.73.0's scheduler integration lets `main()` block on futures to drive completion.

---

## Phase 5 — Recursive async warning

- [ ] Walk each `AsyncFnDef` body looking for direct self-calls without `await`:
  ```mapanare
  async fn foo() { foo() }  // error: direct recursion in async fn without await
  ```
- [ ] **Error** (not warning): "async fn recursing on itself without `await` would run synchronously; use `await foo()` to suspend"
- [ ] This catches a common beginner mistake

---

## Phase 6 — Future<T> arithmetic

- [ ] `Future<Int>` + `Int` is not defined — it's a type error. `Future<T>` cannot be used as its unwrapped type without `await`.
- [ ] Error: "`Future<Int>` cannot be added to `Int`; use `await` to get the `Int` value"
- [ ] This catches the "forgot to await" mistake

---

## Phase 7 — Self-hosted mirror

- [ ] `mapanare/self/types.mn` — add `FUTURE` to TypeKind
- [ ] `mapanare/self/semantic.mn` — mirror all the check_async_fn_def and check_await_expr logic
- [ ] A7 (v4.52.0) wired the self-hosted semantic pass, so these checks are actually fired at compile time for self-hosted .mn files

---

## Phase 8 — Tests

- [ ] `tests/semantic/test_async_semantics.py`:
  - `test_await_inside_async_fn_ok`
  - `test_await_outside_async_fn_errors` — rustc-quality
  - `test_await_in_non_async_closure_errors`
  - `test_await_on_int_errors` — not a Future
  - `test_await_on_string_errors`
  - `test_await_on_future_returns_inner_type`
  - `test_async_fn_type_is_future_wrapped`
  - `test_async_fn_call_returns_future`
  - `test_future_int_plus_int_errors` — missing await
  - `test_recursive_async_without_await_errors`
- [ ] `tests/semantic/test_future_type.py`:
  - `test_future_is_type_constructor`
  - `test_future_displays_as_future_t`
  - `test_nested_future_future_int`  — `Future<Future<Int>>` is a weird but valid type

---

## Phase 9 — Lowering still errors

- [ ] v4.69.0 does NOT implement lowering. The lowerer still produces the "under construction" error.
- [ ] Update the error message to reflect that semantic check passed:
  ```
  error: async fn lowering arrives in v4.70.0 — semantic analysis at v4.69.0 is complete
  ```

---

## Phase 10 — LOW sweep

2 items.

## Phase 11 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.69.0
- [ ] `CHANGELOG.md [4.69.0]` — async semantic pass + Future<T> type constructor
- [ ] `docs/SPEC.md` — new §Futures subsection draft (full section lands in v4.75.0 when end-to-end works)
- [ ] SESSION_REPORT

---

## Exit criteria (15 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `TypeKind.FUTURE` added | grep |
| 2 | `Future<T>` parses as type expression | parse test |
| 3 | Async fn return type wrapped in `Future<T>` in symbol table | unit test |
| 4 | `await` inside async fn accepted | `test_await_inside_async_fn_ok` |
| 5 | `await` outside async fn rejected | `test_await_outside_async_fn_errors` |
| 6 | `await` on non-Future rejected | `test_await_on_int_errors` |
| 7 | `await` returns inner type | `test_await_on_future_returns_inner_type` |
| 8 | Async fn call returns Future<T> | `test_async_fn_call_returns_future` |
| 9 | Missing-await detection (Future<T> vs T mismatch) | `test_future_int_plus_int_errors` |
| 10 | Recursive async without await detected | `test_recursive_async_without_await_errors` |
| 11 | Self-hosted semantic mirrors all checks | self-hosted compile tests |
| 12 | Lowering still errors (updated message) | `test_compiling_async_fn_errors_at_lower` |
| 13 | Fixed-point diff still 0 | verify script |
| 14 | `docs/SPEC.md` §Futures subsection draft | file exists |
| 15 | Standard closeout clean | CI |

---

## What v4.69.0 does NOT do

- **Lowering** — v4.70.0
- **`Future<T>` methods** (`then`, `map`, `block_on`) — v5.x or later
- **Implicit conversion from `T` to `Future<T>`** — no; would mask the "forgot to await" bug
- **`async` closures** — v5.x
- **`async` methods on impl blocks** — probably v4.70.0 if trivial, otherwise v5.x

---

## Reference

- [`v4.67.0/DESIGN.md`](../v4.67.0/DESIGN.md) §3

---

## After v4.69.0

v4.70.0 emits the first half of the LLVM coroutine lowering: the coro-split prelude (`llvm.coro.id`, `llvm.coro.alloc`, `llvm.coro.begin`). Programs with `async fn` will produce IR — not yet runnable, but close.
