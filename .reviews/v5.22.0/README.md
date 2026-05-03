# v5.22.0 Panel — v5.13–v5.21 Terseness-Arc Health Gate

> Seven-reviewer panel reviewing the **v5.11.0 → v5.21.1** arc
> (16 releases — entire terseness arc Te.1–Te.6, Sh.* self-host
> rewrite, Mc.* tooling pack, Dk.* Docker, Te.5 struct
> ergonomics, Te.6 chained comparisons, plus v5.21.1 pre-panel
> hygiene). v5.22.0 is the panel-only release — zero compiler /
> runtime / dispatch edits.
>
> **Aggregate: 9.41 / 10. Decision: Option A (point-release
> health gate clears).** Third consecutive Option A under the
> v5-gate mechanical rule, but third consecutive panel
> micro-regression (9.66 → 9.62 → 9.41). The −0.21 Δ is driven
> by **process-discipline debt that the H.\* hygiene pass did
> not catch**: 3 silently-failing CI gates since v5.17.0
> (Anaconda HIGH, Cobra HIGH), Bo.18r open for the **third
> consecutive panel** (Boa HIGH), a new Bo.25 goldens-badge
> contradiction (Boa HIGH), and a Te.3 brace-deprecation gap
> on single-line shapes that the **PRE_PANEL_AUDIT's own
> pre-flight test command demonstrates** (Coral / Anaconda /
> Rattler all flagged, MEDIUM).

**Panel date:** 2026-05-01
**Aggregate: 9.41 / 10**
**Grade distribution: 5 EXCEEDS / 1 MEETS / 1 PASS-only**
(0 NEEDS WORK; verdicts: 1 PASS, 6 PASS WITH NOTES)
**Decision rule applied:** aggregate ≥ 9.0 AND 0 NEEDS WORK →
**Option A** (point-release health gate clears; no recovery
cycle opened).
**Δ vs prior panel (v5.11.0):** **−0.21** (9.62 → 9.41)

---

## Verdict Table

