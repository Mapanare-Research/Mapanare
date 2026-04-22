# v5.4.0 — Re-panel

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.3.3 shipped, all MEDIUM items closed
**Estimated work:** 1 session (measurement + review)

---

## Goal

Re-panel after the v5.3.1–v5.3.3 closeout arc. Same seven reviewers,
same mechanical rule. Target: aggregate >= 9.5 (v4.36.0 peak was 9.79).

## Expected score recovery

| Reviewer | v5.3.0 | Expected v5.4.0 | Delta | Driver |
|----------|--------|-----------------|-------|--------|
| Rattler | 9.3 | 9.5–9.6 | +0.2–0.3 | In.1-stage2 fix restores correctness |
| Viper | 9.7 | 9.7 | +0.0 | Stable (Own.1 P2 is v5.x) |
| Anaconda | 8.9 | 9.3–9.5 | +0.4–0.6 | Lint GREEN, stream fixed, An.9r fixed |
| Cobra | 8.8 | 9.1–9.3 | +0.3–0.5 | Fixed-point restored |
| Coral | 9.4 | 9.5–9.6 | +0.1–0.2 | SPEC-pkg, signal demo |
| Boa | 9.4 | 9.5–9.6 | +0.1–0.2 | Bo.15/16/17 cleared |
| Mamba | 9.6 | 9.6–9.7 | +0.0–0.1 | Stream-C fix |
| **Aggregate** | **9.30** | **9.45–9.55** | **+0.15–0.25** | — |

## Closeout arc precedent

The v4.121.0–v4.135.0 closeout arc (15 releases) pushed the aggregate
from 8.21 (v4.120.0, Option B) to 8.80 (v4.136.0, Option C). The
current arc is shorter (3 releases) because the items are smaller:
no compiler-semantic changes needed, only cloner extension + docs.
