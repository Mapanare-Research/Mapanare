# v4.25.0 — FFI End-to-End + Tensor Shapes — Continuation Prompt

> Bindings that actually work. Shapes that actually check.
> You are in WSL. Rebuild + golden + stage2 after every change.

---

## Context

v4.20.0's bind.py generates text. This version makes the generated Python
binding actually callable — compile .mn to .so, load in Python, call functions.
Also wires up the tensor shape checking from v4.18.0's infrastructure.

## Key files

- `mapanare/bind.py` — add shared library compilation step
- `mapanare/cli.py` — cmd_bind updates
- `mapanare/semantic.py` — tensor shape validation
- `mapanare/types.py` — TypeInfo.tensor_shape usage

## Rules

- Python end-to-end FIRST (most impactful)
- Shape checking SECOND (builds on existing infrastructure)
- Every feature must have a passing test before moving on
