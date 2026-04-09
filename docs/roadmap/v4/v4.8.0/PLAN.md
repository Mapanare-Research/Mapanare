# Mapanare v4.8.0 — Solid Core (Complete)

> No new features until every known issue is fixed.
> Culebra 2.3.1 (59/59 templates) is the quality gate.

**Status:** IN PROGRESS
**Breaking:** No
**Prerequisite:** v4.7.1

---

## Culebra Baseline (59 templates, scanned 2026-04-09)

### Golden test IR (06_struct, 07_enum, 11_closure)
| Severity | Count | Templates |
|----------|-------|-----------|
| CRITICAL | 3 | `field-index-always-zero` (1), `undefined-named-type` (1), `missing-drop-glue` (1) |
| HIGH | 337 | `stage-output-divergence` (303), `fixed-point-delta` (18), `byte-count-mismatch` (15), `string-track-noop` (1) |
| MEDIUM | 5 | minor |

### C runtime
| Severity | Count | Templates |
|----------|-------|-----------|
| CRITICAL | 10 | `missing-typedef` (9), `c-memcpy-size-mismatch` (1) |
| HIGH | 1 | `c-non-atomic-shared-global` (1) |

**Target: 0 CRITICAL, 0 HIGH on golden IR. 0 CRITICAL on C runtime.**

---

## Phase 1: Fix field-index-always-zero (self-hosted emitter)

**Culebra finding:** `CRITICAL [field-index-always-zero]`
**Root cause:** `hardcoded_field_index()` returns 0 for unregistered structs

- [ ] In emit_llvm.mn, build field→index map from struct definitions during init
- [ ] Replace `hardcoded_field_index(name, field)` calls with map lookup
- [ ] Delete the ~160-line function
- [ ] Rebuild + golden + stage2
- [ ] Culebra rescan: `field-index-always-zero` drops to 0

**Files:** `mapanare/self/emit_llvm.mn`

---

## Phase 2: Fix undefined-named-type (self-hosted emitter)

**Culebra finding:** `CRITICAL [undefined-named-type]`
**Root cause:** Self-hosted emitter doesn't emit `%StructName = type { ... }` definitions

- [ ] In emit_llvm.mn, emit struct type definitions at module top
- [ ] Use struct field info from MIR module
- [ ] Rebuild + golden + stage2
- [ ] Culebra rescan: `undefined-named-type` drops to 0

**Files:** `mapanare/self/emit_llvm.mn`

---

## Phase 3: Fix string-track-noop (Python emitter)

**Culebra finding:** `HIGH [string-track-noop]`
**Root cause:** Some string-producing calls lack tracking allocas

- [ ] Identify which call site is missing tracking
- [ ] Add `_track_string` call
- [ ] Verify with Culebra

**Files:** `mapanare/emit_llvm_text.py`

---

## Phase 4: Fix byte-count-mismatch (Python emitter)

**Culebra finding:** `HIGH [byte-count-mismatch]`
**Root cause:** String constants declare `[N x i8]` with wrong N

- [ ] Run `culebra strings` on golden outputs
- [ ] Fix byte count calculation in emit_llvm_text.py
- [ ] Verify

**Files:** `mapanare/emit_llvm_text.py`

---

## Phase 5: Fix C runtime Culebra findings

**Culebra findings:**
- `CRITICAL [missing-typedef]` (9 locations)
- `CRITICAL [c-memcpy-size-mismatch]` (1 location)
- `HIGH [c-non-atomic-shared-global]` (1 location)

- [ ] Add missing typedefs / forward declarations
- [ ] Fix memcpy size mismatch
- [ ] Fix remaining non-atomic global
- [ ] Verify: `culebra scan runtime/native/*.c` clean

**Files:** `runtime/native/mapanare_core.c`, `runtime/native/mapanare_runtime.c`

---

## Phase 6: MIRType string → enum (self-hosted)

- [ ] Add TypeKind enum to mir.mn
- [ ] Replace all `t.kind == "int"` with enum match
- [ ] Rebuild + golden + stage2

**Files:** `mapanare/self/mir.mn`, `lower.mn`, `lower_state.mn`, `emit_llvm.mn`, `emit_llvm_ir.mn`

---

## Phase 7: Fix self-hosted workarounds

- [ ] PHI zeroinitializer: root-cause and fix
- [ ] substr off-by-one: root-cause and fix
- [ ] ABI mismatch (range): root-cause and fix
- [ ] Rebuild + golden + stage2 after each fix
- [ ] `grep "workaround\|avoid\|bug in stage2" mapanare/self/*.mn` → 0

**Files:** `mapanare/self/emit_llvm.mn`, `runtime/native/mapanare_core.c`

---

## Phase 8: semantic.mn memory safety

**Valgrind trace:** `ast__expr_ident_name` invalid reads in `check_call_resolved`

- [ ] Audit AST accessor functions for unsafe pointer arithmetic
- [ ] Fix memory-safe access patterns
- [ ] Re-enable `check()` in compile()
- [ ] Remove `skip_struct_ret`
- [ ] Rebuild + golden + stage2 + valgrind clean

**Files:** `mapanare/self/semantic.mn`, `mapanare/self/ast.mn`, `mapanare/self/main.mn`, `mapanare/emit_llvm_text.py`

---

## Phase 9: String pooling

**Blocked by Phase 8** (needs skip_struct_ret removed first)

- [ ] Add constant-string marker to tag-bit system
- [ ] `str(true)`/`str(false)` return constant strings
- [ ] Small int pool -128..127
- [ ] Verify with valgrind: no double-free

**Files:** `runtime/native/mapanare_core.c`

---

## Phase 10: Self-hosted optimization passes

- [ ] New module: `mapanare/self/mir_opt.mn`
- [ ] Constant folding (BinOp on Const → Const)
- [ ] Constant propagation (Copy of Const → inline)
- [ ] Dead block elimination (reachability walk)
- [ ] Wire into compile() pipeline
- [ ] Rebuild + golden + stage2

**Files:** `mapanare/self/mir_opt.mn` (new), `mapanare/self/main.mn`

---

## Phase 11: Final Culebra gate + verification

- [ ] `culebra scan /tmp/g06.ll` → 0 CRITICAL, 0 HIGH
- [ ] `culebra scan /tmp/g07.ll` → 0 CRITICAL, 0 HIGH
- [ ] `culebra scan /tmp/g11.ll` → 0 CRITICAL, 0 HIGH
- [ ] `culebra scan runtime/native/mapanare_core.c` → 0 CRITICAL
- [ ] 40/40 golden
- [ ] 11/11 stage2
- [ ] Valgrind clean on golden tests
- [ ] `grep "hardcoded_field_index" mapanare/self/emit_llvm.mn` → 0
- [ ] `grep '== "int"' mapanare/self/*.mn` → 0
- [ ] `grep "workaround\|avoid\|bug in stage2" mapanare/self/*.mn` → 0

---

## Exit Criteria

| Check | Required |
|-------|----------|
| Culebra: 0 CRITICAL on golden IR | YES |
| Culebra: 0 HIGH on golden IR | BEST EFFORT (stage-output-divergence may be structural) |
| Culebra: 0 CRITICAL on C runtime | YES |
| hardcoded_field_index deleted | YES |
| MIRType uses enum | YES |
| All workarounds removed | YES |
| semantic.mn memory-safe | YES |
| skip_struct_ret removed | YES |
| str(true) = constant | YES |
| Self-hosted optimizer exists | YES |
| 40/40 golden | YES |
| 11/11 stage2 | YES |
| Valgrind clean | YES |
