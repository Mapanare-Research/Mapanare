# v5.28.0 RE-PANEL Decision

> **Re-panel of the v5.23.0 → v5.27.0 recovery + prevention +
> arc-closeout arc (8 releases / 9 SESSION_REPORTs).** Panel
> aggregate **9.72 / 10**, 0 NEEDS WORK. Mechanical rule →
> **Option A — v5.28.0 is a clean point release.** **Fourth
> consecutive Option A** under the v5-gate framework, and
> **the largest single-arc recovery in v5 history (+0.31)** —
> the 3-consecutive-panel downward trend (-0.04, -0.21) is
> broken. **First panel above the v5.7.1 / v5.8.0 9.66 ceiling
> in the v5 series.**

**Date:** 2026-05-02
**Aggregate:** 9.72 / 10
**Distribution:** 7 EXCEEDS / 0 MEETS / 0 NEEDS WORK
(7 PASS WITH NOTES, 0 PASS-only)
**Decision:** **Option A — point-release health gate clears.**

## Mechanical rule applied

> Aggregate ≥ 9.0 AND 0 NEEDS WORK AND no NEW HIGH off the
> v5.22.0 docket → Option A.

| Rule | Condition | Outcome | Applied? |
|---|---|---|---|
| Option A (standard) | Aggregate ≥ 9.0 AND 0 NEEDS WORK AND no NEW HIGH off prior docket | Clean point release | **YES: 9.72 ≥ 9.0; 0 NEEDS WORK; 0 NEW HIGH** |
| Option C (closeout) | 8.5 ≤ Aggregate < 9.0 AND 0 NEEDS WORK | Release ships with documented carry-forwards | No: 9.72 ≥ 9.0 |
| Option B (recovery) | Aggregate < 8.5 OR any NEEDS WORK OR any NEW HIGH | Recovery cycle opens at v5.29.0 | No: all gates clear |

**Applied: Option A.** v5.28.0 is a clean point release. No
recovery cycle is opened. The panel surfaced **0 HIGH, 0 MEDIUM,
~13 LOW** findings; none gates the v5.28.0 release itself. The
LOW set constitutes the v5.29.0+ docket, with one
near-duplicate observation from Rattler + Cobra (test-coverage
gap: byte-identity oracle blind to LINK failures) that justifies
elevating to MEDIUM at v5.29.0 if not picked up in a Pv.\*
follow-on.

## Context

v5.0.0 already shipped at v4.143.0 (rc1) → v4.145.0+ (clean
tag); the project is in **point-release maintenance** as of the
v5.x series. The v5-gate mechanical rule continues to apply as
the project's standing health-gate framework.

This is the **fourth consecutive Option A** panel under that
framework (v5.7.1: 9.66; v5.11.0: 9.62; v5.22.0: 9.41; v5.28.0:
9.72). v5.22.0 was the largest single-arc regression since
v5.0.0; v5.28.0 is the largest single-arc recovery in v5
history.

The arc graded — v5.23.0 → v5.27.0 — spans **8 releases over
~3 weeks**, deliberately designed as a **recovery + prevention
+ arc-closeout** arc rather than a feature-velocity arc. v5.28.0
is the panel-only release: **zero compiler edits, zero runtime
edits, zero `mapanare/self/*.mn` source edits** beyond the
Phase 2 H.\* hygiene closures (README + localized READMEs +
known_issues + CARRY_FORWARD ledger updates). Same posture as
v5.22.0 RE-PANEL (9.41/10) and v5.8.0 (9.66/10 project ceiling).

## Score

**Aggregate: 9.72 / 10**
**Grade distribution: 7 EXCEEDS / 0 MEETS / 0 NEEDS WORK**

## Per-reviewer scores

| # | Reviewer | Domain | v5.7.1 | v5.11.0 | v5.22.0 | **v5.28.0** | Δ v5.22.0 | Grade |
|---|---|---|---:|---:|---:|---:|---:|---|
| 1 | Rattler | LLVM IR / codegen | 9.8 | 9.85 | 9.85 | **9.90** | **+0.05** | EXCEEDS |
| 2 | Viper | Memory safety | 9.9 | 9.90 | 9.7 | **9.80** | **+0.10** | EXCEEDS |
| 3 | Anaconda | CI / testing / toolchain | 9.6 | 9.70 | **8.4** | **9.60** | **+1.20** | EXCEEDS |
| 4 | Cobra | Bootstrap / self-hosted | 9.6 | 9.70 | 9.55 | **9.70** | **+0.15** | EXCEEDS |
| 5 | Coral | Language design | 9.6 | 9.50 | 9.55 | **9.70** | **+0.15** | EXCEEDS |
| 6 | Boa | Documentation / DX | 9.4 | 8.90 | 9.0 | **9.55** | **+0.55** | EXCEEDS |
| 7 | Mamba | C runtime / performance | 9.8 | 9.80 | 9.85 | **9.80** | **−0.05** | EXCEEDS |
| | **Aggregate** | — | **9.66** | **9.62** | **9.41** | **9.72** | **+0.31** | — |

