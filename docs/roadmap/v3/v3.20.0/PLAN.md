# Mapanare v3.20.0 — "Sapa" (Type Safety + Optimizer Quality)

> Complete arithmetic trait lowering. Fix optimizer convergence. Start reducing
> the LLVM emitter's type-safety gaps (_coerce_arg, global state).

**Status:** DONE
**Estimated scope:** Medium (2 sessions)
**Breaking:** No
**Prerequisite:** v3.19.0

---

## Items

### 1. Arithmetic trait dispatch not lowered [HIGH]

**File:** `mapanare/lower.py:1538`
**Reporter:** Cobra (H6)

Semantic checker accepts `Vec2 + Vec2` via Add trait, but lowerer only handles
`"eq"` and `"cmp"`. Arithmetic annotations silently ignored. Silent wrong code.

**Fix:** After the `if trait == "cmp":` block (~line 1556), add:
```python
if trait in ("add", "sub", "mul", "div"):
    dest = self._make_value(ty=lhs.ty)
    self._emit(Call(dest=dest, fn_name=trait, args=[lhs, rhs]))
    return dest
```
~20 lines. Method resolution maps trait name to impl method via existing dispatch.

### 2. MIR optimizer O2 single-pass, no convergence [MEDIUM]

**File:** `mapanare/mir_opt.py:1123-1141`
**Reporter:** Cobra (M3)

O2+ passes run once. Copy prop can expose dead code, branch simp can create
unreachable blocks. O1 correctly iterates (max 10), O2 does not.

**Fix:** Wrap lines 1123-1141 in convergence loop:
```python
for _ in range(max_iterations):
    changed = False
    changed |= copy_propagation(fn, stats)
    changed |= branch_simplification(fn, stats)
    ...
    if not changed:
        break
```

### 3. Duplicate constant folding AST+MIR [MEDIUM]

**File:** `mapanare/optimizer.py`
**Reporter:** Cobra (M5)

AST optimizer and MIR optimizer both fold `2 + 3` -> `5`. MIR pass is canonical.

**Fix:** Remove AST-level constant folding from `optimizer.py`. Keep AST optimizer
for non-folding passes only (constant propagation, dead branch elimination).

### 4. Emitter global mutable state (non-reentrant) [MEDIUM]

**File:** `mapanare/emit_llvm_mir.py:148,154,158`
**Reporter:** Cobra (M8)

`_current_alloca_block`, `_target_ptr_size`, `_COERCE_FALLBACK_COUNT` are module
globals. Two emitter instances would corrupt each other.

**Fix:** Move all three to `LLVMMIREmitter` instance variables. Update all references.

### 5. Debug info hardcodes 64-bit struct member sizes [LOW]

**File:** `mapanare/emit_llvm_mir.py:760-770`
**Reporter:** Rattler (L9)

Every struct member reported as 64 bits in DWARF. GDB/LLDB show wrong field widths.

**Fix:** Look up actual field type from `self._struct_types[name].elements[i]`.
Compute DWARF size from LLVM type. Update offset calculation to match.

### 6. `_coerce_arg` reduction — phase 1 [HIGH]

**File:** `mapanare/emit_llvm_mir.py:180-301` (37 call sites)
**Reporter:** Cobra (H1, 3rd review in a row)

**Approach:**
1. Add per-call-site logging (not just global counter)
2. Run full golden test suite, identify top 10 most frequent patterns
3. Fix type propagation in MIR for those patterns
4. Target: reduce from 37 to ~20 call sites

### 7. `Symbol.kind: str` -> enum [LOW]

**File:** `mapanare/semantic.py:155-160`
**Reporter:** Anaconda (I-5)

9 string values for symbol kinds. Should be `SymbolKind` enum.

**Fix:** Create `SymbolKind` enum. Replace all `kind == "variable"` comparisons.

---

## Verification

- [ ] `Vec2 + Vec2` with `impl Add` produces correct output
- [ ] MIR optimizer O2 on loop-heavy program: improved codegen vs O1
- [ ] `_COERCE_FALLBACK_COUNT` reduced by >30% across golden tests
- [ ] `/golden` — all pass
- [ ] MyPy passes after emitter changes
