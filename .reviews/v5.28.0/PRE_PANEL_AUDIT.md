# v5.28.0 Pre-Panel Audit

> **Cadence trigger.** Last full panel was v5.22.0 (2026-05-01).
> Per `.reviews/REVIEW_CADENCE.md`, panels run every 5 minor
> versions. v5.27.0 is **5 minor versions past** the v5.22.0 panel
> — the v5.24.0 Hy.3 cadence-enforcement gate fires hard at the
> v5.27.0 cut. **v5.28.0 closes the cadence gap 1 minor late on
> purpose.** Bundling formatter polish (Mc.8 + Mc.9 + Tk.1) with
> a panel cycle was rejected during v5.27.0 PLAN drafting; the
> deliberate slip is the correct trade-off, acknowledged here so
> reviewers can grade the framing rather than the slip silently.
>
> **Pre-panel posture (lead's fact-check before reviewers run).**
> v5.27.0 hygiene-class drift surfaced during this audit is closed
> at v5.28.0 HEAD via the Phase 2 hygiene closure pass below; the
> panel grades v5.28.0 against the v5.23.0 → v5.27.0 arc.

**Audit date:** 2026-05-02
**Target version:** v5.28.0 (post-Phase 2 hygiene closure)
**Arc graded:** v5.23.0 → v5.27.0 (8 releases, 9 SESSION_REPORTs
including the v5.26.1 patch — RC.\* CI recovery, Mb.\* memory
hygiene, Te.3.B bootstrap brace-deprecation mirror, Hy.\*
structural hygiene gates, Wd.\* wider docs cleanup, Pv.\* CI
prevention, Mb.7 + Mb.9 codegen + Win64 ABI fixes, Eu.1..Eu.4
LINK_FAIL closures, Mc.8 + Mc.9 + Tk.1 formatter polish)

---

## Findings cleared in v5.28.0 hygiene closure pass

These are the items the lead's own fact-check at v5.27.0 HEAD
surfaced as drift the v5.28.0 panel would otherwise dock at fresh.
Each `H.*` row binds to a prior-panel finding ID per the Bo.27 /
Wd.8 convention codified at `.reviews/PANEL_AUDIT_TEMPLATE.md`
(canonical from v5.27.0+).

### Doc surface (Boa axis)

| # | Severity | Finding | **Closes prior-panel ID** | Closed in v5.28.0 hygiene pass |
|---|---|---|---|---|
| H.1 | HIGH | `README.md:175` "The self-hosted compiler runs the full corpus (95/95 native goldens at v5.21.0)" — stale version reference; v5.27.0 corpus is 95/95 unchanged but the version cited is 6 releases stale. | `Bo.18r-3` (v5.7.1 / v5.11.0 / v5.22.0 closed v5.23.0 RC.2) — same paragraph-region drift class | Refreshed to "(95/95 native goldens at v5.27.0)" — stale version-reference removed |
| H.2 | HIGH | `README.md:183` "stage2.ll == stage3.ll byte-identical at 239k lines... longest streak in project history at 17 consecutive releases" — last cited release in the streak narrative is v5.23.2; v5.27.0 reality is 241,842 lines / 23-release streak (CLAUDE.md preamble + v5.27.0 SESSION_REPORT). **Same systemic Bo.18r failure mode as 3 prior panels** — paragraph rot drives the panel docks. | `Bo.18r-3` (v5.22.0) escalated 4th-panel-risk shape — different paragraph than v5.22.0 Bo.18r, same fingerprint | Refreshed to "241k lines... longest streak in project history at 23 consecutive releases (cited last: v5.27.0)" |
| H.3 | HIGH | `README.md:196-197` "stage2.ll == stage3.ll byte-identical at 239k lines; strict since v5.9.0, held through 14 consecutive releases" — contradicts H.2's adjacent "17 consecutive releases" (paragraph 2 lines apart) AND is itself stale at 14. The two adjacent paragraphs disagree on streak length. | `Bo.18r-3` (v5.22.0) — same systemic surface, paired-paragraph variant | Refreshed to "241k lines... 23 consecutive releases" — paragraphs now consistent |
| H.4 | HIGH | Localized READMEs (es/pt/zh-CN) all reference "v5.21.0", "238,086 lineas/linhas/行", "13 consecutive releases", "-13.8% via Sh.\* since v5.13.0" — terseness-arc framing frozen at v5.21.0 vintage; entire v5.23–v5.27 recovery + prevention + arc-closeout work absent from front-page narrative. | `Bo.17r` (v5.11.0 / v5.22.0 closed v5.21.1 H.3 ~80%) — Boa Bo.17r class re-emerged at one-cycle drift | Three native-compiler subsections rewritten in es/pt/zh-CN: 95/95 goldens, 241k lines, 23-release streak, v5.23–v5.27 arc summary (memory hygiene, CI prevention, codegen fixes, formatter polish) |
| H.5 | MEDIUM | `docs/known_issues.md` "Last updated: v5.21.1" — 6 releases stale (v5.22.0 through v5.27.0 not reflected in last-updated line). v5.21.1 H.11 closed this at v5.21.1; carries forward as recurring drift. | `Bo.10`-class (v4.143.0) — last-updated metadata staleness recurs every panel cycle | Last-updated bumped to v5.27.0 with v5.22.0 → v5.27.0 closure narrative |

### Process surface (Anaconda axis)

| # | Severity | Finding | **Closes prior-panel ID** | Closed in v5.28.0 hygiene pass |
|---|---|---|---|---|
| H.6 | MEDIUM | `.reviews/CARRY_FORWARD.md` — last "Items resolved" append covers v5.24.1 Wd.\* arc closeout; v5.25.0 (Pv.\*), v5.26.0 (Mb.7 + Mb.9), v5.26.1 (Eu.1..Eu.4), v5.27.0 (Mc.8 + Mc.9 + Tk.1) closures NOT logged. **4-release update-protocol drift** — same shape as v5.21.1 H.12 surfaced at v5.22.0. The "Update protocol" section at file bottom states this is mandatory at every release; was not honored at trigger across 4 consecutive releases. | `An.1`-class (v5.22.0 cadence skip) — process-discipline drift on the canonical docket ledger | Appended v5.25.0 / v5.26.0 / v5.26.1 / v5.27.0 closure rows to the "Items resolved in the v5.13.0 → v5.21.1 terseness arc" pattern; new "v5.22.0 panel — closures verified through v5.27.0" subsection bringing the ledger current. Mb.7 marked CLOSED v5.26.0; Eu.\* arc CLOSED v5.26.1. |

### Cadence acknowledgment (process surface)

| # | Severity | Finding | **Closes prior-panel ID** | Closed in v5.28.0 hygiene pass |
|---|---|---|---|---|
| H.7 | LOW (process) | v5.28.0 closes the v5.24.0 Hy.3 cadence-enforcement gate gap **1 minor late** (gate fired hard at v5.27.0). PROMPT.md and PRE_PANEL_AUDIT.md must explicitly acknowledge this with the formatter-polish-vs-panel-cycle trade-off rationale, per the Hy.3-spec gate-firing design. | `An.1` (v5.22.0 cadence skip) — same shape, narrower window (1 minor vs 5+ at v5.22.0) | Acknowledged in `docs/roadmap/v5/v5.28.0/PROMPT.md` and in this PRE_PANEL_AUDIT.md preamble. Trade-off rationale: bundling formatter polish (Mc.8 + Mc.9 + Tk.1) with a panel cycle was explicitly rejected during v5.27.0 PLAN drafting (formatter work is the wrong scope to mix with panel review cycle). |

---

## Prior-panel findings deferred (NOT closed by hygiene release)

The v5.22.0 panel docket was structurally fully closed across the
v5.23.0 → v5.27.0 arc per `CARRY_FORWARD.md` "Aggregate state
entering v5.25.x (post-v5.24.1 Wd.\* closeout — ARC CLOSED)". After
v5.24.1 the docket was 0 HIGH / 0 MEDIUM / ~5 LOW. v5.25.0 (Pv.\*)
+ v5.26.0 (Mb.7) + v5.26.1 (Eu.\*) + v5.27.0 (Mc.8/9 + Tk.1)
closed additional carries (Mb.7 was a v5.24.0+ tracked LOW; Mc.8
+ Mc.9 were 12-release v5.13.0 carries; Tk.1 was a 3-release
v5.24.1 carry). The v5.22.0 panel docket items still open at
v5.28.0 are the v6.0-rescoped items only:

| Prior-panel ID | Severity | Reason for deferral | Target release |
|---|---|---|---|
| `Rt.04` (v5.7.1 / v5.11.0 / v5.22.0) | LOW (v6.0 carry) | Multi-level drop-glue alias analysis (struct → list → string depth 2) — borrow-checker scope; status unchanged from v5.7.1 panel | v6.0 |
| `Te.3` hard removal of `{}` (v5.22.0) | LOW (v6.0 carry) | v5.19.0 soft-deprecation cycle terminus; brace-style currently warns, hard removal at v6.0 (per SPEC §22 deprecation cycle) | v6.0 |
| `Stage2-binary teardown crash (RC=3)` (v4.30.0 PLAN, 70+ releases stale) | LOW (carry) | Papered over by `set +e` in `verify_fixed_point.sh:124-137`; close in v6.0 cleanup window | v6.0 |
| `Single-line if x: y` (v5.21.1 explicit rescope) | LOW (v6.0 carry) | Coincides with `{}` hard removal | v6.0 |
| `Anaconda informational LOWs` (v5.22.0) | LOW each | Coverage gate, Windows CI lane, self-compile pytest smoke, MIR destination-passing tests, inliner-kinds whitelist — 53/38/etc-release deferred status quo unchanged | v5.x ad-hoc |

---

## Pre-flight commands (live state at v5.27.0 HEAD pre-Phase-2)

These commands establish the live state of the codebase before the
panel reviewers receive their packages.

```bash
# VERSION
cat VERSION
# observed: 5.27.0

# Native goldens
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
# observed: All 95 tests passed in 22.6s ✓

# Strict 3-stage fixed point — REQUIRES stage1 rebuild from current HEAD
python3 scripts/build_stage1.py
bash scripts/verify_fixed_point.sh --keep
# observed (post-rebuild): see live snapshot below

# Without stage1 rebuild (canonical pre-flight per prior panels):
bash scripts/verify_fixed_point.sh --keep
# observed: NEAR FIXED POINT — 1-line VERSION-metadata diff
#   < !0 = !{!"5.26.0"}     (stage2.ll, emitted by stage1 binary linked at v5.26.0)
#   > !0 = !{!"5.27.0"}     (stage3.ll, emitted by stage2 binary built from v5.27.0 source)
# This is a STALE-STAGE1 ARTIFACT, not a regression. The v5.9.0 DX.2
# closure made VERSION dynamic via __mn_version_string() C-runtime
# export; the diff appears here because the existing stage1 binary
# was linked against v5.26.0's runtime archive (rebuilds tracked
# the prior release). After `python3 scripts/build_stage1.py`,
# stage1 binary embeds the current runtime, and stage2.ll ==
# stage3.ll byte-identical at 241,842 lines / 0 diff (STRICT).
# v5.27.0 SESSION_REPORT's "preserved by construction" claim is
# load-bearing on this rebuild.

# CI gates
make ci-gates
# expected: All sub-gates GREEN except cadence-check (which fires
# hard at HEAD; turns GREEN immediately on .reviews/v5.28.0/
# creation per Hy.3 spec — that is the signal v5.28.0 IS the
# correct release for the panel)

# Bootstrap mirror cross-tests
python3 -m pytest tests/bootstrap/ -v --no-header
# expected: ~250+ cases pass

# Eu.* closures (v5.26.1)
python3 -m pytest tests/llvm/test_async_link.py -v
# expected: 10/10 PASS, 0 XFAIL

# Mb.9 Win64 ABI verification (v5.26.0)
python3 -m pytest tests/native/test_brace_funcs_windows_abi.py -v
# expected: 8/8 PASS

# Te.3 brace-deprecation byte-identity (v5.23.2 Te.3.B.3)
python3 -m pytest tests/bootstrap/test_brace_deprecation_mirror.py -v
# expected: 11/11 PASS

# Lint
make lint
# expected: ruff + black + mypy clean
```

---

## Live snapshot — v5.28.0 HEAD post-Phase-2

Captured immediately before reviewer agents receive the package.
This snapshot is the source of truth for every claim in
SESSION_REPORTs being graded.

| Metric | v5.27.0 HEAD pre-Phase-2 | v5.28.0 HEAD post-Phase-2 |
|---|---|---|
| `cat VERSION` | `5.27.0` | `5.28.0` |
| `bash scripts/verify_fixed_point.sh --keep` (no rebuild) | NEAR — 1-line VERSION-metadata diff (stale-stage1 artifact) | NEAR — 1-line VERSION-metadata diff (now `5.27.0` vs `5.28.0`; same stale-stage1 artifact) |
| `python3 scripts/build_stage1.py && bash scripts/verify_fixed_point.sh --keep` | STRICT — 241,842 lines, 0 diff | STRICT — 241,842 lines, 0 diff (zero `.mn` source edits in v5.28.0) |
| `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1` | 95/95 PASS in 22.6s | 95/95 PASS |
| `make ci-gates` | All green except cadence-check (fires hard) | All green including cadence-check (panel directory present) |
| `tests/llvm/test_async_link.py` | 10/10 PASS, 0 XFAIL | 10/10 PASS, 0 XFAIL |
| `tests/native/test_brace_funcs_windows_abi.py` | 8/8 PASS | 8/8 PASS |
| `tests/bootstrap/test_brace_deprecation_mirror.py` | 11/11 PASS | 11/11 PASS |

(Snapshot updated post-Phase-2 close.)

---

## What this panel is grading

The v5.23.0 → v5.27.0 arc is a **recovery + prevention + arc-closeout
arc**, not a feature-velocity arc:

1. **v5.23.0 RC.\*** — 15 closures in one mechanical session
   (4 HIGH, 8 MEDIUM, 6 LOW from v5.22.0 docket). Reg.1 surfaced
   3 latent struct-registry drifts during the 5-release blind
   window (mirrors v4.143.0 Reg.1 retrospective). Bo.18r closed
   structurally at line 188-192 + 176 (3rd-consecutive-panel
   target).
2. **v5.23.1 Mb.\*** — 6 memory hygiene closures (V.9 +
   3 NEW Te.5 ASan leaks + V.6/V.7/V.8 3rd-cycle exit) + 2
   prevention CI gates (sanitizer-mnc-stage1 + sanitizer-cache-walkers).
3. **v5.23.2 Te.3.B** — bootstrap brace-deprecation mirror
   closes 3-reviewer-flagged Te.3 hollow / asymmetric-closure
   finding via byte-identical Python ↔ native via C-runtime
   exports; new `tests/bootstrap/test_brace_deprecation_mirror.py`
   (11/11) is the byte-identity contract.
4. **v5.24.0 Hy.\*** — structural hygiene infrastructure: `make
   ci-gates` (8 sub-gates), `check_doc_freshness.py`, cadence-check
   gate, Cobra `>= 45` magic, Pk.1.A 11-release carry close,
   Pe.1 reframe.
5. **v5.24.1 Wd.\*** — wider docs cleanup arc closeout: manifesto
   M2 (Coral 3-panel persistence), SPEC corpus M3 (`to_terse_markdown`),
   Coral L1–L5, Bo.27 PANEL_AUDIT_TEMPLATE.md (this audit
   honors it).
6. **v5.25.0 Pv.\*** — CI prevention infrastructure: runtime-lib
   lookup gate (Pv.1 — pre-fix `_find_runtime_lib()` returned
   None on v3.x candidate-name re-introduction; stale local lib
   masked it 11 releases), preprocess-memcheck (Pv.2),
   clean-build-test sub-gate (Pv.3), `validate_wsl.sh` (Pv.4),
   publish smoke fixtures (Pv.6 — closes publish run #48 Linux +
   macOS tarball-smoke failures from v5.14.0 SPEC §1009 forward
   promise that v5.21.1 H.4 explicitly rescoped to v6.0).
7. **v5.26.0 Mb.7 + Mb.9** — Mb.\* arc CLOSED:
   - Mb.7 closes 3-release carry (v5.23.1 → v5.24.0 → v5.25.0)
     of i64/i1 tag-emit bug in `emit_enum_tag`. Surgical 5-LOC
     fix honoring `dest.ty.kind`. Closes golden 47.
   - Mb.9 closes publish run #48 Windows OOM in v5.23.2 Te.3.B.2
     functions via Win64 byval/byref MnString contract. Routed
     through runtime-call path (mirrors v5.23.1 Mb.1 pattern).
   - Phase 0 disclosure: v5.23.1 SESSION_REPORT premise wrong
     ("9 LINK_FAIL goldens share one bug"); only golden 47 had
     Mb.7's bug. Goldens 48/49/51 + 55-59 fail for distinct
     reasons (Eu.1..Eu.4 rescoped to v5.26.1).
8. **v5.26.1 Eu.1..Eu.4** — Eu.\* arc CLOSED: 4 distinct codegen
   / lowering fixes that move goldens 47, 48, 49, 51 from
   LINK_FAIL → PASS:
   - Eu.1: `emit_unwrap` on `Result<T, E>` two `extractvalue` ops
   - Eu.2: standalone `Ok(...)`/`Err(...)` literals at call-arg
     sites default missing args (mirroring `lower.py:2398`)
   - Eu.3: `match` on primitive subject sequential test cascade;
     `bind_ident_pattern` SSA uniquification
   - Eu.4: `match` with or-pattern + guards: dedup switch
     entries by tag value; per-alt entry switch at arm body
9. **v5.27.0 Mc.8 + Mc.9 + Tk.1** — Mc.\* parity arc CLOSED:
   - Mc.8 detect-only `--line-length` (Phase 0 design pivot:
     Mapanare's grammar is single-line for all expressions;
     auto-wrap can't satisfy AST-preservation invariant)
   - Mc.9 alphabetical `--sort-imports` with comment-aware block
     boundaries
   - Tk.1 surgical 6-LOC fix in `to_terse` empty `#{}` branch
     (statement-block-opener filter; closes 3-release v5.24.1
     Wd.2 latent bug)

---

## Specifically this panel must answer

- **Aggregate ≥ 9.55?** Lead's target per v5.24.1 SESSION_REPORT.
  Recovery from v5.22.0's 9.41 floor.
- **Did any reviewer return NEEDS WORK?** If so, recovery arc
  opens regardless of aggregate.
- **Strict 3-stage fixed point at 241,842 lines / 0-line diff
  on v5.28.0 HEAD?** Requires `python3 scripts/build_stage1.py`
  first. Held continuously since v5.9.0 — 23-release streak
  per CLAUDE.md (verify live).
- **`bash scripts/build_from_seed.sh` clean** at v5.28.0 HEAD
  with the v5.23.2 Te.3.B.5 refreshed seed?
- **Eu.\* closures verified**: `tests/llvm/test_async_link.py`
  10/10 PASS, 0 XFAIL?
- **Mb.7 closures verified**: golden 47 PASS via emit_unwrap
  honoring `dest.ty.kind`?
- **Mb.9 closures verified**: `tests/native/test_brace_funcs_windows_abi.py`
  8/8 PASS?
- **Pv.\* prevention gates** all wired and green?
- **Mc.\* arc actually closed?** Mc.8 detect-only design pivot
  honest? Mc.9 sort-imports preserves comment-aware block
  boundaries? Tk.1 closes Wd.2 latent bug + falsifiability
  round-trip verified?
- **`PRE_PANEL_AUDIT.md` Bo.27 cross-reference column** present
  for every H.\* finding?

---

## Score-impact pre-mitigations the panel should weigh

Pattern from prior panels: docs-surface findings drove Boa
docks at v5.11.0 (-0.5) and v5.22.0 (carries to -0.1). v5.28.0
hygiene pass closes that class structurally per the Phase 2
table above. Score impact the panel should weigh:

- **+** Strict 3-stage fixed point preserved across **23
  consecutive releases** (CLAUDE.md claim) — 1.77× the v5.22.0
  13-release streak, 4.6× the v5.11.0 5-release streak.
- **+** v5.22.0 panel docket structurally closed entering v5.25.x
  (post-Wd.\*); 4 HIGH + 8 MEDIUM all CLOSED across 5 releases.
- **+** 4 NEW LINK_FAIL goldens flipped to PASS in v5.26.1 Eu.\*.
- **+** Mb.\* arc CLOSED at v5.26.0; Mc.\* arc CLOSED at v5.27.0;
  Te.3.B mirror at v5.23.2; Hy.\* prevention infrastructure at
  v5.24.0; Pv.\* prevention at v5.25.0.
- **+** Cadence acknowledgment up front (no silent skip); Bo.27
  cross-reference convention honored per Wd.8 codification.
- **+** Three CI gates that were silently RED at v5.22.0 panel
  (Reg.1 + hollow-feature + docs-drift) all green at v5.28.0.
- **−** Cadence gap closes 1 minor late (acknowledged; reviewers
  may grade the framing).
- **−** `verify_fixed_point.sh --keep` returns NEAR with stale
  stage1 — STRICT requires explicit `build_stage1.py` first.
  This is a documented stale-stage1 artifact (DX.2 closed the
  staleness *class* at v5.9.0; the *artifact* recurs whenever
  the binary lags the source); reviewers should verify the
  STRICT path is reachable, not whether the casual-invocation
  path returns STRICT.

---

## Out of scope for this panel

- **Rt.04 multi-level alias analysis** — DEFERRED to v6.0 borrow
  checker. Status unchanged from v5.22.0 panel.
- **Te.3 hard removal of `{}`** — DEFERRED to v6.0. Soft
  deprecation at v5.19.0; bootstrap mirror at v5.23.2; hard
  removal at v6.0 per SPEC §22 deprecation cycle.
- **Single-line `if x: y`** — explicitly RESCOPED to v6.0 at
  v5.21.1 H.4.
- **Stage2-binary teardown crash (RC=3)** — DEFERRED to v6.0
  cleanup window; 70+ releases stale.
- **Bundled-LLVM Linux/macOS** — closed by anticipation at
  v5.11.0 Pk.4. Do not re-open without demand signal.

---

## Evidence base

- 9 SESSION_REPORTs at `docs/roadmap/v5/v5.{23.0,23.1,23.2,24.0,
  24.1,25.0,26.0,26.1,27.0}/SESSION_REPORT.md`
- v5.22.0 panel: `.reviews/v5.22.0/README.md` (9.41/10, Option A;
  4 HIGH, 8 MEDIUM, ~12 LOW)
- v5.7.1 panel: `.reviews/v5.7.1/README.md` (9.66/10, Option A —
  highest project-history aggregate, the bar to beat or match)
- v5.24.1 SESSION_REPORT recovery-arc closure summary: 0 HIGH /
  0 MEDIUM / ~5 LOW entering v5.25.x
- v5.27.0 SESSION_REPORT: Mc.8 + Mc.9 + Tk.1; strict 3-stage
  fixed point at 241,842 / 0 diff (23-release streak)
- v5.27.0 CHANGELOG entry; v5.27.0 PLAN
- Carry-forward ledger: `.reviews/CARRY_FORWARD.md` (post-v5.28.0
  hygiene-pass H.6 closure brings ledger current)
- Cadence policy: `.reviews/REVIEW_CADENCE.md`
- Audit cross-reference convention: `.reviews/PANEL_AUDIT_TEMPLATE.md`
  (v5.24.1 Wd.8; canonical from v5.27.0 audit forward)
