# v4.61.0 Measurements — Arc 6 Panel

## Line counts

| Component | v4.56.0 (arc start) | v4.60.0 (arc end) | Delta |
|-----------|--------------------|--------------------|-------|
| mapanare/*.py | 35,556 | 33,736 | -1,820 |
| runtime/native/*.c | 10,710 | 10,710 | 0 |
| tests/*.py | ~60,000 | 55,024 | ~-5,000 |

## Deletions

| Release | What was deleted | Lines |
|---------|-----------------|-------|
| v4.58.0 | `emit_python_mir.py` + CLI commands + Python-backend tests | ~5,462 |
| v4.59.0 | `jit.py` + `cmd_jit` + `--release` + test runner JIT | ~519 |
| v4.60.0 | (housekeeping only — no code deleted) | 0 |

## Dependencies

| Metric | v4.56.0 | v4.60.0 | Delta |
|--------|---------|---------|-------|
| llvmlite in pyproject.toml | yes (optional) | removed | -1 dep |
| `[llvm]` optional group | exists | removed | cleaner |

## Carry-forward

| Metric | v4.56.0 | v4.60.0 |
|--------|---------|---------|
| OPEN items | 11 | 9 |
| CLOSED items | 8 | 10 |
| A3 (Python emitter) | IN PROGRESS | CLOSED |
| A4 (llvmlite JIT) | DEFERRED | CLOSED |

## Test counts

| Metric | Value |
|--------|-------|
| Regression gate tests (v4.58.0) | 6 (test_python_emitter_deleted.py) |
| Regression gate tests (v4.59.0) | 5 (test_llvmlite_removed.py) |
| CI gates | 3/3 clean |
| Vulture dead code | 0 at 90% confidence |

## Compiler IR

Arc 6 had no compiler changes — main.ll is unchanged from v4.56.0.
