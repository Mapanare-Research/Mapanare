# v5.21.1 — Mc.7 — pre-panel docs hygiene

**Status:** PLANNING
**Breaking:** No. Zero compiler/runtime/dispatch edits.
Doc-surface only.
**Prerequisite:** v5.21.0 shipped (Te.6 — chained comparisons).
**Estimated effort:** 3–6h, single session.

---

## Why this exists

The v5.13–v5.21 terseness arc shipped 6 additive language features
across 10 releases. The v5.11.0 panel docked **-0.5 from Boa** and
**-0.1 from Coral** for docs-surface drift; that drift has now
compounded to 14-release SPEC staleness, 4-release README staleness,
and a broken `if x: y` forward promise from v5.14.0 SPEC.

This release is **pre-panel polish** — same pattern as v5.7.1 (which
preceded the highest-scoring panel in project history at v5.8.0,
9.66/10). Zero compiler edits. Close the doc-surface drift class
**structurally**, not just at the immediate v5.21.0 instances.

The v5.22.0 panel runs after this release ships.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **H.1** | HIGH | `README.md:168` "80/80 native goldens at v5.17.1" → "95/95 at v5.21.0"; line 176 fixed-point line bumped 231,957 → 238,086 lines + carry trail. | 15 min |
| **H.2** | HIGH | `docs/SPEC.md` header bumped 5.7.1 → 5.21.0 cut; "What changed since the v5.7.1 sync" block summarizes Te.1–Te.6 + Sh.* + Mc.* + Te.3 + Dk.*. | 1h |
| **H.3** | HIGH | `docs/SPEC.md` §4.0 (Block Syntax) rewritten for v5.19.0 Te.3: warning text, parse-time semantics, `mnc fmt` auto-migration default, `MAPANARE_NO_BRACE_WARNING=1` opt-out, hard-removal at v6.0. | 30 min |
| **H.4** | HIGH | `docs/SPEC.md:1009` "Single-line `if x: y` form deferred to v5.21.0" → either ship it or rescope to v6.0 with rationale. **Decision-1 below.** | varies |
| **H.5** | HIGH | `docs/SPEC.md` new sections covering Te.5 (StructUpdate, LetDestructure, LetElse, IfLet, WhileLet) + Te.6 (chained-cmp already added at v5.21.0). | 1h |
| **H.6** | MEDIUM | Localized READMEs (es/pt/zh-CN) — three native-compiler subsections rewritten with v5.21.0 status (95/95, 238,086 strict, terseness arc summary in summary). Boa Bo.17r structural closure. | 1h |
| **H.7** | LOW | `examples/chained_cmp.mn` — 3- and 4-element chains + side-effect once-eval demo. Runs through `mnc run` clean. | 15 min |
| **H.8** | LOW | `mapanare/format.py` ChainedCompare arm — single space around each operator in a chain; `mnc fmt --check` round-trips stable. | 30 min |
| **H.9** | LOW | `tests/bootstrap/test_chained_cmp_mirror.py` — 10 cross-bootstrap cases asserting Python ↔ `mnc-stage1` byte-identical IR. Mirrors `test_te5_mirror.py`. | 30 min |
| **H.10** | LOW | `.reviews/CARRY_FORWARD.md` appended for v5.13.0–v5.21.1 arc closures. | 30 min |
| **H.11** | LOW | `docs/known_issues.md` last-updated bumped + arc-closure narrative block. | 15 min |
| **H.12** | LOW | `tests/golden/BENCHMARKS.md` Windows section — Rattler #1 from v5.11.0; either auto-refresh from `cat VERSION` or split into `BENCHMARKS-windows.md`. | 30 min |

---

## Decision-1 — single-line `if x: y` form

The v5.14.0 SPEC promised single-line `if x: y` for v5.21.0;
v5.21.0 shipped Te.6 (chained-cmp) instead. Two paths:

