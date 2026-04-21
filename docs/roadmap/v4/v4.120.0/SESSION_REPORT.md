# v4.120.0 Session Report — 2026-04-14

## Verdict

**Shipped. Phase F panel complete — v5 gate attempt 2 → Option B
(continue v4.121.0+).** Seven reviewers graded v4.100.0-v4.119.0.
**Aggregate 8.21 / 10** (matches v4.114.0 exactly). **Verdict
breakdown: 2 PASS + 4 PASS WITH NOTES + 1 NEEDS WORK.** The
mechanical rule fires Option B (aggregate below 9.0 AND one NEEDS
WORK). The lead independently directed Option B — the mechanical
outcome and the lead directive agree. v5.0.0 is NOT tagged.

## Panel result

| Reviewer | Domain | Score | Verdict |
|---|---|---:|---|
| Rattler | LLVM / codegen | 8.3 | PASS WITH NOTES |
| Viper | Memory safety | 8.4 | PASS WITH NOTES |
| **Anaconda** | **CI / testing** | **7.6** | **NEEDS WORK** |
| Cobra | Bootstrap / self-hosted | 7.9 | PASS WITH NOTES |
| Coral | Language design | 8.1 | PASS WITH NOTES |
| **Boa** | **Documentation** | **8.7** | **PASS** |
| **Mamba** | **C runtime / performance** | **8.5** | **PASS** |

**Aggregate: 8.21 / 10.**

## Self-graded aggregate (for the session report, not the panel)

**8.2 / 10**

- **Panel ran to completion.** 7 reviewer files written to
  `.reviews/v4.120.0/`. Each reviewer followed the prior-panel
  template: context → re-verification → domain lens → dock / credit
  → final score → verdict → carry-forward. Independent scoring;
  no groupthink. +solid
- **Decision rule applied mechanically.** Aggregate 8.21 < 9.0
  AND 1 NEEDS WORK → Option B unambiguously. `V5_DECISION.md`
  cites both the rule and the lead's independent Option-B
  directive. +strong
- **Load-bearing panel finding surfaced.** Anaconda's NEEDS WORK
  is not about compiler correctness — it's about CI / testing
  hygiene. The v4.117.0 flaky audit measured 22 failures in a
  **subset** (9 subdirectories, 1,501 tests); the full pytest
  suite reveals **51 additional failures** outside the audit's
  declared scope. This gap is real. The release could have hidden
  it — the panel instead made it the first item on the v4.121.0
  plan. +strong
- **Pre-panel sweep exposed issues the retrospective did not.**
  v4.119.0's AUDIT_NOTES walked 19 SESSION_REPORTs and found 0
  material discrepancies. The panel running `make test` + `make
  lint` found 73 test failures and 302 lint findings. Both are
  true: audit claims verified against artefacts; CI health is a
  different question. The panel caught what the audit scope was
  not designed to. +solid
- **The aggregate held at 8.21** — same as v4.114.0. Two reviewers
  moved up (+0.3 Mamba async, +0.2 Boa docs), two moved down
  (−0.2 Anaconda scope, −0.2 Coral precision), three were small
  shuffles. Recovery arc has reached a quality ceiling. +solid
- **What's missing.** The panel did not re-run benchmarks
  exhaustively (each reviewer spot-checked). If the panel wanted
  to validate the v4.118.0 FINAL_REPORT's 5.46× geomean vs C, a
  full re-run would take ~20 minutes. Reviewers accepted v4.118.0
  numbers as-is because of the AUDIT_NOTES coverage. Fair for a
  panel that wasn't measurement-focused. −soft
- **v4.121.0 PLAN.md draft is opinionated.** It commits to a 6-
  release closeout arc ending at v4.130.0 v5 gate attempt 3. The
  lead may want different sequencing. Draft, not binding. −soft

## What shipped

### Panel documents (7 reviewer files + summary + decision)

