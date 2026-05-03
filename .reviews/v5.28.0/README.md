# v5.28.0 Panel — v5.23–v5.27 Recovery + Prevention + Arc-Closeout Health Gate

> Seven-reviewer panel reviewing the **v5.23.0 → v5.27.0** arc
> (8 releases, 9 SESSION_REPORTs: RC.\* CI recovery, Mb.\* memory
> hygiene, Te.3.B bootstrap brace-deprecation mirror, Hy.\*
> structural hygiene gates, Wd.\* wider docs cleanup, Pv.\* CI
> prevention, Mb.7 + Mb.9 codegen + Win64 ABI fixes, Eu.1..Eu.4
> LINK_FAIL closures, Mc.8 + Mc.9 + Tk.1 formatter polish).
> v5.28.0 is the panel-only release — zero compiler / runtime /
> self-host source edits beyond the Phase 2 H.\* hygiene
> closures (README + 3 localized READMEs + known_issues +
> CARRY_FORWARD ledger).
>
> **Aggregate: 9.72 / 10. Decision: Option A (point-release
> health gate clears).** **Fourth consecutive Option A** under
> the v5-gate framework, and **the largest single-arc recovery
> in v5 history (+0.31)** — the 3-consecutive-panel downward
> trend (-0.04, -0.21) is broken. **First panel above the
> v5.7.1 / v5.8.0 9.66 ceiling in the v5 series.**

**Panel date:** 2026-05-02
**Aggregate: 9.72 / 10**
**Grade distribution: 7 EXCEEDS / 0 MEETS / 0 NEEDS WORK**
(7 PASS WITH NOTES; 0 PASS-only; 0 NEEDS WORK; 0 REJECT)
**Decision rule applied:** aggregate ≥ 9.0 AND 0 NEEDS WORK
AND no NEW HIGH off the v5.22.0 docket → **Option A**
(point-release health gate clears; no recovery cycle opened).
**Δ vs prior panel (v5.22.0):** **+0.31** (9.41 → 9.72)

---

## Verdict Table

