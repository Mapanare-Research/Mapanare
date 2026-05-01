# v5.22.0 RE-PANEL Decision

> **Re-panel of the v5.11.0 → v5.21.1 terseness arc (16
> releases).** Panel aggregate **9.41 / 10**, 0 NEEDS WORK.
> Mechanical rule → **Option A — v5.22.0 is a clean point
> release.** Third consecutive Option A under the v5-gate
> framework, but third consecutive panel micro-regression
> (9.66 → 9.62 → 9.41) — the framework continues to clear
> healthy releases while the trend signals process-discipline
> debt that the H.\* hygiene pattern has stopped fully
> covering.

**Date:** 2026-05-01
**Aggregate:** 9.41 / 10
**Distribution:** 5 EXCEEDS / 1 MEETS / 1 PASS-only
(0 NEEDS WORK; 1 PASS, 6 PASS WITH NOTES)
**Decision:** **Option A — point-release health gate clears.**

## Mechanical rule applied

> Aggregate ≥ 9.0 AND 0 NEEDS WORK → Option A.

| Rule | Condition | Outcome | Applied? |
|---|---|---|---|
| Option A (standard) | Aggregate ≥ 9.0 AND 0 NEEDS WORK | Clean point release | **YES: 9.0 ≤ 9.41, 0 NEEDS WORK** |
| Option C (closeout) | 8.5 ≤ Aggregate < 9.0 AND 0 NEEDS WORK | Release ships with documented carry-forwards | No: 9.41 ≥ 9.0 |
| Option B (recovery) | Aggregate < 8.5 OR any NEEDS WORK | Recovery cycle opens at v5.22.1 | No: both gates clear |

**Applied: Option A.** v5.22.0 is a clean point release. No
recovery cycle is opened. The panel's 4 HIGH and 8 MEDIUM
findings constitute the v5.22.x / v5.23.0+ docket; none gates
the v5.22.0 release itself.

## Context

v5.0.0 already shipped at v4.143.0 (rc1) → v4.145.0+ (clean
tag); the project is in **point-release maintenance** as of
the v5.x series. The v5-gate mechanical rule continues to
apply as the project's standing health-gate framework.

This is the **third consecutive Option A** panel under that
framework (v5.7.1: 9.66; v5.11.0: 9.62; v5.22.0: 9.41).

The arc graded — v5.11.0 → v5.21.1 — spans **16 releases over
~3 weeks**, the **largest feature-velocity arc in v5
history**. Six additive language features shipped (Te.1
colon-block, Te.2 comprehensions / lambda / implicit-return,
Te.3 `{}` soft-deprecation, Te.4 string-interp parity, Te.5
struct ergonomics, Te.6 chained comparisons) with **zero new
MIR ops, zero new IR shapes, and only two new C-runtime
exports** (`__mn_assert_fail` 8 LOC + `__mn_indent_to_braces`
545 LOC, both bootstrap-mirror plumbing). The Sh.\* mechanical
rewrite shrunk the self-hosted compiler **−11.5%** off the
v5.13.0 baseline (net source delta) without breaking fixed
point at any per-module commit. Goldens 66/66 → 95/95.
Strict 3-stage fixed point preserved at 238,086 lines /
0-line diff across **13 consecutive shipping releases —
longest streak in project history**.

v5.22.0 is the panel-only release: zero compiler / runtime /
self-host source edits beyond the v5.21.1 closeout. Same
posture as v5.8.0 (which graded v5.3.1 → v5.7.1 and produced
the project-record 9.66 panel).

## Score

**Aggregate: 9.41 / 10**
**Grade distribution: 5 EXCEEDS / 1 MEETS / 1 PASS-only
(0 NEEDS WORK)**

## Per-reviewer scores

| # | Reviewer | Domain | v4.154.0 | v5.2.0 | v5.7.1 | v5.11.0 | **v5.22.0** | Δ v5.11.0 | Grade |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | Rattler | LLVM IR / codegen | 9.6 | 9.3 | 9.8 | 9.85 | **9.85** | **±0.0** | EXCEEDS |
| 2 | Viper | Memory safety | 9.6 | 9.7 | 9.9 | 9.90 | **9.7** | **−0.20** | EXCEEDS |
| 3 | Anaconda | CI / testing / toolchain | 9.4 | 8.9 | 9.6 | 9.70 | **8.4** | **−1.30** | MEETS |
| 4 | Cobra | Bootstrap / self-hosted | 9.1 | 8.8 | 9.6 | 9.70 | **9.55** | **−0.15** | EXCEEDS |
| 5 | Coral | Language design | 9.3 | 9.4 | 9.6 | 9.50 | **9.55** | **+0.05** | EXCEEDS |
| 6 | Boa | Documentation / DX | 9.3 | 9.4 | 9.4 | 8.90 | **9.0** | **+0.10** | EXCEEDS |
| 7 | Mamba | C runtime / performance | 9.3 | 9.6 | 9.8 | 9.80 | **9.85** | **+0.05** | EXCEEDS |
| | **Aggregate** | — | **9.37** | **9.30** | **9.66** | **9.62** | **9.41** | **−0.21** | — |

