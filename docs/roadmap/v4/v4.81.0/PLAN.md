# Mapanare v4.81.0 — Arc 10 Panel Release (Integration Tests + Debt Zero)

> **Tenth 5-minor cadence panel.** The first panel of the post-plan era.
> Arc 10 built the integration test harness (v4.77.0), closed all
> Mapanare-owned carry-forward items (v4.78.0-v4.79.0), and delivered
> the documentation Boa has requested since Arc 3 (v4.80.0). The panel
> grades whether the infrastructure is solid and the debt is truly zero.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.80.0
**Delta review:** No
**Full panel:** **YES** — Rattler, Viper, Anaconda, Cobra, Coral, Boa, Mamba
**Estimated work:** 1 sprint + external panel
**Theme:** Arc 10 closes. Integration pipeline validated. Carry-forward at zero. Documentation complete.

---

## Arc 10 scope the panel grades

- **v4.77.0**: Integration test harness — 57 golden tests through full LLVM pipeline (emit -> llvm-as -> opt -> llc -> link -> run), CI gate, RESULTS.md
- **v4.78.0**: Closed carry-forward items 49 (drop-glue struct return escape analysis), 50 (agent destroy inbox drain), A10b (const scope in self-hosted semantic)
- **v4.79.0**: Closed carry-forward items P2 (pattern_matching.py unit tests), P3 (guard fall-through divergence), P6 (unreachable-arm warning coverage). Ledger at 0 Mapanare-owned items.
- **v4.80.0**: Documentation — async cookbook, SPEC Futures section, gdb/lldb debugging tutorial

Panel-specific questions:
- Does the integration test harness actually catch real bugs? Did any golden test reveal a miscompilation that string-match testing missed?
- Is the item 49 escape analysis correct? Does it cover all struct-return patterns, or are there edge cases that still leak?
- Is the item 50 drain loop correct under concurrent access? (Note: agents are single-consumer, so this should be safe, but verify.)
- Does the SPEC Futures section accurately describe the implementation? Any normative claims that contradict the actual behavior?
- Is the debugging tutorial usable by someone who has never used gdb before?
- **Is the carry-forward ledger truly at zero?** Walk every row. Any item marked CLOSED that is not actually closed is a panel failure.

---

## Phase 1 — Pre-panel sweep

- [ ] Run full test suite: `make test`
- [ ] Run integration tests: `pytest tests/integration/ -v`
- [ ] Run valgrind on all golden tests that exercise struct returns, agents, and async
- [ ] Check for flaky tests: run `pytest tests/ -v -n auto` 5 times in a row
- [ ] Verify item 49 fix: compile a struct-return golden through integration pipeline, valgrind clean
- [ ] Verify item 50 fix: run agent destroy test with valgrind
- [ ] Verify A10b fix: const scope golden test passes through both pipelines

## Phase 2 — Documentation polish

- [ ] Final read-through of `docs/cookbook/async.md` — check code examples still compile
- [ ] Final read-through of `docs/SPEC.md` Futures section — cross-reference implementation
- [ ] Final read-through of `docs/guides/debugging.md` — verify gdb commands work on current binary
- [ ] Check all internal links resolve
- [ ] Run `scripts/check_docs_drift.py` if available

## Phase 3 — Measurement refresh

- [ ] `culebra summary mapanare/self/main.ll` — record findings count, health score
- [ ] Integration test metrics:
  - N/57 (or N/58) golden tests pass end-to-end
  - Which tests fail and at which stage
  - Average pipeline time per test
- [ ] Carry-forward metrics:
  - Total items ever opened: count from CARRY_FORWARD.md
  - Total closed: count
  - Remaining open: should be 2 (A5 Culebra-external, A10 accepted)
  - Longest-lived item that was closed: item 49 at 8 cycles
- [ ] Test count delta from v4.76.0 (the end of the previous plan)
- [ ] `MEASUREMENTS.md` written in `.reviews/v4.81.0/`

## Phase 4 — CARRY_FORWARD.md final audit

- [ ] Walk every row in CARRY_FORWARD.md
- [ ] Verify each CLOSED item has evidence that is still valid (test file exists, code change present)
- [ ] Verify the only OPEN items are A5 (Culebra-external) and A10 (accepted grammar gap)
- [ ] Write `LEDGER_AUDIT.md` in `.reviews/v4.81.0/` confirming the zero state

## Phase 5 — Pre-panel audit

- [ ] Fact-check every v4.77.0-v4.80.0 SESSION_REPORT claim
- [ ] Verify all exit criteria from each release are still true
- [ ] Write `.reviews/v4.81.0/PRE_PANEL_AUDIT.md`

## Phase 6 — Panel run

