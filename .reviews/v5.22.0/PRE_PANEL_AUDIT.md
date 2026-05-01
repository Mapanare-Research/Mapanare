# v5.22.0 Pre-Panel Audit

> **Cadence trigger.** Last full panel was v5.11.0 (2026-04-28).
> Per `.reviews/REVIEW_CADENCE.md`, panels run every 5 minor
> versions and on five language-feature releases. v5.21.0 is
> **10 releases past** the last panel and ships **5+ language-
> feature releases** (v5.14.0 Te.1 colon-block + `pass`, v5.15.0
> Te.2 comprehensions/lambda/implicit-return, v5.16.0 Te.4
> string-interp parity, v5.20.0 Te.5 struct ergonomics with new
> StructUpdate / LetDestructure / LetElse / IfLet / WhileLet
> AST nodes, v5.21.0 Te.6 ChainedCompare). This panel is **two
> independent triggers overdue**.
>
> **Pre-panel posture (lead's fact-check before reviewers run).**
> v5.21.1 hygiene release ships first to clear known doc-surface
> drift. The panel grades v5.22.0 against the v5.11.0 → v5.21.0
> arc; v5.21.1 closes the items the panel would otherwise dock
> at fresh.

**Audit date:** 2026-05-01.
**Target version:** v5.22.0 (post-v5.21.1 hygiene).
**Arc graded:** v5.11.0 → v5.21.0 (10 releases — entire terseness
arc Te.1–Te.6, plus Mc.* tooling, Sh.* self-host rewrite,
v5.18.0 LSP, v5.19.0/.1 Docker, v5.20.0 struct ergonomics).

---

## Findings cleared in v5.21.1 hygiene release

These are the items the lead's own fact-check surfaced before
spawning the panel. Each one is a v5.11.0-panel-finding shape
that would have re-opened at this panel; closing them in v5.21.1
prevents a Bo.18r-style two-consecutive-panel regression.

### Doc surface (Boa axis)

| # | Severity | Finding | Closed in v5.21.1 |
|---|---|---|---|
| H.1 | HIGH | `README.md:168` reads "80/80 native goldens at v5.17.1" against a v5.21.0 codebase at 95/95 | bumped to 95/95 + v5.21.0 reference |
| H.2 | HIGH | `README.md:176` reads "stage2.ll byte-identical at 231,957 lines"; actual at v5.20.1/v5.21.0 is 238,086 | line count + carry trail refreshed |
| H.3 | MEDIUM | Localized READMEs (es/pt/zh-CN): bump_version sweep at v5.21.0 updated the badges but the prose body still references "v5.7.0 corpus" / "66/66" / "217k-line stage2.ll" — Boa's Bo.17r finding from v5.11.0 compounded across 10 releases | three native-compiler subsections rewritten in es/pt/zh-CN |
| H.4 | LOW | `examples/` carries no `chained_cmp.mn` — every shipped feature since v5.16.0 has an example | added 21-line example exercising 3-/4-element + side-effect once-eval |

### SPEC surface (Coral axis)

| # | Severity | Finding | Closed in v5.21.1 |
|---|---|---|---|
| H.5 | HIGH | `docs/SPEC.md:4` header reads "Live — synced to the v5.7.1 cut (2026-04-26)" — 14 releases stale, ~4× the 4-release drift Coral docked -0.1 for at v5.11.0 | header bumped to v5.21.0 cut + sync block summarizing the 14-release arc |
| H.6 | HIGH | `docs/SPEC.md` §4.0 (Block Syntax) reads "Mapanare accepts two block syntaxes interchangeably (since v5.14.0)" — does not mention v5.19.0 Te.3 soft-deprecation of `{}`, the parse-time warning, the `mnc fmt` auto-migration default, or `MAPANARE_NO_BRACE_WARNING=1` opt-out. User-visible CLI behavior present in production for 2 releases, absent from SPEC | §4.0 rewritten with v5.19.0 Te.3 status block + warning text + env var |
| H.7 | HIGH | `docs/SPEC.md:1009` says "Single-line `if x: y` form is **not** supported in v5.14.0 (deferred to v5.21.0)" — **broken promise**. v5.21.0 shipped Te.6 (chained comparisons), not single-line `if x: y` | replaced "deferred to v5.21.0" with explicit deferral-to-v6.0 (or shipped if scoped into v5.21.1 — see Decision-1 in v5.21.1 PLAN) |
| H.8 | HIGH | SPEC has no v5.20.0 Te.5 sections (StructUpdate, LetDestructure, LetElse, IfLet, WhileLet, Comprehension since v5.15.0) | new §6.x subsections per v5.20.0 SESSION_REPORT |
| H.9 | MEDIUM | SPEC §2.1 keyword table lists `pass` correctly but does not flag the v5.14.0 colon-block dependency that introduced it | cross-reference added |

### Bootstrap / fixed-point surface (Cobra / Rattler axis)

| # | Severity | Finding | Closed in v5.21.1 |
|---|---|---|---|
| H.10 | LOW | `mapanare/format.py` doesn't handle `ChainedCompare` whitespace canonicalization (PLAN said "Single space around each operator in a chain") | format-pass arm added; `mnc fmt` round-trips chains stable |
| H.11 | LOW | No `tests/bootstrap/test_chained_cmp_mirror.py` cross-bootstrap test asserting Python ↔ `mnc-stage1` byte-identical IR for chains (mirror of `tests/bootstrap/test_te5_mirror.py`) | added; 10 cases, all PASS |

### Process surface (Anaconda axis)

| # | Severity | Finding | Closed in v5.21.1 |
|---|---|---|---|
| H.12 | LOW | `.reviews/CARRY_FORWARD.md` last touched at v5.11.0; intervening releases shipped v5.13.x–v5.21.0 without ledger updates | ledger appended with the 10-release arc's CLOSED items + new v5.22.0 carry-forward column |
| H.13 | LOW | Panel cadence: per `REVIEW_CADENCE.md`, panel was due at v5.16.0 (5 minors past v5.11.0). 5 releases overdue at v5.21.0 | this panel runs at v5.22.0; cadence reset |

---

## What this panel is grading

The v5.11.0 → v5.21.0 arc is **the largest feature-velocity arc
in v5 history.** Specifically:

1. **Te.1 — colon-block syntax (v5.14.0)** + bootstrap mirror
   v5.14.1. Indent-based blocks for every block-introducing
   construct alongside `{}`. New `pass` keyword. New
   `_indent_to_braces` preprocessor in C runtime.
2. **Te.2 — comprehensions, implicit-return one-liner, terse
   lambdas (v5.15.0)** + bootstrap mirror v5.15.1.
3. **Te.4 — self-host string-interpolation parity (v5.16.0)**.
4. **Sh.* — self-host rewrite to terse syntax (v5.17.0–.2)**.
   17 modules, **-3,950 lines (-13.8%)** off the v5.13.0
   baseline. Mechanical `mnc fmt --to-terse` rewrite.
5. **Mc.* — LSP + init + check tooling pack (v5.18.0)**.
6. **Te.3 — `{}` soft-deprecation (v5.19.0)** + Docker
   images (v5.19.1). Brace warning at parse time + `mnc fmt`
   auto-migration default.
7. **Te.5 — struct ergonomics (v5.20.0)** + bootstrap mirror
   v5.20.1. Field shorthand, struct update, let
   destructuring, if-let / while-let / let-else.
8. **Te.6 — chained comparisons (v5.21.0)**. Te.5/Te.6 both
   ship via additive AST nodes; precedence levels of `==`/`!=`
   merged with `<`/`>`/`<=`/`>=`.
9. **Strict 3-stage fixed point preserved across 10 releases**.
   v5.9.0 milestone held continuously: 226,603 → 228,630 →
   231,723 → 231,957 → 232,281 → 238,086 lines, **0-line diff
   at every release**.
10. **Goldens 66/66 → 95/95** (+29 new goldens covering Te.1
    pass, Te.2 comprehensions/lambda/implicit-return, Te.4
    string-interp, Te.5 struct ergonomics, Te.6 chained-cmp).

The panel's job is to fact-check **every claim in every
SESSION_REPORT** in the arc against the code that ships at
v5.22.0.

---

## Specifically this panel must answer

- **Aggregate ≥ 9.5?** Target set by lead. (v5.11.0 panel
  was 9.62; v5.7.1 panel was 9.66; v5.21.0 brings 14
  feature-releases into the surface.)
- **Did any reviewer return NEEDS WORK?** If so, recovery arc
  opens regardless of aggregate.
- **Does Te.6 lower correctly?** `0 < f() < 10` must call
  `f()` exactly once. The
  `tests/golden/95_chained_cmp_side_effect.mn` golden
  verifies at runtime; the panel verifies in IR.
- **Does Te.3 actually deprecate `{}`?** Parser warning fires
  on every brace-shape source, exactly once per file?
  `MAPANARE_NO_BRACE_WARNING=1` suppresses it cleanly?
  `mnc fmt` (no flag) auto-migrates — verified on a fresh
  brace-syntax fixture?
- **Te.5 bootstrap mirror at v5.20.1**: do all 4 Te.5 surface
  forms (field shorthand, struct update, let destructuring,
  if-let / while-let / let-else) produce byte-identical IR
  through `mnc-stage1` vs the Python bootstrap on every
  golden? `tests/bootstrap/test_te5_mirror.py` is the
  contract.
- **v5.17.0 mechanical brace → colon rewrite**: was the
  fixed-point preserved at every per-module commit, not just
  at HEAD? (Per the SESSION_REPORT, yes — verify.)
- **v5.18.0 LSP**: does `pygls` pass the JSON-RPC stdio
  smoke (`tests/lsp/test_initialize_roundtrip.py`)? Does
  `mapa init` scaffold a project that builds clean?
- **v5.19.1 Docker images**: do the GHCR images exist? Does
  the in-image `mnc` wrapper resolve `libmapanare_rt.a`
  correctly?
- **Strict 3-stage fixed point**: stage2.ll == stage3.ll at
  238,086 lines / 0 diff at v5.22.0 HEAD?
- **`bash scripts/build_from_seed.sh` succeeds at v5.22.0
  HEAD** without manual seed refresh between releases other
  than the documented Sh.E v5.17.0 refresh?

---

## Carry-forward state entering this panel (post-v5.21.1)

After v5.21.1 hygiene closes H.1–H.13, the panel inherits a
**clean docket**:

- **0 CRITICAL** open
- **0 HIGH** open
- **0 MEDIUM** open
- **1 LOW (deferred to v6.0)** — Rt.04 multi-level alias
  analysis, correctly RESCOPED to the v6.0 borrow-checker
  arc per the v5.6.6 closeout. No active surface.

If the panel surfaces new findings, they're new — not
ledger items the lead failed to track.

---

## Score-impact pre-mitigations the panel should weigh

Pattern from prior panels: docs-surface findings drove the
v5.11.0 -0.5 (Boa) and -0.1 (Coral). v5.21.1 closes that
class structurally. Score impact the panel should weigh:

- **+** Strict 3-stage fixed point preserved across **10
  consecutive releases** — longest streak in project history
  (was 5 at v5.11.0).
- **+** Self-hosted compiler shrunk **-3,950 lines (-13.8%)**
  via Sh.* without breaking fixed point. Discipline signal.
- **+** Six additive language features shipped (Te.1–Te.6)
  with **zero new MIR ops, zero new IR shapes, zero runtime
  function additions**. Every desugaring routes through
  existing primitives.
- **+** Goldens **66/66 → 95/95** with bootstrap mirror.
- **+** Panel cadence honored (overdue but not skipped).
- **−** SPEC re-sync of 14-release arc happened in v5.21.1
  hygiene, not at-source — the same drift class Coral has
  flagged across 3 panels. Score weighting should reflect
  that closure-by-hygiene-release is worse than closure-by-
  discipline.
- **−** v5.14.0 SPEC made a "deferred to v5.21.0" promise
  about single-line `if x: y` that v5.21.0 did not deliver.
  This is the same regression class as the v4.18.0–v4.26.0
  hollow-features arc, in miniature. v5.21.1 either ships
  or explicitly defers — the panel should grade which path
  the lead chose.

---

## Pre-flight commands the panel should run

```bash
# Fixed-point at HEAD
bash scripts/verify_fixed_point.sh --keep
# expected: stage2.ll == stage3.ll, 238086 lines, 0 diff

# Goldens at HEAD
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
# expected: All 95 tests passed

# Bootstrap mirror cross-tests
python3 -m pytest tests/bootstrap/ -v
# expected: test_te5_mirror.py 12/12, test_string_interp_mirror.py 10/10,
#           test_comprehension_mirror.py 10/10, test_indent_preprocessor.py 201/201,
#           test_chained_cmp_mirror.py 10/10 (added v5.21.1)

# Build from seed
bash scripts/build_from_seed.sh
# expected: clean

# Lint
make lint
# expected: ruff + black + mypy clean

# CHANGELOG honesty
python3 scripts/check_changelog_honesty.py
python3 scripts/check_workflow_shapes.py

# Brace-deprecation flow
echo 'fn main() { print("hi") }' > /tmp/brace.mn
python3 -m mapanare emit-llvm /tmp/brace.mn 2>&1 | head -3
# expected: warning: /tmp/brace.mn: uses deprecated {}-block syntax (1 occurrence). Run `mnc fmt /tmp/brace.mn` to migrate. Hard removal in v6.0.

MAPANARE_NO_BRACE_WARNING=1 python3 -m mapanare emit-llvm /tmp/brace.mn 2>&1 | head -3
# expected: no warning

# Chained-cmp once-evaluation (the load-bearing semantic test)
python3 -m mapanare emit-llvm -O0 tests/golden/95_chained_cmp_side_effect.mn -o /tmp/chain.ll
grep -c "@middle(" /tmp/chain.ll
# expected: small, finite count (one per call site in source) — not doubled
```

---

## Out of scope for this panel

- **Rt.04 multi-level alias analysis** — DEFERRED to v6.0
  borrow checker. Status unchanged from v5.11.0 panel.
- **Mc.\* mnc parity for LSP/fmt/init** — closed at v5.18.0.
  Re-verify at panel; do not re-grade as ongoing work.
- **Bundled-LLVM Linux/macOS** — closed by anticipation at
  v5.11.0 Pk.4. Do not re-open without demand signal.

---

## Evidence base

- 10 SESSION_REPORTs at `docs/roadmap/v5/v5.{13,14,14.1,15,
  15.1,16,17,17.1,17.2,18,19,19.1,20,20.1,21}.0/SESSION_REPORT.md`
- v5.11.0 panel: `.reviews/v5.11.0/README.md` (9.62/10,
  Option A; 1 HIGH, 3 MEDIUM, ~12 LOW)
- v5.7.1 panel: `.reviews/v5.7.1/README.md` (9.66/10,
  Option A — highest project-history aggregate, the bar to
  beat or match)
- Carry-forward ledger: `.reviews/CARRY_FORWARD.md`
- Cadence policy: `.reviews/REVIEW_CADENCE.md`
