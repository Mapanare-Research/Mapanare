---
docket: 3
severity: high
found: "[[v4.99.0]]"
fixed: "[[v4.102.0]]"
status: open
tags: [bug, high, open, phase-a, async, runtime]
---

# Async Can't Link

**Docket #3** from [[v4.99.0]] panel.

## The Bug

`__mn_coro_scheduler_*` functions are not exported to `libmapanare_rt.a`. Five async benchmarks compile to IR but cannot produce native binaries. No async program has ever run natively.

## Planned Fix ([[v4.102.0]])

- Audit `runtime/native/` build scripts
- Rebuild libmapanare_rt.a with scheduler exports
- Verify with `nm libmapanare_rt.a | grep scheduler`
- Compile + link + run async golden tests 55-57

## Notes

[[Mamba]] says the functions exist in C source — it's a Makefile rule issue, not missing code.
