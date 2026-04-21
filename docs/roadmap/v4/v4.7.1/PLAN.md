# Mapanare v4.7.1 — Finish What We Started

> No deferred items. Every exit criterion from v4.5.0-v4.7.0 must be met.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.7.0

---

## Why This Version Exists

v4.2.0-v4.7.0 made structural improvements but deferred items that need the
WSL rebuild cycle. This version closes every gap before v4.8.0 features begin.

---

## Phase 1: Migrate UNKNOWN_TYPE in semantic.py (Python, testable)

### 1A. Audit and categorize all ~85 UNKNOWN_TYPE returns

- [ ] For each `return UNKNOWN_TYPE` in semantic.py:
  - If the function tried to resolve and failed → replace with `ERROR_TYPE` + `self._error()`
  - If it's a "not yet known" placeholder for forward refs → replace with `UNRESOLVED_TYPE`
  - If it's a fallback default → replace with `ERROR_TYPE`
- [ ] Target: 0 remaining `UNKNOWN_TYPE` references in semantic.py

### 1B. Post-analysis validation

- [ ] After `check()` completes, walk all resolved types
- [ ] Any remaining UNRESOLVED → error diagnostic
- [ ] Test: misspelled function name → compile error (not silent success)

---

## Phase 2: Replace hardcoded_field_index (self-hosted, needs rebuild)

- [ ] During emission, build `field_name → index` mapping from struct definitions
- [ ] Replace all calls to `hardcoded_field_index` with map lookup
- [ ] Delete the `hardcoded_field_index` function (~160 lines)
- [ ] `bash scripts/rebuild.sh` + `/golden`

---

## Phase 3: MIRType string kind → enum (self-hosted, needs rebuild)

- [ ] Add `TypeKind` enum to `mir.mn`
- [ ] Replace all `t.kind == "int"` with enum comparison
- [ ] Affects: lower.mn, lower_state.mn, emit_llvm.mn, emit_llvm_ir.mn
- [ ] `bash scripts/rebuild.sh` + `/golden` + `/stage2`

---

## Phase 4: Fix self-hosted workarounds (needs rebuild)

### 4A. PHI zeroinitializer
- [ ] Root-cause the zeroinitializer PHI in stage2
- [ ] Fix the lowerer or emitter
- [ ] Remove the workaround

### 4B. substr off-by-one
- [ ] Test `"hello".substr(1, 3)` with mnc-stage1
- [ ] Find and fix the off-by-one
- [ ] Remove the `.contains() + .replace()` workaround

### 4C. ABI mismatch (range construction)
- [ ] Fix C runtime range signature OR emitter calling convention
- [ ] Remove the inlined range construction workaround

---

## Phase 5: Self-hosted optimization passes (needs rebuild)

- [ ] Add constant folding pass to self-hosted MIR pipeline
- [ ] Add constant propagation (copy of const → inline)
- [ ] Add dead block elimination (reachability walk)
- [ ] `bash scripts/rebuild.sh` + `/golden` + `/stage2`

---

## Phase 6: Verification

- [ ] `.\dev.ps1 validate` or `make lint && make test`
- [ ] `/golden` — all pass
- [ ] `/rebuild` + `/stage2`
- [ ] `grep -c "UNKNOWN_TYPE" mapanare/semantic.py` → 0
- [ ] `grep -c "hardcoded_field_index" mapanare/self/emit_llvm.mn` → 0
- [ ] `grep -c '== "int"' mapanare/self/*.mn` → 0
- [ ] `grep -c "workaround\|avoid\|bug in stage2" mapanare/self/*.mn` → 0
- [ ] Verify fixed point: stage3 == stage4

---

## Exit Criteria

| Check | Required |
|-------|----------|
| UNKNOWN_TYPE references in semantic.py | 0 |
| Post-analysis catches misspelled functions | YES |
| hardcoded_field_index deleted | YES |
| MIRType uses enum (not strings) | YES |
| PHI zeroinitializer workaround removed | YES |
| substr off-by-one workaround removed | YES |
| ABI mismatch workaround removed | YES |
| Self-hosted constant folding exists | YES |
| Self-hosted dead block elimination exists | YES |
| All golden tests pass | YES |
| Self-hosted rebuild + fixed point | YES |
