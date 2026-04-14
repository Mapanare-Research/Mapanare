---
severity: critical
found: "[[v4.106.0]]"
fixed: "[[v4.106.1]]"
status: fixed
tags: [bug, critical, llvm, lambda, codegen, golden-tests]
---

# Lambda Emitter Signature

Multi-argument lambda expressions generated incorrect LLVM function signatures. The emitter produced parameter lists that either duplicated the first parameter's type for all arguments or dropped parameters beyond the first, resulting in type mismatches at call sites. This was load-bearing: 43+ golden tests failed because lambdas with 2+ parameters are pervasive in list operations, stream pipelines, and callback patterns.

## Root Cause
The lambda signature emission path indexed into the parameter type array incorrectly, reusing index 0 for all parameters instead of iterating. Single-argument lambdas (the most common in early tests) worked fine, masking the bug until broader golden test coverage exposed it.

## Fix
Fixed the parameter iteration in the lambda signature emission to correctly index each parameter's type. All 43+ affected golden tests passed immediately after the one-line fix. Fixed in v4.106.1 (hotfix release).
