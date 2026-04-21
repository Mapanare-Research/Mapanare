---
severity: high
found: "[[v4.106.0]]"
fixed: ""
status: open
tags: [bug, high, llvm, abi, option-type, type-encoding]
---

# Option Payload ABI Inconsistency

The `Option<T>` type is inconsistently encoded as `{i1, i64}` in some contexts and `{i1, ptr}` in others, depending on whether the payload type is resolved as a value or pointer at the point of emission. When a function returns `Option<String>` using one encoding and the caller expects the other, the payload bits are misinterpreted -- pointer values read as integers, or integer values dereferenced as pointers.

## Root Cause
The LLVM IR emitter has two code paths for Option encoding: one in the type declaration section (which uses the resolved LLVM type of the payload) and one in the function signature emission (which defaults to `i64` for all payloads to simplify ABI). These two paths were never unified, so the encoding depends on which path runs first for a given Option instantiation.

## Fix
**OPEN.** Requires unifying Option type encoding to a single canonical representation chosen at monomorphization time and used consistently across type declarations, function signatures, call sites, and match destructuring. The `{i1, ptr}` encoding for heap types and `{i1, i64}` for scalar types is the likely resolution, with explicit bitcast at ABI boundaries.