| # | Reviewer | Domain | Verdict | Score | Δ vs v5.22.0 | Top findings |
|---|---|---|---|---:|---:|---|
| 1 | [Rattler](rattler/findings.md) | LLVM IR / codegen | **EXCEEDS** / PASS WITH NOTES | **9.90** | **+0.05** | 23-release strict streak verified live (1.77× project record); Mb.7 anti-pattern absent (0 instances scanned across 241,842 lines); Mb.9 gate 8/8 PASS; Eu.1..Eu.4 4 LINK_FAIL closures all IR-verified; no new MIR/IR shapes (mir.py 65 classes unchanged). 1 LOW (stage2 teardown narrowed to stdout-redirect-specific SIGSEGV — investigation tractable; 80-release carry now actionable), 2 INFORMATIONAL (test_async_link covers 10/95 — Tn.\* extension recommended; Result/Option flat-layout for v6.0). |
| 2 | [Viper](viper/findings.md) | Memory safety | **EXCEEDS** / PASS WITH NOTES | **9.80** | **+0.10** | Every V.\* carry CLOSED (V.9 root cause correctly identified — Python blanket-move zeroing `_str_slots`, surgical fix; Te.5 ASan leaks closed via `emit_track_boxed`; V.6/V.7/V.8 3rd-cycle exit). Eu.3 SSA uniquification correct under cascade dispatch. Pv.2 memcheck gate falsifiable. 1 LOW (Vp.1 — sanitizers.yml comment lies about coverage scope; documentation lie not real coverage gap). "Fine, that doesn't suck." |
| 3 | [Anaconda](anaconda/findings.md) | CI / testing / toolchain | **EXCEEDS** / PASS WITH NOTES | **9.60** | **+1.20** | **Load-bearing recovery axis CLOSED.** All 3 silently-RED CI gates from v5.22.0 (Reg.1, hollow_features, docs_drift) GREEN under live verification; all 9 sub-gates of `make ci-gates` GREEN; cadence-check (Hy.3) fired exactly as designed at v5.27.0; Pk.1.A 11-release carry CLOSED; PRE_PANEL_AUDIT.md honors Bo.27 cross-reference column. 3 LOWs: A.1 CARRY_FORWARD update-protocol drift (caught + fixed in Phase 2 H.6, but needs structural enforcement — recommends `check_carry_forward_freshness.py` gate); A.2 coverage gate ~75-release informational without close-or-decline; A.3 Mc.8 "arc CLOSED" label slightly generous given auto-wrap was advertised. |
| 4 | [Cobra](cobra/findings.md) | Bootstrap / self-hosted | **EXCEEDS** / PASS WITH NOTES | **9.70** | **+0.15** | STRICT 241,842 / 0 diff verified live (post-rebuild); 23-release streak count audits correctly against SESSION_REPORT serial numbers; bootstrap mirror cross-tests 254/254; `>= 45` magic CLOSED v5.24.0 Hy.4 (3-panel ask); Bb.\* seed refresh discipline held (1 justified at v5.23.2 Te.3.B.5, 0 unjustified); all v5.22.0 Cobra-axis HIGH/MEDIUM CLOSED. 3 LOWs: **Cb.New1 — `test_native.py` byte-identity oracle remains blind to LLVM link failures (the structural gap that hid Eu.1..Eu.4 for 3 releases); recommends Tn.\* generalization to all 95 goldens. Independent convergence with Rattler's Ra.Inf1.** O(N²) seen_tags dedup; missing flags in `mnc fmt --help`. |
| 5 | [Coral](coral/findings.md) | Language design | **EXCEEDS** / PASS WITH NOTES | **9.70** | **+0.15** | All M1/M2/M3/L1-L5/TR1 CLOSED at v5.28.0 HEAD; Mc.\* arc CLOSED; Eu.\* arc CLOSED (fixed real language-semantic bugs in match dispatch — match on primitives, or-pattern + guards); Te.3 deprecation cycle policy COMPLIANT; Bo.27 convention COMPLIANT. **First panel above v5.7.1's 9.66 ceiling in v5 series.** 2 LOWs: New.1 (Mc.8 PLAN/PROMPT not amended after Phase 0 pivot — documentation discipline issue); New.2 (Mc.9 SESSION_REPORT "splits into sub-blocks" imprecise — actual mechanism is "comment terminates current block"). |
| 6 | [Boa](boa/findings.md) | Documentation / DX | **EXCEEDS** / PASS WITH NOTES | **9.55** | **+0.55** | **🎉 Bo.18r is finally, structurally, permanently CLOSED!** The 3-consecutive-panel persistence signal (same benchmarks paragraph carrying v5.6.11-vintage language through v5.7.1, v5.11.0, v5.22.0) ended at v5.23.0 RC.2; v5.28.0 Phase 2 H.1/H.2/H.3 closures bumped the same paragraph region to current state. Bo.25 + Bo.21 + Bo.17r (now 100%) + Bo.22 + Bo.26 + Bo.27 all CLOSED. PRE_PANEL_AUDIT.md honors Bo.27 convention perfectly. 2 LOW residuals: B.1 (Bo.22-locale — localized READMEs Hello World still `mapanare run`, English-only closure left this side open); B.2 (Bo.24-locale — Docker + guide links absent from es/pt/zh-CN). **Largest single-panel Boa improvement in project history.** |
| 7 | [Mamba](mamba/findings.md) | C runtime / performance | **EXCEEDS** / PASS WITH NOTES | **9.80** | **−0.05** | C runtime: +306 LOC across 8 releases (only 2 of 8 releases touched runtime — correct pattern). Pe.1 growth +0.316%/release, well under +0.5%/release projection; "curve flattening" framing properly retired at v5.24.0 Hy.6. **Top finding: M.1 — `.h` vs `.c` header asymmetry recurred.** v5.22.0 Mamba #1 closed `__mn_indent_to_braces` at v5.23.0 RC.10; v5.23.2 Te.3.B.2 added 2 new exports without header decls (net +1: 16 → 17). 2-line immediate fix + Pv.7-style structural gate (diff `MN_EXPORT` names .c vs .h) recommended. |
| | **Aggregate** | — | **Option A** | **9.72** | **+0.31** | — |

Score trajectory (last 13 panels):
6.59 → 7.87 → 8.21 → 8.21 → 8.80 → 8.86 → 9.21 → 9.37 → 9.30 →
9.66 → 9.62 → 9.41 → **9.72**.

