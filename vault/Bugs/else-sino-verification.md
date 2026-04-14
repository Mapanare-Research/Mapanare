---
docket: 4
severity: high
found: "[[v4.99.0]]"
fixed: "[[v4.103.0]]"
status: open
tags: [bug, high, open, phase-a, grammar]
---

# else/sino Not Verified End-to-End

**Docket #4** from [[v4.99.0]] panel.

Grammar has `else`/`sino`, SPEC documents it, but benchmarks use `si cond {} si !cond {}` double-negation pattern instead. Nobody verified it actually works.

## Planned Fix ([[v4.103.0]])

- Add golden test `63_else_sino.mn`
- Compile through both Python bootstrap and mnc-stage1
- Fix if broken in either pipeline

Flagged by [[Coral]].
