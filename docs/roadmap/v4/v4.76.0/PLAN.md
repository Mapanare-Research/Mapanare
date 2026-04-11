# Mapanare v4.76.0 — Arc 9 Panel Release (Coroutine Completion Close)

> **Ninth 5-minor cadence panel. The final release in the
> POST_RECOVERY_ROADMAP.** Arc 9 closes. Every `CARRY_FORWARD.md` A-item
> is either closed or explicitly deferred with tracking. The
> coroutine work from v4.72.0-v4.75.0 gets graded end-to-end.
>
> **This is the last planned release in this document.** After
> v4.76.0, the lead chooses what comes next: continue in v4.x with
> more feature work, tag v5.0.0 (zero additional work — v4.76.0 is
> already release-gate quality), or both.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.75.0
**Delta review:** No
**Full panel:** **YES**
**Estimated work:** 1 sprint + external panel
**Theme:** Arc 9 closes. A1 closes. The 45-release plan ends.

---

## Arc 9 scope the panel grades

- v4.72.0: Coroutine lowering pt 2 (suspend/resume/destroy + drop glue in cleanup)
- v4.73.0: Runtime scheduler integration; basic async fn runs end-to-end
- v4.74.0: `for await` syntax + `Stream<T>.next_async()`
- v4.75.0: End-to-end demos + goldens + cookbook chapter; A1 closure

Panel-specific questions:
- Does `53_real_await.mn` actually demonstrate real suspension? Measured wall time matches expected (e.g., concurrent execution faster than sequential).
- Does the scheduler handle the stress test without races or leaks?
- Is the drop glue in cleanup paths correct? Valgrind clean on cancel-before-resume?
- Does `for await` work correctly against real streams (not just unit tests)?
- Is the DWARF scope for async code documented as "v5.x" or does the panel want a placeholder?
- **Are there any hollow features left in the plan's output?** This is the ultimate measure: the recovery arc was about eliminating hollow features; this plan added grammar + semantic + runtime + tests + docs for every feature. Did any slip through?

---

## Phase 1 — Pre-panel sweep

- [ ] Run the full async test suite 10 times in a row. Any flakiness is a bug.
- [ ] Run `valgrind` on every async golden + example. Valgrind-clean is the bar.
- [ ] Run the scheduler stress test (100 coros × 10 suspensions) 10 times. No races.
- [ ] Run `53_real_await.mn` and verify the concurrent-wall-time measurement (Phase 5 from v4.75.0) consistently shows concurrency.
- [ ] Grep the tree for `raise NotImplementedError` — zero hits expected (the v4.29.0 CI gate enforces this).
- [ ] Grep for any v4.75.0-tracked skips — all should be unmarked.

## Phase 2 — Documentation polish

- [ ] `docs/cookbook.md` §Async programming — final read-through
- [ ] `docs/SPEC.md §Futures and Async` — final audit
- [ ] `docs/reference.md` — full async surface documented (async fn, await, Future<T>, for await, block_on, sleep_ms, get_async, stream_next_async)
- [ ] README.md — update "What is Mapanare?" to mention real async/await
- [ ] `CHANGELOG.md` — the v4.76.0 entry is a celebration: "Arc 9 closed. Async/await is real, end-to-end, 10 releases after the design doc."

## Phase 3 — Measurement refresh

- [ ] `culebra summary mapanare/self/main.ll` — record
- [ ] Async-specific metrics:
  - Scheduler overhead per suspend/resume pair (expected: ~microseconds)
  - Coroutine frame size for the `53_real_await.mn` compute_step fn (measured via `llvm.coro.size.i64`)
  - Stress test: 100 coroutines × 10 suspensions complete-to-done time (target: < 1s)
  - Memory overhead per live coroutine (target: < 1KB including frame)
- [ ] `MEASUREMENTS.md` written

## Phase 4 — `CARRY_FORWARD.md` final state

- [ ] Walk the ledger row by row
- [ ] **Target:** every A1-A9 item closed or explicitly deferred to v5.x with a specific tracking note
  - A1 (await coroutine lowering): CLOSED in v4.75.0
  - A2 (DWARF debug info): CLOSED in v4.65.0
  - A3 (Python emitter removal): CLOSED in v4.58.0
  - A4 (llvmlite JIT removal): CLOSED in v4.59.0
  - A5 (Culebra template upstream): OPEN, tracked to Culebra project (not Mapanare)
  - A6 (match shape diff): CLOSED in v4.34.0
  - A7 (self-hosted semantic wiring): CLOSED in v4.52.0
  - A8 (UNRESOLVED/ERROR split): CLOSED in v4.53.0
  - A9 (emit_c.mn): CLOSED in v4.54.0
- [ ] Any open item not closed by v4.76.0 gets a fresh tracking comment. Nothing goes into v5.x without an explicit owner.

