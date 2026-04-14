---
docket: 8
severity: medium
found: "[[v4.99.0]]"
fixed: "[[v4.113.0]]"
status: open
tags: [bug, medium, open, phase-d, async]
---

# Coroutine Frame Layout Coupling

**Docket #8** from [[v4.99.0]] panel.

`mn_coro_is_done` reads a hardcoded offset into the coroutine frame. Fragile under LTO or LLVM version changes.

Flagged by [[Viper]].

## Planned Fix ([[v4.113.0]])

Replace hardcoded offset with stable API: use `llvm.coro.done` intrinsic or add `int8_t status` at fixed offset 0.
