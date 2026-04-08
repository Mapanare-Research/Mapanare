# Mapanare v3.14.0 — "Cuaima" (Type System, Self-Hosted, Docs, CI)

> Fix every type system gap. Advance self-hosted completeness.
> Correct all documentation errors. Make CI honest.
> The last version before v4.0.0 production release.

**Status:** PLANNED
**Estimated scope:** Medium-Large (2-3 sessions)
**Breaking:** No
**Prerequisite:** v3.13.0 (clean C runtime, settled MnList ABI)

---

## Why This Version Exists

The v3.10.0 code review identified 3 categories of non-memory issues:

1. **Type system gaps** — generic arity not validated, arithmetic traits missing,
   `TypeInfo.__hash__` ignores args, ident patterns not treated as wildcards
2. **Self-hosted compiler gaps** — `scope_define` is a no-op (2+ versions),
   Stmt enum missing While/Break/Assert/Continue, no InterpString
3. **Documentation/CI** — tutorial syntax errors, version drift, spec numbering,
   CI `continue-on-error` masking failures

v3.14.0 closes all of these so v4.0.0 is purely a quality gate.

---

## Phase 1: Type System Fixes [P0]

### 1.1 — Generic arity validation

**Files:** `mapanare/types.py`, `mapanare/semantic.py:342-347`

`_resolve_type_expr` accepts any number of type arguments. `List<Int, String>` is
silently accepted.

**Fix:** Add to `types.py`:
```python
BUILTIN_GENERIC_ARITY: dict[str, int] = {
    "List": 1, "Map": 2, "Option": 1, "Result": 2,
    "Signal": 1, "Stream": 1, "Tensor": 1, "Channel": 1,
}
```
Check in `_resolve_type_expr` after resolving args. Error if count mismatches.

### 1.2 — `TypeInfo.__hash__` include args

**File:** `mapanare/types.py:142`

Change: `hash((self.kind, self.name))` -> `hash((self.kind, self.name, tuple(self.args)))`

One-line fix. Prevents `List<Int>` and `List<String>` from hashing identically.

### 1.3 — IdentPattern as wildcard in exhaustiveness

**File:** `mapanare/semantic.py:862`

A binding pattern like `other =>` (where `other` is not a variant name) should be
treated as a wildcard for exhaustiveness purposes. Currently triggers false
non-exhaustive errors.

**Fix:** After checking `IdentPattern.name` against variants, add:
```python
elif isinstance(arm.pattern, IdentPattern) and arm.pattern.name not in all_variants:
    has_wildcard = True
    break
```

### 1.4 — WASM CHAR type mapping

**File:** `mapanare/emit_wasm.py:452-488`

Add `if kind == TypeKind.CHAR: return _WASM_I32` between BOOL and VOID cases.

### 1.5 — Arithmetic traits (Add/Sub/Mul/Div)

**Files:** `mapanare/types.py:303`, `mapanare/semantic.py:596`, `mapanare/emit_llvm_mir.py`

Add `Add`, `Sub`, `Mul`, `Div` to `BUILTIN_TRAITS` with `(self, other: Self) -> Self`
signature. Extend binary op dispatch in semantic checker. Emit trait method calls
in LLVM backend for struct/enum operands with matching impl.

---

## Phase 2: Self-Hosted Compiler [P1]

### 2.1 — Fix `scope_define`

**File:** `mapanare/self/semantic.mn:190-196`

The `push` call is commented out. Root cause: `List.push()` doesn't work on struct
fields passed by value.

**Fix:** Use `mut` local binding pattern:
```mn
fn scope_define(scope: Scope, name: String, sym: Symbol) -> Scope {
    let mut syms: List<Symbol> = scope.symbols
    syms.push(sym)
    return new Scope { parent: scope.parent, symbols: syms }
}
```
The local copy avoids struct-field mutation. This should work because `syms` is a
local, not a field.

### 2.2 — Add While/Break/Continue/Assert to Stmt enum

**Files:** `mapanare/self/ast.mn:104-111`, `parser.mn`, `lower.mn`

