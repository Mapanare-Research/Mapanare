# Mapanare v4.75.0 — End-to-End Async Demos + Goldens

> **Arc 9 release 4.** Integration release. Ships the `53_real_await.mn`
> golden the v4.26.0 panel flagged as missing, plus `http_fanout`
> and the upgraded `chat_stream` demos from the AI/LLM arc.
> `CARRY_FORWARD.md` A1 closes here.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.74.0
**Delta review:** No
**Full panel:** No (v4.76.0)
**Estimated work:** 1 sprint
**Theme:** Async works end-to-end. A1 is closed. The v4.19.0 hollow-feature ghost is laid to rest.

---

## Scope

### The golden that closes A1

`tests/golden/53_real_await.mn`:

```mapanare
import stdlib::time

async fn delay(ms: Int) -> Unit {
    // Suspend for `ms` milliseconds
    await time::sleep_ms(ms)
}

async fn compute_step(i: Int) -> Int {
    await delay(10)  // simulate I/O
    return i * 2
}

async fn run_sequence() -> Int {
    let a: Int = await compute_step(1)  // 2
    let b: Int = await compute_step(2)  // 4
    let c: Int = await compute_step(3)  // 6
    return a + b + c  // 12
}

async fn run_concurrent() -> List<Int> {
    // Start three in parallel, await each
    let fa: Future<Int> = compute_step(10)
    let fb: Future<Int> = compute_step(20)
    let fc: Future<Int> = compute_step(30)
    let a: Int = await fa  // 20
    let b: Int = await fb  // 40
    let c: Int = await fc  // 60
    return [a, b, c]  // [20, 40, 60]
}

fn main() {
    let seq: Int = block_on(run_sequence())
    print("sequential: ", seq)  // 12

    let conc: List<Int> = block_on(run_concurrent())
    print("concurrent: ", conc)  // [20, 40, 60]
}
```

Expected output:
```
sequential: 12
concurrent: [20, 40, 60]
```

This is the golden the v4.26.0 panel specifically named as missing. A1 closes when this runs.

### `http_fanout.mn`

`examples/async/http_fanout.mn`:

```mapanare
import stdlib::net::http

async fn fetch_url(url: String) -> Result<String, HttpError> {
    return await http::get_async(url)
}

async fn fetch_all(urls: List<String>) -> List<String> {
    let futures: List<Future<Result<String, HttpError>>> = urls.map(|u| fetch_url(u))
    let results: List<String> = []
    for future in futures {
        match await future {
            Ok(body) => results.push(body),
            Err(_) => results.push(""),
        }
    }
    return results
}

fn main() {
    let urls = [
        "https://example.com",
        "https://mapanare.dev",
        "https://llvm.org",
    ]
    let bodies: List<String> = block_on(fetch_all(urls))
    for body in bodies {
        print("got ", body.len(), " bytes")
    }
}
```

Real concurrent HTTP fetches. `http::get_async` is a v4.75.0 addition to `stdlib::net::http`.

---

## Phase 1 — `time::sleep_ms` async primitive

- [ ] `stdlib/time.mn` — add `sleep_ms(ms: Int) -> Future<Unit>`
- [ ] Runtime: `__mn_time_sleep_async(ms)` returns a future that becomes ready after `ms` milliseconds. Implementation uses a scheduler timer wheel (lightweight: a sorted list of (deadline, future_ptr) entries; the scheduler wakes on the nearest deadline).

## Phase 2 — `http::get_async`

- [ ] `stdlib/net/http.mn` — add `get_async(url: String) -> Future<Result<String, HttpError>>`
- [ ] Implementation: kicks off an HTTP request in a runtime thread or via non-blocking socket, returns a future that becomes ready on completion
- [ ] For v4.75.0, the simple implementation: spawn a pthread that does the sync fetch and signals the future via the scheduler. Not efficient, but correct.
- [ ] v5.x can replace with real non-blocking I/O via epoll.

## Phase 3 — `53_real_await.mn` golden

- [ ] Create the file
- [ ] Generate reference output
- [ ] Run through mnc-stage1 — must produce the expected output
- [ ] Reference IR saved; subsequent runs compare

## Phase 4 — `http_fanout.mn` example

- [ ] Create `examples/async/http_fanout.mn`
- [ ] Integration test: if network available, verify it runs against 3 real URLs; otherwise use a local mock HTTP server

## Phase 5 — `chat_stream.mn` example upgrade

- [ ] `examples/async/chat_stream.mn` — the v4.50.0 chat agent rewritten with real `for await`
- [ ] Runs against Ollama if available

## Phase 6 — Cookbook chapter

- [ ] `docs/cookbook.md` §Async programming in Mapanare — new chapter:
  1. What is an async fn?
  2. What is a Future<T>?
  3. Using await inside an async fn
  4. Block_on from non-async main
  5. Concurrent execution (starting multiple futures, awaiting each)
  6. Stream async iteration with `for await`
  7. Real-world: HTTP fanout, LLM streaming, delays
