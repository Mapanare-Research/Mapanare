---
severity: critical
found: "[[v4.0.0]]"
fixed: "[[v4.2.0]]"
status: fixed
tags: [bug, critical, llvm, dce, linkage, sret]
---

# Function Stripping at -O1

LLVM's dead code elimination at `-O1` and above removed `internal`-linkage functions that were actually called. The resulting binary had unresolved symbols or silently called stubs, producing crashes or wrong results that only appeared with optimization enabled.

## Root Cause
Functions using `sret` (struct return) parameters confused LLVM's reachability analysis. The `sret` calling convention stores the return value through a pointer parameter rather than in the return register, and LLVM's interprocedural DCE misidentified some of these functions as having no observable side effects. Combined with `internal` linkage (no external visibility), they were marked dead and eliminated.

## Fix
Applied `noinline` attributes to functions using `sret` return convention and ensured critical internal functions use appropriate linkage. Added a post-emission verification pass that cross-checks emitted call targets against defined functions. Fixed in v4.2.0 alongside the [[stack-alignment-crash]].
