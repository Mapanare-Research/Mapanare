---
docket: 5
severity: high
found: "[[v4.99.0]]"
fixed: "[[v4.103.0]]"
status: open
tags: [bug, high, open, phase-a, types]
---

# Closure Type Annotations Broken

**Docket #5** from [[v4.99.0]] panel.

`Fn(Int) -> Int` parses per grammar but lowering failed in v4.98.0 benchmarks. Likely in `lower.py` or `lower.mn` where FnType with explicit parameter types isn't handled.

## Planned Fix ([[v4.103.0]])

- Add golden test `64_closure_typed.mn`
- Trace and fix the lowering failure

Flagged by [[Coral]].
