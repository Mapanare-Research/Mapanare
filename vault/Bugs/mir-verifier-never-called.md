---
severity: critical
found: "[[v4.26.0]]"
fixed: "[[v4.27.0]]"
status: fixed
tags: [bug, critical, mir, verifier, dead-code]
---

# MIR Verifier Never Called

`MIRVerifier` was defined in v4.5.0 with structural checks for MIR modules (type consistency, block termination, instruction well-formedness). It had exactly zero call sites for 21 consecutive releases. The verifier existed in the codebase, was imported in tests, but was never invoked on actual compiler output during compilation or CI.

## Root Cause
The verifier was written as a standalone class but never wired into the compilation pipeline. No post-lowering hook called `MIRVerifier.verify()`, and no test explicitly ran verification on emitted MIR. The class passed import-level checks (it existed, it had no syntax errors) but was functionally dead code for the entire v4.5.0-v4.26.0 span.

## Fix
Integrated `MIRVerifier.verify()` as a mandatory post-lowering pass in the compilation pipeline. Added it to the `--verify` flag and made it run unconditionally in debug builds. When first enabled, it immediately caught several latent MIR malformations. Fixed in v4.27.0.
