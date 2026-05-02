# v5.28.0 — Session Report — RE-PANEL — recovery + prevention + arc-closeout

**Date:** 2026-05-02
**Status:** ready, not tagged
**Predecessor:** v5.27.0 (Mc.8 + Mc.9 + Tk.1 — Mc.\* parity arc CLOSED)
**Arc:** **v5.23–v5.27 recovery + prevention + arc-closeout
arc graded.** Same posture as v5.22.0 RE-PANEL (which graded
v5.13–v5.21 at 9.41/10) and v5.8.0 (which graded v5.3.1 →
v5.7.1 at 9.66/10 — prior project ceiling).

---

## Summary

Panel-only release. The release identity IS the panel itself.
**Zero compiler edits. Zero runtime edits. Zero
`mapanare/self/*.mn` source edits.** Strict 3-stage fixed
point preserved by construction at v5.27.0's 241,842 lines / 0
diff (zero `.mn` source delta in v5.28.0). 7 reviewers graded
the v5.23.0 → v5.27.0 arc (9 SESSION_REPORTs) using the v5-gate
mechanical decision rule.

**Aggregate: 9.72 / 10. Decision: Option A.** Fourth
consecutive Option A under the v5-gate framework, **largest
single-arc recovery in v5 history (+0.31 vs v5.22.0's 9.41
floor)**, and **first panel above the v5.7.1 / v5.8.0 9.66
ceiling in the v5 series**.

The 3-consecutive-panel downward trend (v5.7.1: 9.66 →
v5.11.0: 9.62 → v5.22.0: 9.41 = -0.04, -0.21) is broken with
+0.31. v5.22.0 was the largest single-arc regression since
v5.0.0 (-0.21); v5.28.0 is the largest single-arc recovery
(+0.31). Net 2-panel delta: +0.10.

## Arc graded

| Release | Codename | What it shipped |
|---|---|---|
| v5.23.0 | RC.\* | CI recovery + 4 HIGH closures (Reg.1, Bo.18r-3, Bo.25 + 8 MEDIUM + 6 LOW) — 15 docket items in one mechanical session |
| v5.23.1 | Mb.\* | Memory hygiene: V.9 closure + 3 NEW Te.5 ASan leak closures + V.6/V.7/V.8 3rd-cycle exit + 2 prevention CI gates |
| v5.23.2 | Te.3.B | Bootstrap brace-deprecation mirror — Te.3 hollow / asymmetric closure CLOSED via byte-identity contract |
| v5.24.0 | Hy.\* | Structural hygiene gates: `make ci-gates` (8 sub-gates), `check_doc_freshness.py`, cadence-check, Pk.1.A 11-release carry close, `>= 45` magic |
| v5.24.1 | Wd.\* | Wider docs cleanup (recovery arc closeout): manifesto M2 (3-panel persistence), SPEC corpus M3, Coral L1–L5, Bo.27 PANEL_AUDIT_TEMPLATE.md |
| v5.25.0 | Pv.\* | CI prevention infrastructure: 5 NEW prevention gates (runtime-lib lookup, preprocess-memcheck, clean-build-test, validate-wsl, publish smoke fixtures) + retroactive bugfix close |
| v5.26.0 | Mb.7 + Mb.9 | i64/i1 tag-emit codegen fix + Win64 byval/byref MnString ABI fix (**Mb.\* arc CLOSED**) |
| v5.26.1 | Eu.1..Eu.4 | 4 distinct codegen / lowering closures flipping prev-LINK_FAIL goldens 47/48/49/51 to PASS (**Eu.\* arc CLOSED**) |
| v5.27.0 | Mc.8 + Mc.9 + Tk.1 | Formatter polish (**Mc.\* parity arc CLOSED** — 12-release closure of v5.13.0 docket; **Tk.\* sub-arc opened and closed** in same release) |

## Per-reviewer scores

