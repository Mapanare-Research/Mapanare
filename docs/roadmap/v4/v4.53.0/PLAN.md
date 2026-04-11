# Mapanare v4.53.0 — UNRESOLVED / ERROR Type Split (A8)

> **Arc 5 release 2.** Closes `CARRY_FORWARD.md` A8. The self-hosted
> type system uses a single `UNKNOWN` kind where the Python side splits
> into `UNRESOLVED` (type not yet inferred — progress) and `ERROR`
> (type is definitely wrong — halt). The split makes semantic errors
> fire at the right place instead of cascading.

**Status:** PLANNED
**Breaking:** No (internal type system refactor; no user-visible grammar change)
**Prerequisite:** v4.52.0 (semantic pass must be wired)
**Delta review:** No
**Full panel:** No (v4.56.0)
**Estimated work:** 1 sprint
**Theme:** Error recovery. Make bad code produce good errors instead of cascading garbage.

---

## Why the split matters

Consider:
```mapanare
fn main() {
    let x = unknown_function(42)    // error: unknown_function is undefined
    let y = x + 1                   // error: cannot add UNKNOWN + Int
    let z = y.something()           // error: cannot call method on UNKNOWN
    print(z)                        // error: cannot print UNKNOWN
}
```

Without the split, a single error in the first line cascades into four errors, all of which are noise. The user has to mentally discard three of them.

With the split:
- `unknown_function` is truly undefined → `ERROR`
- `x` gets type `ERROR`
- Downstream uses of `x` see type `ERROR` and **suppress** cascading errors — they know the root cause is upstream

The user sees **one error**: "unknown_function is not defined." The suppressed errors don't fire because the checker recognizes `ERROR` as "already reported upstream; don't complain about derivatives of this."

`UNRESOLVED`, by contrast, is a progress marker: "I don't know this type yet, but I might figure it out on a later pass." Used during mutual recursion or forward references, where the checker visits uses before definitions. At the end of the pass, any `UNRESOLVED` that didn't get resolved becomes an `ERROR` ("I never figured out this type — something is missing").

The Python side split this in v4.5.0. The self-hosted side still uses `UNKNOWN`, which is both an "I don't know yet" and an "I can't figure this out" — mixing them means the checker can't tell "this is progress" from "this is a real error."

---

## Scope

### Type-kind enum extension

Before (self-hosted):
```mapanare
enum TypeKind {
    INT,
    FLOAT,
    STRING,
    BOOL,
    LIST,
    MAP,
    OPTION,
    RESULT,
    STRUCT,
    ENUM,
    FN,
    TENSOR,
    SIGNAL,
    STREAM,
    AGENT,
    UNKNOWN,  // ambiguous — mix of "not yet inferred" and "error"
}
```

After:
```mapanare
enum TypeKind {
    INT,
    ...
    UNRESOLVED,  // progress: type not yet inferred; may be resolved on a later pass
    ERROR,       // final: type is definitely wrong; downstream uses suppress cascade
}
```

### Error suppression rules