## Score trajectory

| Panel | Aggregate | NEEDS WORK | Outcome | Δ |
|---|---:|---:|---|---:|
| v4.99.0 | 6.59 | (recovery) | Option B | — |
| v4.106.0 | 7.87 | 0 | Option B | +1.28 |
| v4.114.0 | 8.21 | 0 | Option B | +0.34 |
| v4.120.0 | 8.21 | 1 (Anaconda) | Option B | ±0.0 |
| v4.136.0 | 8.80 | 0 | Option C (v5.0.0-rc1) | +0.59 |
| v4.143.0 | 8.86 | 0 | Option C (rc1 holds) | +0.06 |
| v4.144.0 | 9.21 | 0 | Option A declared | +0.35 |
| v4.154.0 | 9.37 | 0 | Option A (v5.0.0 tagged) | +0.16 |
| v5.2.0 | 9.30 | 0 | Option A (v5.3.0) | -0.07 |
| v5.7.1 / v5.8.0 | **9.66** | 0 | Option A (v5.8.0; project ceiling) | +0.36 |
| v5.11.0 | 9.62 | 0 | Option A (v5.11.0) | -0.04 |
| v5.22.0 | 9.41 | 0 | Option A (v5.22.0; -1.30 Anaconda) | -0.21 |
| **v5.28.0** | **9.72** | **0** | **Option A (v5.28.0; +1.20 Anaconda recovery)** | **+0.31** |

Full trajectory: 6.59 → 7.87 → 8.21 → 8.21 → 8.80 → 8.86 →
9.21 → 9.37 → 9.30 → 9.66 → 9.62 → 9.41 → **9.72**.

The +0.31 Δ from v5.22.0 to v5.28.0 is the **largest
single-arc recovery in v5 history**, and **the first time the
aggregate has cleared the v5.7.1 / v5.8.0 9.66 ceiling in the
v5 series**. The 3-consecutive-panel downward trend (-0.04,
-0.21) is broken by +0.31 — net +0.06 over two panels, but
the directional reversal is the load-bearing signal.

The +1.20 Anaconda recovery (8.4 → 9.6) is the load-bearing
contribution. Anaconda was the -1.30 single-reviewer regression
at v5.22.0; the recovery axis was whether v5.23.0 RC.\* (3 silent
CI gates closed), v5.24.0 Hy.\* (`make ci-gates` + `check_doc_freshness.py`
+ cadence-check), and v5.25.0 Pv.\* (5 new prevention gates)
actually closed the structural class. Per Anaconda's findings:
yes, demonstrably and structurally, with all 9 sub-gates GREEN
under live verification at v5.28.0 HEAD.

The +0.55 Boa recovery (9.0 → 9.55) is the second load-bearing
contribution. Bo.18r — the 3-consecutive-panel persistence
finding (same paragraph carrying v5.6.11-vintage language
through v5.7.1 / v5.11.0 / v5.22.0) — was finally structurally
closed at v5.23.0 RC.2 via the rounded `239k` framing, and
v5.28.0 Phase 2 H.1/H.2/H.3 hygiene closures bumped the same
paragraph region to `241k / 23 consecutive releases`. **Largest
single-panel Boa improvement in project history.**

The arc graded shipped:

### v5.23.0 → v5.27.0 hero metrics