---

## Overall Team Consensus

**PASS for v5.28.0 as a point release** — the mechanical rule
fires verbatim (9.72 ≥ 9.0; 0 NEEDS WORK; 0 NEW HIGH off prior
docket). All seven reviewers came in either flat-or-positive
(Rattler +0.05, Viper +0.10, Anaconda **+1.20**, Cobra +0.15,
Coral +0.15, Boa **+0.55**, Mamba −0.05). The +1.20 Anaconda
recovery and +0.55 Boa recovery are the load-bearing
contributions; Mamba's −0.05 is a single LOW recurrence
(header asymmetry M.1) on an otherwise project-tied-high axis.

The **headline correctness signal continues to compound**:
strict 3-stage fixed point preserved at 241,842 lines /
0-line diff across **23 consecutive shipping releases**
(longest streak in project history; **1.77× the v5.22.0
13-release streak**; 4.6× the v5.11.0 5-release streak).
Eight releases shipped (RC.\*, Mb.\*, Te.3.B, Hy.\*, Wd.\*,
Pv.\*, Mb.7+Mb.9, Eu.\*, Mc.\*+Tk.\*) with **zero new MIR
ops, zero new IR shapes, and only 2 new C-runtime exports**
(`__mn_count_user_brace_block_openers` +
`__mn_emit_brace_deprecation_warning` — both bootstrap-mirror
plumbing for Te.3.B.2). **4 previously-LINK_FAIL goldens
(47/48/49/51) flipped to PASS** via 4 distinct codegen /
lowering closures (Eu.1..Eu.4); `tests/llvm/test_async_link.py`
10/10 PASS, 0 XFAIL at HEAD.

**The discipline is now structural, not patch-based.** The arc
graded was deliberately designed as recovery + prevention +
arc-closeout, not feature-velocity:
- **Recovery:** v5.23.0 RC.\* closed 15 v5.22.0 docket items
  in one mechanical session (the 4 HIGH + 8 MEDIUM + 6 LOW
  ledger); v5.23.1 Mb.\* closed all V.\* memory hygiene; v5.23.2
  Te.3.B closed the 3-reviewer-flagged Te.3 hollow / asymmetric
  closure; v5.24.0 Hy.\* + v5.24.1 Wd.\* closed structural
  hygiene gates + wider docs cleanup.
- **Prevention:** v5.25.0 Pv.\* added 5 prevention CI gates;
  v5.24.0 Hy.\* added `make ci-gates` (9 sub-gates),
  `check_doc_freshness.py`, cadence-check; the v5.24.1 Wd.8
  PANEL_AUDIT_TEMPLATE.md (Bo.27 convention) prevents the
  audit-line-vs-panel-line mismatch that drove Bo.18r
  persistence.
- **Arc-closeout:** v5.26.0 closed Mb.\* arc; v5.26.1 closed
  Eu.\* arc (4 LINK_FAIL goldens flipped); v5.27.0 closed
  Mc.\* parity arc (12-release closure of v5.13.0 docket).

**Anaconda's +1.20 recovery is the load-bearing signal.** The
v5.22.0 -1.30 dock was driven by 3 silently-RED CI gates that
the project specifically built to catch hollow-feature and
metadata-drift regressions, but had been blind for 5 releases
during the largest feature-velocity arc in v5 history. v5.23.0
RC.1/RC.4/RC.5 closed all three; v5.24.0 Hy.\* added the
structural prevention layer (`make ci-gates` makes future
silent-RED-gate failures impossible at pre-release). v5.25.0
Pv.\* added 5 NEW prevention gates targeting the
"runtime-archive missing", "preprocess memcheck", "WSL
validation", and "publish smoke fixtures" failure modes that
weren't even tracked at v5.22.0. The recovery is structural,
not just symptomatic.

**Boa's Bo.18r 3-consecutive-panel persistence is finally
broken.** The same paragraph carrying v5.6.11-vintage language
across 3 panels (v5.7.1, v5.11.0, v5.22.0) closed at v5.23.0
RC.2 with rounded `239k` framing, and v5.28.0 Phase 2 H.1/H.2/H.3
hygiene closures bumped the same paragraph region to current
state (`241k / 23 consecutive releases`). Bo.27 cross-reference
column convention codified at v5.24.1 Wd.8 + applied at
v5.28.0 PRE_PANEL_AUDIT.md prevents the audit-line-vs-panel-line
mismatch that drove the persistence in the first place.