- [ ] Retarget `.reviews/prompt.md` to v4.81.0. Arc: Arc 10 (Integration Tests + Debt Zero).
- [ ] `mkdir -p .reviews/v4.81.0/` + pre-populate
- [ ] Spawn 7 reviewers with focus assignments:
  - **Anaconda (toolchain)** — PRIMARY for integration test harness. Does the pipeline catch real bugs? Is the CI gate robust?
  - **Boa (Python/DX)** — PRIMARY for documentation. Are the cookbook, SPEC, and debugging guide usable?
  - **Viper (memory safety)** — PRIMARY for items 49 and 50. Is the escape analysis correct? Is the drain loop safe?
  - **Rattler (LLVM)** — integration pipeline IR quality. Does `opt -O2` reveal issues?
  - **Cobra (C++/ABI)** — ABI correctness through the integration pipeline
  - **Mamba (C runtime)** — item 50 drain loop, runtime link correctness
  - **Coral (language design)** — SPEC Futures section quality, cookbook pedagogical value
- [ ] Panel reads `tests/integration/RESULTS.md` as primary evidence

## Phase 7 — Closeout

- [ ] `.reviews/v4.81.0/README.md` written with verdict table
- [ ] If PASS: Arc 10 closes. Proceed to Arc 11 (optimizer improvements or next growth theme).
- [ ] If NEEDS WORK: address findings in v4.81.1 patch before moving to Arc 11. Recovery protocol re-engages.
- [ ] Standard release closeout
- [ ] `SESSION_REPORT.md` with arc retrospective

---

## Exit criteria (11 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Full test suite passes (no flakiness in 5 runs) | CI logs |
| 2 | Integration tests: >=50/57 pass end-to-end | `RESULTS.md` |
| 3 | Valgrind clean on struct-return + agent + async goldens | valgrind output |
| 4 | Documentation code examples all compile | compilation log |
| 5 | CARRY_FORWARD.md audit: 0 Mapanare-owned open items | `LEDGER_AUDIT.md` |
| 6 | `MEASUREMENTS.md` written | `.reviews/v4.81.0/MEASUREMENTS.md` |
| 7 | `PRE_PANEL_AUDIT.md` written | `.reviews/v4.81.0/PRE_PANEL_AUDIT.md` |
| 8 | Panel prompt retargeted + 7 reviewer files | `.reviews/v4.81.0/` |
| 9 | Panel aggregate >= 8.5 | `.reviews/v4.81.0/README.md` |
| 10 | 0 NEEDS WORK verdicts | `.reviews/v4.81.0/README.md` |
| 11 | SESSION_REPORT written with arc retrospective | file |

---

## What this release does NOT do

- **New features** — panel release, zero new code.
- **Optimizer improvements** — that is Arc 11.
- **Self-hosted integration tests** — v4.77.0 harness uses the Python bootstrap. Self-hosted integration is future work.
- **Fix integration test failures** — tests that fail through the pipeline are documented in RESULTS.md. Fixing them is optimizer/emitter work for future arcs.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Panel finds item 49 escape analysis has edge cases | medium | medium | If findings are LOW, track for next arc. If HIGH, v4.81.1 patch |
| Integration tests reveal widespread miscompilation | medium | high | This is the harness working as designed. Document in RESULTS.md. Panel grades the infrastructure, not the pass rate |
| Documentation examples are stale by panel time | low | low | Phase 2 re-verifies all examples |
| Panel score < 8.5 | low | medium | Pre-panel sweep reduces surprise. If close, the arc retrospective identifies what to improve |
| Boa gives NEEDS WORK on documentation quality | low | medium | Phase 2 polish pass. Boa has been specific about what they want; v4.80.0 targets exactly those items |

---

## If the panel says PASS

Arc 10 closes. The first post-plan arc completes successfully. The integration test harness is validated as infrastructure. The carry-forward ledger is at zero. The documentation gaps are closed. Proceed to Arc 11.

Arc 11 theme is the lead's choice. Candidates:
- **Optimizer improvements** — MIR optimization passes that improve the integration test pass rate
- **Self-hosted integration** — wire mnc-stage1 into the integration harness
- **Structured concurrency** — `TaskGroup`, cancellation, timeouts
- **v5.0.0 prep** — whatever is needed to tag a major

## If the panel says NEEDS WORK

v4.81.1 opens as a patch release addressing the panel's docket. Arc 10 does not close until the docket is empty. The next scheduled panel shifts accordingly.

---

## After v4.81.0

If PASS, Arc 11 begins at v4.82.0. The lead picks the theme. The cadence continues: 5 releases per arc, panel on the 5th. The carry-forward discipline, delta reviews, Culebra scans, SESSION_REPORT ledger — all of it carries forward.
