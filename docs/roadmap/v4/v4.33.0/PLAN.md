# Mapanare v4.33.0 — The `?` operator

> **First new language feature in 7 releases.** Delta review is
> mandatory per `REVIEW_CADENCE.md`. This is also the first release
> after the recovery arc — the discipline the arc installed is what
> makes v4.33.0 safe to ship.

**Status:** PLANNED
**Breaking:** No (additive syntax, no existing program breaks)
**Prerequisite:** v4.32.0 (arc-end panel closure complete)
**Delta review:** **YES** — Coral or Rattler lens, 1-hour focused, non-blocking but gating
**Full panel:** No (cadence fires at v4.36.0)
**Estimated work:** 1 sprint
**Theme:** Shorthand for `Result<T, E>` and `Option<T>` early-return. First growth release of Arc 1.

---

## Why now, and why this feature first

**Why now.** The recovery arc (v4.27.0–v4.31.0) shipped zero new features across five releases. v4.32.0 is an arc-end panel closure release — also zero new features. The v4.31.0 panel verdict (9.343 aggregate, 5 PASS + 2 PASS WITH NOTES) terminated the arc cleanly, which means v4.33.0 is the first release the project can legitimately add syntax again. The delta review discipline is new; exercising it on a small, well-understood feature is the right first use.

**Why `?`.** Four reasons:

1. **Ergonomic pain is real.** Every non-trivial Mapanare function that uses `Result<T, E>` today ends up with 3–5 `match` arms for the error path. The pattern is the same every time: pattern-match the `Err` arm, return it unchanged, bind the `Ok` payload. `?` is the minimum syntax that closes that ergonomic gap.
2. **Delta-review-friendly scope.** One new grammar production, one AST node, one semantic check, one lowering rule. Total diff ~300 lines across both pipelines. A 1-hour delta review can fact-check it exhaustively.
3. **Well-understood semantics.** Rust shipped `?` in 2016 and every Rust-inspired language has copied it. The desugaring is textbook: `expr?` → `match expr { Err(e) => return Err(e), Ok(v) => v }`. No novel design work.
4. **Hollow-feature risk is near-zero.** The feature is pure syntactic sugar over existing `match` + early return. If the lowering desugars correctly, it runs correctly — there is no "grammar without runtime" failure mode because there is no new runtime.

---

## The feature, precisely

### Syntax

```mapanare
fn read_config(path: String) -> Result<Config, IoError> {
    let contents: String = read_file(path)?
    let parsed: Config = parse_config(contents)?
    return Ok(parsed)
}
```

Equivalent today (what the lead writes at v4.32.0):

```mapanare
fn read_config(path: String) -> Result<Config, IoError> {
    let contents_result: Result<String, IoError> = read_file(path)
    let contents: String = match contents_result {
        Ok(v) => v,
        Err(e) => return Err(e),
    }
    let parsed_result: Result<Config, IoError> = parse_config(contents)
    let parsed: Config = match parsed_result {
        Ok(v) => v,
        Err(e) => return Err(e),
    }
    return Ok(parsed)
}
```

The old form keeps working — `?` is additive.

### Type system rules (semantic checker)