**Coral's +0.15 lifts the v5 series above the 9.7 ceiling.**
First panel above the v5.7.1 / v5.8.0 9.66 in the v5 series
on the language-design axis. Manifesto coherence M2 closed
verbatim at v5.24.1 Wd.1; SPEC corpus M3 closed via
`to_terse_markdown` markdown rewriter; M1 Te.3 hollow closed
via byte-identity test contract (11/11). The infrastructure
arc enables language growth without needing recovery cycles —
that is the correct use of a recovery + prevention arc, and
Coral grades it as the structural prevention working.

**The interpretation is unambiguous: v5.28.0 the release
ships Option A; v5.28.0 the panel grades the largest
single-arc recovery in v5 history; v5.28.0 the framework
clears its highest aggregate ever.**

---

## Post-Production Health Gate

**YES, unconditionally.** The codebase is healthier than at
v5.22.0 on every axis the lead claimed it would be:
- 23-release fixed-point streak (vs 13)
- 0 LINK_FAIL goldens (vs 4)
- 0 silently-RED CI gates (vs 3)
- 9 prevention sub-gates green (vs 0)
- All Mb.\* / Mc.\* / Eu.\* arcs CLOSED (vs all open)
- Bo.18r-class persistence broken (vs 3-panel running)
- Manifesto coherence + SPEC corpus + Coral L1-L5 + Bo.27
  convention all CLOSED (vs all open)
- v5.22.0 -1.30 Anaconda regression: +1.20 recovery (vs net
  -1.30 dock)

The conditions for a "YES, conditional" health gate would
have required NEW HIGH or MEDIUM findings, NEEDS WORK
verdicts, or aggregate < 9.0. None of those obtain. v5.28.0
is unconditionally healthy.

The action items in the prioritized table below constitute
the v5.28.x / v5.29.0+ docket. The Cobra+Rattler convergent
test-coverage gap (Cb.New1 + Ra.Inf1) is the load-bearing
recommendation — extending link-and-run coverage to all 95
goldens is exactly the structural fix that would prevent a
future Eu.\*-class LINK_FAIL bug from hiding for three
releases.

---

## Prioritized Action Items (deduplicated, with effort)

