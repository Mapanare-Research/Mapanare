# Anaconda — Toolchain Review (Arc 10)

**Grade: 9/10**
**Verdict: PASS**

## Assessment

The integration test harness is the centerpiece of Arc 10 and addresses the gap I have flagged at every panel since Arc 3. For the first time, the project has end-to-end pipeline validation: `.mn -> emit-llvm -> llvm-as -> opt -O2 -> llc -filetype=obj -> clang link -> execute -> stdout check`. This is real compilation testing, not IR string matching.

**Framework design (v4.77.0):**
- `conftest.py` with composable pipeline fixtures — clean separation of stages
- Parametrized discovery of all golden tests via glob
- Per-stage error capture in `PipelineResult` — failures are diagnosed precisely
- `--integration-stage` flag for partial runs (useful for debugging)
- JUnit XML output + `integration_report.py` for RESULTS.md generation

**CI gate (`.github/workflows/integration.yml`):**
- Ubuntu + LLVM-18 toolchain, correct symlinks
- Builds C runtime before tests
- Runs on every push/PR to `dev`
- Uploads results as artifacts

**Results:** 47/59 pass end-to-end. The 5 xfails are legitimate (async not in emit-llvm, try operator type mismatch, guard+or patterns). The 7 skips are correct (external resources). Zero unexpected failures across 2 consecutive runs.

## Specific findings

1. **PASS**: The harness catches the try operator IR type mismatch that string-match testing could not detect.
2. **PASS**: `-relocation-model=pic` correctly discovered and applied during pipeline development.
3. **PASS**: C runtime links cleanly against all 47 passing object files.
4. **NOTE**: The RESULTS.md parser correctly distinguishes xfail from skip using the JUnit XML `type` attribute.

## Score justification

9/10 — the harness is exactly what I have been asking for. It is well-designed, deterministic, and integrated into CI. One point held because the harness only tests the Python bootstrap path, not mnc-stage1. Self-hosted integration testing is the natural next step.
