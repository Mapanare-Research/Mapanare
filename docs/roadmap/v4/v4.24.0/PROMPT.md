# v4.24.0 — async/await Runtime Wiring — Continuation Prompt

> Wire async/await to streams, agents, and ring buffers.
> You are in WSL. Rebuild + golden + stage2 after every change.

---

## Context

v4.19.0 added async/await keywords. This version connects them to the
existing runtime: streams for data flow, agents for cooperative tasks,
SPSC ring buffers for backpressure.

## Key files

- `mapanare/lower.py` — async fn lowering, await expr lowering
- `mapanare/mir.py` — MIR instructions (AsyncSpawn or reuse existing)
- `mapanare/emit_llvm_text.py` — emit ring buffer + task spawn + yield
- `runtime/native/mapanare_core.c` — SPSC ring buffer (already exists)
- `runtime/native/mapanare_runtime.c` — agent scheduler (already exists)

## Rules

- Use EXISTING runtime primitives — do not write new C code unless necessary
- async fn FIRST (stream creation), then await (stream consumption)
- Test each step with a golden test before moving on
