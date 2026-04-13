# Mapanare v4.96.0 — Arc 13 Panel Release (Runtime + Concurrency Maturity)

> **Thirteenth 5-minor cadence panel.** Arc 13 closes. Four releases
> graded: v4.92.0 (real suspension at await points), v4.93.0
> (multi-threaded work-stealing scheduler), v4.94.0 (async benchmark
> suite), v4.95.0 (StringBuilder + O(n^2) string fix). This arc
> upgraded Mapanare's async model from cooperative inline-resume to
> true multi-threaded concurrency and fixed the longest-standing
> performance pathology in the codebase.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.95.0
**Delta review:** No
**Full panel:** **YES**
**Estimated work:** 1 sprint + external panel
**Theme:** Arc 13 closes. Async is multi-threaded. Strings are O(N). The runtime is production-grade.

---

## Arc 13 scope the panel grades

- **v4.92.0:** Real suspension at await points. `await` emits
  `llvm.coro.suspend` that yields to the scheduler. Async file I/O
  golden test. Valgrind + ASan clean.

- **v4.93.0:** Multi-threaded work-stealing scheduler. N worker threads,
  Chase-Lev deques, global overflow queue, thread parking. `spawn()`
  and `block_on()` wired to the scheduler. Fan-out scaling verified.
  TSan clean.

- **v4.94.0:** Async benchmark suite. 5 workloads (sequential chain,
  fan-out, I/O-bound, mixed, backpressure) measured at 1/2/4/N threads.
  Go goroutine comparison. Results published.

- **v4.95.0:** StringBuilder in C runtime. Loop-concat MIR optimization.
  AI stdlib refactored. >= 5x improvement on string-heavy workloads.

### Panel-specific questions

