# v5.3.3 — SPEC + docs polish

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.3.2 shipped
**Estimated work:** 1–2 hours

---

## Goal

Address Coral's SPEC-pkg and demo gap items, plus the SPEC header
staleness that has been flagged for 3 consecutive panels.

## Items

| ID | Severity | Fix | Effort |
|----|----------|-----|--------|
| **SPEC-pkg** | LOW | Add SPEC sections for `mapanare.toml` schema, `mapanare install` semantics, `mapanare.lock` format, version constraint resolution | 1 hour |
| **SPEC header** | LOW | Bump SPEC version to 5.3.3 (27 releases stale at 4.143.0) | 1 min |
| **Demo gap (signals)** | LOW | Add `examples/signals/counter.mn` — standalone reactive signal demo | 30 min |

## Expected panel impact

- **Coral**: +0.1–0.2 (SPEC current, pkg specified, signal demo)
- **Net aggregate lift**: +0.02–0.05

## Exit criteria

- `head -3 docs/SPEC.md` shows v5.3.3
- `pytest tests/test_spec.py` passes
- `examples/signals/counter.mn` runs through Python bootstrap
