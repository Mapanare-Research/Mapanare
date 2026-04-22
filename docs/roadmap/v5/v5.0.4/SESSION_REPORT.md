# v5.0.4 SESSION_REPORT — Cb.15: ABI Classifier to Self-Hosted

**Date:** 2026-04-21
**Scope:** Port ABI.1 sret classifier from Python (`abi.py`) to
self-hosted (`abi.mn` + `emit_llvm.mn`)
**Closes:** Cb.15 (Cobra v4.154.0)

---

## Files changed

### New files

| File | Lines | Role |
|------|-------|------|
| `mapanare/self/abi.mn` | 75 | ABI return-convention classifier: `abi_sysv_use_sret`, `abi_win64_use_sret`, `abi_aapcs64_use_sret`, `abi_classify_return_sret` |

### Modified files

| File | Lines changed | What |
|------|--------------|------|
| `mapanare/self/emit_llvm.mn:13` | +1 | `import self::abi` |
| `mapanare/self/emit_llvm.mn:1607-1666` | +43 new | `enum_byte_size()` + `use_sret_return()` wrapper functions |
| `mapanare/self/emit_llvm.mn:3004` | 1 changed | Call-site sret (registered fn): `is_byref_type_st` → `use_sret_return` |
| `mapanare/self/emit_llvm.mn:3025` | 1 changed | Call-site sret (unregistered fn): `is_byref_type_st` → `use_sret_return` |
| `mapanare/self/emit_llvm.mn:3193` | 1 changed | Return statement: `is_byref_type_st` → `use_sret_return` |
| `mapanare/self/emit_llvm.mn:3455` | 1 changed | Function header: `is_byref_type_st` → `use_sret_return` |
| `scripts/concat_self.sh:16` | +1 | Register `abi.mn` in MODULES (before `mir_opt.mn`) |

### Unchanged (argument passing)

`is_byref_type_st` is still used at 5 sites for **argument** passing
(param byref). Only return-type sret decisions changed.

---

## sret count: pre → post

| Metric | Pre (v5.0.3) | Post (v5.0.4) | Delta |
|--------|-------------|---------------|-------|
| stage2.ll sret occurrences | 2,263 | 4,112 | **+1,849** |
| `{ptr,i64,i64,i64,i64}` by-value returns | 60 | 0 | −60 |
| `{ptr,i64}` register returns | 147 | 147 | 0 |
| `{i1,ptr}` register returns | 35 | 35 | 0 |
| Named-type by-value returns | 443 | 406 | −37 |

---

## Verification

- [x] Cobra's verification grep: `grep -c 'sret\|classify_return\|_use_sret' mapanare/self/emit_llvm.mn` → 12 (was 0)
- [x] Golden tests: 54/66 (unchanged from v5.0.3)
- [x] Fixed-point: NEAR (4-line diff, Dr.1 version placeholder only)
- [x] stage2.ll llvm-as: valid
- [x] stage3.ll llvm-as: valid
- [x] Valgrind: 0 CLEAN / 62 WARNINGS_ONLY / 4 ERRORS (Ge.1 residuals, unchanged)
- [x] ASan: 55 CLEAN / 0 ASAN_ERROR / 11 CRASH_NO_ASAN (unchanged)
- [x] struct_alloc via mnc-stage1: `make_point` now uses sret (was by-value)
- [x] Binary size: 3,583,120 → 3,603,616 bytes (+0.6%)

---

## Hypothesis outcome

The HYPOTHESIS.md predicted struct_alloc would improve from ~70× Rust
to ≤1.5× Rust. This was incorrect — the 70× gap was from Rt.1
(v4.124.0 unboxed enums, eliminating malloc), not from sret. The sret
classifier is documented as "performance neutral" (v4.149.0 SESSION_REPORT).

Both baseline and new struct_alloc run in ~1ms at `-O2`. The fix is
**ABI correctness and parity**, not a performance optimization. The
5% rule does not apply.

---

## Known limitation

Internal compiler structs registered via `make_entry` (e.g., `FnEntry`,
`CompileResult`) have `llvm_type = "%struct.Name"` instead of the
inline `{...}` form. `struct_byte_size` calls `llvm_aggregate_size`
on this, which misparses it as 8 bytes. These structs are misclassified
as register even when their real size exceeds 16B. This is a
**pre-existing limitation** — `is_byref_type_st` had the same
miscounted path — not a regression. See **Rt.4** in PARITY_GAPS.md.

---

## Docket status

| ID | Severity | Status | Note |
|---|---|---|---|
| **Cb.15** | MEDIUM | **CLOSED** | This release |
| Rt.4 | MEDIUM | Open | Becomes more load-bearing after Cb.15 |