| Metric | v5.22.0 | v5.28.0 | Δ |
|---|---:|---:|---|
| Pytest passes (full suite) | 5,800+ | 5,800+ | maintained |
| Goldens (native, mnc-stage1) | 95/95 | **95/95** | maintained |
| LINK_FAIL goldens | 4 (47, 48, 49, 51) | **0** | **-4** |
| Bootstrap mirror cross-tests | 243 | **254** (Te.5 12 + Te.6 10 + comp 10 + interp 10 + indent 201 + brace-deprecation 11) | +11 |
| Strict 3-stage fixed-point streak | 13 releases | **23 releases** | **1.77×** project record |
| stage2.ll lines (preserved at 0 diff) | 238,086 | **241,842** | +1.58% (+0.32%/release average — under +0.5%/release projection) |
| Self-hosted compiler shrunk | -11.5% (net v5.13.0 → v5.21.1) | maintained | unchanged |
| New MIR ops across the arc | 0 | **0** | — |
| New IR shapes across the arc | 0 | **0** | — |
| New runtime function additions across the arc | 2 (`__mn_assert_fail`, `__mn_indent_to_braces`) | **2 more** (`__mn_count_user_brace_block_openers`, `__mn_emit_brace_deprecation_warning` — Te.3.B.2 bootstrap mirror) | bootstrap-mirror plumbing only |
| CI sub-gates | 0 | **9** (silent_skips, changelog_honesty, workflow_shapes, docs_drift, hollow_features, struct_registry, doc_freshness, cadence, clean-build-test) | **+9 structural prevention** |
| Mb.\* / Mc.\* / Eu.\* arcs | open / partial / didn't-exist | **all CLOSED** | — |

### v5.22.0 panel docket closures

| ID | Severity at v5.22.0 | Closing release | Verification |
|---|---|---|---|
| Reg.1 | HIGH | v5.23.0 RC.1 | Live `python3 scripts/check_struct_registry.py` exit 0 |
| Bo.18r-3 | HIGH (3rd consecutive panel) | v5.23.0 RC.2 + v5.28.0 H.1/H.2/H.3 | README:188-192 + 175 + 183 + 196-197 all current |
| Bo.25 | HIGH | v5.23.0 RC.3 | All 4 READMEs goldens badge `95/95`; `bump_version.py` auto-discover wired |
| V.9 | MEDIUM | v5.23.1 Mb.1 | `_last_tracked_str_slot = None` reset; `tests/bootstrap/test_preprocess_memcheck.py` 3/3 PASS |
| Te.5 ASan leaks | MEDIUM | v5.23.1 Mb.2 | `emit_track_boxed(s, ea)` after malloc; baseline TSV refreshed |
| Te.3 hollow / asymmetric closure | MEDIUM (3 reviewers) | v5.23.2 Te.3.B | `tests/bootstrap/test_brace_deprecation_mirror.py` 11/11 PASS |
| Hollow-feature gate calibration | MEDIUM | v5.23.0 RC.4 | `CompClause` + `FieldPattern` in `_AST_INFRASTRUCTURE` |
| Manifesto coherence M2 | MEDIUM (3 panels) | v5.24.1 Wd.1 | `docs/manifesto.md:31` "Indented blocks (with a brace-form legacy through v6.0)" |
| SPEC corpus M3 | MEDIUM | v5.24.1 Wd.2 | `to_terse_markdown` + `<!-- preserve-brace -->`; 26 → 0 brace block-openers |
| Sh.\* shrink baseline labeling | MEDIUM | v5.23.0 RC.12 | Dual-baseline framing in CARRY_FORWARD.md + CLAUDE.md preamble |
| Cadence skip | MEDIUM (process) | v5.24.0 Hy.3 | `check_cadence.py` fires hard at v5.27.0; v5.28.0 closes 1 minor late, acknowledged |
| `make ci-gates` | MEDIUM (structural) | v5.24.0 Hy.1 | 9 sub-gates all GREEN at HEAD |
| `check_doc_freshness.py` | MEDIUM (structural) | v5.24.0 Hy.2 | Wired into `make ci-gates`; clean at HEAD |
| Pk.1.A | LOW (11-release carry) | v5.24.0 Hy.5 | `linux-tarball-smoke` + `macos-tarball-smoke` jobs added |
| `>= 45` magic | LOW (3rd-panel ask) | v5.24.0 Hy.4 | `EXPECTED_PASS=$((TOTAL_GOLDENS - EXPECTED_SEED_FAILS))` formula |
| V.6 / V.7 / V.8 | LOW (3rd cycle) | v5.23.1 Mb.4–6 | `MN_DIR_WALK_MAX_DEPTH` + reparse-skip + `lstat` + `sanitizer-cache-walkers` job |
| Coral L1–L5 / TR1 | LOW each | v5.24.1 Wd.3–7 | All 5 SPEC additions verified at HEAD; `examples/INDEX.md` present |
| Bo.27 audit cross-reference column | LOW (process) | v5.24.1 Wd.8 + applied v5.28.0 | `.reviews/PANEL_AUDIT_TEMPLATE.md`; PRE_PANEL_AUDIT.md honors |
| Mamba #1 (`__mn_indent_to_braces` not in `.h`) | LOW | v5.23.0 RC.10 | Header decl present (Mamba notes recurrence on Te.3.B.2 functions — see NEW finding M.1 below) |
| v5.19.0 SESSION_REPORT missing | LOW | v5.23.0 RC.11 | File present, backfilled |
| Bo.22 (`mapanare run` vs `mnc run`) | LOW (2nd panel) | v5.23.0 RC.14 | English README updated; localized READMEs still `mapanare run` (NEW Boa LOW — see B.1 below) |
| Bo.26 (guides discoverability) | LOW | v5.23.0 RC.15 | 4 guides linked from README |
| `tests/bootstrap/test_indent_preprocessor.py` count | LOW | v5.23.0 RC.13 | Refreshed to 201 |
| Pe.1 reframe | LOW | v5.24.0 Hy.6 | "Curve flattening" framing retired; +0.32%/release vs +0.5% projection |
| `check_docs_drift.py` SPEC.md:1456 | LOW | v5.23.0 RC.5 | `fn id<T>(y: T) -> T = y` |