## Score trajectory

| Panel | Aggregate | NEEDS WORK | Outcome |
|---|---:|---:|---|
| v4.99.0 | 6.59 | (recovery) | Option B |
| v4.106.0 | 7.87 | 0 | Option B |
| v4.114.0 | 8.21 | 0 | Option B |
| v4.120.0 | 8.21 | 1 (Anaconda) | Option B |
| v4.136.0 | 8.80 | 0 | Option C (v5.0.0-rc1) |
| v4.143.0 | 8.86 | 0 | Option C (rc1 holds) |
| v4.144.0 | 9.21 | 0 | Option A declared (tag deferred) |
| v4.154.0 | 9.37 | 0 | Option A (v5.0.0 tagged) |
| v5.2.0 | 9.30 | 0 | Option A (v5.3.0) |
| v5.7.1 / v5.8.0 | **9.66** | 0 | Option A (v5.8.0; project-record) |
| v5.11.0 | 9.62 | 0 | Option A (v5.11.0) |
| **v5.22.0** | **9.41** | **0** | **Option A (v5.22.0)** |

Full trajectory: 6.59 → 7.87 → 8.21 → 8.21 → 8.80 → 8.86 →
9.21 → 9.37 → 9.30 → 9.66 → 9.62 → **9.41**.

The −0.21 Δ from v5.11.0 to v5.22.0 is the **largest single-arc
regression since v5.0.0**, and the **third consecutive panel
trending downward** (9.66 → 9.62 → 9.41 = −0.04 → −0.21). The
trend is informative: every −X arc has been driven by a
different surface (v5.8→v5.11 was Boa docs-surface; v5.11→v5.22
is Anaconda CI-discipline + Boa docs-persistence), but the
shape — the surface the framework wasn't auditing — is
consistent.

## What the arc delivered

### v5.11.0 → v5.22.0 hero metrics

| Metric | v5.11.0 | v5.22.0 | Δ |
|---|---:|---:|---|
| Pytest passes (full suite) | 5,720+ | 5,800+ | +80 |
| Goldens (native, mnc-stage1) | 66/66 | **95/95** | +29 |
| Bootstrap mirror cross-tests | 0 | **243** (Te.5 12 + Te.6 10 + comp 10 + interp 10 + indent 201) | +243 |
| Strict 3-stage fixed-point streak | 5 releases | **13 releases** | longest in project history |
| stage2.ll lines (preserved at 0 diff) | 226,603 | **238,086** | +5.07% |
| Self-hosted compiler (`mapanare/self/`) | 28,698 lines | **24,710 lines** (−11.5% net off v5.13.0) | shrunk while fixed-point preserved |
| New MIR ops across the arc | — | **0** | — |
| New IR shapes across the arc | — | **0** | — |
| New runtime function additions across the arc | — | **2** (`__mn_assert_fail` 8 LOC + `__mn_indent_to_braces` 545 LOC) | bootstrap-mirror plumbing only |
| Additive language features absorbed | — | **6** (Te.1–Te.6) | zero grammar churn beyond documented additive surface |

### v5.11.0 panel docket closures