| # | Severity | Item | Reported by | Effort | Target |
|---|---|---|---|---|---|
| 1 | LOW (recommended escalate to MEDIUM at v5.29.0 if deferred) | **Cb.New1 + Ra.Inf1** — Extend `tests/llvm/test_async_link.py` link-and-run pattern to all 95 goldens via new `test_llvm_link_all.py` (Tn.\* generalization). The byte-identity oracle is blind to LINK failures — exactly the structural gap that hid Eu.1..Eu.4 for 3 releases. | Cobra LOW + Rattler INFORMATIONAL (independent convergence) | 2-4h | v5.29.0 |
| 2 | LOW | **A.1** — New `check_carry_forward_freshness.py` gate. Mirror of `check_doc_freshness.py`. Verifies every released minor/patch since the last "Aggregate state entering vX.Y.Z" line in CARRY_FORWARD.md has a closure row. Closes the 4-release update-protocol drift that Phase 2 H.6 caught. | Anaconda LOW | 2h | v5.29.0 |
| 3 | LOW | **M.1 + Pv.7** — Add `__mn_count_user_brace_block_openers` + `__mn_emit_brace_deprecation_warning` (Te.3.B.2 functions) to `runtime/native/mapanare_core.h`. Then add Pv.7-style structural gate (diff `MN_EXPORT` names between `.c` and `.h`) to `make ci-gates`. Closes the recurrence pattern of v5.22.0 Mamba #1 (now 2-cycle). | Mamba LOW | 2h | v5.28.x |
| 4 | LOW | **Ra.New1** — Run `valgrind --track-origins=yes /tmp/mnc-stage2 emit-llvm test.mn > /dev/null` on the stdout-redirect path. With the `-o file` isolation boundary identified, the 80+-release stage2 teardown crash carry is now investigation-tractable. Likely root cause: stdout-path I/O cleanup ordering vs MnString drop-glue. | Rattler LOW | 2-4h | v5.29.0 (or close in v5.29.0 rather than v6.0) |
| 5 | LOW | **A.3 + Co.New1** — Backfill v5.27.0 PLAN.md with `## Phase 0 pivot` section marking the auto-wrap sections as superseded. Add `## Phase 0 pivot` convention to PLAN.md template for future pivots. | Anaconda + Coral (corroborating) | 30 min | v5.28.x |
| 6 | LOW | **B.1** — Update Hello World invocation in localized READMEs (es/pt/zh-CN) from `mapanare run` to `mnc run`. Bo.22 closure was English-only at v5.23.0 RC.14; localized side recurred. | Boa LOW | 5 min | v5.28.x |
| 7 | LOW | **Vp.1** — Correct the misleading comment at `sanitizers.yml:199-201`. Comment claims `sanitizer-mnc-stage1` job detects an `emit_wrap_some` Mb.2 regression but only greps for `__mn_indent_to_braces`. Actual Mb.2 coverage is via baseline TSV + LSan binary sweep. Documentation lie, not real coverage gap. | Viper LOW | 5 min | v5.28.x |
| 8 | LOW | **Co.New2** — Amend SESSION_REPORT v5.27.0 Mc.9 section: "comments terminate the current block" (not "splits into sub-blocks"). Behavior is correct; documentation is loose. | Coral LOW | 5 min | v5.28.x |
| 9 | LOW | **Cb.New3** — Add `--line-length` and `--sort-imports` to `mnc fmt --help` output. v5.27.0 shipped both flags; help text not updated. | Cobra LOW | 5 min | v5.28.x |
| 10 | LOW | **B.2** — Docker + guide links absent from es/pt/zh-CN READMEs (content-additive). | Boa LOW | 30 min | v5.29.0 |
| 11 | LOW | **A.2** — Coverage gate carry ~75+ releases informational. Explicit close-or-decline decision. | Anaconda LOW | 30 min | v5.29.0 |
| 12 | LOW | **Cb.New2** — O(N²) `seen_tags` dedup in `build_match_arms`. Refactor to set-based dedup. Triggers only on or-patterns with N>20 alternatives (none in current corpus). | Cobra LOW | 15 min | v5.30.0 |

---

## Disagreements

The panel surfaced **0 notable disagreements ≥ 0.3 spread on
the same axis**. Score range was 9.55 (Boa) to 9.90 (Rattler)
— a 0.35 range across 7 reviewers covering orthogonal axes.

**Independent convergence noted:**

1. **Rattler + Cobra on test-coverage gap (Cb.New1 + Ra.Inf1).**
   Both reviewers independently arrived at the recommendation
   to extend `test_async_link.py` link-and-run coverage from
   the current 10 goldens (4 Eu.\* + 6 async-cluster) to all
   95 goldens. **Two independent reviewers on the same finding
   shape is the strongest possible signal** — the v5.29.0
   docket should treat this as MEDIUM-severity-equivalent and
   the v5.33.0 panel should escalate to MEDIUM if not addressed.

2. **Anaconda + Coral on Mc.8 design pivot label (A.3 +
   Co.New1).** Both reviewers independently observed that the
   "Mc.\* arc CLOSED" label is "slightly generous" given Mc.8
   shipped detect-only after auto-wrap was the advertised
   scope. Both judge the SESSION_REPORT documentation honest
   but call out the planning-artifact gap (PLAN/PROMPT not
   amended). Action item #5 above addresses both.

No reviewer dissented on the mechanical decision rule (all 7
verdicts compatible with Option A: 7 PASS WITH NOTES, 0 NEEDS
WORK, 0 NEW HIGH off prior docket).

---

## Improvements Since v5.22.0 Panel

**Correctness axis (Rattler / Cobra / Mamba):**
- Strict 3-stage fixed-point streak: 13 → **23 releases**
  (1.77× project record).
- LINK_FAIL goldens: 4 → **0** (Eu.1..Eu.4 all closed; live
  IR-verified).
- Mb.\* arc: open → **CLOSED v5.26.0** (Mb.7 i64/i1 + Mb.9
  Win64 ABI).
