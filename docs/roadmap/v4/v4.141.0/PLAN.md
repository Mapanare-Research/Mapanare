# Mapanare v4.141.0 — An.2 lint debt + 5th flaky audit

> Clear the repo-wide lint debt (An.2: 204 ruff + 65 black + 36 mypy)
> that Anaconda docketed at v4.120.0 and deferred through the closeout
> arc. Also run the 5th cumulative flaky audit (25 sequential pytest
> runs across 5 audits, 0 flaky target).

**Status:** PLANNED
**Breaking:** No (type annotations, import sorting, dead-code cleanup —
no behavior change)
**Prerequisite:** v4.140.0 (self-hosted parity landed)
**Estimated work:** 1 sprint (mostly mechanical + type-annotation work)
**Theme:** Anaconda's ledger emptied.

---

## Why this release

Anaconda moved from 7.6 NEEDS WORK (v4.120.0) to 8.9 MEETS (v4.136.0)
by closing An.1 at v4.133.0. An.2 (lint debt) was explicitly carried
forward; at v4.136.0 she docked −0.4 from ceiling for it. Closing
An.2 plus a 5th clean flaky audit lifts her to 9.2 at the v4.143.0
panel.

Lint debt at v4.136.0 HEAD (Anaconda's reproducible count):
- **204 ruff findings** (unused imports, line-length, unused vars,
  etc.)
- **65 black** formatting issues (line length, string quoting)
- **36 mypy** strict-mode errors (mostly in `lower.py`, `semantic.py`,
  `lsp/`)

The debt is honestly docketed in `tests/test_ci.py:120-129` with a
skip marker naming An.2, but the gate was expected to re-enable
pre-v5.

---

## Scope

### A — Black: auto-fix 65 files

```bash
black mapanare/ runtime/ tests/ stdlib/ benchmarks/
```

Minimal-risk, auto-applied. Verify no behavior change via full pytest.

### B — Ruff: auto-fix what's safe, manual-review the rest

```bash
ruff check --fix .
```

Remaining findings (if any) get manual inspection:
- unused imports → remove (safe)
- line-length → reformat via black (already done in A)
- unused variables → verify they aren't `_ =` silencing patterns;
  remove if truly unused
- shadowed builtins → rename
- complex expression warnings → either refactor or add `# noqa`
  with justification

### C — Mypy: 36 errors concentrated in 3 files

`mapanare/lower.py` (~15), `mapanare/semantic.py` (~8),
`mapanare/lsp/*` (~13).

Most are:
- missing return-type annotations on internal helpers → add them
- `Any` leaks where `TypeInfo` or `MIRValue` is expected → tighten
- implicit `Optional` from `None` defaults → make explicit
- `list[X]` vs `List[X]` consistency → pick one per project style

### D — Re-enable the CI gate

`tests/test_ci.py:120-129`: remove the `@pytest.mark.skip(reason="An.2
deferred")` block (or equivalent). The `make lint` invocation from
`tests/test_ci.py::test_lint_clean` should now pass.

### E — 5th flaky audit

```bash
for i in 1 2 3 4 5; do
  python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no 2>&1 \
    | tee docs/roadmap/v4/v4.141.0/flaky-runs/run${i}.log
done
```

Expected: 0 failures × 5 runs, byte-identical FAILED sets (trivially
empty). Cumulative: 25 sequential runs across 5 audits, 0 flaky.

Write `FLAKY_AUDIT.md` in `docs/roadmap/v4/v4.141.0/`.

---

## Phase plan

### Phase 1 — Black (safe auto-fix)

```bash
echo "4.141.0" > VERSION
git checkout -b v4.141.0 dev

black mapanare/ runtime/ tests/ stdlib/ benchmarks/
git diff --stat | tail -5
git commit -am "v4.141.0 WIP: black auto-format"

# Regression check
python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no 2>&1 | tail -3
# Expected: 5,119 / 0 byte-identical
```

### Phase 2 — Ruff auto-fix

```bash
ruff check --fix mapanare/ runtime/ tests/ stdlib/ benchmarks/
git diff --stat
git commit -am "v4.141.0 WIP: ruff auto-fix"

# Leftover findings — manual pass
ruff check mapanare/ runtime/ tests/ stdlib/ benchmarks/ 2>&1 | tee /tmp/ruff-remainder.txt
wc -l /tmp/ruff-remainder.txt
# Iterate: address or document each
```

### Phase 3 — Mypy 36 errors

```bash
mypy mapanare/ runtime/ 2>&1 | tee /tmp/mypy-baseline.txt
wc -l /tmp/mypy-baseline.txt

# Fix per-file, one at a time
# Re-run mypy after each file; verify count drops monotonically
```

### Phase 4 — Re-enable CI lint gate

`tests/test_ci.py`: remove the An.2 skip.

```bash
python3 -m pytest tests/test_ci.py -v 2>&1 | tail -10
# test_lint_clean expected to pass
```

### Phase 5 — 5th flaky audit

```bash
mkdir -p docs/roadmap/v4/v4.141.0/flaky-runs
for i in 1 2 3 4 5; do
  echo "=== Run $i ==="
  date +%H:%M:%S
  python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no \
    > docs/roadmap/v4/v4.141.0/flaky-runs/run${i}.log 2>&1
  date +%H:%M:%S
  tail -3 docs/roadmap/v4/v4.141.0/flaky-runs/run${i}.log
done

# Extract FAILED sets (should all be empty)
for i in 1 2 3 4 5; do
  grep '^FAILED' docs/roadmap/v4/v4.141.0/flaky-runs/run${i}.log | sort \
    > docs/roadmap/v4/v4.141.0/flaky-runs/run${i}.failed.sorted
  wc -l docs/roadmap/v4/v4.141.0/flaky-runs/run${i}.failed.sorted
done

# Pairwise diff
for i in 1 2 3 4; do
  j=$((i+1))
  diff docs/roadmap/v4/v4.141.0/flaky-runs/run${i}.failed.sorted \
       docs/roadmap/v4/v4.141.0/flaky-runs/run${j}.failed.sorted
done
# Expected: all diffs empty
```

### Phase 6 — Write FLAKY_AUDIT.md

Template mirrors `docs/roadmap/v4/v4.135.0/FLAKY_AUDIT.md`. Cumulative
table now includes 5 audits:

| Release | Runs | Scope | Flaky | Failures |
|---|---:|---|---:|---:|
| v4.117.0 (1st) | 5 | subset 1501 | 0 | 22 |
| v4.125.0 (2nd) | 5 | full ~5093 | 0 | 39 |
| v4.130.0 (3rd) | 5 | full ~5177 | 0 | 39 |
| v4.135.0 (4th) | 5 | full ~5244 | 0 | 0 |
| **v4.141.0 (5th)** | **5** | **full ~5250+** | **0** | **0** |

**Cumulative: 25 sequential runs across 5 audits, 0 flaky.**

### Phase 7 — Verify + commit

```bash
# Compiler / runtime / goldens unchanged
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 2>&1 | tail -3
bash scripts/verify_fixed_point.sh --keep 2>&1 | tail -5
sha256sum runtime/native/libmapanare_rt.a
# Expected: byte-identical to v4.140.0

# Full lint clean
make lint 2>&1 | tail -3
# Expected: exit 0 clean
```

---

## Exit criteria

| # | Check | Required |
|---|---|---|
| 1 | `make lint` exits 0 (black + ruff + mypy all clean) | yes |
| 2 | `tests/test_ci.py::test_lint_clean` passes (not skipped) | yes |
| 3 | Non-bootstrap pytest baseline hold | yes |
| 4 | Goldens 54/65 byte-identical | yes |
| 5 | Fixed-point md5 unchanged | yes |
| 6 | `libmapanare_rt.a` byte-identical | yes |
| 7 | 5 flaky runs all 0-failure, diffs empty | yes |
| 8 | `FLAKY_AUDIT.md` written with cumulative 5-audit table | yes |
| 9 | An.2 marked CLOSED in DOCKET_LEDGER | yes |

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Black reformat breaks formatted-string-sensitive test | very low | low | Full pytest after Phase 1 catches this |
| Ruff auto-fix removes an "unused" import that actually is used via `importlib` / `__all__` | low | medium | Full pytest after Phase 2; manual review of any `F401` in `mapanare/__init__.py` or similar |
| Mypy fix introduces stricter types that ripple across files | medium | low | Fix bottom-up (leaf files first); expect ~2-3 iterations |
| 5th flaky audit reveals a newly-flaky test from v4.140.0 emitter change | low | high | Investigate + fix before panel; don't claim 5/5 clean if one run fails |

## What this release does NOT do

- Does not touch compiler codegen or runtime C.
- Does not add new tests (except the new SE.1 goldens from v4.140.0
  which are in place).
- Does not close Ge.1 — that's v4.142.0.
- Does not refactor for clarity; lint clean only, not rewrite.

## Score-impact forecast

Anaconda 8.9 → 9.2 at v4.143.0 panel (An.2 closed, 5th flaky audit
strengthens her An.5 finding). Boa +0.05 (docs side-effects from
cleanup). No other reviewer impact.
