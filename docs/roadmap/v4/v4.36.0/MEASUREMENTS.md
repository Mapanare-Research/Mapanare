# v4.36.0 Measurements — Arc 1 Close

**Date:** 2026-04-12
**Tag:** v4.36.0 (pre-panel snapshot)

---

## Codebase size

| Component | Lines |
|-----------|-------|
| Python compiler (`mapanare/*.py`) | 34,459 |
| C runtime (`runtime/native/*.c` + `*.h`) | 13,150 |
| Self-hosted compiler (`mapanare/self/*.mn`) | 37,211 |
| Consolidated self-hosted (`mnc_all.mn`) | 15,845 |

## Test counts

| Suite | Count |
|-------|-------|
| Pytest collected (parser + semantic + llvm) | 708 |
| Golden test files (`tests/golden/*.mn`) | 49 |
| xfailed | 4 |

## Arc 1 delta (v4.32.0 → v4.36.0)

| Metric | v4.31.0 | v4.36.0 | Delta |
|--------|---------|---------|-------|
| Golden tests | 44 | 49 | +5 |
| Pytest (core) | ~665 | 708 | +43 |
| CARRY_FORWARD closed | 43 | 55 | +12 |
| New language features | 0 | 3 (?, guards, or-patterns) | +3 |

## Lint status

| Tool | Status |
|------|--------|
| ruff | 1 finding (E501, pre-existing) |
| black | 4 files need reformat (pre-existing drift) |
| mypy | not run (WSL limitation) |

## Fixed-point

Target: **0 lines diff** (A6 closed in v4.34.0, preserved through v4.35.0).
Status: verified at v4.34.0 tag; v4.35.0 added guards + or-patterns without breaking the invariant (no new grammar affects the self-hosted compiler's own compilation path since the self-hosted compiler doesn't use guards/or-patterns in its own match expressions yet).

## Key evidence

- `mapanare/pattern_matching.py` — shared Maranget engine (v4.34.0)
- `mapanare/ast_nodes.py:OrPattern` — or-pattern AST node (v4.35.0)
- `mapanare/ast_nodes.py:MatchArm.guard` — guard field (v4.35.0)
- `runtime/native/mapanare_io.c` — 3x `pthread_once` closures (v4.35.0)
- `runtime/native/mapanare_gpu.c:1756` — cuda_matmul rc check (v4.36.0)
