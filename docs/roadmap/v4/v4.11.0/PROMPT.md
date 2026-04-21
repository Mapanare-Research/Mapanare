# v4.11.0 — Global Constants + MIRType Enum — Continuation Prompt

> Add global constant support, then migrate MIRType to named constants/enum.
> You are in WSL. Rebuild + stage2 after every .mn change.

---

## Context

v4.10.0 removed skip_struct_ret and added string pooling. Now fix the
self-hosted compiler's lack of global constant support, which blocked
MIRType string→enum in v4.8.0.

## Rules

- The global constant lowering is the KEY blocker — get this right first
- Stage2 must validate (llvm-as) after every change
- MIRType migration is 108 replacements across 4 files — do it atomically
