# v4.114.0 Session Report — 2026-04-14

## Verdict

**Shipped. Phase D panel returned NEEDS WORK.** Aggregate 8.21/10,
below the Phase D PASS threshold of 8.5. Zero NEEDS WORK verdicts,
two PASS (Viper, Boa), five PASS WITH NOTES. Every reviewer who
moved vs v4.106.0 moved up. The gap is 0.29; the direction is
positive; the docket is genuinely empty (11/11 v4.99.0 items
CLOSED with evidence).

**v4.114.1 opens as a patch release** addressing the two HIGH
findings (v4.112.0 release-name accuracy; commit the byref test
case) plus one LOW comment fix. Phase D does not close until the
delta panel at v4.114.1 confirms.

Phase E remains unblocked pending the patch.

## Self-graded aggregate

**7.9 / 10**

- **Panel execution was disciplined.** 7 reviewers ran in a single
  session with PRE_PANEL_AUDIT, MEASUREMENTS, DOCKET_AUDIT as
  inputs. Every reviewer had concrete artifacts to grade; no
  reviewer had to reverse-engineer claims from SESSION_REPORTs
  alone. +solid
- **PRE_PANEL_AUDIT caught real overstatements.** The v4.112.0
  release-name issue is a real finding that reviewers then
  independently surfaced (Rattler + Cobra). Writing the audit
  before spawning reviewers worked as designed — the panel didn't
  grade marketing, it graded reality. +solid
- **Aggregate fell short of 8.5.** The decision rule applies
  mechanically: 8.21 < 8.5 = NEEDS WORK. I could have gamed this
  by calibrating scores higher, but that defeats the purpose of
  the panel. The honest number is the right one. Phase D doesn't
  get to self-certify. +accepted as hard truth
- **v4.114.1 scope is small and targeted.** Two doc fixes + one
  test commit + one comment. Not a structural recovery release.
  The distinction between 8.21 and 8.5 is a 50-line patch, not a
  multi-release restructure. +solid
- **Culebra scan gap persisting three panels is a real
  instrumentation debt.** Every panel I've grade has hit this
  wall. Phase E needs to own it. −soft

## What shipped

### Panel artifacts (production)

- `docs/roadmap/v4/v4.114.0/MEASUREMENTS.md` — 9-section
  quantitative pre-panel input: golden rates both pipelines,
  fixed-point status, stage2, valgrind/ASan results, 11-item docket
  closure table, test collection + self-hosted line count,
  hardcoded-offset audit, Phase D diff summary.
- `docs/roadmap/v4/v4.114.0/DOCKET_AUDIT.md` — line-by-line
  verification of all 11 v4.99.0 docket items with file:line
  code-change references, test coverage per item, regression
  status. 11/11 CLOSED.
- `docs/roadmap/v4/v4.114.0/artifacts/sweep.log` —
  pre-panel sweep raw facts.
- `docs/roadmap/v4/v4.114.0/artifacts/valgrind.log` — async
  golden valgrind output.
- `docs/roadmap/v4/v4.114.0/artifacts/asan.log` — async +
  struct subset ASan output.
- `.reviews/v4.114.0/PRE_PANEL_AUDIT.md` — fact-check of 19
  claims across v4.111.0-v4.113.0 SESSION_REPORTs.
- `.reviews/v4.114.0/01-rattler.md` through `07-mamba.md` — 7
  reviewer perspectives, ~1000 lines total.
- `.reviews/v4.114.0/README.md` — panel verdict table, decision
  rule application, findings for v4.114.1 + Phase E.
- `.reviews/v4.114.0/culebra_summary.md` — documents the
  854K-line scan gap.
- `.reviews/v4.114.0/phase_d_journal.jsonl` — Phase D culebra
  milestones.
- `.reviews/prompt.md` retargeted to v4.114.0 framing.

### Zero code changes

Panel release. Nothing under `mapanare/`, `runtime/`, `tests/` was
modified beyond the standard `BENCHMARKS*.md` / `HISTORY.jsonl`
auto-regeneration from running `scripts/test_native.py`.

## Panel results — headline

| Reviewer | Score | Primary finding |
|---|---:|---|
| Rattler | 8.2 | v4.112.0 release name overclaims; byref fix itself is clean |
| Viper | **8.5** | Coroutine frame fix does what I asked; byte-for-byte memory-neutral verified |
| Anaconda | 7.8 | Self-hosted CI gate still missing; fixed-point CI red |
| Cobra | 8.0 | Byref fix algorithm matches Python; commit `/tmp/byref_test.mn` |
| Coral | 8.3 | SPEC §2.1.1 clean; Sh.4-Sh.7 self-hosted feature gaps for Phase E |
| Boa | **8.5** | Async error messages specific and actionable; site 2 verified |
| Mamba | 8.2 | Runtime ABI stable; comment site 4 cleanup intent |

Aggregate 8.21. Decision: NEEDS WORK per aggregate < 8.5 rule.

## Exit criteria (11 items)

