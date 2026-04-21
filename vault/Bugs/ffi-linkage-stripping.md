---
severity: critical
found: "[[v4.26.0]]"
fixed: "[[v4.27.0]]"
status: fixed
tags: [bug, critical, llvm, ffi, linkage]
---

# FFI Linkage Stripping

The LLVM emitter used `.replace("define internal ", "define ")` as a sledgehammer to make FFI-exported functions visible. This stripped `internal` linkage from every function in the module, not just the FFI-annotated ones, defeating LLVM's ability to internalize and optimize non-exported symbols.

## Root Cause
A quick fix for FFI symbol visibility was applied as a global string replacement on the emitted IR text rather than selectively adjusting linkage on functions marked `@extern` or `@ffi`. The replacement had no guard clause or function-name check.

## Fix
Replaced the blanket string substitution with targeted linkage emission: functions annotated with `@extern` or `@ffi` emit `define` (external linkage), all others emit `define internal`. Applied in v4.27.0 as part of the initial recovery batch.
