# v4.22.0 — Dead Block Elimination — Continuation Prompt

> Fix the BFS. Enable the pass. Measure the reduction.
> You are in WSL. Rebuild + golden + stage2 after every .mn change.

---

## Context

Dead block elimination was implemented in v4.12.0, attempted in v4.16.0,
and deferred both times. The BFS in `collect_targets` misses some block
references. This version diagnoses the exact gap and fixes it.

## Key files

- `mapanare/self/mir_opt.mn` — dead_block_elim_function, collect_targets
- `mapanare/self/emit_llvm.mn` — PHI emission (may need filtering)

## Commands

```bash
bash scripts/rebuild.sh
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
python3 scripts/ir_doctor.py stage2
```

## Rules

- Diagnose FIRST (Phase 1), then fix (Phase 2-3), then enable (Phase 4)
- Use `--filter 12_while` to test the specific failing case
- If the BFS fix breaks other tests, the fix is wrong — investigate more
- Measure before AND after (record numbers in commit message)
