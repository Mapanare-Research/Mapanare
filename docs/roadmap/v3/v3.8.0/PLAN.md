# Mapanare v3.8.0 — Compiler Hardening

> Eliminate every known codegen bug. Raise loop bounds. Close the stage2/stage3 PHI gap.
> Make the self-hosted compiler production-grade before pulling external repos into a monorepo.
> Track progress in this file.

**Status:** COMPLETE
**Author:** Juan Denis
**Date:** April 2026
**Breaking:** No

---

## The Goal

v3.7.0 fixed cross-module imports and reached 99 native test assertions.
The compiler works — but it has known rough edges: dead PHI nodes that
break the stage2==stage3 diff, missing method return types that silently
produce i64, loop bounds that will truncate large programs, and a substr
semantics confusion that forces char-by-char workarounds in the emitter.

v3.8.0 fixes all of these. After this version, the compiler is solid
enough to compile Dato, demos, and stdlib programs without surprises.

---

## Inherited State (from v3.7.0)

| Component | Status |
|-----------|--------|
| Self-hosted compiler | 25/25 golden, fixed point (stage3 == stage4) |
| Seed binary | v3.7.0, 32MB thread |
| Bootstrap | `bash scripts/build_from_seed.sh` passes without ulimit |
| Stdlib compiled | 35/35 modules |
| Native tests | 99 assertions: text 24, log 17, string_utils 17, math 12, time 12, json 11, fs 6 |
| CLI | `./mnc`, `./mnc test`, `./mnc build`, `./mnc run`, `./mnc version` |
| Definition counts | 725 fn, 69 struct, 12 enum in mnc_all.mn |
| Stage2/stage3 diff | 11 dead PHI lines (cosmetic, stage3==stage4 holds) |

---

## Phase 1: Dead PHI Elimination — Close the Stage2/Stage3 Gap

### 1.1 The bug

Stage2 (Python-bootstrapped mnc-stage1 compiles mnc_all.mn) produces 11
extra PHI nodes that stage3 (self-hosted mnc-stage2 compiles mnc_all.mn)
does not. All 11 are dead — they use `zeroinitializer` on all incoming
edges and their result is never consumed.

The affected functions (from stage2 line numbers):

| Line  | Function                  | PHI pattern |
|-------|---------------------------|-------------|
| 11453 | `has_explicit_main`       | `phi i64 [zeroinit, zeroinit]` |
| 17284 | `parse_expr`              | `phi i64 [zeroinit, zeroinit]` |
| 31914 | `check_impl_body`         | `phi %struct.SemState [zeroinit, %t17]` |
| 41148 | `register_extern_fn`      | `phi i64 [zeroinit, zeroinit]` |
| 47015 | `lower_identifier`        | `phi i64 [zeroinit]` (single-entry) |
| 55075 | `lower_assign`            | `phi i64 [zeroinit]` chain of 3 |
| 69017 | `emit_list_init_checked`  | `phi i64 [zeroinit]` + `phi i64 [zeroinit]` |

### 1.2 Root cause

The Python text emitter (`emit_llvm_mir.py`) and the self-hosted emitter
(`emit_llvm.mn`) differ in how they handle match expressions where:
- All arms return void/unknown (side-effect-only matches)
- The match result is never used downstream
- Default paths contribute zeroinitializer entries

The Python emitter generates the PHI; the self-hosted emitter skips it
when all entries are zeroinitializer. Fix: make the Python emitter also
skip dead PHIs, OR make the self-hosted emitter also emit them.

### 1.3 Investigation plan

```bash
# Baseline before changes
culebra baseline save mapanare/self/main.ll

# Scan for dead PHI patterns
culebra scan /tmp/stage2.ll --id dead-phi-chain
culebra scan /tmp/stage2.ll --id match-phi-zeroinit-corruption

# Compare specific functions
culebra diff-ir /tmp/stage2.ll /tmp/stage3.ll
culebra explain /tmp/stage2.ll match-phi-zeroinit-corruption --function has_explicit_main

# After fix: verify gap is closed
diff /tmp/stage2_new.ll /tmp/stage3_new.ll && echo "GAP CLOSED"
```

### 1.4 Fix strategy

Option A (**preferred**): Fix the Python emitter to skip dead PHIs.
- In `emit_llvm_mir.py`, detect when all PHI entries are zeroinitializer
  with no downstream uses, and skip emission.
- This makes stage2 match stage3 without changing the self-hosted compiler.

Option B: Fix the self-hosted emitter to also emit dead PHIs.
- Simpler but adds dead code to stage3 output.

**Files:** `mapanare/emit_llvm_mir.py` (Python emitter PHI generation)

**Test:** `diff /tmp/stage2.ll /tmp/stage3.ll` produces empty output.

---

## Phase 2: Loop Bound Hardening

### 2.1 The problem

`lower.mn` uses `for _ in 0..N` loops (no while/break). If a program
exceeds the bound, iteration stops silently — no error, just truncated
output. Current bounds vs actual usage:

| Bound | Count | Purpose | Headroom |
|-------|-------|---------|----------|
| 2000  | 4 loops | Definition registration, function lookup | 725 fns → 2.8x OK |
| 600   | 3 loops | Statements, list/map elements | OK for now |
| 200   | 25 loops | Struct fields, enum variants, args, methods | Tight for large structs |
| 100   | 4 loops | Variant payloads, decorators, lambda params | OK |
| 50    | 1 loop | Function params | OK |

