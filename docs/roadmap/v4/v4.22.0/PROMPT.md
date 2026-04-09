# v4.22.0 — Dead Block Elimination — Continuation Prompt

> Fix the BFS. Enable the pass. Measure the reduction.
> You are in WSL. Rebuild + golden + stage2 after every .mn change.
> Run lint before every commit. Do NOT defer — this must ship enabled.

---

## Context

Dead block elimination was implemented in v4.12.0 and attempted again in
v4.16.0. Both times it was deferred because the BFS in `collect_targets`
misses block references from while/for loop patterns, causing dangling
label references in the emitted LLVM IR.

The v4.16.0 attempt found:
- `%while_header0`, `%for_header0`, `%if_else1` — removed by BFS but still
  referenced in branch instructions of surviving blocks
- 16/41 golden tests failed with "use of undefined value"
- PHI filtering in emitter caused crashes (EmitState field access corruption)

This version diagnoses the exact BFS gap and fixes it properly.

## The Specific Bug

When the self-hosted lowerer emits a while loop:
```
entry:
  br label %while_header0
while_header0:
  %cond = ...
  br i1 %cond, label %while_body1, label %while_exit2
```

The entry block's last instruction is a Jump to `while_header0`. The BFS
in `dead_block_elim_function` starts from the entry block and scans its
instructions for targets. BUT `collect_targets` only handles Jump, Branch,
and Switch instructions. The Jump instruction should be handled — so why
does the BFS miss `while_header0`?

Possible causes to investigate:
1. The entry block's terminator isn't a Jump in the MIR (could be something else)
2. `instr_kind` returns the wrong string for the instruction
3. The BFS loop count (5000) is too low for the entry block's instruction count
4. The entry block has additional instructions after the jump that confuse the scan

## Key Files

| File | What to Check |
|------|---------------|
| `mapanare/self/mir_opt.mn:89-111` | `collect_targets` — handles "jump", "branch", "switch" |
| `mapanare/self/mir_opt.mn:123-178` | `dead_block_elim_function` — BFS implementation |
| `mapanare/self/mir_opt.mn:184-199` | `optimize_mir` — where dead block elim is called (currently disabled) |
| `mapanare/self/mir.mn:474-520` | `instr_kind` — instruction type dispatch |
| `mapanare/self/mir.mn:580-600` | `instr_jump_target`, `instr_branch_true/false` |
| `mapanare/self/lower.mn` | How while/for loops emit their header jumps |
| `mapanare/self/emit_llvm.mn:2889-2962` | PHI emission — may need block-existence filtering |

## Debugging Strategy

1. **Dump MIR before optimization.** Add a debug print in `optimize_mir` that
   shows block labels and instruction kinds for a small function (e.g., from
   `tests/golden/12_while.mn`). This reveals what the MIR looks like before
   dead block elim runs.

2. **Trace the BFS.** Add temporary prints in `dead_block_elim_function` showing:
   - Which block is being processed
   - What targets were found
   - Which blocks were marked reachable
   This immediately reveals which step fails.

3. **Compare with working case.** `tests/golden/01_hello.mn` has no loops and
   passes. `tests/golden/12_while.mn` fails. The diff in their MIR structure
   reveals the gap.

## Commands

```bash
# Rebuild after every change
bash scripts/rebuild.sh

# Test specific failing case
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 --filter 12_while

# Test all golden
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# Stage2 validation
python3 scripts/ir_doctor.py stage2 --timeout 60

# Culebra after emitter changes
culebra scan mapanare/self/main.ll --severity critical

# Measure IR size (before and after)
wc -l mapanare/self/main.ll

# Lint before commit
black --check . && ruff check . && mypy mapanare/
```

## Rules

- Diagnose FIRST (Phase 1), then fix (Phase 2-3), then enable (Phase 4)
- Use `--filter 12_while` to test the specific failing case first
- If the BFS fix breaks other tests, the fix is wrong — investigate more
- Measure IR line count BEFORE enabling dead block elim, then AFTER
- Record both numbers in the commit message
- Do NOT disable dead block elim to "fix" failures — fix the root cause
- If PHI nodes need filtering, add it in mir_opt.mn (not emit_llvm.mn)

## Exit Criteria with Proof Commands

| Criterion | Proof Command |
|-----------|---------------|
| Dead block elim enabled | `grep -c 'dead_block_elim_function' mapanare/self/mir_opt.mn` shows it's called in `optimize_mir` |
| All golden pass | `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1` → "All N tests passed" |
| Stage2 valid | `python3 scripts/ir_doctor.py stage2 --timeout 60` → "11/11 stage2 modules valid" |
| IR size reduced | `wc -l mapanare/self/main.ll` before vs after (put both in commit message) |
| Lint clean | `black --check . && ruff check . && mypy mapanare/` → all pass |