| ID | Severity at v5.11.0 | Closed | Closing release | Verification |
|----|---|---|---|---|
| Bo.21 | HIGH | YES | v5.21.1 H.1 (via bump_version sweep) | All 4 READMEs at 5.21.1 |
| Bo.17r | MEDIUM | YES (~80%) | v5.21.1 H.3 | es/pt/zh-CN bodies sync'd to 95/95 + Te.1–Te.6 subsection |
| Coral SPEC re-sync | MEDIUM | YES | v5.21.1 H.2 / H.3 / H.5 | SPEC header at v5.21.0; §2.2 / §3.7 / §4.0 / §4.3.1 all current |
| Mc.\* parity | MEDIUM | YES | v5.18.0 | `mnc lsp`/`fmt`/`init`/`check` all reachable |
| Pk.1.A | LOW | NO | — | Linux/macOS versioned-tarball smoke gates still missing across 11 releases |
| Cobra per-PR fixed-point gate | LOW (3rd-time ask) | YES (mea culpa — was always wired) | v4.29.0 (`.github/workflows/ci.yml:858`) | confirmed by Cobra at v5.22.0 |
| `>= 45` magic | LOW | NO | — | 3rd-time ask |
| Viper V.6 / V.7 / V.8 | LOW | NO | — | 3rd-cycle carry (DX.4 walkers + Win32 reparse + no sanitizer sweep) |
| Bo.18r (README contradiction) | MEDIUM | NO | — | **3rd consecutive panel** — v5.21.1 H.1 closed sibling line 176, walked past panel-flagged 188-192 |
| Bo.22 (`mapanare run` vs `mnc run`) | LOW | NO | — | 2nd consecutive panel |

**4 of 10 carry-forward items closed; 6 remain open.** That is
better than v5.7.1 → v5.11.0 (1/3 closed) but the **two
HIGH/MEDIUM items still open** (Bo.18r persistence, Pk.1.A) are
both 3+-cycle carries.

### New findings at v5.22.0

| ID | Severity | Reported by | Class |
|----|---|---|---|
| Reg.1 | HIGH | Anaconda + Cobra | `check_struct_registry.py` regex hard-codes brace headers; inert since v5.17.0 Sh.\* (5 releases of registry blindness) |
| Bo.25 | HIGH | Boa | Goldens badge `66/66` vs body `95/95` across all 4 READMEs (same systematic-skill-gap shape as v5.11.0 Bo.21) |
| V.9 | MEDIUM | Viper | `__mn_indent_to_braces` MnString leak on every colon-syntax compile through `mnc-stage1` (missing tracked-output annotation) |
| Te.3 hollow | MEDIUM | Coral M1 / Anaconda §3 / Rattler #1 | Brace-warning misses single-line shape; native `mnc-stage1` has zero brace-deprecation logic (PY: closed | SH: open asymmetric closure) |
| Hollow-feature gate | MEDIUM | Anaconda §2.B | `check_no_hollow_features.py` step 3 RED on `CompClause` (v5.15.0) + `FieldPattern` (v5.20.0) — whitelist calibration miss |
| Manifesto coherence (M2) | MEDIUM | Coral | "Curly braces for blocks" line untouched against brace-deprecated codebase (3rd consecutive panel of manifesto drift) |
| SPEC example corpus (M3) | MEDIUM | Coral | 72% brace-style examples against §4.0 declaring colon-canonical |
| Sh.\* shrink baseline labeling | MEDIUM | Cobra #2 / Rattler #4 | "−13.9% off v5.13.0" actually measures pre-Sh.B-immediate; net v5.13.0 → v5.21.1 is −8.18% |
| Cadence skip | MEDIUM (process) | Anaconda §1 | 5-minor (v5.16.0) + 5-language-feature (v5.20.0) triggers fired and not honored at trigger; documented as overdue but not run on schedule |
| Bo.26, Bo.27 | LOW | Boa | Discoverability gap on `docs/guides/{formatter,init}.md`; PRE_PANEL_AUDIT cross-reference column missing |
| Mamba #1 / #3 | LOW | Mamba | `__mn_indent_to_braces` missing from `.h`; O(line-count) allocs in indent preprocessor (only-if-perf-cares) |
| Rattler #2 | LOW | Rattler | `docs/roadmap/v5/v5.19.0/SESSION_REPORT.md` does not exist on disk (3 commits in log; SR never written) |
| Stage2-teardown RC=3 | LOW (carry) | Rattler #5 | 70+ releases stale since v4.30.0 PLAN; papered over by `set +e` |
| Coral L1–L5 / TR1 | LOW | Coral | SPEC §27 deprecation crosslink, broken-promise wording, `mnc fmt` flag mention, examples directory micro-organization |

**4 HIGH** (2 from prior panel still open + 2 new), **8
MEDIUM** (1 carried + 7 new), **9 LOW** (5 carried + 4 new).
Despite the score regression, the H.\*-class carry trail is
**better managed** than at v5.7.1 → v5.11.0: every flagged
item has a tracked closure target and a suggested fix shape.

## Carry-forward (for v5.22.x / v5.23.0+ / v6.0)

### HIGH (4 items, all v5.22.x targets)