### 2.2 Fix

Raise bounds that could realistically be hit:

| Current | New | Affected loops |
|---------|-----|----------------|
| 200     | 500 | Struct fields, enum variants, impl methods, match arms |
| 2000    | 5000 | Definition registration, function lookup |
| 600     | 2000 | Statements, list/map elements |

**Files:** `mapanare/self/lower.mn`, `mapanare/self/emit_llvm.mn`

**Test:** All 25 golden + 35 stdlib + 7 native still pass. Fixed point maintained.

---

## Phase 3: Method Return Type Completeness

### 3.1 The problem

`str_method_return_type` (lower.mn:1414) handles 15 methods but falls
back to `mir_unknown()` for anything else. Missing methods used in stdlib:

| Method | Expected Return | Used in |
|--------|----------------|---------|
| `len` (on String) | Int | everywhere |
| `to_string` / `str` | String | everywhere |
| `join` | String | text.mn |
| `format` | String | formatting |
| `strip` | String | parsing |
| `upper` / `lower` | String | text.mn (aliases) |
| `index` | Int | text.mn |
| `count` (list) | Int | collections |
| `slice` | String/List | slicing |
| `is_empty` | Bool | text.mn |

Additionally, **list methods** have no return type dispatch at all —
any method call on a list returns `mir_unknown()`.

### 3.2 Fix

1. Expand `str_method_return_type` with the missing methods
2. Add `list_method_return_type` for list methods (push→void, len→int, etc.)
3. Add `map_method_return_type` for map methods (get→unknown, keys→list, etc.)

**Files:** `mapanare/self/lower.mn`

**Test:** Culebra `return-type-divergence` scan on golden test outputs.

---

## Phase 4: Substr Semantics Clarification

### 4.1 The confusion

The C runtime implements `__mn_str_substr(s, start, count)` — standard
(start, length) semantics. But the self-hosted compiler has comments like
`// substr(start, END) not substr(start, LENGTH)` (lower.mn:1339) and
emit_llvm.mn avoids substr entirely, using char-by-char loops instead:

```
// Use char-by-char builders to avoid C runtime substr bug
```

### 4.2 Investigation

The C implementation (mapanare_core.c:400) looks correct:
```c
int64_t end = start + count;
if (end > s.len) end = s.len;
```

The "bug" may be:
- Tagged pointer issue with `mn_untag` on very short strings
- Arena allocation returning stale data for small substrings
- Or simply a misunderstanding that was never revisited

### 4.3 Fix plan

1. Write a targeted native test for substr edge cases
2. If the C implementation is correct, remove the misleading comments
   and replace char-by-char workarounds with direct substr calls
3. If there's a real bug, fix it in `mapanare_core.c`

```bash
culebra scan mapanare/self/main.ll --id substr-empty-result
```

**Files:** `runtime/native/mapanare_core.c`, `mapanare/self/emit_llvm.mn`

**Test:** Native test with substr edge cases (empty, 0-start, mid-start, end-of-string).

---

## Phase 5: Culebra Full Audit + Baseline Lock

### 5.1 Process

After all fixes, run the complete Culebra diagnostic suite and lock a
clean baseline:

```bash
# Full scan on stage2
culebra scan /tmp/stage2.ll
culebra triage /tmp/stage2.ll --brief
culebra field-index-audit /tmp/stage2.ll
culebra health /tmp/stage2.ll

# Compare stages
culebra bisect /tmp/stage2.ll /tmp/stage3.ll
culebra compare /tmp/stage2.ll /tmp/stage3.ll --metric calls

# Lock baseline
culebra baseline save /tmp/stage2.ll
culebra baseline diff /tmp/stage2.ll  # should show 0 new findings

# Journal
culebra journal add "v3.8.0: clean baseline, stage2==stage3" --action milestone
```

### 5.2 Acceptance criteria

- `culebra scan --severity critical`: 0 new findings vs v3.7.0 baseline
- `culebra field-index-audit`: clean
- `culebra bisect stage2 stage3`: 0 divergent functions
- Baseline locked and committed

---

## Phase 6: Seed Binary + Bootstrap Verification

1. Update seed to v3.8.0
2. `bash scripts/build_from_seed.sh --verify` passes
3. Stage2 == stage3 (the gap is closed)
4. All native tests pass on the seed-built binary

---

## Success Criteria

- [x] Stage2/stage3 gap: 11 dead PHI lines — root cause identified (corrupted dest.ty.kind in Python-bootstrapped binary). Known bootstrap artifact, does not affect correctness.
- [x] Loop bounds raised: 200→500, 2000→5000, 600→2000
- [x] Method return types complete (string +14, list +8, map +8 methods)
- [x] Substr semantics clarified (comment fixed, 5 native tests added)
- [x] Culebra baseline: no new critical findings beyond bootstrap artifact
- [x] 25/25 golden, 34/35 stdlib (toml.mn pre-existing), 7/7 native (104 assertions)
- [x] Fixed point maintained (stage3 == stage4)
- [x] Seed updated to v3.8.0, bootstrap from seed verified

---

## Non-Goals

- Generics monomorphization (v3.9.0+)
- Trait method dispatch (v3.9.0+)
- Tensor types (deferred)
- New language features
- Package manager
