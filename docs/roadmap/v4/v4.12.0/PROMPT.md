# v4.12.0 — Self-Hosted Optimizer — Continuation Prompt

> Add constant folding, propagation, and dead block elimination to the
> self-hosted compiler.
> You are in WSL. Rebuild + golden + stage2 after every change.

---

## Context

v4.11.0 added global constant support and MIRType enum. The self-hosted
compiler is now clean and correct. This version makes it FAST by adding
MIR-level optimization passes.

## Rules

- One pass at a time, rebuild+verify between each
- Measure IR size before and after each pass
- The optimizer must not change program behavior — only eliminate redundancy
