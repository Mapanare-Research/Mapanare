# Mapanare v5.3.0 — "THE PANEL"

> **Seven-reviewer review of the v5.0 → v5.2 arc.** Mechanical rule
> same as v4.136.0: aggregate ≥ 9.0 AND 0 NEEDS WORK → tag
> achievement. Else iterate in a v5.3.x closeout arc until the next
> panel re-clears. This is the first full v5 panel (v4.136.0 panel
> produced v5.0.0-rc1 but pre-dated v5.0 final).

**Status:** PLANNED (skeleton)
**Breaking:** No
**Prerequisite:** v5.2.0 shipped (package registry live)
**Estimated work:** 1-2 sessions (measurement + review); closeout
arc scoped separately if aggregate < 9.0

---

## Why this release exists

The Mapanare panel cadence, from precedent:

| Panel | Date | Aggregate | Decision |
|---|---|---|---|
| v4.26.0 | — | 9.44 | Option A — flagged 6 hollow features |
| v4.36.0 | — | 9.79 | Peak, Option A |
| v4.76.0 | — | 8.86 | Individual 10/10 (Mamba) |
| v4.99.0 | — | 6.59 | **Option B — trough, kicked off recovery** |
| v4.120.0 | — | 8.21 | Option B (1 NEEDS WORK — Anaconda CI) |
| **v4.136.0** | — | **8.80** | **Option C — v5.0.0-rc1 tagged** |
| v4.143.0 | — | 8.86 | Option C (rc1 held; 0 NEEDS WORK) |
| v4.144.0 | — | 9.21 | Option A — 6 EXCEEDS |
| v5.3.0 | — | TBD | TBD |

A panel every 20-25 releases keeps the quality bar honest. v5.3.0
follows that cadence over v5.0.1–v5.2.0 (~9 releases, ~3 months
elapsed). The scope is smaller than v4.136.0 because v5 started
clean.

## Scope

**In scope:**
- Baseline metrics refresh: `MEASUREMENTS.md` with current numbers
- Flaky audit: 5× sequential pytest (expect 0 flaky per v4.153.0
  streak)
- Sanitizer sweep: valgrind + ASan on current goldens
- Benchmark refresh: cross-language + async corpora
- Fixed-point verification on Linux + Windows + macOS
  (v5.1.1 enables Windows; Linux verified since v4.134.0; macOS
  tracked for this release or v5.3.x)
- Seven reviewers graded against the same rubric as v4.136.0:
  - Rattler — correctness + diagnostics
  - Viper — memory safety
  - Anaconda — CI / testing / gates
  - Cobra — build-from-seed / fixed-point
  - Coral — language / SPEC / docs
  - Boa — release hygiene / versioning
  - Mamba — runtime / C / sanitizers

**Out of scope:**
- New features (panel is pure review)
- Any compiler source changes
- Docket closures (they happen in the closeout arc, not the panel
  release itself)

## Exit criteria

- Seven reviewers deliver reviews under `.reviews/v5.2.0/{01-07}-*.md`
- Aggregate score computed in `.reviews/v5.2.0/V5_DECISION.md`
- Mechanical-rule decision documented
- v5.3.0 `SESSION_REPORT.md` summarizes the panel + decision
- `ROADMAP.md` gains a "Where We Are (v5.3.0 ...)" entry

## Possible outcomes

- **Aggregate ≥ 9.0 AND 0 NEEDS WORK** → Option A. v5.3.0 is the
  release; carry-forward items become v5.4+ planning.
- **8.5 ≤ aggregate < 9.0 AND 0 NEEDS WORK** → Option C. Spawn a
  closeout arc v5.3.x → re-panel at v5.4.0.
- **Aggregate < 8.5 OR any NEEDS WORK** → Option B. Full recovery
  arc like v4.99.0 → v4.120.0 (20 releases); re-panel when the
  NEEDS WORK items close.

## Risks

**Risk 1 — reviewers find a regression that landed between v5.0.0
and v5.2.0.**
Likely suspects: new list-IR-inlining bugs (v5.1.0), MIR-pass
re-enable (v5.1.2) breaking fixed point.
*Mitigation:* pre-panel refresh (v5.2.1 or similar) with a full
sanitizer sweep. Same pattern as v4.135.0 prepping for v4.136.0.

**Risk 2 — package registry (v5.2.0) found unsafe.**
Publishing infrastructure can be a NEEDS WORK magnet on first panel.
*Mitigation:* scope v5.2.0 conservatively (MVP, not feature-parity
with cargo). Accept that the first panel may dock the release for
missing yank semantics or weak auth.