- **Reg.1** — `check_struct_registry.py` regex extension to colon-form + parser update for indent-based bodies + investigation of any drift accumulated during the 5-release blind window. **2h.**
- **Bo.18r** — `README.md:188-192` benchmarks paragraph rewrite to "238k / 13-release strict streak / 5,800+" framing. Closes Bo.18r + Bo.19 + Bo.20 in one keystroke. **3 min. 3rd consecutive panel.**
- **Bo.25** — Goldens badge `66/66` → `95/95` across all 4 READMEs. Structural fix: extend `bump_version.py` to auto-discover and update the goldens badge. **1 min one-shot, 10 min structural.**

### MEDIUM (8 items, mixed v5.22.x and v5.23.0)

- **Te.3 hollow** — `count_user_brace_block_openers` token-walk + native `mnc-stage1` mirror (~50 LOC). **2-4h. v5.22.x.**
- **V.9** — `__mn_indent_to_braces` tracked-output-string annotation in `mapanare/self/parser.mn` + valgrind regression CI gate. **1-2h. v5.22.x. MANDATORY follow-up.**
- **Bo.22** — `mapanare run` → `mnc run` in README Hello World. **5 min. v5.22.x. 2nd consecutive panel.**
- **Manifesto coherence (M2)** — `docs/manifesto.md:31` "Curly braces for blocks" rewrite. **5 min. v5.22.x. 3rd consecutive panel of manifesto drift.**
- **`check_no_hollow_features.py`** — add `CompClause` + `FieldPattern` to `_AST_INFRASTRUCTURE` whitelist. **5 min. v5.22.x.**
- **`check_docs_drift.py`** — close SPEC.md:1456 violation. **1 min. v5.22.x.**
- **`make ci-gates`** Makefile target running the full CI gate inventory locally. **30 min. v5.22.x.**
- **`check_doc_freshness.py`** — structural fix for the H.\* / Bo.\* drift class. **2-4h. v5.23.0.**
- **SPEC example corpus (M3)** — `mnc fmt --to-terse` over `docs/SPEC.md`. **30 min. v5.23.0.**
- **Sh.\* baseline labeling** — normalize references in v5.17.x SESSION_REPORTs / CARRY_FORWARD.md / CLAUDE.md. **30 min. v5.22.x.**

### LOW (~10 items)

- **Pk.1.A** (11-release carry; Linux/macOS versioned-tarball smoke gates) — v5.23.0.
- **`>= 45` magic** (3rd-panel ask) — v5.22.x.
- **`tests/bootstrap/test_indent_preprocessor.py` count** documentation refresh — v5.22.x.
- **V.6 / V.7 / V.8** (3-cycle DX.4 walker + Win32 reparse + no sanitizer sweep) — v5.23.0.
- **`__mn_indent_to_braces`** missing from `mapanare_core.h` — v5.22.x.
- **v5.19.0 SESSION_REPORT** retroactive backfill — v5.22.x.
- **Bo.26** (`docs/guides/{formatter,init}.md` discoverability) — v5.22.x.
- **Bo.27** (PRE_PANEL_AUDIT cross-reference column) — v5.27.0 audit.
- **Cadence enforcement** CI gate or pre-release script — v5.23.0.
- **Coral L1–L5 / TR1** (SPEC discoverability + narrative polish) — v5.23.0+.

### v6.0 carry (deferred — borrow checker scope or hard-removal scope)

- **Rt.04** — Multi-level alias analysis (struct → list → string depth 2). Status unchanged from v5.7.1 / v5.11.0 / v5.22.0 panels.
- **Te.3 hard removal of `{}`** — v5.19.0 soft-deprecation cycle terminus.
- **Stage2-teardown crash (RC=3)** — papered over by `set +e` since v4.28.0; 70+ releases stale; close in v6.0 cleanup window.
- **Single-line `if x: y`** — v5.21.1 explicitly rescoped to v6.0 to coincide with `{}` hard removal.

## Key concerns across reviewers