| # | Reviewer | Domain | Score | Δ vs v5.22.0 | Verdict |
|---|---|---|---:|---:|---|
| 1 | Rattler | LLVM IR / codegen | **9.90** | **+0.05** | EXCEEDS / PASS WITH NOTES |
| 2 | Viper | Memory safety | **9.80** | **+0.10** | EXCEEDS / PASS WITH NOTES |
| 3 | Anaconda | CI / testing / toolchain | **9.60** | **+1.20** | EXCEEDS / PASS WITH NOTES (load-bearing recovery) |
| 4 | Cobra | Bootstrap / self-hosted | **9.70** | **+0.15** | EXCEEDS / PASS WITH NOTES |
| 5 | Coral | Language design | **9.70** | **+0.15** | EXCEEDS / PASS WITH NOTES |
| 6 | Boa | Documentation / DX | **9.55** | **+0.55** | EXCEEDS / PASS WITH NOTES (largest single-panel Boa improvement in project history) |
| 7 | Mamba | C runtime / performance | **9.80** | **−0.05** | EXCEEDS / PASS WITH NOTES |
| | **Aggregate** | — | **9.72** | **+0.31** | **Option A** |

## Cadence-gap closure

v5.28.0 closes the v5.24.0 Hy.3 cadence-enforcement gate gap
**1 minor late on purpose.** The gate fires hard at lag ≥5
minor versions since last panel; v5.27.0 cut at exactly 5
minors past v5.22.0, fired hard, and v5.28.0 closes the gap
1 minor late. Bundling formatter polish (Mc.8 + Mc.9 + Tk.1)
with a panel cycle was rejected during v5.27.0 PLAN drafting
— formatter work is the wrong scope to mix with panel review
discipline. The deliberate slip is the correct trade-off.

**Acknowledged in three locations:** `docs/roadmap/v5/v5.28.0/PROMPT.md`
preamble, `.reviews/v5.28.0/PRE_PANEL_AUDIT.md` preamble + H.7
row, and this SESSION_REPORT. Two reviewers (Anaconda,
Coral) independently judged the framing honest based on
documentation discipline (the gate that fired was built by
the same team that owns the slip; the Hy.3 spec was not
disabled or special-cased; the trade-off was made before the
fact, not after).

Cadence-check sub-gate of `make ci-gates` turns GREEN
immediately on `.reviews/v5.28.0/` directory creation per the
Hy.3 spec. **Next routine panel due v5.33.0** (5 minors past
v5.28.0).

## Phase plan executed

**Phase 0 — verify v5.27.0 baseline (1 session, ~30 min):**
- VERSION = 5.27.0 ✓
- Goldens 95/95 PASS in 22.6s ✓
- Strict 3-stage fixed point: STRICT at 241,842 / 0 diff
  post-stage1 rebuild ✓
- `make ci-gates` all 9 sub-gates GREEN ✓
- Surveyed H.\* findings against v5.27.0 HEAD: 7 candidates
  identified.

