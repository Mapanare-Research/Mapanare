# v4.36.0 Session Report — Arc 1 Panel Release

**Date:** 2026-04-12
**Scope:** Arc 1 panel (zero new features) + LOW sweep + documentation polish
**Breaking:** No
**Panel:** Full 7-reviewer (first 5-minor cadence panel since v4.31.0)

---

## What shipped

### Phase 1: LOW item sweep

- **L7 CLOSED:** `cuda_matmul` upload/download return values checked at `runtime/native/mapanare_gpu.c:1756`. Error path frees all GPU buffers.
- **A10 ADDED:** Self-hosted bounded-for sentinels (442 sites across 8 modules) tracked as carry-forward. Grammar gap — `loop {}` would close it in v4.37.0+.

### Phase 2: Ledger drain

- CARRY_FORWARD.md audited end-to-end
- 55/67 items CLOSED (up from 43 at v4.31.0)
- 12 items OPEN: 8 DEFERRED to v5.0.0+, 2 tracked to v4.37.0+ (items 49, 50), 1 tracked to Culebra (A5), 1 new (A10)
- Dual-closure status verified: items 30-31 still asymmetric (PY closed, SH open — 1 site each)
- LEDGER_AUDIT.md written

### Phase 3: Documentation polish

- `docs/SPEC.md` §5.5-5.8: guards, or-patterns, `?` operator
- `docs/cookbook.md`: three new sections (guards, or-patterns, `?` operator)

### Phase 4: Measurements

- 34,459 lines Python compiler, 13,150 lines C runtime, 37,211 lines self-hosted
- 708 pytest tests (core), 49 golden tests
- MEASUREMENTS.md written

### Phase 5: Pre-panel audit

- 18/18 SESSION_REPORT claims from v4.32.0-v4.35.0 verified (100% pass rate)
- PRE_PANEL_AUDIT.md written

### Phase 6: Panel run

- 7 reviewers spawned in parallel (Viper, Boa, Cobra, Mamba, Anaconda, Rattler, Coral)
- Each reviewer read their v4.31.0 file for continuity
- Panel verdict: **PASS — 9.50/10 aggregate (6 PASS + 1 PASS WITH NOTES + 0 NEEDS WORK)**
- Arc 1 officially **CLOSED**. v4.37.0 opens Arc 2 (LSP maturity).
- 6 MEDIUM action items filed to CARRY_FORWARD.md for v4.37.0+

---

## Arc 1 summary (v4.32.0-v4.36.0)

| Release | Theme | Key deliverable |
|---------|-------|-----------------|
| v4.32.0 | Arc-end closure | 9 HIGH/MEDIUM items from v4.31.0 docket |
| v4.33.0 | Error handling | `?` operator (first new feature in 7 releases) |
| v4.34.0 | Pattern matching | Maranget decision-tree rewrite (A6 closed) |
| v4.35.0 | Pattern matching | Match guards + or-patterns (21 new tests) |
| v4.36.0 | Panel | Full 7-reviewer audit + LOW sweep |

---

## Files changed

| File | What |
|------|------|
| `runtime/native/mapanare_gpu.c` | cuda_matmul rc check |
| `.reviews/CARRY_FORWARD.md` | A10 added, L7 closed |
| `docs/SPEC.md` | §5.5-5.8 (guards, or-patterns, ?) |
| `docs/cookbook.md` | 3 new sections |
| `docs/roadmap/v4/v4.36.0/LEDGER_AUDIT.md` | NEW |
| `docs/roadmap/v4/v4.36.0/MEASUREMENTS.md` | NEW |
| `docs/roadmap/v4/v4.36.0/PRE_PANEL_AUDIT.md` | NEW |
| `.reviews/v4.36.0/` | Panel review directory |
| `VERSION` | 4.35.0 → 4.36.0 |
| `CHANGELOG.md` | v4.36.0 entry |
| `CLAUDE.md` | Current version updated |