**Closure rate: 25 of 25 v5.22.0 panel docket items CLOSED at
v5.28.0 HEAD.** This is the highest closure rate in v5 history
across a single recovery arc. The 4 v6.0-rescoped items (Rt.04
multi-level alias, Te.3 hard removal, single-line `if x: y`,
Stage2 teardown crash) carry forward as planned.

### New findings at v5.28.0

| ID | Severity | Reported by | Class |
|---|---|---|---|
| **B.1** | LOW | Boa | Localized READMEs (es/pt/zh-CN) Hello World still uses `mapanare run` instead of `mnc run` (Bo.22-locale recurrence; English-only closure at v5.23.0 RC.14 left localized side open) |
| **B.2** | LOW | Boa | Docker + guide links absent from es/pt/zh-CN READMEs (Bo.24-locale, content-additive); CLAUDE.md cosmetic note ("ready, not tagged" labels) |
| **A.1** | LOW | Anaconda | CARRY_FORWARD.md update-protocol drifted 4 releases (v5.25.0 → v5.27.0) before Phase 2 H.6 caught it. Documented and fixed but the protocol needs structural enforcement. **Suggest: new `check_carry_forward_freshness.py` gate** (mirror of `check_doc_freshness.py`) verifying every released minor/patch since the last "Aggregate state entering vX.Y.Z" line has a closure row. |
| **A.2** | LOW | Anaconda | Coverage gate carry ~75+ releases informational without formal close-or-decline. **Suggest: explicit close-or-decline decision in v5.29.0+ docket.** |
| **A.3** | LOW | Anaconda | Mc.8 "arc CLOSED" label slightly generous given auto-wrap was the advertised scope and detect-only is what shipped. Coral New.1 corroborates (PLAN/PROMPT not amended after Phase 0 pivot). |
| **M.1** | LOW | Mamba | `.h` vs `.c` header asymmetry recurred. v5.22.0 Mamba #1 closed `__mn_indent_to_braces` at v5.23.0 RC.10; v5.23.2 Te.3.B.2 added `__mn_count_user_brace_block_openers` + `__mn_emit_brace_deprecation_warning` without header decls. Net +1 export in `.c` not in `.h` (16 → 17). **2-line immediate fix + Pv.7-style structural gate (diff `MN_EXPORT` names between `.c` and `.h`) recommended for v5.28.x or v5.29.0.** |
| **Vp.1** | LOW | Viper | `sanitizers.yml` `sanitizer-mnc-stage1` job comment (lines 199-201) claims it detects an `emit_wrap_some` Mb.2 regression but greps only for `__mn_indent_to_braces`. Documentation lie, not real coverage gap (actual Mb.2 coverage via baseline TSV + LSan). Misleads next reviewer. |
| **Co.New1** | LOW | Coral | Mc.8 PLAN/PROMPT not amended after Phase 0 pivot (PLAN.md Phase 2 still describes auto-wrap). Documentation-discipline issue; SESSION_REPORT corrects. |
| **Co.New2** | LOW | Coral | Mc.9 SESSION_REPORT "splits into sub-blocks" imprecise — actual mechanism is "comment terminates the current block." Behavior correct. |
| **Cb.New1** | LOW | Cobra | `test_native.py` byte-identity oracle remains blind to LLVM link failures — the exact structural gap that hid Eu.1..Eu.4 for three releases. **Suggest: Tn.\* generalization extending `tests/llvm/test_async_link.py` link-and-run pattern to all 95 goldens for v5.29.0+.** |
| **Cb.New2** | LOW | Cobra | O(N²) `seen_tags` dedup in `build_match_arms` (amused, not alarmed; only triggers on or-patterns with N>20 alternatives, none in current corpus). |
| **Cb.New3** | LOW | Cobra | `mnc fmt --help` does not list `--line-length` and `--sort-imports` (v5.27.0 flags). 1-line fix. |
| **Ra.New1** | LOW | Rattler | Stage2 teardown crash (carry from v5.22.0) narrowed to **stdout-redirect-specific SIGSEGV (RC=139)** — `-o file` path is RC=0 clean. Investigation tractable via `valgrind --track-origins=yes /tmp/mnc-stage2 emit-llvm test.mn > /dev/null`. The `-o file` vs stdout dispatch fork in `main.mn` is the isolation boundary. **80+ release carry now actionable.** |
| **Ra.Inf1** | INFORMATIONAL | Rattler | `test_async_link.py` covers 10 of 95 goldens. **Same shape as Cb.New1 — independent convergence.** Recommends Pv.\*-style extension. |
| **Ra.Inf2** | INFORMATIONAL | Rattler | `Result<T, E>` / `Option<T>` IR representation `{i1, {T, E}}` requires double-extractvalue (Eu.1). Idiomatic flat-layout `{i1, i[max(sizeof(T), sizeof(E))*8]}` would eliminate the double-extractvalue and enable SROA. v6.0 scope. |

