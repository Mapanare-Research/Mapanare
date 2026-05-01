# v5.22.0 — RE-PANEL — terseness-arc closeout

**Date:** 2026-05-01.
**Cycle:** Phase 0 → Phase 5 in one session.
**Status:** **READY** (pending closeout + tag promotion).

---

## Headline

v5.22.0 is the **panel-only release** closing the v5.13–v5.21
terseness arc. **Zero compiler / runtime / dispatch edits.**
Zero `mapanare/` edits. Zero `runtime/native/` edits. Zero
`mapanare/self/*.mn` edits. The release identity is the panel
itself: 7 reviewers grade the 16-release surface (v5.11.0 →
v5.21.1), the mechanical decision rule fires, the ledger
updates, the cadence resets.

**Aggregate: 9.41 / 10 → Option A** (point-release health gate
clears). Third consecutive Option A under the v5-gate
mechanical rule (v5.7.1: 9.66; v5.11.0: 9.62; v5.22.0: 9.41).
Same posture as v5.8.0 (which graded v5.3.1 → v5.7.1 at
9.66 — project ceiling). Δ vs v5.11.0: **−0.21** (largest
single-arc regression since v5.0.0). All 7 reviewers returned
PASS or PASS WITH NOTES; **0 NEEDS WORK**.

Strict 3-stage fixed point preserved at **238,086 lines / 0
diff** through this release (zero-edit posture; the v5.9.0
milestone now holds across **13 consecutive shipping releases
— longest streak in project history**, 2.6× the v5.11.0 streak).

## Phase 0 — pre-panel verification

All H.1–H.13 PRE_PANEL_AUDIT closures verified at v5.21.1
HEAD before spawning reviewers:

| Check | Result |
|---|---|
| `bash scripts/verify_fixed_point.sh --keep` | stage2.ll == stage3.ll, **238086 lines, 0 diff** |
| `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1` | **All 95 tests passed** in 18.2s |
| `python3 -m pytest tests/bootstrap/test_te5_mirror.py tests/bootstrap/test_chained_cmp_mirror.py tests/bootstrap/test_string_interp_mirror.py tests/bootstrap/test_comprehension_mirror.py tests/bootstrap/test_indent_preprocessor.py -v` | **243 passed in 59s** (Te.5 12 + Te.6 10 + comp 10 + interp 10 + indent 201) |
| `bash scripts/build_from_seed.sh` | clean, mnc binary produced (5,421,552 bytes) |
| `make lint` | ruff + black + mypy clean, 56 source files |
| `python3 scripts/check_changelog_honesty.py` | clean for `[5.21.1]` |
| H.1, H.2 README staleness | NO hits in README.md (acceptable historical refs in SPEC.md only) |
| H.3 SPEC §4.0 Te.3 documentation | hits at `MAPANARE_NO_BRACE_WARNING` + `v5.19.0` references |
| H.4 broken `if x: y` promise | NO `deferred to v5.21.0` hits in SPEC.md |
| H.5 Te.5/Te.6 SPEC sections | 4× `since v5.20.0|since v5.21.0` hits across §3.7 + §4.3.1 + §2.2 |
| H.6 localized READMEs | NO `v5.7.0 corpus|66/66` hits in es/pt/zh-CN |
| H.7 example present | `examples/chained_cmp.mn` exists |
| H.9 cross-bootstrap test present | `tests/bootstrap/test_chained_cmp_mirror.py` exists, 10/10 PASS |
| H.11 known_issues last-updated bump | `v5.21.1` confirmed in header |
| H.12 BENCHMARKS Windows split | `tests/golden/BENCHMARKS-windows.md` exists |

All gates clear → panel spawned.

## Phase 1 — reviewer panel (parallel)

Seven reviewers spawned in parallel via `Agent` tool calls,
each with their character, focus, output filename, and the
"do NOT view other reviewers' work during review" instruction.
Each reviewer read `.reviews/v5.22.0/prompt.md` (charter),
PRE_PANEL_AUDIT.md, the v5.11.0 panel README + their own
v5.11.0 review, REVIEW_CADENCE.md, CARRY_FORWARD.md, the 16
SESSION_REPORTs, and the 6 design docs before forming a
verdict.