## Phase 5 — Final pre-panel audit

- [ ] Fact-check every v4.72.0-v4.75.0 SESSION_REPORT claim
- [ ] `PRE_PANEL_AUDIT.md` written

## Phase 6 — Panel run

- [ ] Retarget `.reviews/prompt.md` to v4.76.0. Arc: Arc 9 (coroutine completion).
- [ ] `mkdir -p .reviews/v4.76.0/` + pre-populate
- [ ] Spawn 7 reviewers. All lenses relevant — this is the biggest feature the project has ever shipped:
  - **Rattler (LLVM)** — primary. Coroutine lowering is his domain; grade the whole chain
  - **Cobra (C++/ABI)** — C++20 coroutines are the precedent; compare Mapanare's shape
  - **Mamba (C runtime)** — scheduler and the drop-glue cleanup paths
  - **Viper (memory safety)** — coroutine frames are heap-allocated; lifetime, cancellation, drop
  - **Anaconda (toolchain)** — pass pipeline, CI integration
  - **Boa (Python/DX)** — developer experience
  - **Coral (language design)** — does the user-facing async surface match DESIGN.md §3?
- [ ] Panel reads DESIGN.md as primary context before reading code

## Phase 7 — Closeout

- [ ] `.reviews/v4.76.0/README.md` written
- [ ] If PASS: arc 9 closes. **The 45-release plan is complete.** The lead chooses what comes next.
- [ ] If NEEDS WORK: recovery protocol. The plan explicitly covers this case — recovery sliding doesn't end the document, it extends it.
- [ ] Standard release closeout.

---

## Exit criteria (13 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Full async test suite runs 10×, no flakiness | CI logs |
| 2 | Valgrind clean on every async golden + example | valgrind |
| 3 | Scheduler stress test passes 10× | runtime log |
| 4 | `53_real_await.mn` shows real concurrency | wall time measurement |
| 5 | Documentation polish complete | `check_docs_drift.py` |
| 6 | Metrics recorded | `MEASUREMENTS.md` |
| 7 | A1-A9 all closed or explicitly deferred with tracking | `LEDGER_AUDIT.md` |
| 8 | `LEDGER_AUDIT.md` / `PRE_PANEL_AUDIT.md` | files |
| 9 | Panel prompt retargeted + pre-populated with DESIGN.md | diff + ls |
| 10 | 7 reviewer files + README.md | listed |
| 11 | Panel verdict ≥ 9.0 with zero NEEDS WORK (target) | README.md |
| 12 | CHANGELOG celebration entry | diff |
| 13 | SESSION_REPORT written | file |

---

## What v4.76.0 does NOT do

- **New features.** Panel release.
- **Any changes beyond docs polish + metric refresh + panel run**

---

## If the panel says PASS

The recovery arc discipline continues. `REVIEW_CADENCE.md` schedules the next full panel at v4.81.0 (5-minor cadence). The lead is free to:
- **Continue in v4.x** with whatever growth they want: structured concurrency, autograd, GPU kernel fusion, distributed agents, and so on. Each new arc follows the same 5-release-plus-panel pattern.
- **Tag v5.0.0** at v4.76.0 with no additional work — the v4.76.0 panel is already release-gate quality. v5.0.0 = v4.76.0 with a different version label.
- **Do both.** Tag v5.0.0 to mark the milestone, and simultaneously open v4.77.0 (or v5.1.0) for the next arc.

The plan explicitly does not decide this. Whoever has the lead at v4.76.0 chooses.

---

## If the panel says NEEDS WORK

Recovery arc protocol re-engages:
- v4.77.0 opens as a recovery-style closeout release with the panel's docket
- The arc 9 theme technically extends — "coroutines aren't done yet"
- The next scheduled panel shifts to whenever the docket closes
- No shame, no blame. This is the cadence working.

---

## Reference

- [`POST_RECOVERY_ROADMAP.md`](../POST_RECOVERY_ROADMAP.md) — the full plan this release ends
- [`.reviews/REVIEW_CADENCE.md`](../../../../.reviews/REVIEW_CADENCE.md)
- [`.reviews/v4.31.0/README.md`](../../../../.reviews/v4.31.0/README.md) — the arc-end panel that started this whole trajectory

---

## After v4.76.0

**The 45-release plan is complete.**

The lead decides what happens next. The recovery-arc discipline the project installed in v4.27.0-v4.31.0 has now been the normal operating mode for 45 releases. Every feature shipped had a delta review. Every 5 minors got a panel. Every `CARRY_FORWARD.md` item had a tracking version. Eight CI gates caught regressions at PR time.

Whatever comes after v4.76.0 — growth releases, recovery releases, major bumps — the playbook is the same. The plan was not about the specific features; it was about the cadence. The cadence works.
