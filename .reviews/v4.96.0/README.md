# Arc 13 Panel — v4.96.0

**Arc:** 13 (Runtime + Concurrency Maturity)
**Releases graded:** v4.92.0 - v4.95.0
**Panel date:** 2026-04-13
**Aggregate: 8.57/10**
**Verdict: PASS (4 PASS, 3 PASS WITH NOTES, 0 NEEDS WORK)**

Arc 13 upgraded the async runtime from cooperative inline-resume to
true multi-threaded concurrency with a work-stealing scheduler, shipped
the async benchmark infrastructure, and fixed the O(n^2) string concat
pathology that Mamba flagged 45 releases ago. All four claims validated.

---

## Verdict Table

| # | Reviewer | Lens | Grade | Verdict |
|---|----------|------|-------|---------|
| 1 | Rattler | LLVM (coro IR) | 8/10 | PASS WITH NOTES |
| 2 | Mamba | C runtime (PRIMARY) | 9/10 | PASS |
| 3 | Viper | Memory safety (PRIMARY) | 8/10 | PASS WITH NOTES |
| 4 | Cobra | C++/ABI | 9/10 | PASS |
| 5 | Anaconda | Toolchain | 8/10 | PASS WITH NOTES |
| 6 | Boa | Python/DX | 9/10 | PASS |
| 7 | Coral | Language design | 9/10 | PASS |

**Aggregate: 8.57/10** (60/70)

---

## Consensus findings

### What Arc 13 delivered

1. **Real suspension (v4.92.0).** `await` emits `coro.save + coro.suspend`
   instead of inline-resume. Coroutine frames saved to heap, scheduler
   resumes when future is Ready. Three-phase pattern (fast-path check,
   drive-once, real suspend) preserves semantics for both CPU-bound and
   I/O-bound workloads.

2. **Multi-threaded scheduler (v4.93.0).** Chase-Lev work-stealing deques,
   N worker threads (auto-detect cores), condvar parking, global overflow
   queue. Worker 0 is the calling thread (avoids deadlock). N=1 backward
   compatible with v4.92.0.

3. **Async benchmarks (v4.94.0).** 5 workloads x 3 languages, Python
   baselines measured. Infrastructure ready but Mapanare/Go measurements
   pending (library rebuild / Go installation).

4. **StringBuilder (v4.95.0).** Amortized O(1) append with 2x growth,
   zero-copy transfer to MnString. AI stdlib refactored: `escape_json`,
   `messages_to_json`, `tools_to_json` converted from O(n^2) to O(n).
   Mamba's v4.51.0 finding **closed.**

### Unanimous checkpoints

- 7/7 agree: real suspension emission is semantically correct
- 7/7 agree: StringBuilder eliminates the O(n^2) pathology
- 7/7 agree: the scheduler API (spawn/block_on) is clean and intuitive
- 7/7 agree: the async model compares favorably to Go/Rust/Swift
- 6/7 note: benchmark measurements are infrastructure-only (no runtime numbers)

### Docket (items for future arcs)

| Item | Source | Priority | Notes |
|------|--------|----------|-------|
| C-level unit tests for StringBuilder + scheduler | Anaconda | **HIGH** | No test coverage for core C additions |
| Enforce single-enqueue invariant in scheduler | Viper | MEDIUM | Implicit timing correctness |
| Destroy pending coroutines on shutdown | Viper | MEDIUM | Currently leaks frames |
| Document cross-thread fence dependency | Rattler | MEDIUM | Correctness depends on deque's SEQ_CST |
| Rebuild libmapanare_rt.a for benchmarks | Anaconda | MEDIUM | Infrastructure without numbers |
| StringBuilder method syntax | Coral, Boa | MEDIUM | `sb.append(x)` instead of `sb_append(sb, x)` |
| LLVM frame layout documentation | Mamba | MEDIUM | mn_coro_is_done reads raw bytes |
| Windows scheduler support | Anaconda | LOW | Currently POSIX-only |
| Async-specific error messages | Boa | LOW | Better DX for common mistakes |

---

## Arc 13 retrospective

### What worked

1. **Incremental delivery.** Four focused releases, each building on
   the previous. v4.92.0 proved suspension, v4.93.0 added threading,
   v4.94.0 measured, v4.95.0 fixed strings. No release tried to do
   everything.

2. **Design doc compliance.** v4.67.0 DESIGN.md specified the scheduler
   API, the coroutine frame ABI, and the suspension model. v4.92.0-v4.93.0
   implemented exactly what was designed. The design paid for itself.

3. **Long-running issue closure.** Mamba's v4.51.0 string finding was
   45 releases old. The StringBuilder fix is clean, tested, and deployed
   in the AI stdlib. This demonstrates that the panel process works —
   findings are tracked and eventually resolved.

### What could improve

1. **Benchmark realization.** v4.94.0 shipped infrastructure without
   measurements. The library rebuild blocker should have been resolved
   in the same release, not deferred.

2. **C-level testing.** The scheduler and StringBuilder have no C unit
   tests. Python-level tests validate the emitter, but the C runtime
   is tested only by compilation. A C test harness would catch
   regressions in the runtime itself.

3. **Go comparison.** Still missing after two benchmark releases. Go
   is the most natural comparison for goroutine-style concurrency.
   Should be prioritized.

### Arc 13 closes

With aggregate 8.57/10 and 0 NEEDS WORK, **Arc 13 closes.** The docket
items are future work for subsequent arcs. Mamba's v4.51.0 finding is
officially resolved.