- Eu.\* arc: didn't exist → **CLOSED v5.26.1** (4 distinct
  codegen / lowering closures).
- No new MIR ops / no new IR shapes across 8 releases (verified
  in `mir.py` 65 classes unchanged).
- C runtime delta: +306 LOC over 8 releases; Pe.1 growth at
  +0.32%/release (under +0.5% projection); 6 of 8 releases
  zero-C — correct pattern.

**Memory safety axis (Viper):**
- V.9 + V.6 + V.7 + V.8 (3rd-cycle carries) all CLOSED
  v5.23.1 Mb.\*.
- 3 NEW Te.5 ASan leak regressions CLOSED v5.23.1 Mb.2 via
  `emit_track_boxed` after malloc.
- Eu.3 SSA uniquification (`bind_ident_pattern` `tmp_counter`)
  prevents `%x.addr` collisions under cascade dispatch.
- Pv.2 preprocess-memcheck gate falsifiable; valgrind
  regression CI gates wired (Mb.3, Mb.6).

**Process axis (Anaconda — load-bearing):**
- v5.22.0 -1.30 dock fully recovered (+1.20 at v5.28.0).
- 3 silent-RED CI gates at v5.22.0 (Reg.1, hollow_features,
  docs_drift) all GREEN at HEAD via v5.23.0 RC.1/RC.4/RC.5.
- 5 NEW prevention gates wired at v5.25.0 Pv.\*.
- Cadence-check fired exactly as designed at v5.27.0;
  v5.28.0 closes 1 minor late with explicit acknowledgment
  in 3 documented locations.
- Pk.1.A 11-release carry CLOSED v5.24.0 Hy.5.
- PRE_PANEL_AUDIT.md honors Bo.27 cross-reference column.

**Documentation axis (Boa):**
- Bo.18r 3-consecutive-panel persistence: STRUCTURALLY CLOSED.
- Bo.25 (goldens badge): closed v5.23.0 RC.3 with
  `bump_version.py` extension.
- Bo.21, Bo.17r, Bo.22 (English), Bo.26, Bo.27: all CLOSED.
- `examples/INDEX.md` (Wd.7) intact; `docs/known_issues.md`
  Last-updated bumped (Phase 2 H.5).

**Language design axis (Coral):**
- M1/M2/M3 all CLOSED.
- L1–L5 / TR1 all CLOSED.
- Mc.\* arc CLOSED at v5.27.0 (12-release closure of v5.13.0).
- Eu.\* arc CLOSED at v5.26.1 (real language-semantic
  closures: match on primitives, or-pattern + guards).
- Te.3 deprecation cycle policy compliant (SPEC §22).

---

## Regressions Since v5.22.0 Panel

**0 HIGH, 0 MEDIUM regressions.**

**Minor LOW regressions:**
- Header asymmetry recurrence (M.1, Mamba) — same shape as
  v5.22.0 Mamba #1, different exports (Te.3.B.2 functions).
  Action item #3 addresses with structural fix.
- Bo.22 closure was English-only; localized side recurred (B.1).
  Action item #6 addresses.
- CARRY_FORWARD update-protocol drifted 4 releases before
  Phase 2 H.6 caught it (A.1). Action item #2 addresses with
  structural enforcement gate.

**Process observation:** All 3 minor LOW regressions are
recurrence patterns of v5.22.0 findings on a different
surface. Each has a structural fix path that follows the
same Hy.\* / Pv.\* prevention pattern that closed the
v5.22.0 silent-CI-gate class.

---

## Decision

**Option A — point-release health gate clears.**

Mechanical rule applied:
> Aggregate **9.72 ≥ 9.0** ✅
> **0 NEEDS WORK** verdicts ✅
> **0 NEW HIGH** off the v5.22.0 docket ✅
> → Option A.

**This is the fourth consecutive Option A** under the v5-gate
mechanical rule (v5.7.1: 9.66; v5.11.0: 9.62; v5.22.0: 9.41;
v5.28.0: **9.72**). The aggregate trend reverses sharply at
v5.28.0 (-0.04 → -0.21 → +0.31), and **v5.28.0 is the first
panel above the v5.7.1 9.66 ceiling in the v5 series**.

