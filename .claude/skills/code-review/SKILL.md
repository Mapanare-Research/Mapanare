---
name: code-review
description: Run a full 7-reviewer panel code review of the Mapanare codebase. Produces individual reviews and a summary README. Usage: /code-review [label] — label defaults to today's date (YYYYMMDD).
---

# Code Review

Run a full panel code review of the Mapanare project following `.reviews/prompt.md`.

## Instructions

### 1. Determine review label

The user may provide a label as an argument (e.g., `v2.0.0`, `pre-release`, or a bare date like `20260328`).

- If a label is provided, use it as-is for the output directory name.
- If no label is provided, generate one from today's date: `YYYYMMDD` (e.g., `20260328`).
- If `.reviews/{label}/` already exists, append `-N` (e.g., `20260328-2`).

Store the resolved label for use below.

### 2. Find the previous review

Look for the most recent existing review directory under `.reviews/` (excluding `chats/`). Read its `README.md` to establish the baseline for comparison. Note the date, scores, and key issues.

### 3. Gather project state

Run these in parallel to build context:

```bash
# Test count
pytest --co -q 2>/dev/null | tail -1

# Line counts for key files
wc -l mapanare/*.py runtime/native/*.c runtime/native/*.h mapanare/self/*.mn

# Recent git activity since last review
git log --oneline --since="30 days ago" | head -30

# Current version
cat VERSION
```

### 4. Read the review prompt

Read `.reviews/prompt.md` for the full panel definition, review process, and output format. Follow it exactly.

### 5. Conduct the review

For each of the 7 reviewers, in order:

1. **Read the source files** relevant to their domain. Each reviewer must read 8-15 files. Use the Read tool, not summaries.
2. **Write the individual review** to `.reviews/{label}/NN-codename.md` following the format in `prompt.md`.
3. Move to the next reviewer.

The reviewers and their focus areas:

| # | File | Reviewer | Primary files to read |
|---|------|----------|-----------------------|
| 1 | `01-viper.md` | Viper (Rust/Safety) | `types.py`, `semantic.py`, `mir.py`, `emit_llvm_mir.py`, `runtime/native/*.c`, `MEMORY_MODEL.md` |
| 2 | `02-boa.md` | Boa (Python/Ergonomics) | `cli.py`, `diagnostics.py`, `emit_python_mir.py`, `test_runner.py`, `runtime/*.py`, tutorials |
| 3 | `03-cobra.md` | Cobra (C++/Compilation) | `mir.py`, `mir_builder.py`, `lower.py`, `mir_opt.py`, `optimizer.py`, `emit_llvm_mir.py` |
| 4 | `04-mamba.md` | Mamba (C/Runtime) | `runtime/native/*.c`, `runtime/native/*.h`, `emit_llvm_mir.py` (runtime calls) |
| 5 | `05-anaconda.md` | Anaconda (Toolchain) | `Makefile`, `.github/workflows/*`, `scripts/*`, `mir.py` (verifier), CI configs |
| 6 | `06-rattler.md` | Rattler (LLVM/Codegen) | `emit_llvm_mir.py`, `emit_llvm.py`, `tests/llvm/*`, `tests/golden/*`, emitted IR samples |
| 7 | `07-coral.md` | Coral (Language Design) | `SPEC.md`, `mapanare.lark`, `ast_nodes.py`, `types.py`, `semantic.py`, `self/*.mn` |

### 6. Write the summary

After all 7 individual reviews are written, produce `.reviews/{label}/README.md` following the summary format in `prompt.md`:

- Verdict table
- Overall consensus with score range
- Release gate (blockers vs nice-to-haves)
- Prioritized action items (deduplicated, with effort estimates)
- Disagreements and resolutions
- Improvements since previous review (quantitative tables)
- Summary paragraph

### 7. Report to the user

Print:
- The review label and output directory
- The verdict table (compact)
- Top 5 action items
- Link to the full README
