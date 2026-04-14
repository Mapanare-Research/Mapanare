---
docket: 9
severity: medium
found: "[[v4.51.0]]"
fixed: "[[v4.108.0]]"
status: open
tags: [bug, medium, open, phase-c, performance, runtime]
---

# String Concat 2.2x Slower Than Python

**Docket #9.** Originally flagged by [[Mamba]] in v4.51.0 (Arc 4 panel).

## The Problem

`__mn_str_concat` allocates per call. `s = s + chunk` in a loop is O(n^2). Python's `+=` optimization and Rust's `String::push_str` are fundamentally faster.

Current: 95.2ms (Mapanare) vs 43.7ms (Python) vs 0.7ms (Rust) for 10K concats.

## Planned Fix ([[v4.108.0]])

- `mapanare_string_builder_t` in C runtime (exponential growth buffer)
- MIR optimization pass to detect `str = str + x` in loops
- AI stdlib (`llm.mn`, `embedding.mn`) refactored to use StringBuilder
- Target: < 43ms (beat Python)

## Impact

This is the **only benchmark where Mapanare is slower than Python**. Fixing it removes the last embarrassment from the comparison table.
