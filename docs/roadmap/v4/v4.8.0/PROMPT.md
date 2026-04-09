# v4.8.0 — Solid Core — Continuation Prompt

> Fix every known issue. Culebra is the quality gate. No new features.
> You are in WSL. Run rebuild + golden + stage2 after every .mn change.
> Run Culebra after every emitter or runtime change.

---

## Context

v4.2.0-v4.7.1 made structural improvements. v4.8.0 finishes the remaining
items with proper WSL verification. Culebra v2.3.1 (59/59 templates) scans
are mandatory — findings drive the priority order.

## Execution Order

1. field-index-always-zero fix (hardcoded_field_index replacement)
2. undefined-named-type fix (struct type definitions in self-hosted emitter)
3. string-track-noop fix (missing _track_string in Python emitter)
4. byte-count-mismatch fix (string constant sizes)
5. C runtime Culebra findings (typedef, memcpy, atomic)
6. MIRType string → enum
7. Self-hosted workarounds (PHI/substr/ABI)
8. semantic.mn memory safety → remove skip_struct_ret
9. String pooling
10. Self-hosted optimizer passes
11. Final Culebra gate

## Rules

- `python3 scripts/build_stage1.py` after EVERY .mn change
- `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1` after every build
- `python3 scripts/ir_doctor.py stage2 --timeout 30` after emitter changes
- `culebra scan /tmp/golden_output.ll` after emitter changes
- `culebra scan runtime/native/mapanare_core.c` after C runtime changes
- Commit after each phase
- If a phase breaks golden or stage2, fix before moving on