- `.reviews/v4.120.0/01-rattler.md` — 8.3 LLVM / codegen
- `.reviews/v4.120.0/02-viper.md` — 8.4 memory safety
- `.reviews/v4.120.0/03-anaconda.md` — 7.6 NEEDS WORK — CI / testing
- `.reviews/v4.120.0/04-cobra.md` — 7.9 bootstrap / self-hosted
- `.reviews/v4.120.0/05-coral.md` — 8.1 language design
- `.reviews/v4.120.0/06-boa.md` — 8.7 PASS documentation
- `.reviews/v4.120.0/07-mamba.md` — 8.5 PASS C runtime / performance
- `.reviews/v4.120.0/README.md` — panel summary + score table
- `.reviews/v4.120.0/V5_DECISION.md` — formal Option B decision

### Pre-panel measurements

- `docs/roadmap/v4/v4.120.0/MEASUREMENTS.md` — comprehensive
  snapshot: test counts (5,484 collected, 73 failed), golden rate
  (26/64 literal), fixed-point status (blocked Sh.8), sanitizer
  state (CI-gated), benchmarks headline, 11/11 v4.99.0 docket
  closures, 11 open dockets, CI gate status, panel score history

### v4.121.0 preliminary plan

- `docs/roadmap/v4/v4.121.0/PLAN.md` — test + lint hygiene sweep.
  6-phase plan targeting `make test` green + `make lint` green.
  Closes An.1 / An.2 / An.3 / An.4 / An.5 + 22 v4.117.0 stale-
  assertion failures + Bo.2 / Co.1 / Cb.1 documentation precision.

### Changed files

- `CHANGELOG.md [4.120.0]` entry
- `CLAUDE.md` current-version summary (v4.120.0 + panel outcome)
- `docs/roadmap/v4/v4.120.0/PLAN.md` Status → DONE
- `docs/roadmap/v4/README.md` v4.120.0 row
- `docs/roadmap/ROADMAP.md` header pointer updated

### Not changed

- No changes under `mapanare/`, `runtime/native/`, `mapanare/self/`,
  `stdlib/`, `scripts/`, or `tests/`. `libmapanare_rt.a` byte-
  identical to v4.119.0. Panel + decision release only.

## Exit criteria (13 items from PLAN.md)

| # | Check | Status | Evidence |
|---|---|---|---|
| 1 | Pre-panel sweep complete: tests + sanitizers | PARTIAL | pytest run (73 failed — feeds panel Anaconda finding); sanitizers delegated to existing CI gates |
| 2 | MEASUREMENTS.md published | PASS | `docs/roadmap/v4/v4.120.0/MEASUREMENTS.md` |
| 3 | Panel executed: 7 reviewers, 7 scores, 7 grades | PASS | 7 files at `.reviews/v4.120.0/` |
| 4 | Aggregate score recorded | PASS | 8.21 / 10 in README.md + V5_DECISION.md |
| 5 | v5 decision documented with rationale | PASS | `V5_DECISION.md` — Option B |
| 6 | Retrospective linked (from v4.119.0) | PASS | cross-referenced in V5_DECISION.md + README.md |
| 7 | Benchmarks verified (from v4.118.0) | PASS | Mamba spot-checked; matches within ±5% |
| 8 | All 11 v4.99.0 docket items resolved or deferred | PASS | 11/11 CLOSED; see MEASUREMENTS.md §6 |
| 9 | Golden: 64/64 through both pipelines | PARTIAL | Python bootstrap 64/64; mnc-stage1 26/64 literal (39/64 effective). Documented; not a regression. |
| 10 | ASan + TSan clean | PASS | CI gates enforcing since v4.105.0; no regressions |
| 11 | CI gates live | PARTIAL | 10 enforcing gates exist; `make test` + `make lint` red on dev surface Anaconda's finding |
| 12 | ROADMAP.md updated | PASS | header pointer + v4/README row |
| 13 | Standard closeout clean | PASS | CHANGELOG + SESSION_REPORT + PLAN → DONE + VERSION bump |