1. **Reg.1 — 5 releases of silent CI gate inertness** (Anaconda HIGH + Cobra HIGH; same finding, two independent surfaces). The gate that v4.143.0 commissioned to catch Ge.1-class drift has been blind during the 10-release feature-velocity arc that should have stressed it most. **No prior assurance that no actual field-name drift accumulated** during Te.5 / Te.6 / Sh.\*. After regex restoration, the v4.143.0 retrospective precedent ("3 real latent drifts on first run") suggests a non-zero count is likely.
2. **Bo.18r — 3rd consecutive panel** (Boa HIGH). The H.\* hygiene release pattern, while structurally healthier than no-hygiene, has a systematic blind spot: the lead patches what the audit cites; panel-flagged line numbers slip past when not cross-referenced into the audit. Boa's Bo.27 (cross-reference column) is the suggested process fix.
3. **Te.3 hollow-surface** (Coral M1 / Anaconda §3 / Rattler #1; same finding, three independent reviewers). The PRE_PANEL_AUDIT.md's own pre-flight test command demonstrates that the warning does NOT fire on the canonical single-line shape. Asymmetric closure: `PY: closed | SH: open` (native `mnc-stage1` has zero brace-deprecation logic). Should have been tracked per `.reviews/CARRY_FORWARD.md` dual-closure convention.
4. **Cadence skip** (Anaconda §1). 5-minor + 5-language-feature triggers both fired and were skipped. Documented as overdue (PRE_PANEL_AUDIT line 1-12), but documentation does not constitute honoring. The cadence rule was written precisely because the v4.18–v4.26 hollow-features regression accumulated in an 8-version no-review window.
5. **V.9 lifecycle leak** (Viper MEDIUM). Bounded to single-shot in `mnc-stage1`; OS reaps on exit; not crashing anything in production. **Unbounded if the runtime is embedded in a long-lived process** (LSP server with re-parse path, watch-mode compiler). The byte-identical oracle (`test_indent_preprocessor.py`) cannot detect lifecycle issues — a class blind spot the panel formally surfaces.

## Precedent

This decision follows the same structure as v5.7.1 / v5.8.0
and v5.11.0 panels: Option A applied at aggregate ≥ 9.0 with
0 NEEDS WORK. The v5.22.0 aggregate (9.41) is the **lowest
Option A aggregate since v5.2.0** (which scored 9.30); v5.7.1
remains the project ceiling at 9.66.

The −0.21 v5.11.0 → v5.22.0 regression confirms the
"hygiene-via-release" cap Coral flagged structurally: the
pattern works (closes the H.\* drift class cleanly each
release), but **closure-by-hygiene-release ceiling is around
9.55–9.66**. To break above 9.66, the lead needs hygiene-at-
source on the next arc — which is what `check_doc_freshness.py`
+ `make ci-gates` are structurally intended to provide.

## Cadence reset

**Next routine panel:** **v5.27.0** (5 minors past v5.22.0).

**Alternate trigger:** if 5 language-feature releases ship
before v5.27.0, the alternate cadence threshold fires earlier.
Both triggers were honored as overdue at v5.22.0; **must be
honored on schedule going forward** per Anaconda §1's
recommendation. Cadence enforcement gate (action item #13)
should land at v5.23.0 to prevent another silent skip.

---

## Sign-off

This panel certifies v5.22.0 as a healthy point release under
the v5-gate mechanical rule. The release ships. The next panel
(target: v5.27.0 routine cadence, or earlier if 5
language-feature releases land first) will verify:

1. Whether the v5.22.x docket items closed (Reg.1, Bo.18r,
   Bo.25, Te.3 hollow, V.9, manifesto, hollow-feature gate,
   docs-drift gate, `make ci-gates`, `__mn_indent_to_braces`
   header, v5.19.0 SR backfill, Sh.\* baseline labeling,
   `>= 45` magic, indent-preprocessor count refresh,
   Bo.22, Bo.26).
2. Whether the v5.23.0+ structural items landed
   (`check_doc_freshness.py`, cadence enforcement gate,
   Pk.1.A close, V.6/V.7/V.8 close, SPEC example corpus
   sweep, Coral L1–L5).
3. Whether the −0.21 → next-panel trend reverses (if the
   pattern continues at −0.2 / panel for two more cycles, the
   v5.32.0 panel would land at 9.0 — and at that point the
   framework would be clearing point releases on the wire of
   the rule, which is a different process state).

**Three consecutive panels with the same Bo.18r finding has
now occurred. A fourth-panel recurrence would warrant a
docs-and-CI recovery release in the spirit of v4.27.0–v4.31.0
even if the aggregate clears 9.0** — at that point the
framework would be ratifying a process regression rather than
catching it.

The discipline that produced the 13-release strict-fixed-point
streak is real; the discipline that produced the 5-release
silent CI-gate streak is the same project, on a different
surface. v5.22.x's job is to extend the former pattern to
the latter surface.

*La culebra está delgada y cómoda — pero el registro tiene
polvo, y el espejo de bronce está manchado en una esquina
que el barniz no llegó a alcanzar.*