| # | Check | Status |
|---|---|---|
| 1 | `make test` passes | PASS-ish (63 pre-existing failures, 0 new) |
| 2 | Golden 64/64 through Python bootstrap | 63/64 (pre-existing `51_match_guards_and_or`) |
| 3 | Golden pass count through self-hosted recorded | 26/64 recorded |
| 4 | Fixed-point verification result recorded | Blocked at Stage 1 (Sh.8) — recorded |
| 5 | Valgrind clean on async + coroutine goldens | 0 errors / 0 contexts |
| 6 | ASan clean on golden subset | 0 errors on all tested binaries |
| 7 | `MEASUREMENTS.md` written | yes |
| 8 | Docket #1-#11 verified | 11/11 CLOSED with evidence |
| 9 | `PRE_PANEL_AUDIT.md` written | yes |
| 10 | Panel prompt retargeted + 7 reviewer files | yes |
| 11 | Panel aggregate in `.reviews/v4.114.0/README.md` | 8.21 recorded |

## v4.114.1 patch scope (HIGH + LOW findings only)

1. **Doc fix (R1, Cb1):** update CLAUDE.md and
   `docs/roadmap/v4/README.md` v4.112.0 row to name the release as
   "divergence analysis + byref fix" rather than "fixed-point
   verification." Leave SESSION_REPORT.md (which was honest) as-is.
2. **Test commit (Cb1):** add `tests/bootstrap/byref_test.mn` or
   `tests/golden/65_byref_sizing.mn` reproducing the v4.112.0
   acceptance case (16-byte `Small` by value vs 80-byte `Large` by
   reference).
3. **Code comment (M1):** add `/* exit(1) below reclaims the frame */`
   in `mapanare_runtime.c` at the site-4 (`__mn_coro_register_wait`
   overflow) bail path.

Estimated scope: 50 lines across 4 files. Delta panel (Rattler +
Cobra + Anaconda) re-grades after patch. If aggregate clears 8.5
on that delta, Phase D closes.

## Phase E deferred items

| ID | Owner | Description |
|---|---|---|
| A.1 | toolchain | Self-hosted pipeline CI gate (carry-forward v4.106.0) |
| A.2 | toolchain | Fixed-point CI gate — either close Sh.8 or document gate absence |
| B.1 | DX | Env-var based mocking for async error-site reachability tests |
| Co.1 | runtime | Pre-existing user-code coroutine leaks in 56/57 |
| Sh.1-Sh.8 | self-hosted | Self-hosted emitter feature parity |
| Instr.1 | tooling | Culebra scan over 854K-line main.ll (three panels blocked) |

## Risk register hindsight

| Risk (from PLAN) | Predicted | Actually happened |
|---|---|---|
| Panel finds docket #7 (byref) not actually fixed | low × high | NO — Cobra confirmed algorithm matches Python, fix is clean. Grade 8.5 on that sub-item. |
| Panel finds coroutine frame still has hardcoded offsets | low × high | NO — grep audit clean, Viper confirmed. |
| Self-hosted golden count is below 64 | medium × medium | YES — 26/64 as expected. Panel graded documentation/categorization, not count. |
| Fixed-point still diverges after byref fix | medium × medium | YES — Sh.8 blocks Stage 1. Flagged as release-name accuracy, not technical failure. |
| Panel score < 8.5 | low × medium | **YES — 8.21.** Prediction was wrong; probability was higher than "low." |
| New issue not on v4.99.0 docket | medium × low | YES — new dockets A.1, A.2, B.1, Co.1, Instr.1 opened. Small. |

## Phase D retrospective

Three releases, 90 lines of executable code, 11 docket items closed.

**What worked:**

- Single-item-per-release discipline. v4.111.0 = 1 file (34 lines).
  v4.112.0 = 1 file (48 lines). v4.113.0 = 3 files (~200 lines, most
  doc). Small releases landed cleanly.
- PRE_PANEL_AUDIT before spawning reviewers. Catches overstatements
  at the "self" level so reviewers don't have to.
- Byte-for-byte control experiments. v4.113.0's valgrind control
  (HEAD~4 rebuild + re-run) is the template for future ABI-adjacent
  changes.
- Honest dockets. Sh.1 through Sh.8 were opened with specific
  descriptions at the time they were discovered; nothing was papered
  over.

**What to improve:**

- Release names should match what the release delivers.
  "v4.112.0: fixed-point verification" was aspirational when the
  fixed-point script fails at Stage 1. A better name: "v4.112.0:
  byref size fix + divergence analysis."
- Test artifacts must be committed. `/tmp/` files disappear.
- Culebra scan gap persisted three panels. Third time is a pattern.

## Next session

**v4.114.1 patch release.** Three items above. Delta panel
(Rattler + Cobra + Anaconda) after shipping. If delta aggregate
clears 8.5, Phase D closes and v4.115.0 opens Phase E.

## One-line summary

v4.114.0: Phase D panel returned 8.21 NEEDS WORK (below 8.5 bar
despite zero NEEDS WORK verdicts); v4.114.1 patch with 50-line
scope schedules before Phase E unblocks.