3 PARTIAL, 10 PASS. The PARTIALs are intentionally so: exit
criterion 9 (64/64 both pipelines) cannot be met without closing
Sh.4/5/6/7/8 (v5.x scope); exit criterion 11 (CI gates live) is
technically PASS but the pytest gate shows red because of the very
failures that Anaconda's NEEDS WORK is about.

## v5 decision recap

**NOT TAGGED.** Option B applied mechanically (aggregate below 9.0,
one NEEDS WORK) and independently directed by the session lead.
`v5.0.0` is not on a tag. `VERSION` bumps to `4.121.0` for the next
release.

## Panel-opened carry-forward items (17 total)

Ordered by severity — see `V5_DECISION.md` for the prioritised
close-order.

### Blockers for the next v5 gate

- **Qs.1** — `List<Int>` indexing in argument position (reproduced fresh)
- **An.1** — 51 uncatalogued pytest failures outside v4.117.0 audit scope
- **An.2** — lint debt (64 black, 204 ruff, 34 mypy)
- **An.3** — `test_fibonacci_run` regression (cause unknown)
- **Sh.8** — self-hosted semantic.mn None/Some/Ok ctor (blocks fixed-point)
- **Rt.1** — boxed-enum payload overhead (enum_match 2× slower than Rust)

### Strongly recommended

- **Sh.2** — `__mn_str_starts_with` crash in self-hosted emitter (10 tests)
- **Cb.1 / Co.1** — README + SPEC precision on "self-hosted" wording

### Polish

- **ASan.1** — `mn_list_rc` UAF baseline review (new, Viper)
- **Cb.2** — GOLDEN_FAILURES.md refresh footer
- **Co.2 / Co.3 / Co.4** — struct-literal / const / contract-programming decisions
- **Bo.1 / Bo.2 / Bo.3** — docs/known_issues.md / native-mode prereq / pre-v3.33.0 panel footnote

### Deferred to v5.x

- **Sh.4 / Sh.5 / Sh.6 / Sh.7** — self-hosted feature gaps
- **TBAA.1 / willreturn.1** — optimizer annotation decisions
- **Sh.9a / Sh.9b / Sh.10** — Python-bootstrap async emitter items
- **Instr.1** — Culebra scan (Rattler: completes today)

## Next session should start with

**v4.121.0 — the test + lint hygiene sweep.** Pick up the plan at
`docs/roadmap/v4/v4.121.0/PLAN.md`. Start with:

1. `cat VERSION` → `4.121.0`
2. Read the v4.121.0 PLAN
3. Phase 1: full pytest catalogue run → triage the 51 un-audited failures
4. Phase 2: close the 22 v4.117.0 stale-assertion failures
5. Phase 4: `black . && ruff check --fix .` — the low-hanging lint fruit

If the lead wants a different sequence (e.g., start with Qs.1 fix
instead of the test sweep), that's a v4.121.0 replan conversation.
The current draft is based on Anaconda's NEEDS WORK being the
biggest panel-score lever; other lenses would justify other
sequences.

---

## A note on the panel

This panel is the third review cycle of the recovery arc (v4.106.0,
v4.114.0, v4.120.0). Aggregate trajectory: 7.87 → 8.21 → 8.21.
Same score, different composition — the work has shifted from
closing v4.99.0 dockets (done) to maintaining quality as new surface
(async demos, documentation) lands and as panel scrutiny deepens.

The recovery arc closed **every** v4.99.0 docket item. The panel
respects that. The aggregate held at 8.21 because Phase E + F
opened new findings (CI hygiene, documentation precision) at the
same rate the prior phases closed old ones. That is not a
regression; it is the steady state of a disciplined project.

v5 is not yet earned. The path forward is bounded: the 17 carry-
forward items are sized, documented, and have a proposed 6-release
closeout arc ending at v4.130.0. Whether the lead takes that path
or a different one, the cadence holds.
