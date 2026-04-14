---
severity: critical
found: "[[v4.26.0]]"
fixed: "[[v4.27.0]]"
status: fixed
tags: [bug, critical, parser, semantic, recovery-arc]
---

# Hollow Features

Six features shipped as parser-only aliases with no semantic enforcement: `const` (parsed but never checked for mutation), `@gpu` (decorator accepted, no codegen), `await` (lowered as identity), tensor shape annotations (syntax only), FFI argument types (ignored at link time), and CHANGELOG test entries (listed but never executed). All six passed CI because the grammar accepted them and nothing downstream rejected the absence of real implementation.

## Root Cause
Features were added to the Lark grammar and AST nodes but never wired through `semantic.py`, `lower.py`, or the emitters. The test suite validated parse-round-trip and AST construction, not behavioral correctness. No integration tests exercised the actual runtime semantics of these features.

## Fix
Discovered during the v4.26.0 audit. Each hollow feature was addressed individually across the v4.27.0-v4.31.0 recovery arc: semantic passes added for `const` immutability, `@gpu` kernel dispatch wired through MIR to LLVM, `await` redesigned as [[Path B]] (removed then re-implemented properly in v4.72.0-v4.76.0), tensor shapes enforced in the type checker, FFI argtypes validated at link, and CHANGELOG tests integrated into CI. This bug triggered the 50-release recovery effort that defined Arc 4.