**No recovery cycle is opened.** The v5.28.x / v5.29.0+ docket
constitutes ~12 LOW items. The Cobra+Rattler convergence on
test-coverage gap (Cb.New1 + Ra.Inf1) is the load-bearing
recommendation; **escalate to MEDIUM at v5.29.0 if not picked
up in a Pv.\* follow-on**.

**Cadence reset:** next routine panel due at **v5.33.0** (5
minors past v5.28.0).

See [V5_DECISION.md](V5_DECISION.md) for the formal Option A
text.

---

## Evidence

**Live verification at v5.28.0 HEAD (commit `4a236cc`):**
- `python3 scripts/build_stage1.py && bash
  scripts/verify_fixed_point.sh --keep` → **STRICT, 241,842
  lines, 0 diff** (post-rebuild; pre-rebuild returns NEAR with
  documented stale-stage1 VERSION-metadata diff)
- `python3 scripts/test_native.py --stage1
  mapanare/self/mnc-stage1` → **All 95 tests passed** in 22.6s
- `make ci-gates` → **All 9 sub-gates GREEN** (silent_skips,
  changelog_honesty, workflow_shapes, docs_drift, hollow_features,
  struct_registry, doc_freshness, cadence, clean-build-test)
- `python3 -m pytest tests/llvm/test_async_link.py -v` →
  **10 passed, 0 XFAIL** in 4.81s (4 prev-LINK_FAIL goldens
  flipped to PASS via Eu.1..Eu.4)
- `python3 -m pytest tests/native/test_brace_funcs_windows_abi.py -v`
  → **8 passed** (Mb.9 Win64 byval/byref ABI verified)
- `python3 -m pytest tests/bootstrap/test_brace_deprecation_mirror.py -v`
  → **11 passed** (Te.3.B byte-identity contract)
- `make lint` → ruff + black + mypy clean, 56 source files
- Mb.7 anti-pattern scan: 0 instances of `zext i1 → br i1`
  pattern across 241,842 lines of stage2.ll
- README.md / 3 localized READMEs: 95/95 + 241k / 23-release
  streak (Phase 2 H.1-H.4 closures)

**Reviewer outputs:**
- [rattler/findings.md](rattler/findings.md), [viper/findings.md](viper/findings.md),
  [anaconda/findings.md](anaconda/findings.md), [cobra/findings.md](cobra/findings.md),
  [coral/findings.md](coral/findings.md), [boa/findings.md](boa/findings.md),
  [mamba/findings.md](mamba/findings.md)

**Lead's pre-panel artifacts (Phase 2 H.\* hygiene closures
committed `069ff24`):**
- [PRE_PANEL_AUDIT.md](PRE_PANEL_AUDIT.md) — 7 H.\* findings
  (H.1-H.6 closed in Phase 2 hygiene; H.7 cadence
  acknowledgment in PROMPT.md + PRE_PANEL_AUDIT.md preambles).
  Each H.\* binds to a prior-panel finding ID per Bo.27 / Wd.8
  convention.
- [prompt.md](prompt.md) — shared panel brief.
- 7× `<reviewer>/prompt.md` — per-reviewer persona + focus.
- `docs/roadmap/v5/v5.28.0/SESSION_REPORT.md` — closeout
  narrative (Phase 5).

**Prior panel:** [.reviews/v5.22.0/](../v5.22.0/) — 9.41/10,
Option A, 4 HIGH / 8 MEDIUM / ~12 LOW. **Every HIGH and MEDIUM
CLOSED** at v5.28.0 HEAD (25 of 25 docket items closed; only
LOW v6.0-rescoped items carry forward).

**Project ceiling displaced:** v5.7.1 / v5.8.0's 9.66 was the
project ceiling for 13 panels (v5.7.1 → v5.22.0). v5.28.0's
9.72 is the new project ceiling.

---

*Panel run: 2026-05-02. 7 reviewers, 7 personalities, 7 axes,
7 verdicts. Aggregate **9.72 / 10** → **Option A**. Cadence
reset to v5.33.0. **Largest single-arc recovery in v5 history;
first time above the v5.7.1 9.66 ceiling in the v5 series.**
La culebra está delgada, cómoda, y por primera vez ha mudado
la piel del techo de v5.7.1 — el espejo de bronce está limpio,
el registro está al día, y la próxima escama crece donde antes
había drift.*