**0 HIGH** new + **0 MEDIUM** new + **~14 LOW** new (mostly
process-discipline polish). The Rattler+Cobra independent
convergence on test-coverage gap (`Ra.Inf1` + `Cb.New1`) is the
**load-bearing recommendation**: extending link-and-run coverage
beyond the 10 async-cluster + Eu.\* goldens to all 95 would
catch future LINK_FAIL regressions within the same release
cycle. **At v5.29.0 if not picked up in a Pv.\* follow-on, this
should escalate to MEDIUM** — the structural gap that hid
Eu.1..Eu.4 for three releases (v5.23.1 → v5.26.0) is exactly
the failure mode the v5.22.0 panel was designed to catch
structurally.

## Carry-forward (for v5.28.x / v5.29.0+ / v6.0)

### HIGH (0 items)

None.

### MEDIUM (0 items)

None.

### LOW (~14 items, mostly v5.29.0+ targets)

- **Cb.New1 + Ra.Inf1 (link-coverage gap, convergent)** — extend
  `test_async_link.py` link-and-run pattern to all 95 goldens
  via new `test_llvm_link_all.py` (Tn.\* generalization).
  **2-4h. v5.29.0.** **Escalate to MEDIUM if deferred past
  v5.29.0.**
- **A.1 (CARRY_FORWARD update-protocol drift)** — new
  `check_carry_forward_freshness.py` gate. **2h. v5.29.0.**
- **A.2 (coverage gate close-or-decline)** — explicit decision.
  **30 min. v5.29.0.**
- **A.3 + Co.New1 (Mc.8 PLAN/PROMPT not amended)** — add
  `## Phase 0 pivot` section convention; backfill v5.27.0
  PLAN.md. **30 min. v5.28.x.**
- **M.1 (header asymmetry recurrence)** — 2-line fix in
  `mapanare_core.h`; `Pv.7`-style structural gate diffing
  `MN_EXPORT` names between `.c` and `.h`. **2h. v5.28.x.**
- **Vp.1 (sanitizers.yml comment)** — 1-line comment correction.
  **5 min. v5.28.x.**
- **Co.New2 (Mc.9 SESSION_REPORT imprecision)** — 1-paragraph
  rewrite. **5 min. v5.28.x.**
- **B.1 (Bo.22-locale)** — 5-min update of localized README
  Hello Worlds. **v5.28.x.**
- **B.2 (Bo.24-locale)** — Docker + guide links in localized
  READMEs (content-additive). **30 min. v5.29.0.**
- **Cb.New3 (`mnc fmt --help` flags)** — 1-line addition.
  **5 min. v5.28.x.**
- **Cb.New2 (O(N²) seen_tags)** — refactor to set-based dedup.
  **15 min. v5.30.0.**