1. `expr?` requires `expr: Result<T, E>` or `expr: Option<T>`. Any other type is a compile error with a rustc-quality message pointing at the expression and suggesting the explicit `match` form.
2. The enclosing function's return type must be compatible:
   - If `expr: Result<T, E>`, enclosing fn must return `Result<_, E2>` where `E` is compatible with `E2` (equality for now — no implicit `From` widening; that's tracked for later).
   - If `expr: Option<T>`, enclosing fn must return `Option<_>`.
3. Using `?` outside a function (e.g., at module top level) is a compile error.
4. Using `?` inside a closure whose return type doesn't match — compile error with a pointer at the closure's inferred return type.

### Lowering (pure desugar)

`expr?` lowers to a fresh `match` MIR block:

```
; fresh %result = lower(expr)
; fresh %early_return_block:
switch %result.tag:
  case 0 (Ok):     ; jump to continuation with %result.payload bound
  case 1 (Err):    ; return Err(%result.payload) from enclosing function
  case 2 (None):   ; return None from enclosing function
                   ; only reachable when %result is Option<T>
```

No new LLVM instructions. No new runtime primitives. The existing `match` lowerer handles it via the fresh match block. **This is important:** `?` shares a lowering path with normal `match`, so the v4.34.0 match-lowering rewrite (decision-tree compilation) will automatically improve the IR quality of `?` chains too, for free.

### Binding precedence

`?` binds tighter than binary operators but looser than field access and indexing:

- `foo.bar?` → `(foo.bar)?`
- `foo[0]?` → `(foo[0])?`
- `foo? + bar` → `(foo?) + bar`
- `foo? * 2` → `(foo?) * 2`
- `foo?.bar` is a grammar error — it should be written `foo?`.`bar` in a chained form, and actually this is ambiguous enough that v4.33.0 **requires parentheses**: `(foo?).bar`. v4.34.0+ can revisit if the ergonomic win is worth the grammar complication.

---

## Phase 0 — pre-commit sanity

- [ ] Confirm v4.32.0 tag is clean: all 18 exit criteria from `v4.32.0/PLAN.md` green.
- [ ] `git status` clean.
- [ ] `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1` — 44/44 baseline before any v4.33.0 changes.
- [ ] `bash scripts/verify_fixed_point.sh` — fixed-point clean at baseline.
- [ ] Read `.reviews/REVIEW_CADENCE.md` §Delta Triggers — confirm `?` triggers a delta review (it's a new token / new production, clearly yes).
- [ ] Decide delta reviewer lens: **Coral** (language design) is primary — this is a syntax decision with no novel codegen; Rattler is backup if Coral wants a second opinion on the desugar shape.

---

## Phase 1 — Python pipeline

### Phase 1.1: Grammar

- [ ] `mapanare/mapanare.lark` — add `postfix_try` production.

  The exact position in the grammar matters. `?` must bind tighter than binary ops but looser than index/field access. Looking at the existing precedence:

  - Level 1: primary (literals, identifiers, parens)
  - Level 2: postfix (field, index, call) — **this is where `?` goes**
  - Level 3: unary (`-x`, `!x`)
  - Levels 4–16: binary ops by precedence
  - Level 17: assignment

  New production:
  ```
  postfix: primary (postfix_tail)*
  postfix_tail: field_access | index_access | call_args | TRY_OP
  TRY_OP: "?"
  ```

  `TRY_OP` is a terminal, not a string literal, so the parser can report it distinctly in error messages.

- [ ] `mapanare/mapanare.lark` — confirm the lexer doesn't already use `?` for anything else. Search: `grep -n '?' mapanare/mapanare.lark`. If there's a conflict (e.g. `?` as a nullable-type marker), resolve it first. Expected: no conflict, because `?` was never a Mapanare token before today.

- [ ] `mapanare/mapanare.lark` — update the contextual-keywords table documentation comment if one exists, noting that `?` is now a postfix operator.

### Phase 1.2: AST

- [ ] `mapanare/ast_nodes.py` — add the `TryExpr` dataclass:

  ```python
  @dataclass
  class TryExpr(Expr):
      """
      `expr?` — shorthand for early-return on Err/None.
      Lowers to match + return. v4.33.0.
      """
      expr: Expr
      span: Span
  ```

  Position in the file: after `FieldAccess` and `IndexGet`, since it's a sibling postfix form. Keep the ordering consistent with the grammar so future readers can trace one-to-one.

### Phase 1.3: Parser transformer

- [ ] `mapanare/parser.py` — add `postfix_try` handler:

  ```python
  def postfix_try(self, children):
      inner = children[0]
      span = Span(
          line=inner.span.line,
          column=inner.span.column,
          end_line=inner.span.end_line,
          end_column=inner.span.end_column + 1,  # +1 for the ? token
      )
      return TryExpr(expr=inner, span=span)
  ```

  The span computation matters for the semantic diagnostic — when the type check fails, the underline should cover `expr?`, not just `expr`.

- [ ] `mapanare/parser.py` — wire `postfix_try` into the `postfix` rule's `postfix_tail` dispatch. Follow the same shape as `field_access` and `index_access` transformers.

### Phase 1.4: AST walker registration

- [ ] `mapanare/semantic.py` — `SemanticChecker.check_expr` visitor: add the `isinstance(expr, TryExpr)` branch. This is the v4.31.0 `scripts/check_no_hollow_features.py` step 3 requirement — every AST expression class must have an `isinstance` check in the walker. v4.33.0 honors the rule.

- [ ] `mapanare/lower.py` — `Lowerer.lower_expr`: add the `isinstance(expr, TryExpr)` branch, dispatching to a new `_lower_try_expr` method.

- [ ] `mapanare/optimizer.py` — if there's an AST-level optimizer pass that walks expression trees, add the `TryExpr` case. Constant-folding doesn't apply (the whole point of `?` is that the value is not known until runtime), but other passes (dead code elimination, copy propagation) may need to walk through.

### Phase 1.5: Semantic check

- [ ] `mapanare/semantic.py` — `check_try_expr(node: TryExpr) -> Type`:

  ```python
  def check_try_expr(self, node: TryExpr) -> Type:
      inner_type = self.check_expr(node.expr)
      enclosing_fn = self._enclosing_fn_or_error(node)
      if enclosing_fn is None:
          self._error(SemanticError(
              line=node.span.line,
              column=node.span.column,
              end_line=node.span.end_line,
              end_column=node.span.end_column,
              message="`?` can only be used inside a function body",
              suggestion="remove the `?` or wrap in `fn main() { ... }`",
              filename=self.filename,
          ))
          return Type.error()

      # Case 1: Result<T, E>
      if inner_type.kind == TypeKind.RESULT:
          t, e = inner_type.args
          enclosing_ret = enclosing_fn.return_type
          if enclosing_ret.kind != TypeKind.RESULT:
              self._error(SemanticError(
                  ...,
                  message=f"`?` on a `Result` value requires the enclosing function to return `Result<_, _>`, but `{enclosing_fn.name}` returns `{enclosing_ret}`",
                  suggestion="change the return type to `Result<_, _>` or use an explicit `match`",
              ))
              return Type.error()
          _, enclosing_e = enclosing_ret.args
          if not types_compatible(e, enclosing_e):
              self._error(SemanticError(
                  ...,
                  message=f"error types don't match: `?` propagates `{e}` but `{enclosing_fn.name}` returns `Result<_, {enclosing_e}>`",
                  suggestion=f"change the error type or wrap the error: `.map_err(|e| /* convert {e} to {enclosing_e} */)`",
              ))
              return Type.error()
          return t

      # Case 2: Option<T>
      if inner_type.kind == TypeKind.OPTION:
          t = inner_type.args[0]
          enclosing_ret = enclosing_fn.return_type
          if enclosing_ret.kind != TypeKind.OPTION:
              self._error(SemanticError(
                  ...,
                  message=f"`?` on an `Option` value requires the enclosing function to return `Option<_>`, but `{enclosing_fn.name}` returns `{enclosing_ret}`",
                  suggestion="change the return type to `Option<_>` or use `.unwrap_or(...)`",
              ))
              return Type.error()
          return t

      # Case 3: anything else
      self._error(SemanticError(
          ...,
          message=f"`?` requires `Result<_, _>` or `Option<_>`, got `{inner_type}`",
          suggestion="the `?` operator only works on values that can be `Err` or `None`",
      ))
      return Type.error()
  ```

- [ ] `mapanare/semantic.py` — helper `_enclosing_fn_or_error` that walks up the scope stack to find the current function. Probably already exists; reuse it.

- [ ] `mapanare/semantic.py` — helper `types_compatible(a, b) -> bool` that checks error-type compatibility. For v4.33.0: equality + parameterized-type recursion. No implicit widening.

### Phase 1.6: Lowering

- [ ] `mapanare/lower.py` — `_lower_try_expr(node: TryExpr) -> MIRValue`:

  The desugar target is a fresh match MIR block. Approach:

  1. Lower the inner expression to a `MIRValue` of type `Result<T, E>` or `Option<T>`.
  2. Create two new basic blocks: `try_ok_<N>` and `try_err_<N>` where N is a unique counter.
  3. Emit a tag-switch MIR instruction on the inner value (the existing `_lower_match` helper already does this for regular `match`; factor out the low-level `emit_tag_switch(value, cases)` helper so both can reuse it).
  4. In `try_err_<N>`: construct a return instruction that wraps the payload in the enclosing function's error type and returns it.
  5. In `try_ok_<N>`: bind the payload as the result value of the `TryExpr`. Subsequent lowering sees this as a normal SSA value.
  6. Fall-through from `try_ok_<N>` to the rest of the enclosing block.

- [ ] Make sure the early-return from `try_err_<N>` properly runs drop glue for any live values. The existing `return` lowering in `_lower_return` already invokes drop glue — make sure the `try_err_<N>` path goes through the same code path, not a hand-rolled return.

- [ ] `mapanare/mir.py` — no changes to MIR structure. `TryExpr` is pure AST-level sugar; by the time the MIR is built, there is no trace of `?`.

### Phase 1.7: LLVM emitter

**No changes.** The match + return path is already wired end-to-end. This is the feature's safest property — v4.33.0 ships with zero changes to `emit_llvm_text.py`, so the risk of regression in the emitter is zero.

**Verification:** compile `tests/golden/47_try_operator.mn` at `-O0` and inspect the emitted IR. Should contain:
- A `switch` instruction on the result's tag
- An early-return block for the `Err` arm
- A continuation block for the `Ok` arm

Should NOT contain:
- Any new LLVM instruction kinds
- Any new runtime call

---

## Phase 2 — Self-hosted mirror

> **Non-optional.** The v4.31.0 panel's Rattler review flagged the
> Python-vs-self-hosted emitter asymmetry as a carry-forward risk.
> v4.32.0 closed the existing asymmetry. v4.33.0 must not reintroduce
> it. Every new feature in a Python-side file also lands in the
> self-hosted equivalent.

### Phase 2.1: Self-hosted lexer

- [ ] `mapanare/self/lexer.mn` — recognize `?` as a token. Look at the existing `char_to_token` or equivalent function; add a branch for `'?'` that produces a `TOK_QUESTION` or similar.

  The lexer is character-by-character, so this is a single-character token — simpler than the multi-char Python-side Lark terminal but semantically equivalent.

- [ ] Regression check: does the lexer currently treat `?` as an error? If yes, the v4.32.0 test corpus has tests that assert that behavior — those tests need to update. If no (lexer silently drops it), there's a quiet bug that v4.33.0 uncovers.

### Phase 2.2: Self-hosted parser

- [ ] `mapanare/self/parser.mn` — in the postfix-expression parser function (probably `parse_postfix` or `parse_primary_suffix`), add a branch for `TOK_QUESTION` that wraps the current expression in a `TryExpr` AST node.

- [ ] `mapanare/self/ast.mn` — add the `TryExpr` struct. Mirror the Python AST:

  ```mapanare
  type TryExpr = {
      expr: Expr,
      span: Span,
  }
  ```

  And a constructor function `new_try_expr(expr: Expr, span: Span) -> Expr` following the project convention ("let r: T = first_field; return r").

- [ ] Add `TryExpr` to the tagged-union enum (`ExprKind` or whatever it's called) with a new variant `EXPR_TRY`.

### Phase 2.3: Self-hosted semantic

- [ ] `mapanare/self/semantic.mn` — add `check_try_expr(node: TryExpr, ctx: SemanticCtx) -> Type`.

  This is the harder mirror because the self-hosted semantic is less mature than the Python one (see A7 tracked for v4.52.0). For v4.33.0:

  - If the self-hosted semantic check is fully wired (v4.52.0 is behind us), mirror the full Python check.
  - If the self-hosted semantic is **still a stub** (v4.32.0 did not yet wire it), add the type check but know it won't fire at compile time until v4.52.0. The grammar + lower path will still work — users who compile a broken `?` usage will get a lowering error instead of a semantic error. That's a degraded error message, not a correctness bug.

- [ ] Document the degraded-error state in the v4.33.0 `SESSION_REPORT.md` so the v4.52.0 release knows to validate that self-hosted semantic checks `TryExpr` when it wires the rest of `semantic.mn`.

### Phase 2.4: Self-hosted lowering

- [ ] `mapanare/self/lower.mn` — add `lower_try_expr(node: TryExpr, state: LowerState) -> LowerResult`.

  Follow the same desugar-to-match structure. Create two new blocks via `add_block`, emit a tag-switch, populate the `Err` block with a return, bind the `Ok` block's continuation.

- [ ] Drop glue: ensure `lower_try_expr`'s error-path return runs the same drop glue that `lower_return_stmt` does. Factor out a `lower_early_return(state, value) -> LowerResult` helper if needed.

### Phase 2.5: Rebuild + validate

- [ ] `python scripts/build_stage1.py` — rebuild `mnc-stage1` from the self-hosted sources.
- [ ] `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1` — existing golden tests still pass (no regressions).
- [ ] `bash scripts/verify_fixed_point.sh` — fixed-point diff ≤100 lines (the target is ≤69, matching v4.32.0's baseline; any increase needs investigation).

---

## Phase 3 — Tests

### Phase 3.1: Golden test

- [ ] `tests/golden/47_try_operator.mn` — new file:

  ```mapanare
  enum IoError {
      NotFound,
      PermissionDenied,
      InvalidInput,
  }

  fn read_line(n: Int) -> Result<String, IoError> {
      if n == 0 {
          return Err(IoError::NotFound)
      }
      if n < 0 {
          return Err(IoError::InvalidInput)
      }
      return Ok("line " + int_to_str(n))
  }

  fn read_three_lines(start: Int) -> Result<List<String>, IoError> {
      let a: String = read_line(start)?
      let b: String = read_line(start + 1)?
      let c: String = read_line(start + 2)?
      return Ok([a, b, c])
  }

  fn main() {
      let ok_case: Result<List<String>, IoError> = read_three_lines(1)
      match ok_case {
          Ok(lines) => print(lines[0]),
          Err(_) => print("error"),
      }

      let err_case: Result<List<String>, IoError> = read_three_lines(0)
      match err_case {
          Ok(_) => print("unexpected ok"),
          Err(IoError::NotFound) => print("not found"),
          Err(_) => print("other error"),
      }
  }
  ```

  Expected output:
  ```
  line 1
  not found
  ```

- [ ] Generate reference IR: `python scripts/test_native.py --bless` (or the v4.x equivalent).
- [ ] Commit `tests/golden/47_try_operator.mn` AND `tests/golden/47_try_operator.ref.ll`.

### Phase 3.2: Parser tests

- [ ] `tests/parser/test_try_operator.py` — positive and negative cases:

  - `test_simple_try_on_result_parses`
  - `test_simple_try_on_option_parses`
  - `test_chained_try_parses` — `foo()?.bar?` (after parentheses resolution, this is `((foo())?).bar` followed by `?` on the field access result; might actually require `((foo())?.bar)?` with explicit parens)
  - `test_try_on_nested_call_parses` — `inner(x, y)?`
  - `test_try_on_field_parses` — `(obj.field)?`
  - `test_try_on_index_parses` — `(list[0])?`
  - `test_standalone_question_mark_is_parse_error` — `?foo`, `foo ? bar`, etc.
  - `test_try_without_operand_is_parse_error`

### Phase 3.3: Semantic tests

- [ ] `tests/semantic/test_try_operator.py`:

  - `test_try_on_result_in_result_fn_ok` — valid Result-in-Result case
  - `test_try_on_option_in_option_fn_ok` — valid Option-in-Option case
  - `test_try_on_result_in_option_fn_errors` — expect rustc-quality error message
  - `test_try_on_option_in_result_fn_errors` — same
  - `test_try_on_int_errors` — wrong inner type
  - `test_try_on_string_errors` — wrong inner type
  - `test_try_at_module_top_errors` — outside any function
  - `test_try_error_type_mismatch` — `Result<T, E1>` in `Result<T, E2>` where E1 ≠ E2
  - `test_try_error_type_nested_match` — `Result<T, List<Int>>` vs `Result<T, List<String>>` — expected error
  - `test_error_message_contains_suggestion` — verify the suggestion text appears in the rendered error

### Phase 3.4: End-to-end LLVM tests

- [ ] `tests/llvm/test_try_operator.py`:

  - `test_try_compiles_to_switch_plus_return` — inspect emitted IR, confirm pattern match
  - `test_try_runs_ok_path` — compile + run, verify Ok payload is returned
  - `test_try_runs_err_path` — compile + run, verify Err is propagated
  - `test_try_runs_option_path` — compile + run, verify Option/None propagation
  - `test_try_runs_drop_glue_on_early_return` — allocate a `String` before the `?`, trigger the Err path, verify the `String` is freed (no leak in valgrind)
  - `test_chained_try_works` — three `?` in a row in one function, both success path and first-fail path

### Phase 3.5: Self-hosted regression

- [ ] `tests/self_hosted/test_try_operator.py` — compile `tests/golden/47_try_operator.mn` through `mnc-stage1`, run the binary, verify output matches the reference.

### Phase 3.6: Test count sanity

- [ ] Count of golden tests: should be 45 (44 at v4.32.0 + 1 new).
- [ ] Count of pytest: should be +~15 from v4.32.0 (10 parser + semantic + 5 e2e).
- [ ] `python scripts/check_silent_skips.py tests/` — clean.

---

## Phase 4 — LOW item sweep

The v4.31.0 arc-end panel surfaced a LOW tail that v4.32.0 scoped out. v4.33.0 takes 3 of those items as "quality crumbs" on top of the main feature work.

### Phase 4.1: `mn_signal_propagate` unbounded recursion (Viper, 8th cycle)

- [ ] `runtime/native/mapanare_core.c:2091-2125` — the propagate DFS loop has no depth bound. A pathological computed-signal chain overflows the stack.
- [ ] Add `MN_SIGNAL_PROPAGATE_MAX_DEPTH = 1024` constant. Increment depth counter on each recursive call, abort with a clear error on exceed ("signal graph too deep — max depth 1024 exceeded").
- [ ] Test: construct a signal graph that would have previously overflowed, verify it aborts cleanly instead.

### Phase 4.2: `mnc-stage1` shipped unstripped (Mamba)

- [ ] `Makefile` or `scripts/build_stage1.py` — add `strip mapanare/self/mnc-stage1` as a post-link step (optional, gated on `STRIP=1` env var so debug builds can opt out).
- [ ] Or: ship debug symbols in a separate `.dwp` file via `objcopy --only-keep-debug` + `--strip-debug`. This preserves debuggability while cutting the binary size.
- [ ] Binary goes from 3.3MB to ~1.5MB.
- [ ] Smoke test: `./mapanare/self/mnc-stage1 version` still works (no dynamic debug dependency broke).

### Phase 4.3: Viper M5 — agent destroy message leak (2nd cycle, ledger row #50 added in v4.32.0)

- [ ] `runtime/native/mapanare_runtime.h` — add `message_dtor_fn: void (*)(void*)` field to `mapanare_agent_t`.
- [ ] `mapanare_agent_init` — take a `message_dtor_fn` parameter, default `NULL`.
- [ ] `mapanare_agent_destroy` — drain loop calls `message_dtor_fn(msg)` if non-NULL before discarding.
- [ ] If the compiler-generated agent wrapper knows the message type (it does — `info.message_type` is available in `_emit_agent_wrap`), pass a generated destructor through at spawn time.
- [ ] TSan test: allocate agents with `String`-typed messages, destroy with messages still in the inbox, verify no memory leak via valgrind.

---

## Phase 5 — Documentation

### Phase 5.1: Cookbook

- [ ] `docs/cookbook.md` §Error Handling — add "Using `?` for concise Result chains" subsection with the before/after example from the "Why this feature first" section of this PLAN. Include both the Result case and the Option case.

### Phase 5.2: SPEC

- [ ] `docs/SPEC.md` §Expressions — add a `?` row to the expression forms table:

  | Expression | Syntax | Type rule |
  |---|---|---|
  | Try | `expr?` | `expr: Result<T, E>` and enclosing fn returns `Result<_, E>` → value has type `T`; same pattern for `Option<T>`. |

- [ ] `docs/SPEC.md` §Error Handling — full subsection explaining `?` semantics, the desugar, the error-type compatibility rule, the "no implicit widening" decision.

### Phase 5.3: reference.md

- [ ] `docs/reference.md` — add `?` to the operator precedence table. Position: between postfix `[...]` / `.field` and unary `-` / `!`.

### Phase 5.4: docs drift CI

- [ ] All new code blocks in cookbook / SPEC / reference must parse through the Lark parser (the v4.31.0 `check_docs_drift.py` CI gate enforces this). Mark any illustrative pseudocode with `<!-- pseudo -->`.

---

## Phase 6 — Delta review

### Phase 6.1: Prep the reviewer

- [ ] Create `.reviews/deltas/v4.33.0-try_operator.md` as a stub file with:
  - The PR diff summary (git range from v4.32.0 to HEAD)
  - Links to the new golden test, pytest files, SPEC section
  - The desugar rule spelled out explicitly
  - The type compatibility rule and why no implicit widening (for now)
  - Any design questions the reviewer should explicitly validate

- [ ] Choose the reviewer. **Default: Coral.** Rationale: new syntax, language-design decision, comparison to Rust/Swift/Zig. Rattler is backup if Coral wants a second opinion on the desugar shape. Anaconda if Coral is unavailable.

### Phase 6.2: Delta review execution

- [ ] Reviewer reads:
  - `mapanare/mapanare.lark` `postfix_try` production
  - `mapanare/ast_nodes.py` `TryExpr` definition
  - `mapanare/semantic.py` `check_try_expr` (this is the hot spot for language-design scrutiny)
  - `mapanare/lower.py` `_lower_try_expr` (this is the hot spot for correctness)
  - `mapanare/self/` mirror files — confirm parity
  - `tests/golden/47_try_operator.mn` and `.ref.ll`
  - `tests/semantic/test_try_operator.py` (especially the negative cases — are the error messages rustc-quality?)

- [ ] Reviewer verdict: PASS / PASS WITH NOTES / FAIL.
  - PASS: feature is correctly specified and implemented. Merge.
  - PASS WITH NOTES: acceptable with nits that can be follow-ups. Merge with issues filed.
  - FAIL: blocks merge. Reviewer writes specific file:line objections; the lead fixes; re-review.

- [ ] Reviewer output: a file at `.reviews/deltas/v4.33.0-try_operator.md` with the verdict, the specific items checked, and any notes.

### Phase 6.3: Address findings

- [ ] If the delta review is PASS with notes, the notes are filed as `v4.34.0` items (either in `CARRY_FORWARD.md` as LOW rows or inline in `v4.34.0/PLAN.md`).
- [ ] If the delta review is FAIL, v4.33.0 slips until the fix is ready. No merge until re-review PASS.

---

## Phase 7 — Closeout

### Phase 7.1: Full validation suite

- [ ] `black --check .` — clean
- [ ] `ruff check .` — clean
- [ ] `mypy mapanare/ runtime/` — clean
- [ ] `pytest tests/ -n auto` — all passing
- [ ] `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1` — 45/45 golden tests
- [ ] `python scripts/ir_doctor.py stage2` — 11/11 stage2 modules valid
- [ ] `bash scripts/verify_fixed_point.sh` — fixed-point ≤100 diff lines
- [ ] `make check-runtime-sources` — clean
- [ ] `python scripts/check_silent_skips.py tests/` — clean
- [ ] `python scripts/check_changelog_honesty.py` — clean
- [ ] `python scripts/check_docs_drift.py` — clean
- [ ] `python scripts/check_no_hollow_features.py` — clean (step 3: confirms `TryExpr` has an `isinstance` check in `lower.py`)

### Phase 7.2: CHANGELOG + VERSION + SESSION_REPORT

- [ ] `VERSION` — bump `4.32.0` → `4.33.0`
- [ ] `CHANGELOG.md` — new `[4.33.0]` entry. **Every backticked path must resolve on disk.** Every test name must exist. Every symbol must be greppable. The recovery-arc discipline holds.
- [ ] `docs/roadmap/v4/v4.33.0/SESSION_REPORT.md` — honest session log.
- [ ] `docs/roadmap/ROADMAP.md` — v4.33.0 row added
- [ ] `docs/roadmap/v4/README.md` — v4.33.0 row added (or v4.33.0 replaces "planned" with "shipped")
- [ ] `.reviews/CARRY_FORWARD.md` — 3 LOW rows marked CLOSED with evidence from Phase 4 sweep
- [ ] `.reviews/deltas/v4.33.0-try_operator.md` — committed alongside the feature

---

## Exit criteria (20 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Grammar accepts `x?` at postfix position | `tests/parser/test_try_operator.py::test_simple_try_on_result_parses` passes |
| 2 | `TryExpr` AST node round-trips through the parser | same file, all positive parse cases pass |
| 3 | Semantic rejects `x?` in a function that doesn't return `Result<_>` / `Option<_>` with rustc-quality message | `tests/semantic/test_try_operator.py::test_try_on_result_in_option_fn_errors` and the message-content test pass |
| 4 | Semantic rejects `x?` where `x` is not `Result<_, _>` / `Option<_>` | `test_try_on_int_errors`, `test_try_on_string_errors` pass |
| 5 | Semantic rejects `x?` at module top level | `test_try_at_module_top_errors` passes |
| 6 | Semantic accepts compatible `Result<T, E>` in `Result<_, E>` | `test_try_on_result_in_result_fn_ok` passes |
| 7 | Semantic accepts compatible `Option<T>` in `Option<_>` | `test_try_on_option_in_option_fn_ok` passes |
| 8 | Lowering desugars to match + early return — verified by reading emitted IR | `tests/llvm/test_try_operator.py::test_try_compiles_to_switch_plus_return` passes |
| 9 | Ok-path runs correctly | `test_try_runs_ok_path` passes |
| 10 | Err-path runs correctly and propagates the error | `test_try_runs_err_path` passes |
| 11 | Drop glue runs on early-return path (no memory leak) | `test_try_runs_drop_glue_on_early_return` valgrind-clean |
| 12 | Self-hosted mirror compiles and passes | `scripts/test_native.py --stage1 mapanare/self/mnc-stage1` returns 45/45 |
| 13 | `47_try_operator.mn` runs on both Python bootstrap and LLVM pipeline | golden harness comparison clean |
| 14 | Delta review returns PASS | `.reviews/deltas/v4.33.0-try_operator.md` committed with verdict |
| 15 | SPEC and cookbook updated; `check_docs_drift.py` clean | CI gate clean |
| 16 | LOW item: `mn_signal_propagate` depth limit + test | Phase 4.1 evidence |
| 17 | LOW item: `mnc-stage1` stripped or separate .dwp file | binary size measured before/after |
| 18 | LOW item: agent destroy message dtor | Phase 4.3 evidence + TSan test |
| 19 | `CARRY_FORWARD.md` updated (3 LOW rows CLOSED) | manual diff review |
| 20 | `SESSION_REPORT.md` written with fact-checkable claims | file exists at `docs/roadmap/v4/v4.33.0/SESSION_REPORT.md` |

---

## What v4.33.0 explicitly does NOT do

- **`try { ... }` blocks** (Rust-style try-block early-return block). Separate feature, separate design; not in scope. Candidate for a later v4.x release if user feedback demands it.
- **Implicit `From<E1> for E2` error conversion** (Rust-style `impl From`). Would require trait-based error widening, which is a bigger design question. Tracked as v4.x backlog.
- **`?` inside closures** — v4.33.0 semantics check the **outer function's** return type. `?` inside a closure that has its own return type is a compile error (rustc-quality message) for v4.33.0. Supporting it requires closure-return-type inference that's already solid but needs the `?` check to walk through the closure scope stack. Small follow-up, tracked as a v4.34.0+ nice-to-have.
- **`?` on user-defined Result-shaped types** — the v4.33.0 rule requires the inner type to be exactly `Result<T, E>` or `Option<T>`. User-defined two-variant enums (like `Either<L, R>`) do NOT get `?`. Making `?` dispatch through a trait is possible but is a bigger design question.
- **`foo?.bar` without explicit parens** — requires parser work to disambiguate; the v4.33.0 rule is that `?` always needs its operand fully specified. Users write `(foo?).bar`. If this is painful, address in a v4.34.0+ follow-up.
- **Any changes to `mapanare.lark`'s existing tokens** — `?` is a new token, adds no ambiguity, displaces nothing. Verify in Phase 1.1.
- **Any changes to `emit_llvm_text.py`** — the feature is pure AST-level desugar. The LLVM emitter sees no new instructions. This is a hard invariant; if it's violated during implementation, the scope has expanded and the release should slip.

---

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `?` introduces a grammar ambiguity with some existing token | low | medium | Phase 1.1 verifies no conflict before any downstream work |
| The semantic error messages don't meet "rustc quality" | medium | low | Phase 3.3 includes message-content tests; if they fail, iterate on wording before merging |
| The lowering desugar leaks memory on early-return | medium | medium | Phase 3.4 includes a valgrind test for the drop-glue path; if it fails, fix before merging |
| The self-hosted semantic stub can't check `TryExpr` because A7 isn't wired yet | high | low | Accepted: document the degraded error state in SESSION_REPORT, fix at v4.52.0 |
| Delta review surfaces design questions about error-type compatibility (implicit widening, `From` trait) | medium | low | Accepted: those are explicitly out of scope for v4.33.0 and can be filed as v4.34.0+ backlog |
| `mnc-stage1` strip step breaks something | low | low | Phase 4.2 includes a smoke test; opt-out via env var if users want debug symbols |
| Agent message dtor breaks an existing agent use case | low | medium | Default is NULL (existing behavior); opt-in for agents with managed messages. Zero-behavior-change for existing code |

---

## Reference

- [`docs/roadmap/v4/POST_RECOVERY_ROADMAP.md`](../POST_RECOVERY_ROADMAP.md) §Arc 1 — the context for why v4.33.0 is the `?` operator release
- [`.reviews/v4.31.0/README.md`](../../../../.reviews/v4.31.0/README.md) — the arc-end panel verdict
- [`.reviews/REVIEW_CADENCE.md`](../../../../.reviews/REVIEW_CADENCE.md) §Delta triggers — why `?` needs a delta review
- [`.reviews/CARRY_FORWARD.md`](../../../../.reviews/CARRY_FORWARD.md) — the 3 LOW items Phase 4 closes
- Rust Reference §operators.question-mark — https://doc.rust-lang.org/reference/expressions/operator-expr.html#the-question-mark-operator (the canonical reference for the semantics we're copying)

---

## After v4.33.0

v4.34.0 opens with the match decision-tree rewrite + exhaustiveness checker. Zero new syntax, pure correctness work. It closes `CARRY_FORWARD.md` A6 (the 69-line stage2/stage3 diff) and sets up v4.35.0's match guards + or-patterns release.

See [`docs/roadmap/v4/v4.34.0/PLAN.md`](../v4.34.0/PLAN.md).
