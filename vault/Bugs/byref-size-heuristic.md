---
docket: 7
severity: medium
found: "[[v4.99.0]]"
fixed: "[[v4.112.0]]"
status: open
tags: [bug, medium, open, phase-d, abi]
---

# Byref Size Heuristic Divergence

**Docket #7** from [[v4.99.0]] panel.

Self-hosted emitter returns 256 for ALL named structs. Python emitter computes actual size. Latent ABI inconsistency that breaks fixed-point convergence.

Flagged by [[Cobra]].

## Planned Fix ([[v4.112.0]])

Fix `mapanare/self/emit_llvm.mn` to compute real struct sizes from field types instead of hardcoding 256.
