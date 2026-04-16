# v4.138.0 Session Report — Docs sweep (Boa carry-forward)

**Date:** 2026-04-15
**Branch:** `v4.138.0` from `dev`
**Theme:** Close every Boa carry-forward from the v4.136.0 panel (Bo.1–Bo.7).

---

## Changes

### Bo.5 — CLI version fix (`mapanare/cli.py`)

Replaced `importlib.metadata` version lookup (which returned stale `2.0.1`
from egg-info) with a direct read of the `VERSION` file. The `VERSION`
file is already the single source of truth for `pyproject.toml`
(`version = {file = "VERSION"}`); now the CLI matches.

### Bo.6 — `docs/guides/getting_started.md` refresh

- Golden count updated from `39/65` to `53/65`.
- Removed Sh.2 and Sh.11 from "doesn't do yet" table (both closed).
- Added strict 3-stage fixed-point status note.
- Cross-reference to `docs/known_issues.md` for full open-item list.

### Bo.2 — Native-mode prerequisites section

Added detailed prerequisites table to `docs/guides/getting_started.md`
with tool/version/install columns for LLVM 17+, clang, opt/llc/llvm-as/lli,
valgrind (optional), and Python 3.11+. Windows/WSL note included.

### Bo.4 + Bo.7 — Localized README sync

Updated `docs/README.es.md`, `docs/README.zh-CN.md`, `docs/README.pt.md`:
- Version badge: `4.31.0` → `5.0.0-rc1`
- Test badge: `4845` → `5139+`
- Description text: added fixed-point, benchmark numbers, WebAssembly mention
- Added WebAssembly shield badge (matching English README)
- Benchmark link to `benchmarks/FINAL_REPORT_v4.136.md`

### Bo.1 — `docs/known_issues.md`

Created new file listing all user-facing open items with symptoms,
workarounds, and tracking versions. Four sections: self-hosted feature
gaps (Sh.4/5/6/7/9a/9b), grammar/language (Gr.1/2, Sem.1), runtime
(Rt.2/3), ecosystem (no package manager).

### Bo.3 — STATISTICS.md merge note

Added header note to `docs/roadmap/v4/v4.120.0/STATISTICS.md` directing
readers to per-release MEASUREMENTS.md files and panel aggregates.

### VERSION propagation

- `VERSION` bumped to `4.138.0`
- `libmapanare_rt.a` rebuilt with `-DMAPANARE_VERSION="4.138.0"`
- `mnc-stage1` rebuilt via `scripts/build_stage1.py` (VERSION propagated)

---

## Verification

| Check | Result |
|---|---|
| `mapanare --version` | `4.138.0` |
| Non-bootstrap pytest | **5,142 / 0** (was 5,139 / 0 at v4.137.0; +3 from new `docs/known_issues.md` parametrized doc link tests) |
| Doc link tests | 662 passed, 1 skipped |
| Golden tests (mnc-stage1) | **53/65** byte-identical to v4.135.0+ |
| Fixed-point | Unchanged (no compiler source edits) |
| `libmapanare_rt.a` | Rebuilt for VERSION; source-identical to v4.137.0 |
| `mnc-stage1` | Rebuilt for VERSION; 3,480,720 bytes stripped |

---

## Docket ledger delta

| Docket | Action |
|---|---|
| Bo.1 | Re-opened v4.136.0 → **CLOSED v4.138.0** |
| Bo.2 | Re-opened v4.136.0 → **CLOSED v4.138.0** |
| Bo.3 | Re-opened v4.136.0 → **CLOSED v4.138.0** |
| Bo.4 | Opened v4.136.0 → **CLOSED v4.138.0** |
| Bo.5 | Opened v4.136.0 → **CLOSED v4.138.0** |
| Bo.6 | Opened v4.136.0 → **CLOSED v4.138.0** |
| Bo.7 | Opened v4.136.0 → **CLOSED v4.138.0** |

**Net ledger state:** 63 dockets opened since v4.99.0 · **40 closed (63%)** ·
23 open: **0 CRITICAL · 0 HIGH · 10 MEDIUM · 13 LOW**.

---

## What this release does NOT change

- No compiler source edits (Python emitter, self-hosted .mn, parser, semantic, MIR).
- No runtime C source edits (only rebuilt for VERSION propagation).
- No new tests added.
- No SPEC changes (deferred to v4.139.0).

## Expected panel impact

Boa 8.4 → ~8.9 at v4.143.0 panel. Indirect: Anaconda +0.1 (doc-link
tests cleaner), Coral +0.05 (known_issues.md clarifies v5.x scope).
