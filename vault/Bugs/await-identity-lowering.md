---
severity: high
found: "[[v4.19.0]]"
fixed: "[[v4.30.0]]"
status: fixed
tags: [bug, high, async, lowering, hollow-feature]
---

# Await Identity Lowering

`await expr` was lowered as `return self._lower_expr(expr.expr)` -- a pure identity transformation. There was no coroutine frame, no suspension point, no scheduler yield. The keyword parsed, the AST node existed, the lowerer accepted it, and the emitter produced valid IR that simply evaluated the inner expression synchronously. Grammar theatre at its most complete.

## Root Cause
The `await` keyword was added to the grammar in v4.19.0 with an `AwaitExpr` AST node. The lowerer handled it by recursively lowering the inner expression and returning the result directly. No MIR instruction for suspension or coroutine state was ever defined, so the lowerer had nothing meaningful to emit. Tests only checked that `await x` parsed and produced a value.

## Fix
Removed the hollow `await` implementation entirely in v4.30.0 as [[Path B]] (delete and redo properly). Async/await was re-implemented correctly in v4.72.0-v4.76.0 with proper coroutine frames, suspension points, and scheduler integration via the cooperative agent runtime.