**Path A — ship it in v5.21.1 (~1h).** Single-line form parses
as: `if cond: stmt` ≡ `if cond { stmt }`. Lark grammar gains
`KW_IF expr COLON stmt` alternative; transformer wraps stmt in
a `Block`. `_indent_to_braces` already handles colon-blocks; for
single-line, the body is on the same line so the preprocessor
needs to be taught. Bootstrap mirror (~30 min). New goldens for
`if x: y`, `else: y`, chained `if x: y; else if z: w`. Strict
fixed-point preserved by construction.

**Path B — rescope to v6.0 with rationale.** SPEC §4.0 §1009
rewritten as: "Single-line colon form (`if x: y`) is **deferred
to v6.0** to coincide with `{}` hard removal — until then,
single-line form would be ambiguous with the hard-removal
deprecation pattern." (~10 min.)

**Recommendation:** Path A — single-line is a 1-hour shippable
piece that closes a stale promise in the same release; matches
the user-facing terseness story.

If Path B is chosen, this release's identity changes from
"Mc.7 — pre-panel docs hygiene" to "Mc.7 — docs hygiene + Te.3
deferral re-scope" with a SESSION_REPORT note that v5.14.0's
forward promise was wrong.

---

## Phase plan

**Phase 0 — audit verification.** Re-run the v5.21.0 doc-drift
audit at HEAD; confirm H.1–H.12 still apply. Lock Decision-1.

**Phase 1 — README + localized READMEs (H.1, H.6).** Boa-axis
items. The bump_version.py script has already updated badges;
this phase rewrites prose body content. Verify `cat VERSION`
matches every badge instance.

**Phase 2 — SPEC sync (H.2, H.3, H.4, H.5).** Coral-axis items.
Most weight here. Header re-sync + §4.0 Te.3 documentation +
broken-promise closure (Decision-1) + Te.5/Te.6 sections.

**Phase 3 — Examples + format + bootstrap mirror (H.7, H.8,
H.9).** Anaconda + Cobra axis items.

**Phase 4 — Ledger + CHANGELOG (H.10, H.11).** Process items.

**Phase 5 — Validation.** `make lint`, `python3 scripts/
check_changelog_honesty.py`, `python3 scripts/
check_workflow_shapes.py`, `bash scripts/verify_fixed_point.sh
--keep`, `python3 scripts/test_native.py --stage1 mapanare/
self/mnc-stage1`, `bash scripts/build_from_seed.sh`. All must
pass.

**Phase 6 — SESSION_REPORT + bump VERSION 5.21.0 → 5.21.1.**

---

## What does NOT ship

- **Compiler edits.** Zero. Strict 3-stage fixed point preserved
  by construction at 238,086 lines / 0 diff.
- **Runtime edits.** Zero. C runtime delta is empty.
- **MIR / IR changes.** Zero.
- **New language features** beyond Decision-1 if Path A fires.
- **Tag promotion.** Awaits user approval.

---

## Success criteria

- All 12 H.* items closed at HEAD
- Strict 3-stage fixed point preserved (238,086 lines / 0 diff)
- Goldens 95/95 (or 96+/96+ if Decision-1 = Path A ships
  single-line `if x: y` with new goldens)
- `bash scripts/build_from_seed.sh` succeeds
- `make lint` clean
- `python3 scripts/check_changelog_honesty.py` clean
- `mnc fmt --check` clean on goldens + `mapanare/self/`
- v5.22.0 panel can run with PRE_PANEL_AUDIT showing zero
  open H.* items at v5.21.1 HEAD

---

## Out of scope (deferred)

- Anything that touches `mapanare/`, `runtime/native/`, or
  `mapanare/self/*.mn` source files (other than format.py
  H.8 which is non-grammatical).
- Rt.04 multi-level alias analysis — DEFERRED to v6.0.
- New SPEC features beyond v5.13–v5.21 already-shipped surface.
- v5.22.0 panel itself — runs separately at the v5.21.1 →
  v5.22.0 boundary per `.reviews/v5.22.0/prompt.md`.
