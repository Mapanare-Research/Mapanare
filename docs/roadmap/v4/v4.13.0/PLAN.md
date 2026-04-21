# Mapanare v4.13.0 — Culebra Gate + Foundation Complete

> Zero Culebra findings. Every exit criterion met. Foundation is complete.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.12.0

---

## Scope

Final verification version. Run Culebra v2.3.1+ on everything, fix any
real findings, document false positives, and declare the foundation complete.

---

## Phase 1: Fix Culebra template false positives

- [ ] Report false positives to Culebra repo:
  - `missing-typedef`: anonymous struct typedef is valid C (9 sites)
  - `c-memcpy-size-mismatch`: double→uint64_t type pun (same size)
  - `c-non-atomic-shared-global`: local variable flagged as global
  - `field-index-always-zero`: correct index-0 access flagged
  - `undefined-named-type`: type IS defined, regex doesn't look up
- [ ] Fix templates in Culebra repo or document as known false positives

## Phase 2: Full Culebra scan

- [ ] Scan ALL golden test outputs (40 files)
- [ ] Scan C runtime (mapanare_core.c, mapanare_runtime.c)
- [ ] Scan stage2 IR (if main.ll is too large, scan individual modules)
- [ ] Triage: real findings vs false positives

## Phase 3: Fix any real findings

- [ ] Fix any genuine CRITICAL or HIGH findings
- [ ] Rebuild + golden + stage2

## Phase 4: Final verification

- [ ] 40/40 golden
- [ ] 11/11 stage2
- [ ] Valgrind clean on golden tests
- [ ] Python test suite passes
- [ ] No workaround comments in emit_llvm.mn
- [ ] MIRType uses named constants or enum
- [ ] skip_struct_ret removed
- [ ] str(true) = constant
- [ ] Self-hosted optimizer exists
- [ ] Culebra: 0 real CRITICAL findings

## Phase 5: Write final summary

- [ ] `docs/roadmap/v4/REFACTOR_SUMMARY.md` — complete v4.2.0-v4.13.0 arc
- [ ] Lines deleted, bugs fixed, Culebra accuracy
- [ ] What was deferred, what was achieved

---

## Exit Criteria (THE gate for new features)

| Check | Required |
|-------|----------|
| Culebra: 0 real CRITICAL on golden IR | YES |
| Culebra: 0 real CRITICAL on C runtime | YES |
| All self-hosted workarounds removed | YES |
| skip_struct_ret removed | YES |
| semantic.mn enabled and memory-safe | YES |
| Self-hosted optimizer exists | YES |
| MIRType uses named constants | YES |
| str(true) = constant | YES |
| 40/40 golden | YES |
| 11/11 stage2 | YES |
| Valgrind clean | YES |
| Foundation declared complete | YES |

---

**After v4.13.0:** New language features begin (v4.14.0+):
- Compile-time tensor shapes
- `@gpu` auto-kernel extraction
- Reactive async
- Auto-generated FFI bindings
