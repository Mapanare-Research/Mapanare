---
severity: critical
found: "[[v4.0.0]]"
fixed: "[[v4.2.0]]"
status: fixed
tags: [bug, critical, llvm, stack, alignment, runtime-crash]
---

# Stack Alignment Crash

Dynamic `alloca` instructions emitted in non-entry basic blocks misaligned RSP on x86-64. When control flow reached libc functions using SSE (notably `snprintf` via `println`), the `movaps` instruction faulted on the unaligned stack, producing a SIGSEGV with no obvious connection to the Mapanare source code.

## Root Cause
LLVM requires dynamic allocas in the entry block to maintain the ABI-mandated 16-byte stack alignment. The emitter placed allocas at their point of use (inside loops, conditionals, match arms), causing RSP to drift off alignment. SSE instructions in called C library functions require 16-byte aligned operands and crashed immediately.

## Fix
Hoisted all `alloca` instructions to the entry block of each function during LLVM IR emission. Variable-length allocas that depend on runtime values use a two-step pattern: entry-block alloca with a fixed upper bound, then a store at the use site. Fixed in v4.2.0. This was one of the first critical runtime bugs in Arc 4.