**Phase 1 — panel infrastructure (~1h):**
- Created `.reviews/v5.28.0/` directory tree with subdirectory-
  per-reviewer convention (per v5.28.0 PROMPT.md spec; evolution
  from v5.22.0's flat `01-rattler.md` shape).
- Wrote shared `prompt.md` (~330 lines): panel charter, required
  reading, what-this-panel-must-answer, the 7 reviewers, review
  file format, pre-flight verification, process instructions.
- Wrote `PRE_PANEL_AUDIT.md`: 7 H.\* findings (H.1-H.6 closures
  + H.7 cadence acknowledgment); each H.\* binds to prior-panel
  finding ID per Bo.27 / Wd.8 convention; live snapshot at
  v5.27.0 HEAD pre-Phase-2; out-of-scope items.
- Wrote 7 per-reviewer `prompt.md` files (~80-180 lines each):
  persona + focus + reviewer-specific live verification commands.
- Committed (`4a236cc`).

**Phase 2 — H.\* hygiene closures (~30 min):**
- H.1, H.2, H.3 (HIGH, Boa axis — Bo.18r-class): README.md
  fixed-point status paragraphs at lines 175 / 183 / 196-197
  bumped from v5.21.0 / 239k / 17 + 14 consecutive releases
  to v5.27.0 / 241k / 23 consecutive releases.
- H.4 (HIGH, Boa axis — Bo.17r-class): 3 localized READMEs
  (es/pt/zh-CN) native-compiler subsection rewritten:
  v5.21.0 → v5.27.0; 238,086 → 241,842 lines; 13 → 23
  consecutive releases; -3,950 lines (-13.8%) → -2,285 lines
  (-8.18%) net v5.13.0 → v5.21.1 dual-baseline framing per
  v5.23.0 RC.12 normalization. Added v5.23-v5.27 arc summary
  paragraph in each language.
- H.5 (MEDIUM, Boa axis — Bo.10-class): docs/known_issues.md
  Last-updated bumped from v5.21.1 to v5.27.0 with v5.23-v5.27
  closure narrative (8-release arc summary).
- H.6 (MEDIUM, Anaconda axis — An.1-class): CARRY_FORWARD.md
  appended v5.25.0 Pv.\* (6 closures) + v5.26.0 Mb.7 + Mb.9
  (Mb.\* arc CLOSED) + v5.26.1 Eu.1..Eu.4 (Eu.\* arc CLOSED) +
  v5.27.0 Mc.8 + Mc.9 + Tk.1 (Mc.\* parity arc CLOSED) closure
  rows. New "Aggregate state entering v5.28.0 panel" subsection:
  0 HIGH / 0 MEDIUM / ~5 LOW (mostly v6.0-rescoped). Updated
  arc closure summary table.
- H.7 (LOW, process — An.1-class): cadence acknowledgment
  documented in PROMPT.md + PRE_PANEL_AUDIT.md preambles.
- Verified: `make ci-gates` all 9 sub-gates GREEN post-edits;
  `make lint` clean.
- Committed (`069ff24`).

**Phase 3 — 7 reviewer agents (parallel, ~25 min wall-time):**
- Spawned 7 agents IN PARALLEL with reviewer-specific persona +
  focus + output file. Independent context — no
  cross-contamination. Each agent read CLAUDE.md, the shared
  brief, the lead's PRE_PANEL_AUDIT.md, the v5.22.0 prior panel
  artifacts, the 9 SESSION_REPORTs, and the codebase HEAD.
  Each ran live verification commands and produced findings.md.
- All 7 agents completed. 2 agents (Coral, Rattler) had `Write`
  tool blocked by sub-agent policy and returned content as text;
  lead wrote those findings.md from agent responses.
- Total findings.md content: ~2,500 lines / ~134 KB across 7
  reviewers.
- Committed (`b6c0202`).

**Phase 4 — aggregation (~1h):**
- Wrote V5_DECISION.md: formal Option A document mirroring
  v5.22.0 V5_DECISION shape; per-reviewer score table; trajectory
  table (13 panels); v5.22.0 docket closure verification (25/25
  CLOSED); 14 NEW LOW findings catalog with Bo.27 prior-panel
  bindings; carry-forward delta; cadence reset.
- Wrote `.reviews/v5.28.0/README.md`: panel index with verdict
  table, consensus, action items, regressions/improvements,
  evidence base.
- Committed.

**Phase 5 — closeout (this session):**
- Updated CARRY_FORWARD.md with v5.28.0 panel closures (was
  done in Phase 2 H.6).
- Bumped VERSION to 5.28.0 via `scripts/bump_version.py` sweep
  (badges across 4 READMEs + SPEC.md header).
- Wrote this SESSION_REPORT.
- Added CLAUDE.md release-notes entry for v5.28.0.
- Added CHANGELOG.md `[5.28.0]` entry.
- Final commit "Release v5.28.0: RE-PANEL — v5.23-v5.27 arc
  panel; Option A; +0.31 recovery; first above v5.7.1 ceiling".

## Phase 0 surprise — STRICT vs NEAR fixed point

The canonical pre-flight `bash scripts/verify_fixed_point.sh
--keep` returns NEAR with a 1-line VERSION-metadata diff:
```
< !0 = !{!"5.26.0"}     (stage2.ll)
> !0 = !{!"5.27.0"}     (stage3.ll)
```

This is a **stale-stage1 artifact**, not a regression. The
existing `mapanare/self/mnc-stage1` binary was built/linked at
v5.26.0; its embedded version reads "5.26.0" at runtime via the
v5.9.0 DX.2 `__mn_version_string()` C-runtime export. After
`python3 scripts/build_stage1.py` rebuilds stage1 from current
HEAD source, stage1 binary embeds "5.27.0" and stage2.ll ==
stage3.ll byte-identical at 241,842 lines / 0 diff (STRICT).

The v5.27.0 SESSION_REPORT's "preserved by construction at
241,842 lines / 0 diff (23-release strict streak)" claim is
load-bearing on this rebuild — verifiable but conditional.
v5.28.0 PRE_PANEL_AUDIT.md documents both paths explicitly so
reviewers can verify the STRICT path is reachable, not whether
the casual-invocation path returns STRICT.

**Reviewer verification:** Both Rattler and Cobra (the
correctness-axis reviewers) explicitly ran the post-rebuild
path and verified STRICT 241,842 / 0 diff at HEAD. The naive
invocation path returns NEAR with the documented stale-stage1
artifact.

## Phase 3 — Sub-agent Write tool blocked

2 of 7 agents (Coral, Rattler) had their `Write` tool blocked
by sub-agent policy ("subagents should return findings as text,
not write report files"). Both returned the complete findings.md
content as text in their result; the lead wrote the files from
those responses verbatim. The other 5 agents (Boa, Anaconda,
Mamba, Viper, Cobra) wrote findings.md directly without
intervention.

This is a sub-agent isolation policy artifact, not a content
issue — the reviewer's analysis was independent and complete in
both cases. Recommend documenting the pattern in
`.reviews/PANEL_AUDIT_TEMPLATE.md` so future panel cycles know
to expect manual file-write fallback for some agents.

## Source delta

**Compiler / runtime / self-host source:** **0 lines.**

**Doc + ledger / panel artifact:**
- `.reviews/v5.28.0/prompt.md` (new, ~330 lines)
- `.reviews/v5.28.0/PRE_PANEL_AUDIT.md` (new, ~250 lines)
- `.reviews/v5.28.0/<reviewer>/prompt.md` × 7 (new, ~700 lines total)
- `.reviews/v5.28.0/<reviewer>/findings.md` × 7 (new, ~2,500 lines total)
- `.reviews/v5.28.0/V5_DECISION.md` (new, ~430 lines)
- `.reviews/v5.28.0/README.md` (new, ~470 lines)
- `.reviews/CARRY_FORWARD.md` (Phase 2 H.6: +~150 lines for v5.25-v5.27 closure rows + arc summary)
- `README.md` (Phase 2 H.1/H.2/H.3: 3 paragraphs updated)
- `docs/README.{es,pt,zh-CN}.md` (Phase 2 H.4: 3 native-compiler subsections updated + v5.23-v5.27 arc summary added)
- `docs/known_issues.md` (Phase 2 H.5: Last-updated bumped + closure narrative)
- `docs/roadmap/v5/v5.28.0/SESSION_REPORT.md` (this file, new)
- `CLAUDE.md` (Phase 5: release-notes entry for v5.28.0 added to preamble)
- `CHANGELOG.md` (Phase 5: `[5.28.0]` entry added)
- `VERSION` (Phase 5: 5.27.0 → 5.28.0)
- 4× README badges (Phase 5: bumped via `scripts/bump_version.py`)

## Risk assessment retrospective

The PLAN identified 3 risks; all 3 materialized differently
than predicted:

1. **NEW HIGH from a reviewer angle not anticipated.** Predicted
   surface: WSL-specific tooling drift (Pv.4) or WASM/Android
   sub-arcs. Actual surface: 0 NEW HIGH across all 7 reviewers.
   The convergent test-coverage gap (Cb.New1 + Ra.Inf1) is the
   closest the panel got to a HIGH; both reviewers correctly
   classified as LOW with a "escalate to MEDIUM at v5.29.0 if
   deferred" annotation. The structural prevention infrastructure
   v5.24.0-v5.25.0 shipped did its job.

2. **Cadence-gate slip framing.** Predicted: a reviewer flags
   process discipline. Actual: explicit acknowledgment in 3
   locations (PROMPT, PRE_PANEL_AUDIT, this SESSION_REPORT) +
   2 reviewers (Anaconda, Coral) independently judged the
   framing honest. Net score impact: 0.

3. **Mb.7's stage2/3 fixed-point risk.** Predicted: line count
   baseline movement might be flagged as streak break. Actual:
   line count delta documented (v5.26.0 +158 lines, v5.26.1
   +1,849 lines, v5.27.0 +0). Rattler and Cobra both verified
   the deltas are consistent with new lowerer/emitter arms
   (Mb.7's narrow fix + Eu.\* enum-payload arms) rather than
   regressions. Streak preserved at 23 consecutive releases by
   construction.

The risk inventory was over-cautious — recovery + prevention
arcs are by design lower-risk than feature-velocity arcs.

## Carry-forward (entering v5.28.x / v5.29.0+)

- **0 HIGH** open
- **0 MEDIUM** open
- **~14 LOW** open (mostly process polish; see V5_DECISION.md
  carry-forward table for full list with effort estimates and
  target releases)
- **4 v6.0-rescoped** (Rt.04 multi-level alias, Te.3 hard
  removal, single-line `if x: y`, Ra.Inf2 Result/Option flat
  layout)
- **1 v6.0 carry candidate-close** (Stage2 teardown crash —
  Rattler narrowed to stdout-redirect-specific SIGSEGV;
  investigation now tractable; consider closing in v5.29.0
  rather than v6.0)

The Cobra+Rattler convergent test-coverage gap (Cb.New1 +
Ra.Inf1) is the **load-bearing v5.29.0+ recommendation** —
extending `tests/llvm/test_async_link.py` link-and-run pattern
to all 95 goldens via new `test_llvm_link_all.py` (Tn.\*
generalization). This is exactly the structural gap that hid
Eu.1..Eu.4 for three releases (v5.23.1 → v5.26.0). **Escalate
to MEDIUM at v5.29.0 if not picked up in a Pv.\* follow-on.**

## Live verification at v5.28.0 HEAD

```bash
cat VERSION
# observed: 5.28.0

python3 scripts/build_stage1.py && bash scripts/verify_fixed_point.sh --keep
# observed: STRICT, stage2.ll == stage3.ll, 241,842 lines, 0 diff
# (post-rebuild; pre-rebuild returns NEAR with documented
#  stale-stage1 VERSION-metadata diff)

python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
# observed: All 95 tests passed in 22.6s ✓

make ci-gates
# observed: All 9 sub-gates GREEN
# (silent_skips, changelog_honesty, workflow_shapes, docs_drift,
#  hollow_features, struct_registry, doc_freshness, cadence,
#  clean-build-test)

python3 -m pytest tests/llvm/test_async_link.py -v
# observed: 10 passed, 0 XFAIL in 4.81s
# (4 prev-LINK_FAIL goldens 47/48/49/51 flipped to PASS via
#  Eu.1..Eu.4)

python3 -m pytest tests/native/test_brace_funcs_windows_abi.py -v
# observed: 8 passed (Mb.9 Win64 byval/byref ABI verified)

python3 -m pytest tests/bootstrap/test_brace_deprecation_mirror.py -v
# observed: 11 passed (Te.3.B byte-identity contract)

make lint
# observed: ruff + black + mypy clean, 56 source files

bash scripts/build_from_seed.sh
# observed: clean, mnc binary produced
```

## Files

- `.reviews/v5.28.0/README.md` — panel index synthesis
- `.reviews/v5.28.0/V5_DECISION.md` — formal Option A decision
- `.reviews/v5.28.0/PRE_PANEL_AUDIT.md` — lead's pre-panel
  fact-check (Bo.27 cross-reference column)
- `.reviews/v5.28.0/prompt.md` — shared panel brief
- `.reviews/v5.28.0/<reviewer>/{prompt.md,findings.md}` × 7
- `.reviews/CARRY_FORWARD.md` — canonical docket ledger
  (updated through v5.27.0 closures + v5.22.0 panel closure
  verification + new v5.28.0 LOWs)
- `docs/roadmap/v5/v5.28.0/PLAN.md` — release plan
- `docs/roadmap/v5/v5.28.0/PROMPT.md` — execution prompt
- `docs/roadmap/v5/v5.28.0/SESSION_REPORT.md` — this file

---

*v5.28.0 RE-PANEL ships clean. Aggregate 9.72/10 → Option A;
+0.31 vs v5.22.0 (largest single-arc recovery in v5 history);
first panel above v5.7.1's 9.66 ceiling in v5 series. Cadence
reset to v5.33.0. La culebra está delgada, cómoda, y por
primera vez ha mudado la piel del techo de v5.7.1.*