- Does real suspension actually interleave coroutines? (Not just
  "suspend and resume" but "make progress on coroutine B while A is
  suspended.") Verify with the I/O golden test wall time.
- Is the work-stealing scheduler free of data races under stress?
  TSan clean after 100 repetitions of the 1K-task stress test?
- Do the async benchmarks show meaningful scaling with thread count?
  Is the Go comparison honest? (Same algorithm, same workload.)
- Is the StringBuilder a real fix or a band-aid? Does the AI stdlib
  actually use it? Is the O(N) scaling verified at large N?
- Are there coroutine frame leaks in the multi-threaded case? (A
  coroutine spawned on thread A, stolen by thread B, completed on
  thread B — does `coro.destroy` run on the right thread?)
- **Memory safety across all new paths:** valgrind on real suspension,
  ASan on scheduler, TSan on multi-threaded fan-out. All clean?

---

## Phase 1 — Pre-panel sweep

- [ ] Run the full async test suite 10 times in a row with N threads (default). Any flakiness is a bug.
- [ ] Run the full async test suite 10 times with 1 thread. Verify deterministic.
- [ ] Run `valgrind` on every async golden test (55, 56, 58, 59). Valgrind clean.
- [ ] Run TSan build on every async golden test. TSan clean.
- [ ] Run the scheduler stress test (1000 tasks x 10 suspensions x 8 threads) 100 times. Zero races.
- [ ] Run the string benchmark at 10K and 100K iterations. Verify >= 5x and O(N) scaling.
- [ ] Reproduce all async benchmark numbers from v4.94.0 (within 10% variance).
- [ ] Grep the tree for `raise NotImplementedError` — zero hits expected.

## Phase 2 — Documentation polish

- [ ] Update `docs/roadmap/v4/v4.67.0/DESIGN.md` with a new section or appendix: "Arc 13 Resolution" documenting that Option B (multi-threaded scheduler) is now implemented, with references to v4.92.0-v4.93.0.
- [ ] `docs/SPEC.md` async section — verify it reflects real suspension semantics (not inline-resume)
- [ ] `docs/reference.md` — verify `spawn()`, `block_on()`, `StringBuilder` are documented
- [ ] `docs/cookbook.md` — verify async examples match the real suspension model
- [ ] `CHANGELOG.md` — the v4.96.0 entry summarizes the entire arc: "Arc 13 closed. Async is multi-threaded with real suspension. O(n^2) string concat fixed."

## Phase 3 — Measurement refresh

- [ ] `culebra summary mapanare/self/main.ll` — record
- [ ] Async-specific metrics:
  - Scheduler spawn overhead per task (target: < 1us)
  - Suspend/resume latency per await point (target: < 5us)
  - Work-stealing rate under contention (steals/sec at 8 threads)
  - Fan-out 1K tasks: throughput at 1, 4, 8 threads
  - String benchmark: 10K concat before/after ratio
  - Memory per coroutine frame (measured via `llvm.coro.size.i64`)
- [ ] `MEASUREMENTS.md` written

## Phase 4 — Pre-panel audit

- [ ] Fact-check every v4.92.0-v4.95.0 SESSION_REPORT claim
- [ ] Verify all 4 releases' exit criteria are satisfied (walk each PLAN.md)
- [ ] `PRE_PANEL_AUDIT.md` written

## Phase 5 — Panel run

- [ ] Retarget `.reviews/prompt.md` to v4.96.0. Arc: Arc 13 (Runtime + Concurrency Maturity).
- [ ] `mkdir -p .reviews/v4.96.0/` + pre-populate
- [ ] Spawn 7 reviewers. Reviewer focus assignments:
  - **Mamba (C runtime)** — primary on StringBuilder quality, scheduler C code quality, arena interaction, memory management correctness. This is his original finding (v4.51.0) — he grades whether it is truly fixed.
  - **Viper (memory safety)** — primary on real suspension memory safety (coroutine frame lifetimes, cancel-before-complete, cross-thread frame ownership). Valgrind + ASan + TSan results.
  - **Rattler (LLVM)** — coroutine IR correctness. Does the real suspend emission match DESIGN.md section 4.7.2? Does `presplitcoroutine` + CoroSplit still work correctly with the new scheduler interaction?
  - **Cobra (C++/ABI)** — scheduler ABI. Are the C runtime function signatures stable? Could a Mapanare program link against a different runtime version? Are there hidden ABI breaks in the coroutine frame?
  - **Anaconda (toolchain)** — CI integration: TSan gate, valgrind gate, async benchmark reproducibility, cross-platform (Linux, macOS, WSL).
  - **Boa (Python/DX)** — developer experience of the async model. Is `spawn()` + `block_on()` intuitive? Does the error message for "await outside async fn" make sense?
  - **Coral (language design)** — does the multi-threaded async surface match what users expect from a modern language? How does it compare to Go/Rust/Swift ergonomically?
- [ ] Panel reads DESIGN.md §5 (runtime scheduler) as primary context, plus the new `SCHEDULER.md` from v4.93.0

## Phase 6 — Closeout

- [ ] `.reviews/v4.96.0/README.md` written
- [ ] If PASS (aggregate >= 8.5, 0 NEEDS WORK): Arc 13 closes. Proceed to Arc 14.
- [ ] If NEEDS WORK: recovery protocol re-engages. Patch release v4.96.1 addresses the panel's docket.
- [ ] Standard release closeout: `VERSION`, `CHANGELOG.md`, `SESSION_REPORT.md`

---

## Exit criteria (11 items)

| # | Check | Evidence |
|---|---|---|
| 1 | 10x async test suite run, zero flakiness | CI logs |
| 2 | Valgrind clean on all async golden tests (55, 56, 58, 59) | valgrind logs |
| 3 | TSan clean on all async golden tests + stress test | TSan logs |
| 4 | Scheduler stress test: 1000 tasks x 10 suspensions x 8 threads x 100 reps, zero races | TSan log |
| 5 | Async benchmark numbers reproduced (within 10% of v4.94.0) | v4.94.0 JSON vs new run |
| 6 | String benchmark: >= 5x improvement, O(N) scaling verified | STRING_RESULTS.md |
| 7 | Documentation updated (DESIGN.md, SPEC.md, reference.md, cookbook.md) | diff |
| 8 | `MEASUREMENTS.md` + `PRE_PANEL_AUDIT.md` written | files |
| 9 | Panel prompt retargeted + pre-populated | diff + ls |
| 10 | 7 reviewer files + README.md | listed |
| 11 | Panel verdict: aggregate >= 8.5, zero NEEDS WORK | `.reviews/v4.96.0/README.md` |

---

## What v4.96.0 does NOT do

- **New features.** Panel release — zero new features.
- **Scheduler optimization.** If the panel flags performance issues, those become Arc 14 work. This release measures and grades; it does not tune.
- **Any changes beyond docs polish + metric refresh + panel run.**

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| TSan races show up under 100x stress that did not appear in v4.93.0 | low | high | If found, fix in pre-panel sweep before running the panel. Do not run the panel with known races. |
| Mamba grades StringBuilder harshly (design disagreements) | medium | medium | Ensure the implementation follows C runtime conventions from the rest of the codebase. Show benchmarks. |
| Async benchmark numbers regressed since v4.94.0 | low | medium | Investigate and explain. A 10% variance is expected; > 10% is a bug to fix before the panel. |
| Panel score below 8.5 | medium | medium | Study Arc 9 panel (8.86/10) as the bar. The arc is smaller in scope (4 releases vs 5) but each release is high-impact. |
| A reviewer finds a real suspension bug (use-after-free on cancel) | low | critical | This would be a critical finding. Fix before the panel if found in pre-panel sweep. Delay the panel if needed. |

---

## If the panel says PASS

Arc 13 closes. The cadence continues with Arc 14. Possible themes:
- Structured concurrency (nurseries, task groups, cancellation propagation)
- Event-driven I/O (epoll/kqueue integration into the scheduler)
- Distributed agents (multi-node actor model)
- Self-hosted compiler async support (`emit_llvm.mn` coroutine emission)

## If the panel says NEEDS WORK

Recovery protocol: v4.96.1 opens as a patch release. The panel's
docket is the work list. Arc 13 does not close until the docket clears.
The next scheduled panel shifts accordingly.

---

## After v4.96.0

The lead decides the next arc. The runtime and concurrency layer is now
production-grade: real suspension, multi-threaded scheduling, O(N) string
allocation. The async model is measured against Go and the gap is
documented. Whatever comes next builds on a solid foundation.