- [ ] 2500+ words, 6+ code blocks (parseable)

## Phase 7 — SPEC sync

- [ ] `docs/SPEC.md §Futures and Async` — full section, not a draft
- [ ] Replace the v4.69.0 draft
- [ ] Full semantics spelled out

## Phase 8 — A1 closure

- [ ] `.reviews/CARRY_FORWARD.md` — row A1 (real `await` coroutine lowering) marked CLOSED with evidence pointing at `53_real_await.mn` + the v4.72.0-v4.75.0 release chain

## Phase 9 — Full async test suite

- [ ] `tests/async/test_golden_real_await.py` — runs the golden, verifies output
- [ ] `tests/async/test_http_fanout.py` — integration test, skips if no network
- [ ] `tests/async/test_chat_stream_async.py` — integration test, skips if no Ollama
- [ ] `tests/async/test_time_sleep_ms.py` — verifies `sleep_ms` delays for the expected duration (within tolerance)
- [ ] `tests/async/test_concurrent_futures.py` — verifies that three futures started before any await actually run concurrently (measured by total wall time < sum of individual times)

## Phase 10 — LOW sweep

Last chance before the arc 9 panel. 2-3 items.

## Phase 11 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.75.0
- [ ] `CHANGELOG.md [4.75.0]` — **the big one**. async/await shipped, A1 closed, all planned async features runnable end-to-end
- [ ] SESSION_REPORT with a celebration block: v4.19.0 claimed async; v4.24.0 claimed it again; v4.26.0 panel called the bluff; v4.75.0 makes it true

---

## Exit criteria (18 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `time::sleep_ms(ms) -> Future<Unit>` implemented | `test_time_sleep_ms` |
| 2 | `http::get_async(url) -> Future<Result>` implemented | `test_http_fanout` or unit |
| 3 | `53_real_await.mn` golden exists | `ls tests/golden/` |
| 4 | Golden produces expected "sequential: 12" output | runtime log |
| 5 | Golden produces expected "concurrent: [20, 40, 60]" output | runtime log |
| 6 | Concurrent execution is actually concurrent (wall time < sum) | `test_concurrent_futures` |
| 7 | `http_fanout.mn` example runs | integration test |
| 8 | `chat_stream.mn` example runs against Ollama | integration test |
| 9 | Cookbook §Async chapter written (2500+ words) | word count + parseable |
| 10 | SPEC §Futures and Async written | diff |
| 11 | A1 marked CLOSED in `CARRY_FORWARD.md` | ledger diff |
| 12 | All v4.75.0-tracked `pytest.mark.skip` entries unmarked | conftest diff |
| 13 | Valgrind clean on all async goldens and examples | valgrind |
| 14 | Self-hosted mirror runs the golden through mnc-stage1 | `test_native.py` |
| 15 | Fixed-point diff still 0 | verify |
| 16 | `scripts/check_no_hollow_features.py` step 3 covers the async AST | CI gate |
| 17 | SESSION_REPORT includes celebration | diff |
| 18 | Standard closeout clean | CI |

---

## What v4.75.0 does NOT do

- **Structured concurrency** (task groups, supervision) — v5.x
- **Cancellation / timeouts** — v5.x
- **Non-blocking I/O via epoll/kqueue** — v5.x (v4.75.0 uses pthreads under the hood for `http::get_async`)
- **`async` closures** — v5.x
- **`async` trait methods** — v5.x
- **DWARF debug info for coroutines** — v5.x

All of these are legitimate future work. v4.75.0 ships the core feature; v5.x ships ergonomics and polish.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| `time::sleep_ms` timer wheel has drift | low | low | Document the precision limit (~1ms) |
| `http::get_async` pthread-based impl leaks on cancel | medium | medium | Document that cancel isn't supported in v4.75.0 |
| The concurrent-execution test is flaky due to system timing | medium | low | Generous tolerance; only check "concurrent < sequential" not exact ratios |
| Valgrind discovers coroutine frame leaks on some code path | medium | high | Test comprehensively; if found, file as v4.75.1 point release blocker |
| The full async surface surfaces a drop-glue gap | medium | medium | Already tested in v4.72.0; v4.75.0 extends with real-world code paths |

---

## Reference

- [`v4.67.0/DESIGN.md`](../v4.67.0/DESIGN.md)
- [`.reviews/CARRY_FORWARD.md`](../../../../.reviews/CARRY_FORWARD.md) A1
- [`.reviews/v4.26.0/README.md`](../../../../.reviews/v4.26.0/README.md) — the panel that called the bluff on the v4.24.0 async claim

---

## After v4.75.0

v4.76.0 is the **arc 9 panel release** — the ninth and final 5-minor cadence panel in this plan. The coroutine arc closes. A1 is officially, externally validated.