| # | Reviewer | Domain | Verdict | Score | Δ vs v5.11.0 | Top findings |
|---|---|---|---|---:|---:|---|
| 1 | [Rattler](01-rattler.md) | LLVM IR / codegen | **EXCEEDS** / PASS WITH NOTES | **9.85** | ±0.0 | Live-verified strict 3-stage fixed point at 238,086 / 0 diff (13-release streak — 2.6× the v5.11.0 5-release streak); zero new MIR ops / IR shapes across 10 releases; Te.6 once-evaluation verified in IR (1 `@middle` per chain instance). 1 NEW MEDIUM (Te.3 brace-warning misses single-line shape AND native `mnc-stage1` has zero brace-deprecation logic), 4 LOW (incl. missing `v5.19.0/SESSION_REPORT.md`, Sh.\* shrink baseline ~2.4pp high). |
| 2 | [Viper](02-viper.md) | Memory safety | **EXCEEDS** / PASS WITH NOTES | **9.7** | **−0.2** | Drop glue across 7 new AST nodes (Te.5 + Te.6 + Te.4 + Te.2) clean by construction — desugar to existing primitives, no new lifetime classes. Valgrind on `95_chained_cmp_side_effect.mn`: 0 leaks, 0 errors. v5.20.1 latent-bug fixes (alloca-void, TK_UNKNOWN demotion) verified. **1 NEW MEDIUM (V.9)** — `__mn_indent_to_braces` leaks the final `joined` MnString on every colon-syntax compile through `mnc-stage1`; bounded to single-shot but unbounded if embedded; missing tracked-output-string annotation on the `extern "C" fn` decl. V.6/V.7/V.8 still open (3rd cycle, cumulative −0.05 discipline drift). |
| 3 | [Anaconda](03-anaconda.md) | CI / testing / toolchain | **MEETS** / PASS WITH NOTES (bordering NEEDS WORK) | **8.4** | **−1.3** | **Three structurally-wired CI gates silently RED at HEAD**: `check_struct_registry.py` (23 violations, inert since v5.17.0 Sh.\* — regex hard-codes brace headers), `check_no_hollow_features.py` step 3 (2 violations on `CompClause` v5.15.0 + `FieldPattern` v5.20.0 — whitelist calibration miss), `check_docs_drift.py` (SPEC.md:1456 untyped param). **5 releases of registry blindness** during the largest feature-velocity arc in v5 history. Cadence skip (5-minor + 5-language-feature triggers both fired and skipped) docked −0.4. Pk.1.A still open across 11 releases. v5.19.0 SESSION_REPORT missing. |
| 4 | [Cobra](04-cobra.md) | Bootstrap / self-hosted | **EXCEEDS** / PASS WITH NOTES | **9.55** | **−0.15** | Strict 3-stage fixed point preserved at 238,086 / 0 diff — 13-release streak, longest in project history. Bootstrap mirror cross-tests all green (Te.5 12/12, Te.6 10/10, comp 10/10, interp 10/10, indent 201/201 — actual is 201, audit cited 142). v5.20.1 alloca-void + TK_UNKNOWN demotion fixes verified in `lower.mn`. **1 HIGH** (Reg.1 — same finding as Anaconda, independent surface), 1 MEDIUM (Sh.\* shrink baseline labeling — actual −11.5% off v5.13.0, not −13.9%; the headline measures pre-Sh.B-immediate). 3 LOW (`>=45` magic still open 3rd panel; `test_indent_preprocessor.py` count drift; let-else asymmetric closure). **Mea culpa:** per-PR fixed-point CI gate WAS already wired at v4.29.0; missed at v5.8.0/v5.11.0 reviews. CLOSED. |
| 5 | [Coral](05-coral.md) | Language design | **EXCEEDS** / PASS WITH NOTES | **9.55** | **+0.05** | Te.1–Te.6 compose without grammar churn beyond documented additive surface; SPEC reads top-to-bottom as a single language. 3 MEDIUM: **M1 Te.3 brace-warning hollow on single-line shape** (PRE_PANEL_AUDIT's own pre-flight demonstrates the gap), **M2 manifesto coherence** ("Curly braces for blocks" line untouched against brace-deprecated codebase — 3rd consecutive panel of manifesto drift), **M3 SPEC example corpus 72% brace-style** against colon-canonical SPEC. Hygiene-via-release vs hygiene-at-source: **the lead's pattern works (v5.7.1, v5.21.1 closed cleanly) but ceiling-effects at 9.55–9.66**; recommends `scripts/check_doc_freshness.py` CI gate as the structural fix. SPEC re-sync MEDIUM from v5.11.0 fully closed. |
| 6 | [Boa](06-boa.md) | Documentation / DX | **EXCEEDS** / PASS WITH NOTES | **9.0** | **+0.1** | v5.21.1 H.\* closures honored: Bo.21 version badges STAYS CLOSED, Bo.17r localized READMEs CLOSED structurally (~80%), H.6 SPEC §4.0 Te.3 rewrite gorgeous, H.7 broken-promise rescope honest, H.4 chained_cmp example beautiful. **2 HIGH**: **Bo.18r STILL OPEN — third consecutive panel** (`README.md:188-192` benchmarks paragraph still v5.7.1-vintage "NEAR / 4-line VERSION-metadata diff over a 217k-line stage2.ll / 5,720+ tests"; H.1 closed the *sibling* line 176, walked past the actual paragraph), **NEW Bo.25 goldens badge stuck at 66/66** across all four READMEs while body says 95/95. 1 MEDIUM (Bo.22 `mapanare run` vs `mnc run` — 2nd consecutive panel). 4 LOW. **Process observation (Bo.27)**: PRE_PANEL_AUDIT.md should add a "Closes prior-panel finding" cross-reference column — that one process change would have caught Bo.18r persistence. |
| 7 | [Mamba](07-mamba.md) | C runtime / performance | **EXCEEDS** / **PASS** | **9.85** | **+0.05** | C runtime delta v5.11.0 → v5.22.0: **+553 lines** across 10 releases. Two new exports (`__mn_assert_fail` v5.13.1, 8 LOC; `__mn_indent_to_braces` v5.14.1, ~545 LOC) — lead's "zero new runtime function additions" claim is off by two but both honestly documented. Te.6 desugar emits zero new runtime calls; `__mn_chain_N` are stack `alloca`s — verified in IR (1× `@middle(`, 5× `__mn_chain_0` SSA refs, all stack-resident). Pe.1 trajectory re-pressurized: +5.07% over 10 releases vs predicted +1.7% — honest growth from bootstrap-side AST additions, not a v6.0 budget concern. 3 LOW (`__mn_indent_to_braces` not declared in `.h`; "curve flattening" framing should be retired; O(line-count) allocs in indent preprocessor). |
| | **Aggregate** | — | **Option A** | **9.41** | **−0.21** | — |

Score trajectory (last 12 panels):
6.59 → 7.87 → 8.21 → 8.21 → 8.80 → 8.86 → 9.21 → 9.37 → 9.30 →
9.66 → 9.62 → **9.41**.

---

## Overall Team Consensus

**PASS for v5.22.0 as a point release** — the mechanical rule
fires verbatim (9.41 ≥ 9.0; 0 NEEDS WORK). Six of seven
reviewers came in either flat-or-positive on their individual
axes (Rattler ±0.0, Viper −0.2, Cobra −0.15, Coral +0.05,
Boa +0.1, Mamba +0.05); the load-bearing −1.3 from Anaconda
is the −0.21 aggregate drag.

The **headline correctness signal is exemplary**: strict 3-stage
fixed point preserved at 238,086 lines / 0-line diff across
**13 consecutive shipping releases** (longest streak in project
history; 2.6× the v5.11.0 5-release streak). Six additive
language features absorbed (Te.1 colon-block, Te.2
comprehensions / lambda / implicit-return, Te.3 `{}`
soft-deprecation, Te.4 string-interp parity, Te.5 struct
ergonomics, Te.6 chained comparisons) with **zero new MIR ops,
zero new IR shapes, and only two new C-runtime exports**
(`__mn_assert_fail` 8 LOC + `__mn_indent_to_braces` 545 LOC,
both bootstrap-mirror plumbing, neither Te.\* surface).
Self-hosted compiler shrunk **−11.5%** off the v5.13.0 baseline
(net source delta) without breaking fixed point at any
per-module commit. Goldens 66/66 → 95/95. Bootstrap mirror
cross-tests all green: Te.5 12/12, Te.6 10/10, comp 10/10,
interp 10/10, indent-preprocessor 201/201.

**The drag is process discipline, not engineering.** The arc
graded shipped extraordinary feature velocity, but three
structurally-wired CI gates the project specifically built to
catch hollow-feature and metadata-drift regressions
(`check_struct_registry.py`, `check_no_hollow_features.py` step
3, `check_docs_drift.py`) have been **silently failing for the
entire Sh.\* arc** (5+ releases) without surfacing in any
pre-release checklist. The v5.21.1 pre-panel hygiene pass
specifically targeted the H.\* docs-surface drift class but did
NOT include a "structural CI gate status" fact-check, and the
panel discovered red gates on first run. This is the same shape
as the v5.11.0 Bo.21 / Bo.18r findings, repeated on a different
surface: the lead has internalized H.\*-style audits but the
audit blind spot is what isn't on the audit list.

**Boa's Bo.18r is open for the third consecutive panel.**
v5.21.1 H.1 closed `README.md:176` (the line the lead's audit
saw) but walked past `README.md:188-192` (the line the v5.11.0
panel review cited). Same shape as v5.9.2 Dn.1 → v5.11.0
Bo.18r. Three same-paragraph findings across consecutive panels
is not "the audit missed it again" — it is the **systematic
gap between H.\*-numbered (lead's self-audit) and Bo.\*-numbered
(panel docket) line references** that v5.21.1 PRE_PANEL_AUDIT.md
inherited and did not bridge.

**Te.3 brace-deprecation is partially hollow.** Three
independent reviewers (Coral M1, Anaconda §3, Rattler #1)
flagged it on first pre-flight: the **PRE_PANEL_AUDIT.md's own
canonical test command** (`echo 'fn main() { print("hi") }' >
/tmp/brace.mn; python3 -m mapanare emit-llvm ...`) does NOT
fire the warning the audit said it would. Detector at
`mapanare/parser.py::count_user_brace_block_openers` is
line-based — counts `{` only at end-of-line — so the
all-on-one-line shape silently bypasses the deprecation. AND
the native `mnc-stage1` has **zero brace-deprecation logic at
all** (`grep MAPANARE_NO_BRACE_WARNING mapanare/self/*.mn`
returns zero hits). This is hollow-feature class
(SPEC §27 deprecation cycle requires the warning to fire on
every brace shape across both compilers across the 2-release
soak window). The fix is straightforward; the gap is that the
lead's own pre-flight test was wrong about it.

The interpretation is unambiguous: **v5.22.0 the release ships
Option A; v5.22.0 the audit-and-gate discipline that produced
v5.21.1 hygiene is the surface that needs structural follow-up.**

---

## Post-Production Health Gate

**YES, conditional.** The codebase is healthier than at v5.11.0
on every correctness axis the lead claimed it would be (13
fixed-point releases vs 5; 95/95 goldens vs 66/66; six
additive features absorbed; self-host shrunk; runtime delta
≈ flat). The conditions are process discipline, not code:

1. **Reg.1 (HIGH, Anaconda + Cobra)** — `check_struct_registry.py`
   regex must accept colon-form headers AND every flagged
   drift-after-restore must be investigated. Inert for 5
   releases is worse than no gate. Must close before v5.23.0
   feature work.
2. **Bo.18r (HIGH, Boa, 3rd consecutive panel)** — README:188-192
   benchmarks paragraph rewrite. 3-minute fix; pattern is now
   long-running. Must close at v5.22.x.
3. **Bo.25 (HIGH, Boa, NEW)** — Goldens badge 66/66 → 95/95
   across all four READMEs. 1-minute one-shot fix; structural
   fix is to extend `bump_version.py` to auto-discover the
   goldens count.
4. **Te.3 hollow-surface (MEDIUM, Coral M1 + Anaconda + Rattler)**
   — `count_user_brace_block_openers` token-walk + bootstrap
   mirror. Must close before v6.0 hard removal.
5. **Coral's hygiene-at-source recommendation (MEDIUM, structural)**
   — `scripts/check_doc_freshness.py` CI gate as the structural
   prevention for the H.\* / Bo.\* drift class. Same docket as
   v5.11.0 panel's "Do.\*" recommendation; still not landed.

These are the v5.22.0 panel's **action items for v5.23.0+**.
None gates the v5.22.0 release itself — but a fourth-panel
recurrence of Bo.18r, or a sixth release of silent Reg.1 gate
inertness, would warrant a docs-and-CI recovery release in the
spirit of v4.27.0–v4.31.0.

---

## Prioritized Action Items (deduplicated, with effort)

| # | Severity | Item | Reported by | Effort | Target |
|---|---|---|---|---|---|
| 1 | HIGH | **Reg.1** — Extend `check_struct_registry.py` `STRUCT_HEADER_RE` regex to accept `struct Name:` colon-form. Then re-run gate against `mapanare/self/*.mn` HEAD; investigate every flagged drift (5 releases of blind window — expect non-zero count post-restore, per v4.143.0 retrospective precedent). | Anaconda §2.A, Cobra #1 | 2h | v5.22.x |
| 2 | HIGH | **Bo.18r** — Rewrite `README.md:188-192` benchmarks-section lead-in paragraph. Replace v5.7.1-vintage NEAR / 217k / 5,720+ language with rounded "238k / 13-release strict streak / 5,800+" framing. Closes Bo.18r + Bo.19 + Bo.20 in one keystroke. **3rd consecutive panel.** | Boa #1 | 3 min | v5.22.x |
| 3 | HIGH | **Bo.25** — Goldens badge `66/66` → `95/95` across `README.md`, `docs/README.es.md`, `docs/README.pt.md`, `docs/README.zh-CN.md`. Structural fix: extend `scripts/bump_version.py` to auto-discover `tests/golden/*.mn` count and update the badge in lockstep with the version badge. | Boa #2 | 1 min one-shot, 10 min structural | v5.22.x |
| 4 | MEDIUM | **Te.3 hollow** — Fix `count_user_brace_block_openers` to scan tokens (or any-position `{`) rather than end-of-line; mirror the detector in `mapanare/self/parser.mn` (~50 LOC) so `mnc-stage1` also fires the warning. Add a regression test for the all-on-one-line shape. Update PRE_PANEL_AUDIT.md test command to actually demonstrate the warning. | Coral M1, Anaconda §3, Rattler #1 | 2-4h | v5.22.x (before v6.0) |
| 5 | MEDIUM | **`check_no_hollow_features.py`** step 3 — add `CompClause` (v5.15.0 Te.2) and `FieldPattern` (v5.20.0 Te.5.D) to `_AST_INFRASTRUCTURE` whitelist. | Anaconda §2.B | 5 min | v5.22.x |
| 6 | MEDIUM | **V.9** — Fix `__mn_indent_to_braces` returned-MnString leak via tracked-output-string annotation in `mapanare/self/parser.mn`. Add CI gate at `.github/workflows/sanitizers.yml`: valgrind `mnc-stage1 emit-llvm <colon-syntax-golden>.mn`, fail on non-zero leak exit. **Mandatory regression test**, the byte-identical oracle cannot detect lifecycle issues. | Viper V.9 | 1-2h | v5.22.x |
| 7 | MEDIUM | **Bo.22** — README Hello World + Write-Python-Compile-Native sections: `mapanare run` → `mnc run`, `mapanare init` → `mnc init`, `mapanare check` → `mnc check`, `mapanare lsp` → `mnc lsp`. Add `mapanare` alias note parenthetically. **2nd consecutive panel.** | Boa #3 | 5 min | v5.22.x |
| 8 | MEDIUM | **Manifesto coherence (M2)** — `docs/manifesto.md:31` "Curly braces for blocks" line must be re-written. Either two-line edit ("Indented blocks (with brace-form legacy through v6.0)") or drop the line entirely and let SPEC be the canonical syntax description. **3rd consecutive panel of manifesto drift.** | Coral M2 | 5 min | v5.22.x |
| 9 | MEDIUM | **SPEC example corpus (M3)** — `mnc fmt --to-terse` over `docs/SPEC.md`. 26 of 36 block-openers are still brace-style against §4.0 declaring colon-canonical. Preserve any historical-artifact examples (Chapter 27 stability discussion). | Coral M3 | 30 min | v5.23.0 |
| 10 | MEDIUM | **`check_docs_drift.py`** — close SPEC.md:1456 violation (`fn id(y) = y` doesn't parse — untyped param). Annotate `y: Int` or add `<!-- pseudo -->` opt-out marker. | Anaconda §2.C | 1 min | v5.22.x |
| 11 | MEDIUM | **Process structural fix (Coral)** — Add `scripts/check_doc_freshness.py` CI gate. Closes the H.\* / Bo.\* drift class structurally. Same docket as v5.11.0 panel's "Do.\*" recommendation, still not landed. | Coral, Boa Bo.27 | 2-4h | v5.23.0 |
| 12 | MEDIUM | **Process structural fix (Anaconda)** — Add `make ci-gates` Makefile target running the full CI gate inventory locally as a single command. Pre-release checklist shrinks to "run `make ci-gates`; expect zero violations." Eliminates the wired-but-unchecked failure mode. | Anaconda §2.D | 30 min | v5.22.x |
| 13 | LOW | **Cadence enforcement** — Add a CI gate (or pre-release script) that fires when ≥5 minor versions OR ≥5 language-feature releases have shipped without a panel. v5.16.0 + v5.20.0 cadence triggers fired and were skipped. | Anaconda §1 | 1h | v5.23.0 |
| 14 | LOW | **Sh.\* baseline labeling** — Normalize all v5.17.x SESSION_REPORTs / CARRY_FORWARD.md / CLAUDE.md preamble references to either "−3,988 lines (−13.9%) off pre-Sh.B-immediate baseline" OR "−2,285 lines (−8.18%) net v5.13.0 → v5.21.1". Both are honest; current labels are not. | Cobra #2, Rattler #4 | 30 min | v5.22.x |
| 15 | LOW | **Bo.27** — PRE_PANEL_AUDIT.md gains a "Closes prior-panel finding" cross-reference column at the next pre-panel audit (v5.27.0). Binds H.\* hygiene findings to Bo.\*/V.\*/Co.\*/etc. panel-history IDs. Process observation behind the H.\*-vs-Bo.\* mismatch driving Bo.18r persistence. | Boa #6 | 5 min per audit | v5.27.0 |
| 16 | LOW | **`__mn_indent_to_braces`** missing from `mapanare_core.h` (defined `MN_EXPORT` but no public-API header decl). Add the prototype; closes .h ↔ .c asymmetry. | Mamba #1 | 1 min | v5.22.x |
| 17 | LOW | **Pk.1.A** — Linux/macOS versioned-tarball smoke gates. v5.13.0 alias-drop deadline cited in 6 written locations did not ship. **Open across 11 releases.** | Anaconda §4 | 1h | v5.23.0 |
| 18 | LOW | **v5.19.0 SESSION_REPORT** — write the missing report retroactively (3 commits in log: Te.3.A/B/C/D/E + scope-split). Even brief is fine. | Rattler #2, Anaconda LOW | 1h | v5.22.x |
| 19 | LOW | **`>=45` magic-number** — replace with self-evident formula tracking corpus growth. **3rd panel ask.** | Cobra #3 | 30 min | v5.22.x |
| 20 | LOW | **`tests/bootstrap/test_indent_preprocessor.py` count** — audit cites 142, actual is 201. Refresh PRE_PANEL_AUDIT.md and CARRY_FORWARD.md. | Cobra #4 | 5 min | v5.22.x |
| 21 | LOW | **V.6 / V.7 / V.8** — DX.4 walkers unbounded recursion + Win32 reparse-point loop + no ASan/valgrind sweep on v5.10.0+ deltas. **All open across 3 panels.** Cumulative −0.05 discipline drift. | Viper V.6/V.7/V.8 | 4h | v5.23.0 |
| 22 | LOW | **Stage2-binary teardown crash (RC=3)** — papered over by `set +e` in `verify_fixed_point.sh`. **70+ releases stale** since v4.30.0 PLAN. | Rattler #5, carry-forward | 4h | v6.0 cleanup window |
| 23 | LOW | **L2 / L3 / L4 / L5 / TR1** — SPEC §27 deprecation crosslink, broken-promise wording, `mnc fmt` flag mention, generic-bound trait sketch, examples directory micro-organization. | Coral L1-L5 | 1h total | v5.23.0+ |
| 24 | LOW | **Bo.26** — `docs/guides/formatter.md` and `docs/guides/init.md` not linked from any README or SPEC. 3-min fix. | Boa #5 | 3 min | v5.22.x |

---

## Disagreements

The panel surfaced **three notable spreads ≥ 0.3** on the same axis:

1. **Process / CI discipline:** Anaconda 8.4 vs Cobra 9.55 (1.15 spread). Both cite the same Reg.1 finding (HIGH on both reviews), but Anaconda weights it as part of a broader 3-gate-failure pattern (`check_struct_registry.py` + `check_no_hollow_features.py` + `check_docs_drift.py` + cadence skip) and docks more heavily; Cobra treats it as one HIGH item against an otherwise exemplary bootstrap-axis arc. **The panel agrees with Anaconda's framing on the structural shape (3 silent gates is a process regression, not 1 fix item)** but with Cobra's framing on individual severity (release ships; blast radius is bounded by the byte-identity check that did NOT fail).

2. **Documentation-surface drift severity:** Boa 9.0 (with 2 HIGH) vs Coral 9.55 (with 3 MEDIUM). Same surface (manifesto, README, SPEC examples), different weighting. **Boa's HIGH on Bo.18r persistence reflects "third consecutive panel of the same paragraph" as a category-of-finding signal**; Coral's MEDIUM on M2 manifesto reflects "single-line edit in a low-traffic file." Both are right; the spread reflects the difference between "user lands on README" surface (Boa axis) and "user reads the manifesto by choice" surface (Coral axis).

3. **C-runtime delta:** Mamba 9.85 (PASS only — no NOTES) vs Viper 9.7 (MEDIUM V.9 leak). Mamba audited the byte count (+553 lines, "no Te.\* surface", honest growth) and signed off; Viper ran valgrind and found a tracked-string-annotation gap that produces a per-compile leak that scales linearly with input size. Both findings are mutually consistent — the byte count *is* honest; the lifecycle annotation *is* missing — but they emphasize different facets of "runtime hygiene." Score impact: Viper's V.9 (−0.1) lands; Mamba's "no Te.\* surface" (no deduction) also lands. **The panel's takeaway is V.9 deserves the v5.22.x landing.**

No reviewer dissented on the mechanical decision rule (all 7
verdicts compatible with Option A: 1 PASS + 6 PASS WITH NOTES,
0 NEEDS WORK).

---

## Improvements Since v5.11.0 Panel

**Correctness axis (Rattler / Cobra / Mamba):**
- Strict 3-stage fixed-point streak: 5 → 13 releases (longest in project history).
- Goldens: 66/66 → 95/95.
- New MIR ops across 10 releases: 0.
- New IR shapes across 10 releases: 0.
- New runtime function additions across 10 releases: 2 (`__mn_assert_fail` 8 LOC + `__mn_indent_to_braces` 545 LOC; both bootstrap-mirror plumbing).
- Te.6 once-evaluation: verified in IR, byte-identity preserved on single-comparison shapes (D6).
- v5.20.1 latent-bug fixes (alloca-void, TK_UNKNOWN demotion): in scope, fixed cleanly.

**Memory safety axis (Viper):**
- Drop glue across 7 new AST nodes: clean by construction.
- Valgrind on `95_chained_cmp_side_effect.mn`: 0 leaks, 0 errors.
- Own.1 P2 / Ve.1–4 / Lk.1: all CLOSED, all stay closed.
- Rt.04: still correctly RESCOPED to v6.0.

**Language design axis (Coral):**
- SPEC re-sync MEDIUM from v5.11.0: fully closed at v5.21.1 H.\* (Coral gives back the −0.10 dock).
- Six additive features absorbed without grammar churn beyond documented additive surface.
- Te.5 SPEC §3.7 + Te.6 SPEC §2.2 + Te.3 SPEC §4.0 read as a single coherent terseness story.

**Documentation axis (Boa):**
- Bo.21 (version badges HIGH): CLOSED at v5.21.1 H.1, STAYS CLOSED.
- Bo.17r (localized READMEs MEDIUM): CLOSED structurally at v5.21.1 H.3 (~80%).
- H.6 SPEC §4.0 Te.3 rewrite: gorgeous (3 paragraphs covering colon-canonical / brace-deprecated / warning-shape / opt-out / fmt flag).
- H.7 broken-promise rescope: honest (deferred to v6.0 with rationale).
- New `examples/chained_cmp.mn`: 30-line, exercises 3-/4-/once-eval.

**Process axis:**
- v5.21.1 hygiene release as a panel pre-flight: same posture as v5.7.1 → v5.8.0 (project-record 9.66 panel).
- Per-PR fixed-point CI gate: confirmed wired since v4.29.0 (Cobra mea culpa from v5.8.0 / v5.11.0).
- bump_version.py sweep: load-bearing for the version-badge close.

---

## Regressions Since v5.11.0 Panel

**Process discipline (Anaconda −1.3, the load-bearing regression):**
- 3 structural CI gates silently RED at HEAD across the entire Sh.\* arc (5+ releases): `check_struct_registry.py`, `check_no_hollow_features.py` step 3, `check_docs_drift.py`.
- Cadence: 5-minor (v5.16.0) AND 5-language-feature (v5.20.0) triggers both fired and were not honored at the trigger; documented as overdue but not run on schedule.
- Pk.1.A: 11 releases of carry-forward without close. v5.13.0 alias-drop deadline cited in 6 written locations did not ship.
- v5.19.0 SESSION_REPORT: missing on disk despite Te.3 having shipped (3 commits in log).

**Docs-surface (Boa, persistence):**
- Bo.18r: README:188-192 benchmarks paragraph still v5.7.1-vintage. **3rd consecutive panel.** Same paragraph, same fix shape, three releases of escalation.
- Bo.25 (NEW): Goldens badge `66/66` across all four READMEs while body says `95/95`. Same systematic-skill-gap shape as v5.11.0 Bo.21.
- Bo.22: `mapanare run` vs `mnc run` in README Hello World. **2nd consecutive panel.**
- Manifesto coherence: "Curly braces for blocks" untouched against brace-deprecated codebase. **3rd consecutive panel of manifesto drift** (Coral).

**Memory hygiene:**
- V.6 / V.7 / V.8: open across 3 panels (DX.4 walkers + Win32 reparse-point + no sanitizer sweep). Cumulative −0.05 discipline drift.
- V.9 (NEW): `__mn_indent_to_braces` MnString leak on every colon-syntax compile. The byte-identical oracle (`test_indent_preprocessor.py`) cannot detect lifecycle issues — a class blind spot.

**Hollow-feature surface:**
- Te.3 brace-deprecation gap on single-line shape: PRE_PANEL_AUDIT's own pre-flight test command demonstrates the gap. Three independent reviewers flagged it (Coral, Anaconda, Rattler).
- Native `mnc-stage1` has zero brace-deprecation logic: **asymmetric closure** vs Python (PY: closed | SH: open). Should have been tracked per `.reviews/CARRY_FORWARD.md` dual-closure convention.

---

## Decision

**Option A — point-release health gate clears.**

Mechanical rule applied:
> Aggregate **9.41 ≥ 9.0** ✅
> **0 NEEDS WORK** verdicts ✅
> → Option A.

**This is the third consecutive Option A** under the v5-gate
mechanical rule (v5.7.1: 9.66; v5.11.0: 9.62; v5.22.0: 9.41).
The aggregate trended down −0.04 → −0.21 across the three
panels — the framework continues to clear releases that ship
healthy, but the trend is a process-discipline signal, not a
correctness signal.

**No recovery cycle is opened.** The action items in the
prioritized table above constitute the v5.23.0+ docket, with
HIGH items targeted to v5.22.x (Reg.1, Bo.18r, Bo.25) before
new feature work resumes.

**Cadence reset:** next routine panel due at **v5.27.0** (5
minors past v5.22.0). If 5 language-feature releases ship
before v5.27.0, the alternate cadence trigger fires earlier;
both triggers were honored as overdue at v5.22.0 and must be
honored on schedule going forward.

See [V5_DECISION.md](V5_DECISION.md) for the formal Option A
text.

---

## Evidence

**Live verification at v5.22.0 HEAD (commit `24d5be7`):**
- `bash scripts/verify_fixed_point.sh --keep` → stage2.ll == stage3.ll, **238086 lines, 0 diff**.
- `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1` → **All 95 tests passed** in 18.2s.
- `python3 -m pytest tests/bootstrap/test_te5_mirror.py tests/bootstrap/test_chained_cmp_mirror.py tests/bootstrap/test_string_interp_mirror.py tests/bootstrap/test_comprehension_mirror.py tests/bootstrap/test_indent_preprocessor.py -v` → **243 passed in 59s** (Te.5 12, Te.6 10, comp 10, interp 10, indent 201).
- `bash scripts/build_from_seed.sh` → clean, mnc binary produced (5,421,552 bytes).
- `make lint` → ruff + black + mypy clean, 56 source files.
- `python3 scripts/check_changelog_honesty.py` → clean for `[5.21.1]`.
- Goldens badge / README contradiction: `grep -nE "goldens-[0-9]+|95/95 native goldens" README.md docs/README.{es,pt,zh-CN}.md` → 4× `goldens-66%2F66`, 4× body `95/95`.
- Te.3 single-line gap: `echo 'fn main() { print("hi") }' > /tmp/brace.mn; python3 -m mapanare emit-llvm /tmp/brace.mn 2>&1` → no warning fires.
- Reg.1: `python3 scripts/check_struct_registry.py; echo "exit: $?"` → **23 violations, exit 1**.
- Hollow-feature gate: `python3 scripts/check_no_hollow_features.py` → 2 violations (`CompClause`, `FieldPattern`).

**Reviewer outputs:**
- [01-rattler.md](01-rattler.md), [02-viper.md](02-viper.md), [03-anaconda.md](03-anaconda.md), [04-cobra.md](04-cobra.md), [05-coral.md](05-coral.md), [06-boa.md](06-boa.md), [07-mamba.md](07-mamba.md)

**Lead's pre-panel artifacts (v5.21.1 hygiene release):**
- [PRE_PANEL_AUDIT.md](PRE_PANEL_AUDIT.md) — 13 H.\* findings, all closed at v5.21.1 docs-surface; the panel verified the closures and surfaced 3 categories the audit missed (CI gate inertia; Bo.18r persistence on a different line than the audit cited; Te.3 hollow-surface that the audit's own pre-flight demonstrates).
- [prompt.md](prompt.md) — panel charter.
- `docs/roadmap/v5/v5.21.1/SESSION_REPORT.md` — Mc.7 closure narrative for the 12 H.\* findings.

**Prior panel:** [.reviews/v5.11.0/](../v5.11.0/) — 9.62/10, Option A, 1 HIGH, 3 MEDIUM, ~12 LOW.

---

*Panel run: 2026-05-01. 7 reviewers, 7 personalities, 7 axes,
7 verdicts. Aggregate 9.41/10 → Option A. Cadence reset to
v5.27.0. La culebra está delgada y cómoda — pero todavía debe
limpiar el polvo del registro.*