- **Ra.New1 (Stage2 teardown stdout-specific narrowed)** —
  `valgrind --track-origins=yes` investigation. **2-4h. v5.29.0.**
  Investigation tractable with new isolation boundary.

### v6.0 carry (4 items, deferred)

- **Rt.04** — Multi-level alias analysis. Status unchanged from
  v5.7.1 / v5.11.0 / v5.22.0 / v5.28.0 panels.
- **Te.3 hard removal of `{}`** — v5.19.0 soft-deprecation
  cycle terminus.
- **Single-line `if x: y`** — v5.21.1 explicit rescope.
- **Stage2-binary teardown crash (RC=3)** — papered over by
  `set +e` since v4.30.0 PLAN; **v5.28.0 Rattler narrowed to
  stdout-redirect-specific SIGSEGV** — investigation now
  tractable; consider closing in v5.29.0+ rather than v6.0.
- **Ra.Inf2 (Result/Option flat-layout)** — v6.0 IR shape
  refactor; eliminates Eu.1 double-extractvalue, enables SROA.

## Key concerns across reviewers

1. **Convergent test-coverage gap (Cb.New1 + Ra.Inf1, two
   independent reviewers).** `test_native.py`'s byte-identity
   oracle is blind to LLVM link failures. The Eu.1..Eu.4 bugs
   were hidden for three releases (v5.23.1 → v5.26.0) because
   the byte-identity oracle compared Python ↔ native IR but
   didn't actually link/run. `tests/llvm/test_async_link.py`
   (v5.26.1) is the reference implementation for a `Tn.\*`
   generalization that would cover all 95 goldens. **Two
   independent reviewers arriving at the same finding shape is
   strong consensus.** Should escalate to MEDIUM in v5.29.0
   docket if not picked up in a Pv.\* follow-on.
2. **Header asymmetry recurrence (M.1, Mamba).** v5.22.0 Mamba
   #1 closed for `__mn_indent_to_braces` at v5.23.0 RC.10; the
   identical failure shape recurred at v5.23.2 with the
   Te.3.B.2 functions. **Same fingerprint, different exports.**
   Mamba's recommended Pv.7-style structural gate (diff
   `MN_EXPORT` names between `.c` and `.h`) is the right
   structural fix — same Hy.\*/Pv.\* discipline that closed the
   Reg.1 / Bo.18r / cadence-skip recurrence patterns.
3. **Mc.8 design pivot — generous label vs honest scope-shift
   (A.3 + Co.New1, two reviewers).** SESSION_REPORT documents
   the Phase 0 pivot from auto-wrap to detect-only honestly,
   but PLAN.md and PROMPT.md were not amended. The "Mc.\* arc
   CLOSED" claim is defensible given Mc.5 (emit-wasm) was also
   honestly rescoped to v6.0, but the planning-artifact gap is
   real. Coral's recommendation (add `## Phase 0 pivot` section
   to PLAN.md template for future pivots) is the right
   structural fix.
4. **CARRY_FORWARD.md update-protocol drift (A.1, Anaconda).**
   The lead's PRE_PANEL_AUDIT caught the 4-release drift as
   H.6 and closed it in Phase 2, but the protocol should be
   structurally enforced rather than relying on pre-panel
   audit catches. **Same shape as v5.22.0 cadence-skip class
   on a different surface.**
5. **Stage2 teardown crash narrowed (Ra.New1, Rattler).** 80+
   release carry now actionable: stdout-redirect-specific
   SIGSEGV with `-o file` clean. Recommends closing in v5.29.0
   rather than v6.0.

## Disagreements

The panel surfaced **0 notable disagreements ≥ 0.3 spread on
the same axis**. Score range was 9.55 (Boa) to 9.90 (Rattler)
— a 0.35 range, but reviewers cover orthogonal axes so this is
not a same-axis disagreement.

**Convergence noted:** Rattler + Cobra independently arrived
at the same finding shape (`Ra.Inf1` + `Cb.New1` —
test-coverage gap on byte-identity oracle blindness to LINK
failures). Anaconda + Coral independently judged the Mc.8
design-pivot label as "slightly generous but defensible"
(`A.3` + `Co.New1` corroborates). These are **strong
multi-reviewer signals** that should drive the v5.29.0+
docket.

## Improvements Since v5.22.0 Panel

**Correctness axis (Rattler / Cobra / Mamba):**
- Strict 3-stage fixed-point streak: 13 → **23 releases**
  (1.77× project record).
