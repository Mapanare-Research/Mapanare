# v4.77.0 Session Report — 2026-04-13

## Verdict

- **46/58 golden tests pass the full LLVM pipeline end-to-end.**
- 5 xfail (known gaps), 7 skip (external resources). Zero unexpected failures.
- Arc 10 opens. The first post-plan release is infrastructure, not features.

## What shipped

### Integration test framework (`tests/integration/`)

A pytest-based harness that takes each golden `.mn` file through the full
native compilation pipeline:

```
emit-llvm → llvm-as → opt -O2 → llc -filetype=obj -relocation-model=pic → clang link → execute
```

Key components:
- `conftest.py` — pipeline fixtures with per-stage error capture
- `test_golden_pipeline.py` — parametrized discovery of all 58 golden tests
- `expected/` — 46 expected stdout files generated from known-good runs
- `--integration-stage` flag to stop early (e.g., `--integration-stage=llvm-as`)

### CI gate (`.github/workflows/integration.yml`)

Runs on every push/PR to `dev`:
1. Ubuntu latest + LLVM-18 (llvm-as, opt, llc, clang)
2. Build C runtime via `make build-rt`
3. `pytest tests/integration/ -v --tb=short --junitxml=integration-results.xml`
4. Generate `RESULTS.md` via `scripts/integration_report.py`
5. Upload results as artifact

### Results report (`scripts/integration_report.py`)

Parses JUnit XML and generates a Markdown table with per-test per-stage
pass/fail status. Distinguishes PASS/FAIL/XFAIL/SKIP.

## Results breakdown

| Category | Count | Tests |
|----------|-------|-------|
| Pass (full pipeline) | 46 | 01-33, 41-43, 45, 48-50, 49t-52t, 53, 54 |
| Xfail: emit fails | 4 | 51_match_guards_and_or, 55-57 async |
| Xfail: llvm-as rejects IR | 1 | 47_try_operator |
| Skip: external resources | 7 | 34-40 (file, stdin, crypto, regex, http, gpu) |

## Decisions made

1. **Python bootstrap** as the compilation backend (not mnc-stage1). The goal
   is to validate the IR-to-binary pipeline, not re-test the self-hosted emitter.

2. **opt -O2** as the optimization level. The whole point is to find what breaks
   under real optimization. All 46 passing tests survive -O2.

3. **-relocation-model=pic** for llc. Required on Ubuntu/WSL where the default
   linker creates PIE executables.

4. **Link against libmapanare_rt.a** (static archive) + `-lm -lpthread -ldl`.
   Clean link for all 46 passing tests — no missing symbols.

5. **xfail, not skip** for known failures. xfail tests run and are tracked;
   they become the work queue for future arcs.

## Known gaps (work queue for future arcs)

| Gap | Test | Stage | Root cause |
|-----|------|-------|------------|
| try operator IR | 47_try_operator | llvm-as | Type mismatch in unwrap lowering |
| guard+or patterns | 51_match_guards_and_or | emit | Combined guard+or not in emit-llvm |
| async/await | 55-57 | emit | async functions not yet in LLVM emitter |

## Performance

- Full suite runs in ~40 seconds (58 tests, sequential)
- Each test: ~0.7s average (dominated by emit-llvm subprocess startup)
- No parallelization yet (pytest-xdist would cut this to ~10s)

## Next session should start with

- v4.78.0: carry-forward items 49 (drop-glue struct return), 50 (agent destroy
  in-flight leak), A10b (const scope in self-hosted semantic)