Add 4 variants:
```mn
enum Stmt {
    Let(String, Bool, Option<TypeExpr>, Expr),
    ExprStmt(Expr),
    Return(Option<Expr>),
    For(String, Expr, Block),
    While(Expr, Block),
    Break,
    Continue,
    Assert(Expr, Option<String>),
    SignalDecl(String, Bool, Option<TypeExpr>, Expr, Bool),
    StreamDecl(String, Option<TypeExpr>, Expr)
}
```

Update parser `parse_stmt` for KW_WHILE/KW_BREAK/KW_CONTINUE/KW_ASSERT.
Update lowerer to handle new variants.

### 2.3 — Add InterpString to Expr enum

**Files:** `mapanare/self/ast.mn`, `parser.mn`, `lower.mn`, `lexer.mn`

Add `InterpString(List<InterpPart>)` variant. Parse `"...{expr}..."` syntax.
Lower to concat chain.

---

## Phase 3: Documentation [P0 — v4.0.0 blocker]

### 3.1 — Fix getting-started tutorial

**File:** `docs/getting-started.md`

- `Point(3.0, 4.0)` -> `new Point { x: 3.0, y: 4.0 }` (match grammar)
- `Shape_Circle(5.0)` -> `Circle(5.0)` (match spec/golden tests)
- Remove dead `return 0.0` after exhaustive match
- Every code sample must compile

### 3.2 — Fix version drift + debug info producer

**Files:** `mapanare/self/main.mn:31`, `mapanare/emit_llvm_mir.py:666`

- Update self-hosted version: `"mapanare 3.14.0"`
- Read VERSION file for debug info producer instead of hardcoded `"2.0.1"`
- Add `main.mn` to `/bump-version` skill targets

### 3.3 — Spec section 27 numbering + batch keyword

**File:** `docs/SPEC.md`

- Fix `24.1`/`24.2`/`24.3` -> `27.1`/`27.2`/`27.3`
- Remove `batch` keyword from spec (signals work without it — phantom feature)

### 3.4 — Update CLAUDE.md line counts

**File:** `CLAUDE.md`

Module table says "9,400+ lines across 10 modules" — actual is 15,084 across 11.
Update individual module line counts.

---

## Phase 4: CI Integrity [P0]

### 4.1 — Remove `continue-on-error` on stage1 build

**File:** `.github/workflows/ci.yml:67`

A broken compiler build currently shows green CI. Remove `continue-on-error: true`
from the `Build mnc-stage1` step.

### 4.2 — Add `-Werror` to local build scripts

**Files:** `scripts/build_stage1.py:88`, `scripts/build_from_seed.sh:76`

Add `-Wall -Wextra -Werror` to all gcc/clang invocations. Match CI strictness.

---

## New Culebra Template

1. **`bootstrap/scope-define-noop.yaml`** — Detect self-hosted functions with
   commented-out `push` returning empty scopes. Regression gate for Phase 2.1.

---

## Verification Checklist

- [ ] `./dev.ps1 validate` — all tests pass
- [ ] `pytest tests/semantic/test_types.py -v` — new arity/hash tests
- [ ] `/stage2` — self-hosted produces valid IR with scope_define working
- [ ] `/golden` — 32/32 pass
- [ ] `/culebra-scan` — clean
- [ ] `grep "continue-on-error" .github/workflows/ci.yml` — zero on critical steps
- [ ] Compile getting-started tutorial examples — all parse
- [ ] `grep -r "24\\.1\\|24\\.2" docs/SPEC.md` — zero matches

## Expected Impact

| Reviewer | v3.13.0 (est) | Expected v3.14.0 | Delta |
|----------|---------------|-------------------|-------|
| Cobra | 8.9 | 9.2-9.5 | +0.3-0.6 |
| Anaconda | 9.0 | 9.3-9.5 | +0.3-0.5 |
| Coral | 8.5 | 9.0-9.3 | +0.5-0.8 |
| Boa | 9.1 | 9.3 | +0.2 |
| Aggregate | ~8.8 | ~9.0-9.2 | +0.2-0.4 |

---

## After v3.14.0 -> v4.0.0

With v3.13.0 + v3.14.0 complete, v4.0.0 becomes a pure quality gate:
- 3 end-to-end demo programs
- Spec updated for v3.x features
- Fixed point verification
- Release artifacts
- Target: 9.0+ aggregate, zero NEEDS WORK
