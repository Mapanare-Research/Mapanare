# Anaconda — Toolchain Review (v4.61.0)

Grade: 9/10
Verdict: PASS WITH NOTES

## Findings

1. **CLEAN DELETION** — llvmlite fully gone from pyproject.toml. Regression gate (5 tests) guards against re-introduction.

2. **cmd_build ERROR HANDLING SOLID** — clang subprocess captures stderr, prints on failure, exits with code 1. Temp .ll cleaned in finally block.

3. **build_stage1.py STDERR SWALLOWED** — `check=True` + `capture_output=True` means CalledProcessError hides the actual clang error. Developer sees Python traceback, not IR error.

4. **CLANG NOT IN DECLARED DEPENDENCIES** — clang is now a hard runtime requirement with no programmatic guard in cmd_build. User gets FileNotFoundError rather than an actionable message (build_stage1.py has a shutil.which check but cmd_build does not).

5. **DEPENDENCY COUNT REDUCTION** — measurable win. llvmlite was the heaviest optional dependency; its removal simplifies the install matrix.