- LINK_FAIL goldens: 4 → **0** (Eu.1..Eu.4 closures verified
  live in IR; `tests/llvm/test_async_link.py` 10/10 PASS, 0
  XFAIL).
- Mb.\* arc: open → **CLOSED** (v5.26.0 Mb.7 + Mb.9; codegen
  i64/i1 fix + Win64 byval/byref ABI).
- Eu.\* arc: didn't exist → **CLOSED** (v5.26.1 Eu.1..Eu.4;
  4 distinct codegen / lowering closures).
- No new MIR ops, no new IR shapes across 8 releases (verified
  in `mir.py` 65 classes unchanged).
- C runtime delta: +306 LOC across 8 releases (only 2 of 8
  releases touched runtime — correct pattern).
- Pe.1 growth rate: +0.32%/release (well under +0.5%/release
  v5.24.0 Hy.6 reframe projection).

**Memory safety axis (Viper):**
- V.9 + V.6 + V.7 + V.8 (3rd-cycle carries) all CLOSED at
  v5.23.1 Mb.\*.
- 3 NEW Te.5 ASan leak regressions (post-v5.22.0 panel)
  CLOSED at v5.23.1 Mb.2 via `emit_track_boxed`.
- Eu.3 SSA uniquification (`bind_ident_pattern` `tmp_counter`)
  prevents `%x.addr` collisions under cascade dispatch.
- Pv.2 preprocess-memcheck gate falsifiable; valgrind regression
  CI gates wired (Mb.3 sanitizer-mnc-stage1, Mb.6
  sanitizer-cache-walkers).

**Process axis (Anaconda — load-bearing):**
- v5.22.0 -1.30 dock fully recovered (+1.20 at v5.28.0).
- 3 silent-RED CI gates at v5.22.0 (Reg.1, hollow_features,
  docs_drift) all GREEN at HEAD.
- 5 NEW prevention gates wired (Pv.1..Pv.6) — runtime-lib
  lookup, preprocess-memcheck, clean-build-test, validate_wsl,
  publish smoke fixtures.
- Cadence-check (Hy.3) fired exactly as designed at v5.27.0;
  v5.28.0 closes 1 minor late with explicit acknowledgment in
  3 documented locations.
- Pk.1.A 11-release carry CLOSED v5.24.0 Hy.5.
- PRE_PANEL_AUDIT.md honors Bo.27 cross-reference column
  (every H.\* row binds to prior-panel ID).

**Documentation axis (Boa):**
- Bo.18r 3-consecutive-panel persistence: STRUCTURALLY CLOSED
  at v5.23.0 RC.2 + v5.28.0 Phase 2.
- Bo.25 (goldens badge): closed at v5.23.0 RC.3 with
  `bump_version.py` extension.
- Bo.21 (version badges): STAYS CLOSED.
- Bo.17r (localized READMEs): closed ~80% at v5.21.1 H.3,
  re-emerged at v5.27.0, closed 100% at v5.28.0 Phase 2 H.4.
- Bo.22 (`mapanare run` vs `mnc run`): closed for English
  README at v5.23.0 RC.14 (localized side as B.1 LOW
  carry-forward).
- Bo.26 (guides discoverability): closed v5.23.0 RC.15.
- Bo.27 (audit cross-reference column): codified at v5.24.1
  Wd.8 + applied at v5.28.0 PRE_PANEL_AUDIT.md.

**Language design axis (Coral):**
- M1 Te.3 hollow / asymmetric closure (3 reviewers): CLOSED
  v5.23.2 Te.3.B; 11/11 byte-identity test contract.
- M2 Manifesto coherence (3 panels): CLOSED v5.24.1 Wd.1.
- M3 SPEC corpus 72% brace-style: CLOSED v5.24.1 Wd.2 via
  `to_terse_markdown`; 26 → 0 brace block-openers.
- L1–L5 / TR1: all CLOSED v5.24.1 Wd.3–7.
- Mc.\* parity arc CLOSED at v5.27.0 (12-release closure of
  v5.13.0 docket).
- Eu.\* arc CLOSED at v5.26.1 — fixed real language-semantic
  bugs in match dispatch.
- Te.3 deprecation cycle policy (SPEC §22) compliant.

## Regressions Since v5.22.0 Panel

**None at HIGH or MEDIUM severity.** The arc closed every
v5.22.0 panel HIGH and MEDIUM.