- `ERROR + anything = ERROR` (arithmetic on an error value is an error, but don't report)
- `ERROR.field = ERROR` (field access on an error value is an error, but don't report)
- `ERROR(arg) = ERROR` (calling an error value is an error, but don't report)
- `ERROR` used in a context that requires a specific type: do NOT report a new error; the `ERROR` is already reported upstream

### Unresolved → Error transition

- At the end of the semantic pass, walk the type table. For every entry still `UNRESOLVED`, emit a "type could not be resolved" error and set it to `ERROR`.
- In the Python side, this is already done (v4.5.0). Mirror it self-hosted.

---

## Phase 1 — Audit Python side

- [ ] `mapanare/types.py` — read the `TypeKind` enum. Confirm `UNRESOLVED` and `ERROR` are present. Read the methods that handle them.
- [ ] `mapanare/semantic.py` — find the error-suppression code. Typical pattern:
  ```python
  def check_binary_op(self, node: BinaryOp) -> Type:
      left_ty = self.check_expr(node.left)
      right_ty = self.check_expr(node.right)
      if left_ty.is_error() or right_ty.is_error():
          return Type.error()  # suppress cascading error
      # ... normal binop type check
  ```
- [ ] Audit all type-check methods. List every place where `ERROR` propagation should suppress cascading.

---

## Phase 2 — Self-hosted type system extension

- [ ] `mapanare/self/types.mn` — add `UNRESOLVED` and `ERROR` to the `TypeKind` enum.
- [ ] Keep `UNKNOWN` as an alias temporarily (or just replace) — pick one and document.
- [ ] Helper functions:
  ```mapanare
  fn type_is_error(t: Type) -> Bool { return t.kind == TypeKind::ERROR }
  fn type_is_unresolved(t: Type) -> Bool { return t.kind == TypeKind::UNRESOLVED }
  fn type_error() -> Type { return Type { kind: TypeKind::ERROR, ... } }
  fn type_unresolved() -> Type { return Type { kind: TypeKind::UNRESOLVED, ... } }
  ```

---

## Phase 3 — Self-hosted semantic pass update

- [ ] `mapanare/self/semantic.mn` — audit every type-check function. For each:
  - If it recurses into sub-expressions, check for `ERROR` at the sub level and suppress cascading
  - When it reports an error (`record_error`), set the returning type to `ERROR`, not `UNKNOWN`
- [ ] Specific functions to update:
  - `check_binary_op` — `ERROR` on either side → return `ERROR`, no new error
  - `check_field_access` — `ERROR` receiver → return `ERROR`, no new error
  - `check_fn_call` — `ERROR` callee → return `ERROR`, no new error
  - `check_index_get` — same
  - `check_method_call` — same
  - `check_match_expr` — `ERROR` scrutinee → return `ERROR`, no new error
  - `check_pattern` — `ERROR` expected type → still report missing pattern errors (those aren't cascading from the value)

---

## Phase 4 — Unresolved → Error transition

- [ ] At the end of `semantic_check`, walk the program's type table. For every expression still typed `UNRESOLVED`:
  - Fire an error: "type of this expression could not be inferred; add an explicit annotation"
  - Set to `ERROR`
- [ ] This catches mutual recursion failures that can't be resolved.

---

## Phase 5 — Tests

- [ ] `tests/semantic/test_error_suppression.py`:
  - `test_single_undefined_symbol_fires_one_error` — 4 cascading uses, only 1 error
  - `test_arithmetic_on_error_suppresses_cascade`
  - `test_field_access_on_error_suppresses_cascade`
  - `test_method_call_on_error_suppresses_cascade`
  - `test_match_on_error_suppresses_cascade`
  - `test_unresolved_becomes_error_at_end_of_pass`
  - `test_mutual_recursion_resolves_unresolved`
- [ ] `tests/self_hosted/test_error_cascade_self_hosted.py` — same tests, run through `mnc-stage1`, verify the error count matches the Python side

## Phase 6 — Fixed-point

- [ ] Fixed-point diff stays at 0 — the change is in the semantic pass, not the lowering.

## Phase 7 — LOW sweep

2 items.

## Phase 8 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.53.0
- [ ] `CHANGELOG.md [4.53.0]` — A8 closure
- [ ] `.reviews/CARRY_FORWARD.md` — A8 CLOSED
- [ ] SESSION_REPORT

---

## Exit criteria (12 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Self-hosted `TypeKind` has `UNRESOLVED` + `ERROR` variants | grep `types.mn` |
| 2 | Type helper functions exist | grep |
| 3 | `check_binary_op` suppresses cascade on ERROR | `test_arithmetic_on_error_suppresses_cascade` |
| 4 | `check_field_access` suppresses cascade | corresponding test |
| 5 | `check_fn_call` suppresses cascade | same |
| 6 | `check_method_call` suppresses cascade | same |
| 7 | `check_match_expr` suppresses cascade | same |
| 8 | UNRESOLVED → ERROR transition at end of pass | `test_unresolved_becomes_error_at_end_of_pass` |
| 9 | Mutual recursion resolves correctly | `test_mutual_recursion_resolves_unresolved` |
| 10 | Error count for cascading scenarios matches Python side | `test_single_undefined_symbol_fires_one_error` |
| 11 | Fixed-point diff still 0 | `verify_fixed_point.sh` |
| 12 | A8 CLOSED in `CARRY_FORWARD.md` | ledger diff |

---

## What v4.53.0 does NOT do

- **Delete `UNKNOWN`** — keep as alias for one release for safety. v4.54.0+ removes.
- **Full error recovery** beyond cascade suppression — the checker doesn't try to "fix" or "continue despite" errors
- **Multi-pass type inference** (Hindley-Milner style) — not in scope

---

## Reference

- [`.reviews/CARRY_FORWARD.md`](../../../../.reviews/CARRY_FORWARD.md) A8

---

## After v4.53.0

v4.54.0 closes A9 — the `emit_c.mn` decision (rewrite or delete the 770-line self-hosted C emitter).
