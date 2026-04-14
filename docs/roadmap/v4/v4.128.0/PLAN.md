# Mapanare v4.128.0 — Documentation + SPEC Sync

> **Buffer release 3.** Close documentation gaps before the v4.130.0
> panel. SPEC.md audit against current implementation. Fix stale
> sections. Verify all examples compile and run. Sync cookbook with
> v4.120.0-v4.127.0 changes. Boa (DX reviewer) and Coral (language
> design reviewer) both grade documentation currency.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.127.0
**Delta review:** No
**Full panel:** No (deferred to v4.130.0)
**Estimated work:** 1 sprint
**Theme:** Sync documentation with reality. No new guides -- just make existing docs honest.

---

## Scope

The language specification (`docs/SPEC.md`) and supporting documentation
were last synced in v4.116.0. Since then, v4.120.0-v4.127.0 made
significant changes: test hygiene sweep, DWARF warning, List<Int>
indexing fix, dead-code sweep (optimizer.py + TBAA deletion), unboxed
enum payloads, benchmark refresh, golden test push, and fixed-point
refinement. Any SPEC section referencing deleted features (TBAA,
deprecated optimizer passes) is now stale. Any example using pre-v4.122.0
list indexing patterns may be incorrect.

This release audits SPEC.md section by section, fixes the most critical
divergences, verifies all `examples/` programs, and ensures the cookbook
reflects current behavior. Documentation precision, not documentation
expansion.

## Phase 1 — SPEC.md audit

- [ ] Read SPEC.md end-to-end. For each section, check:
  - Does the described behavior match the current implementation?
  - Are referenced features still present (not deleted in v4.123.0 dead-code sweep)?
  - Are code examples syntactically correct for the current grammar?
  - Are type system descriptions current (especially after v4.124.0 enum unboxing)?
- [ ] Mark each section as:
  - **OK** — current and accurate
  - **STALE** — references deleted features or outdated behavior
  - **MISSING** — feature exists but is not documented
  - **WRONG** — actively incorrect (describes behavior that does not match implementation)
- [ ] Write `docs/roadmap/v4/v4.128.0/SPEC_AUDIT.md` with per-section status

## Phase 2 — Fix critical SPEC divergences

- [ ] Fix all **WRONG** sections first (highest priority)
- [ ] Fix **STALE** sections that reference deleted features:
  - TBAA metadata (deleted in v4.123.0) — remove or update references
  - Deprecated optimizer passes — update optimizer section
  - Any references to `println` (deprecated since v3.x) — update to `print`
- [ ] Fix **STALE** sections that reference outdated behavior:
  - Enum representation (updated in v4.124.0 with unboxed payloads)
  - List indexing (fixed in v4.122.0)
- [ ] Add brief notes for **MISSING** sections (one paragraph each, not full documentation)

## Phase 3 — Verify examples

- [ ] Run all programs in `examples/` through the Python bootstrap:
  ```bash
  for f in examples/*.mn; do python -m mapanare run "$f"; done
  ```
- [ ] Run all programs in `examples/wasm/` through the WASM emitter:
  ```bash
  for f in examples/wasm/*.mn; do python -m mapanare emit-wasm "$f" -o /dev/null; done
  ```
- [ ] Record pass/fail for each example
- [ ] Fix any broken examples (update syntax, fix imports, adjust for API changes)

## Phase 4 — Sync cookbook and guides

- [ ] Check `docs/guides/` — are getting-started, cookbook, and tutorial examples current?
- [ ] If any code examples use syntax or APIs changed in v4.120.0-v4.127.0, update them
- [ ] Verify the getting-started guide works end-to-end (per Bo.2 from v4.121.0)
- [ ] Check `docs/manifesto.md` — is the design philosophy still aligned with current direction?

## Phase 5 — LOW sweep + closeout

- [ ] `make test` — all green
- [ ] `make lint` — all clean
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.128.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (7 items)

| # | Check | Evidence |
|---|---|---|
| 1 | SPEC.md audit complete (every section marked OK/STALE/MISSING/WRONG) | `SPEC_AUDIT.md` |
| 2 | All WRONG sections fixed | commit diffs |
| 3 | All STALE sections referencing deleted features updated | commit diffs |
| 4 | All `examples/` programs compile and run | test log |
| 5 | Cookbook / guides current with v4.120.0-v4.127.0 changes | commit diffs or "no changes needed" note |
| 6 | `make test` green | CI logs |
| 7 | Standard closeout clean | CHANGELOG + SESSION_REPORT + VERSION bump |

---

## What this release does NOT do

- **Write new guides or tutorials.** This is a sync release, not a content-creation release.
- **Add new SPEC sections for unspecified features.** MISSING sections get a one-paragraph stub, not full documentation.
- **Change compiler or runtime code.** All changes are in `docs/` and `examples/`. If an example is broken because of a compiler bug, file a docket item -- do not fix the compiler here.
- **Run a panel.** Next panel is v4.130.0.
- **Rewrite the manifesto.** Check for alignment; do not rewrite.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| SPEC.md is very large and the audit takes the entire sprint | medium | medium | Prioritize WRONG and STALE over OK sections. Skip deep audit of sections known to be stable (e.g., lexer grammar, basic types). |
| Multiple examples are broken and require compiler fixes | low | high | Document broken examples with docket IDs. Fix only examples that need documentation-level changes (syntax updates). |
| SPEC sections reference features that are partially implemented | medium | low | Mark as STALE with a note about implementation status. Honest documentation. |
| Cookbook has never been maintained and is entirely stale | medium | medium | If the cookbook is beyond repair, delete it and note its absence. An absent cookbook is better than a wrong one. |

---

## After v4.128.0

v4.129.0 — pre-panel prep and third flaky audit. Final verification before the v4.130.0 panel. Sanitizer runs, 5x flaky audit, pre-panel audit document.
