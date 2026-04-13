# v4.57.0 Session Report — 2026-04-12

## Verdict
- All 10 exit criteria green
- A3 carry-forward updated (deprecation warnings shipped, deletion v4.58.0)
- A4 retargeted from v5.0.0 to v4.59.0
- A10b deferred from v4.57.0 to v4.58.0+ (no compiler changes in this release)

## Completed
- Phase 1: DeprecationWarning on `PythonMIREmitter` public entries
  - Import-time warning at `mapanare/emit_python_mir.py:16-22`
  - `__init__` warning at `mapanare/emit_python_mir.py:86-92`
  - `emit()` warning at `mapanare/emit_python_mir.py:117-123`
  - All warnings reference v4.58.0 and `docs/migration/v4.57-to-v4.58.md`
- Phase 2: stderr warnings in CLI commands
  - `cmd_compile` updated at `mapanare/cli.py:280-294` (both `warnings.warn` + `print` to stderr)
  - `_compile_source` updated at `mapanare/cli.py:123-131` (`warnings.warn`)
  - `cmd_repl` startup warning at `mapanare/cli.py:478-483`
- Phase 3: Migration guide written at `docs/migration/v4.57-to-v4.58.md`
  - Covers all CLI commands, library API, test infrastructure, FAQ, timeline
- Phase 4: `_PYTHON_MIR_XFAIL` retargeted from v5.0.0 to v4.58.0
  - All 11 v5.0.0 references in `tests/conftest.py` updated
- Phase 5: 7 tests in `tests/test_deprecation_warnings.py`
  - `test_instantiation_warns`, `test_emit_warns`, `test_import_warns`
  - `test_compile_warns_stderr`
  - `test_migration_guide_exists`, `test_migration_guide_mentions_key_topics`
  - `test_emitter_produces_valid_python` (regression)
- Phase 6: CHANGELOG `[4.57.0]` entry with prominent deprecation notice
- Phase 7: LOW sweep — A3 updated, A4 retargeted, A10b deferred

## Carry-forward closed
- A3: IN PROGRESS (deprecation warnings shipped v4.57.0; deletion tracked v4.58.0)

## Carry-forward still open
- A1: DEFERRED → v4.67.0+ (coroutine foundation, Arc 8)
- A2: DEFERRED → v5.x (DWARF, but Arc 7 starts at v4.62.0)
- A4: DEFERRED → v4.59.0 (llvmlite JIT removal)
- A10: OPEN → v4.37.0+ (bounded-for sentinels, grammar gap)
- A10b: OPEN → v4.58.0+ (const scope in self-hosted semantic.mn)
- 49: OPEN (drop-glue skip-struct-ret)
- 50: OPEN (agent destroy in-flight messages)
- P2: OPEN (pattern_matching.py unit tests)
- P3: OPEN (guard fall-through divergence)
- P6: OPEN (unreachable-arm warning test)

## Measurements
- No compiler IR changes (warnings-only release)
- Pytest: 5043 passed, 50 skipped, 63 xfailed (unchanged from v4.56.0 + 7 new)
- Golden tests: unchanged (no compiler changes)
- Stage2: unchanged (no compiler changes)
- New tests: 7 (tests/test_deprecation_warnings.py)

## Decisions Made
- Decision 1: specific v4.58.0 target in all warning messages (not vague)
- Decision 2: both import-time and __init__ warnings (not just one)
- Decision 3: thorough migration guide (covers all CLI, API, FAQ, timeline)

## Verification Results
- `check_no_hollow_features.py`: clean
- `check_silent_skips.py tests/`: clean
- `check_changelog_honesty.py`: clean
- `pytest tests/test_deprecation_warnings.py`: 7/7 passed
- `pytest tests/` (full): 5043 passed, pre-existing failures only

## Tool discipline retrospective
- No Culebra commands run (no compiler/IR changes)
- lint: black --check, ruff check on changed files
- test: pytest on new tests + full suite regression check

## Next Session Should Start With
- Read `docs/roadmap/v4/v4.58.0/PLAN.md` (Python emitter deletion)
- Read `docs/roadmap/v4/POST_RECOVERY_MASTER_PROMPT.md`
- A10b investigation (const scope in semantic.mn)
