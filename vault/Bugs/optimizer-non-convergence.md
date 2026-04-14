---
severity: high
found: "[[v4.26.0]]"
fixed: "[[v4.30.0]]"
status: fixed
tags: [bug, high, mir, optimizer, convergence, diagnostics]
---

# Optimizer Non-Convergence

The MIR optimizer's fixed-point iteration loop could fail to converge (oscillating between two states), and the only indication was a `logging.warning()` message. No test checked for convergence, no metric tracked iteration counts, and nobody read the warning logs. Programs compiled with non-convergent optimization silently received partially-optimized or mis-optimized MIR.

## Root Cause
Two optimizer passes (constant folding and copy propagation) could undo each other's transformations in specific patterns involving signal-derived values. The iteration loop had a maximum iteration cap but treated hitting the cap as a warning rather than an error. The `logging.warning` was lost in normal output.

## Fix
Promoted non-convergence from `logging.warning` to an Internal Compiler Error (ICE) that halts compilation with a diagnostic showing which passes are cycling. Added iteration-count metrics to the optimizer's output. Added a regression test with a known-oscillating pattern. Fixed in v4.30.0.
