# Rattler — LLVM Review (v4.61.0)

Grade: 8/10
Verdict: PASS WITH NOTES

## Findings

1. **NO CLANG PRE-CHECK IN cmd_build** — `cli.py:568` calls `subprocess.run(["clang", ...])` without `shutil.which` guard. User gets raw `FileNotFoundError` instead of actionable message. The linker path already uses `shutil.which`.

2. **BOOTSTRAP TESTS LACK CLANG SKIP GUARD** — `test_self_hosted_ir_verifies` and `test_self_hosted_ir_compiles_to_object` call llvm-as/clang unconditionally. On CI without LLVM, these hard-fail rather than skip.

3. **llvm-as EQUIVALENCE SOUND** — Using llvm-as as IR verifier is a strict superset of old llvmlite `parse_assembly` path. No functional regression.

4. **MONOCULTURE ACCEPTABLE** — clang as sole compilation path with no fallback. The dependency reduction justifies this, but a gcc fallback for `.ll` -> `.o` would future-proof.

5. **ARC SCOPE CLEAN** — ~1,820 lines deleted from mapanare/ are exactly the two deprecated backends with no collateral damage to text emitter or C backend.