| # | Reviewer | Score | Δ vs v5.11.0 | Verdict | Output |
|---|----------|---:|---:|---|---|
| 1 | Rattler | 9.85 | ±0.0 | PASS WITH NOTES | `.reviews/v5.22.0/01-rattler.md` |
| 2 | Viper | 9.7 | −0.20 | PASS WITH NOTES | `.reviews/v5.22.0/02-viper.md` |
| 3 | Anaconda | 8.4 | **−1.30** | PASS WITH NOTES (bordering NEEDS WORK) | `.reviews/v5.22.0/03-anaconda.md` |
| 4 | Cobra | 9.55 | −0.15 | PASS WITH NOTES | `.reviews/v5.22.0/04-cobra.md` |
| 5 | Coral | 9.55 | +0.05 | PASS WITH NOTES | `.reviews/v5.22.0/05-coral.md` |
| 6 | Boa | 9.0 | +0.10 | PASS WITH NOTES | `.reviews/v5.22.0/06-boa.md` |
| 7 | Mamba | 9.85 | +0.05 | PASS | `.reviews/v5.22.0/07-mamba.md` |
| | **Aggregate** | **9.41** | **−0.21** | **Option A** | — |

## Phase 2 — panel summary

`.reviews/v5.22.0/README.md` written: verdict table, score
trajectory (12 panels), overall consensus, post-production
health gate (YES, conditional), prioritized action items
(24-row deduplicated table; 4 HIGH + 8 MEDIUM + ~12 LOW),
disagreements (3 ≥ 0.3 spreads), improvements vs v5.11.0,
regressions vs v5.11.0, decision (Option A formal), evidence.

## Phase 3 — V5_DECISION

`.reviews/v5.22.0/V5_DECISION.md` written: formal Option A
decision text mirroring `.reviews/v5.7.1/V5_DECISION.md`
format. Mechanical rule applied verbatim (9.41 ≥ 9.0; 0
NEEDS WORK → Option A). Per-reviewer score history table
(v4.154.0 → v5.22.0). Score trajectory across 12 panels.
Hero metrics (v5.11.0 → v5.22.0). v5.11.0 panel docket
final disposition (10-row table). v5.22.0 panel new findings
(13-row table). Carry-forward (HIGH 4 / MEDIUM 8 / LOW ~12 /
v6.0 4). Cadence reset note.

## Phase 4 — ledger update

`.reviews/CARRY_FORWARD.md` extended with two new sections:

1. **"v5.22.0 panel — closures verified"** — re-grades all
   16 v5.11.0 panel docket items against v5.22.0 HEAD.
   - **5 closed**: Bo.21, Bo.17r (~80%), Coral SPEC re-sync,
     Mc.\* docket, Cobra per-PR fixed-point gate (mea culpa).
   - **11 still open**: Pk.1.A (11-release carry), `>=45`
     magic (3rd panel ask), V.6/V.7/V.8 (3rd cycle each),
     Bo.18r (3rd panel — escalated to HIGH at v5.22.0),
     Bo.22 (2nd panel), Bo.19, Bo.20, Pe.1 (reframed),
     Anaconda informational LOWs.
2. **"v5.22.0 panel — new findings"** — 21 new rows: 2 HIGH
   (Reg.1, Bo.25), 8 MEDIUM (V.9, Te.3 hollow / asymmetric
   closure, hollow-feature gate, Manifesto M2, SPEC corpus
   M3, cadence skip, Sh.\* baseline labeling, `make ci-gates`,
   `check_doc_freshness.py`), 11 LOW.

**Aggregate state entering v5.22.x:** 4 HIGH / 8 MEDIUM /
~12 LOW / 1 v6.0-rescoped (Rt.04).

## Phase 5 — closeout

This SESSION_REPORT, CHANGELOG entry, CLAUDE.md release note,
VERSION bump 5.21.1 → 5.22.0, `bump_version.py` sweep (badges
+ CHANGELOG comparison links), CRLF restoration on touched
files (`README.md`, `docs/README.{es,pt,zh-CN}.md`,
`CHANGELOG.md`).

## Why the score dropped −0.21

The −0.21 Δ is **not driven by feature regression** — the arc
graded shipped six additive language features (Te.1–Te.6) with
zero new MIR ops, zero new IR shapes, only two new C-runtime
exports (`__mn_assert_fail` 8 LOC + `__mn_indent_to_braces`
545 LOC, both bootstrap-mirror plumbing). The Sh.\* mechanical
rewrite shrunk the self-hosted compiler by **−11.5%** off the
v5.13.0 baseline (net source delta) without breaking fixed
point at any per-module commit. Goldens 66/66 → 95/95.
Bootstrap mirror cross-tests all green. **The correctness
axis is exemplary.**