**Minor LOW regressions:**
- Header asymmetry recurrence (M.1, Mamba — same shape as
  v5.22.0 Mamba #1 on different exports).
- Bo.22 closure was English-only; localized side recurred (B.1).
- CARRY_FORWARD update-protocol drifted 4 releases before
  Phase 2 caught it (A.1).

**Process observation:** Both M.1 and A.1 are recurrence
patterns of v5.22.0 findings on a different surface. Both
have a structural fix path (Pv.7-style header diff gate +
`check_carry_forward_freshness.py` gate) that follows the
same Hy.\* / Pv.\* prevention pattern that closed the
v5.22.0 silent-CI-gate class.

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

**No recovery cycle is opened.** The action items in the
LOW carry-forward table constitute the v5.28.x / v5.29.0+
docket. The Cobra+Rattler convergence on test-coverage gap
(Cb.New1 + Ra.Inf1) is the load-bearing recommendation —
**escalate to MEDIUM at v5.29.0 if not picked up in a Pv.\*
follow-on**, since this is exactly the structural gap that
hid Eu.1..Eu.4 for three releases.

**Cadence reset:** next routine panel due at **v5.33.0** (5
minors past v5.28.0). Cadence-check gate (Hy.3) will fire
hard at v5.33.0 if no panel runs by then.

See [README.md](README.md) for the full panel synthesis.

## Precedent

This decision follows the same structure as v5.7.1 / v5.8.0,
v5.11.0, and v5.22.0 panels: Option A applied at aggregate
≥ 9.0 with 0 NEEDS WORK and no NEW HIGH off prior docket.

The v5.28.0 aggregate (9.72) is the **highest aggregate in v5
history**, displacing v5.7.1 / v5.8.0's 9.66 as the project
ceiling.

The +0.31 v5.22.0 → v5.28.0 recovery confirms that the
"hygiene-via-release ceiling around 9.55-9.66" Coral flagged
at v5.22.0 was breakable through structural-prevention
infrastructure, not through more polish releases. v5.24.0 Hy.\*
(`make ci-gates`, `check_doc_freshness.py`, cadence-check) +
v5.25.0 Pv.\* (5 prevention gates) were the structural
mechanisms; v5.23–v5.24 recovery arc cleared the existing
docket; v5.26-v5.27 closed the codegen + formatter parity arcs.

## Cadence reset

**Next routine panel:** **v5.33.0** (5 minors past v5.28.0).

**Alternate trigger:** if 5 language-feature releases ship
before v5.33.0, the alternate cadence threshold fires earlier.
Cadence-check (Hy.3) fires hard at v5.33.0 cut if no panel
runs.

---

## Sign-off

This panel certifies v5.28.0 as a healthy point release under
the v5-gate mechanical rule. The release ships. The next panel
(target: v5.33.0 routine cadence, or earlier if 5
language-feature releases land first) will verify:

1. Whether the v5.28.x / v5.29.0+ LOW docket items closed
   (M.1 header asymmetry + Pv.7 gate, A.1 CARRY_FORWARD
   freshness gate, Cb.New1 + Ra.Inf1 link-coverage extension,
   Vp.1 sanitizers.yml comment, B.1 localized Hello World,
   etc.).
2. Whether the Cb.New1 + Ra.Inf1 convergent test-coverage gap
   was picked up in a Pv.\* follow-on, or whether it requires
   MEDIUM escalation at v5.29.0.
3. Whether the v5.28.0 +0.31 recovery represents a sustained
   reversal or a one-time post-recovery-arc bounce. **A
   v5.33.0 panel landing at ≥ 9.55 would confirm the structural
   prevention infrastructure is doing its job; landing back at
   9.55-9.66 would suggest the ceiling Coral flagged at v5.22.0
   is real and v5.28.0's 9.72 is the high-water mark.**
4. Whether the Stage2 teardown crash (Ra.New1) was closed at
   v5.29.0 (now investigation-tractable) or maintained as v6.0
   carry.

**The discipline that produced the v5.7.1 → v5.21.1 13-release
strict-fixed-point streak now extends to 23 releases. The
discipline that produced the v5.22.0 -1.30 process-discipline
regression is structurally prevented by Hy.\* + Pv.\* gates.
The arc graded delivered exactly what a recovery + prevention
+ arc-closeout arc should deliver — and the panel grades it as
the strongest single arc in v5 history.**

*La culebra está delgada, cómoda, y por primera vez ha mudado
la piel del techo de v5.7.1 — el espejo de bronce está limpio,
el registro está al día, y la próxima escama crece donde antes
había drift.*
