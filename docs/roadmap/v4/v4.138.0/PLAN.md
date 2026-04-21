# Mapanare v4.138.0 — Docs sweep (Boa's 8.4 → 8.9 delta)

> **Docs hygiene release.** Close every Boa carry-forward from
> v4.136.0 (Bo.1 through Bo.7) in one focused pass. Total effort ~3.5
> hours of writing per Boa's own estimate.

**Status:** PLANNED
**Breaking:** No (docs + one CLI flag fix)
**Prerequisite:** v4.137.0 (Ch.1 closed)
**Estimated work:** 1 short sprint
**Theme:** Day-1 papercuts + localized README parity + carry-forwards.

---

## Why this release

Boa was the sole negative delta at the v4.136.0 panel (8.7 → 8.4,
−0.3). Her grade is MEETS only because "no doc regression makes a new
user write incorrect code." The items are real but small: each is
10 min to 1 hr of writing; collectively they lift her score ~0.5.

---

## Scope — Boa's ledger

### Bo.4 — localized READMEs sync (medium, ~30 min)

v4.136.0 closed the main `README.md`. Localized versions may still
show old version badges and stale benchmark links:

- `docs/README.es.md`
- `docs/README.zh-CN.md`
- `docs/README.pt.md`

Mirror the v4.136.0-era bumps:
- version badge → `5.0.0-rc1`
- benchmark link → `benchmarks/FINAL_REPORT_v4.136.md`
- benchmark numbers → 42.6× faster than Python, 1.12× of Rust, 4.86× slower than C
- roadmap table row parity (if present)

### Bo.5 — `mapanare --version` reads VERSION file (low, ~10 min)

Reported: fresh install prints `2.0.1` instead of `5.0.0-rc1`.
Root cause: `mapanare/cli.py` reads version via `pkg_resources` /
`importlib.metadata` rather than the `VERSION` file.

Fix:
```python
# mapanare/cli.py
from pathlib import Path
_VERSION_FILE = Path(__file__).resolve().parent.parent / "VERSION"
__version__ = _VERSION_FILE.read_text().strip() if _VERSION_FILE.exists() else "unknown"
```

Or read during setup.py / pyproject.toml build. Either works; the
`VERSION` file is the single source of truth.

### Bo.6 — getting_started.md refresh (low, ~10 min)

`docs/guides/getting_started.md` §5 still reads:

> "39/65 golden tests pass through mnc-stage1"

Update to `53/65` (v4.136.0 reality). Also remove Sh.11 from the
"open issues" row — closed v4.134.0.

### Bo.1 — docs/known_issues.md (low, ~1 hr)

Carry-forward from v4.120.0. Create `docs/known_issues.md` listing
user-facing open items:
- Sh.4 async (self-hosted emitter)
- Sh.6 tensor (self-hosted emitter)
- Sh.7 closure-typed params (self-hosted)
- Sh.9a / Sh.9b / Sh.10 async emitter workarounds
- Gr.1 multi-line list/tensor literals
- Gr.2 qualified type refs in type position (blocks stdlib/gpu)
- Sem.1 module-level `let mut` scoping
- Package manager absent (v5.x ecosystem scope)

Each entry: symptom, workaround (if any), tracking release.

### Bo.2 — getting-started native-mode prerequisites (low, ~30 min)

Carry-forward from v4.120.0. Add a section to `docs/guides/getting_started.md`
listing native-mode requirements:
- LLVM 17+ (`opt`, `llc`, `clang`)
- `clang` on PATH for final link
- WSL2 or Linux for `mnc-stage1` (Windows: Python bootstrap only)
- `llvm-as` + `lli` for validation
- (Optional) `valgrind`, `llvm-symbolizer` for debugging

### Bo.3 — STATISTICS.md merge (low, ~15 min)

Carry-forward from v4.120.0. `STATISTICS.md` was consolidated into
`MEASUREMENTS.md` pattern at v4.127.0+, but a panel footnote was lost.
Restore as a top-of-file link or note.

### Bo.7 — localized README version parity (see Bo.4 overlap)

Executed alongside Bo.4.

---

## Phase 1 — Audit current state

```bash
# Version drift across translations
grep -HE '(version|Version).{0,40}([0-9]+\.[0-9]+\.[0-9]+)' docs/README.es.md docs/README.zh-CN.md docs/README.pt.md

# Benchmark link drift
grep -HE 'FINAL_REPORT_v?[0-9]' docs/README.*.md README.md

# Getting-started stale counts
grep -HE '39/65|Sh\.11' docs/guides/getting_started.md docs/getting_started.md 2>&1 | head -10

# Version print
python3 -c "from mapanare import cli; print(cli.__version__)" 2>&1 | head -3
mapanare --version 2>&1 | head -3
```

## Phase 2 — Edits in dependency order

1. **Bo.5** first (CLI version fix, isolated change in `mapanare/cli.py`)
2. **Bo.6** (`docs/guides/getting_started.md` counts)
3. **Bo.4 / Bo.7** (localized READMEs — copy English edits to 3 files)
4. **Bo.2** (prerequisites section in getting_started)
5. **Bo.1** (`docs/known_issues.md` new file)
6. **Bo.3** (STATISTICS link/note)

## Phase 3 — Verify

```bash
python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no 2>&1 | tail -3
# Expected: 5,119 passed / 0 failed (byte-identical to v4.137.0)

python3 -m pytest tests/test_doc_links.py -v 2>&1 | tail -10
# New docs/known_issues.md should pass link checker

mapanare --version 2>&1
# Expected: 4.138.0 (not 2.0.1)

# Goldens + fixed-point unchanged (no compiler edits)
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 2>&1 | tail -3
```

---

## Exit criteria

| # | Check | Required |
|---|---|---|
| 1 | `mapanare --version` prints `4.138.0` (reads VERSION file) | yes |
| 2 | `docs/README.es.md` / `.zh-CN.md` / `.pt.md` version badges + benchmark links match English | yes |
| 3 | `docs/guides/getting_started.md` reflects 53/65 goldens, no stale Sh.11 | yes |
| 4 | `docs/known_issues.md` exists, lists open user-facing items with workarounds | yes |
| 5 | Native-mode prerequisites section present in getting-started | yes |
| 6 | STATISTICS.md merge note/link restored | yes |
| 7 | Non-bootstrap pytest: 5,119 / 0 byte-identical | yes |
| 8 | Goldens / fixed-point unchanged | yes |
| 9 | `libmapanare_rt.a` byte-identical | yes |
| 10 | Bo.1–Bo.7 all marked CLOSED in DOCKET_LEDGER.md | yes |

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| CLI version read breaks when installed from sdist (no VERSION in egg-info) | low | low | Include VERSION in `setup.py` / `pyproject.toml` data_files or use `importlib.resources` |
| Localized READMEs diverge on prose (only English is source) | medium | low | Document `docs/README.es.md` etc. as badges-and-benchmark-only mirrors for now; full localization is v5.x |
| `docs/known_issues.md` duplicates DOCKET_LEDGER | medium | low | Cross-link; known_issues is user-facing, ledger is engineering-facing |

## What this release does NOT do

- Does not touch compiler, runtime, or self-hosted.
- Does not update SPEC (v4.139.0 handles Coral's SPEC items).
- Does not add new examples or cookbook entries.

## Score-impact forecast

Boa 8.4 → 8.9 at v4.143.0 panel. Indirect: Anaconda +0.1 (doc-link
tests pass cleaner), Coral +0.05 (known_issues.md clarifies v5.x
scope).