The drag is **process discipline that the H.\* hygiene pattern
did not catch**:

1. **Anaconda −1.3** (the load-bearing regression) — three
   structurally-wired CI gates silently RED at HEAD across the
   entire Sh.\* arc (5+ releases): `check_struct_registry.py`
   (regex hard-codes brace headers), `check_no_hollow_features.py`
   step 3 (whitelist calibration miss on `CompClause` +
   `FieldPattern`), `check_docs_drift.py` (SPEC.md:1456 untyped
   param). The v5.21.1 pre-panel hygiene pass specifically
   targeted the H.\* docs-surface drift class but did NOT include
   a "structural CI gate status" fact-check, and the panel
   discovered red gates on first run. **−0.6** for the 3 gates
   + **−0.4** cadence skip + **−0.2** Pk.1.A 11-release carry
   + **−0.1** brace-deprecation diagnostic gap.

2. **Boa Bo.18r open for 3rd consecutive panel** — v5.21.1 H.1
   closed the *sibling* line `README.md:176` (the line the
   lead's audit cited); Bo.18r occupies `README.md:188-192`
   (the line the v5.11.0 panel review cited). Same shape as
   v5.9.2 Dn.1 → v5.11.0 Bo.18r. The systematic gap is between
   H.\*-numbered (lead's self-audit) and Bo.\*-numbered (panel
   docket) line references; the audit's H.1 was *adjacent to*
   but not *coextensive with* Bo.18r. Severity escalated
   MEDIUM → HIGH at v5.22.0.

3. **NEW Bo.25** — Goldens badge `66/66` across all 4 READMEs
   while body says `95/95`. Same systematic-skill-gap fingerprint
   as v5.11.0 Bo.21 (which closed at `bump_version.py` sweep).
   Three releases of badge lag.

4. **Te.3 hollow-surface** — flagged by three independent
   reviewers (Coral M1 + Anaconda §3 + Rattler #1). The
   PRE_PANEL_AUDIT.md's own canonical pre-flight test command
   (`echo 'fn main() { print("hi") }' > /tmp/brace.mn; python3
   -m mapanare emit-llvm ...`) does NOT fire the warning the
   audit said it would. Detector at `count_user_brace_block_openers`
   is line-based — counts `{` only at end-of-line. AND the
   native `mnc-stage1` has zero brace-deprecation logic at all
   (asymmetric closure: PY: closed | SH: open). Should have
   been tracked per the dual-closure convention.

The interpretation: **v5.22.0 the release ships Option A;
v5.22.0 the audit-and-gate discipline that produced v5.21.1
hygiene is the surface that needs structural follow-up.** Coral
and Anaconda both recommend `scripts/check_doc_freshness.py` +
`make ci-gates` as the structural prevention.

## Cadence reset

**Next routine panel due at v5.27.0** (5 minors past v5.22.0).
Alternate trigger fires earlier if 5 language-feature releases
ship before then. Both v5.16.0 (5-minor) and v5.20.0
(5-language-feature) triggers fired and were skipped at
v5.22.0; **must be honored on schedule going forward** per
Anaconda §1's recommendation. Cadence enforcement gate (action
item #13 in panel README) targeted for v5.23.0.

## Carry-forward delta vs v5.11.0 entry state

**Entering v5.11.0 panel:** 0 HIGH open / 0 MEDIUM open / 1
v6.0 carry. New findings: 1 HIGH (Bo.21), 3 MEDIUM (Bo.18r,
Bo.17r, Coral SPEC re-sync), ~12 LOW. Exit state: 1 HIGH / 3
MEDIUM / ~12 LOW.

**Entering v5.22.0 panel** (post-v5.21.1 hygiene): the lead
expected 0 HIGH / 0 MEDIUM / 1 v6.0 carry. Per the panel: **2
HIGH carried** (Bo.18r escalated, plus Pk.1.A wasn't actually
closed — it's been open across 11 releases, just downgraded to
LOW after v5.11.0). Plus the panel surfaced **2 new HIGH**
(Reg.1, Bo.25) and **7 new MEDIUM** that the audit didn't
catch. Exit state: 4 HIGH / 8 MEDIUM / ~12 LOW.

**This is the structural lesson of the v5.22.0 panel:** the
H.\* audit is a useful pre-panel discipline pattern but does
not constitute a complete panel surface. The lead's audit
catches the items the lead remembers; the panel catches the
items the lead didn't remember. The v5.27.0 audit should add
the Bo.27 cross-reference column (binding H.\* findings to
prior-panel finding IDs) and a `make ci-gates` invocation
(catching wired-but-unchecked structural gates).

## What the panel CANNOT do (per `REVIEW_CADENCE.md`)

> Panel CANNOT loosen the cadence. It can only:
> - Pass: cadence resets to v5.27.0
> - Pass-with-notes (Option C): cadence resets, action items feed v5.22.x+ work
> - Recovery (Option B): cadence shifts; next panel runs at recovery-arc terminator

The v5.22.0 panel applied the mechanical decision rule
verbatim. Aggregate 9.41 ≥ 9.0; 0 NEEDS WORK; → Option A.
The lead does not negotiate the result. The action items are
recommendations for v5.23.0+; none gates v5.22.0.

## Risk register validation

The PLAN's risk register is validated post-panel:

| Risk | Predicted likelihood | Actual at v5.22.0 |
|---|---|---|
| Aggregate < 9.0 → recovery cycle | LOW | Did not fire — 9.41 |
| Reviewer NEEDS WORK on a v5.13–v5.21 claim | MEDIUM | Did not fire — 0 NEEDS WORK |
| v5.21.1 doesn't ship before v5.22.0 panel | HIGH if skipped | Mitigated — v5.21.1 shipped |
| 0.5+ spread Boa↔Coral | LOW | Spread is 0.55 (9.0 vs 9.55) but converged on action items |
| Decision-1 Path A buggy | LOW | Path B was chosen — moot |
| Cadence-skip pattern repeats at v5.27.0 | MEDIUM | Anaconda flagged + recommended CI gate |

## Success criteria (PLAN §"Success criteria")

| Criterion | Status |
|---|---|
| All 7 review files in `.reviews/v5.22.0/` | ✅ 01-rattler.md … 07-mamba.md |
| Aggregate ≥ 9.0 AND 0 NEEDS WORK → Option A | ✅ 9.41 / 0 NEEDS WORK |
| `.reviews/v5.22.0/README.md` summary written | ✅ |
| `.reviews/v5.22.0/V5_DECISION.md` Option A formal text | ✅ |
| `.reviews/CARRY_FORWARD.md` updated | ✅ |
| `docs/roadmap/v5/v5.22.0/SESSION_REPORT.md` documents the cycle | ✅ this file |
| Strict 3-stage fixed point still 238,086 / 0 diff | ✅ verified |
| Goldens 95+/95+ | ✅ 95/95 |
| `make lint` clean | ✅ |
| `bash scripts/build_from_seed.sh` clean | ✅ |
| CHANGELOG entry | ✅ closeout step |
| CLAUDE.md release note | ✅ closeout step |
| VERSION bumped 5.21.1 → 5.22.0 | ✅ closeout step |
| `bump_version.py` sweep applied | ✅ closeout step |
| Cadence counter reset for v5.27.0 | ✅ documented |

## Out of scope (explicitly held)

- **Compiler / runtime / dispatch edits.** Zero. v5.22.0 is the
  panel surface; any code edit shifts what the panel grades.
- **Action item implementation.** The 24-row prioritized table
  in `.reviews/v5.22.0/README.md` constitutes the v5.22.x +
  v5.23.0+ docket; none of those items shipped in v5.22.0.
- **Tagging or pushing.** Per project convention, the user
  approves tag promotion explicitly.

## Pending v6.0 work (carried forward unchanged)

- **Rt.04** — Multi-level alias analysis (struct → list →
  string depth 2). Status unchanged from v5.7.1 / v5.11.0 /
  v5.22.0 panels.
- **Te.3 hard removal of `{}`** — v5.19.0 soft-deprecation
  cycle terminus.
- **Stage2-binary teardown crash (RC=3)** — papered over by
  `set +e`; 70+ releases stale since v4.30.0 PLAN.
- **Single-line `if x: y`** — explicitly rescoped to v6.0 at
  v5.21.1 H.7 to coincide with `{}` hard removal.

---

*Panel ran 2026-05-01. Aggregate 9.41/10 → Option A. Cadence
reset to v5.27.0. La culebra está delgada y cómoda — pero el
registro tiene polvo, y el espejo de bronce está manchado en
una esquina que el barniz no llegó a alcanzar.*
