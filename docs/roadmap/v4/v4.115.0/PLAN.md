# Mapanare v4.115.0 — Async I/O Demo Running Natively

> **Phase E release 1.** The v4.99.0 reviewers noted: no async program
> has been demonstrated with real I/O. The cooperative inline-resume
> model works for compute but has never been shown with real I/O-bound
> workloads. This release writes two async example programs that
> perform actual file and network I/O, compiles them through
> mnc-stage1, links with libmapanare_rt.a, and runs the resulting
> binaries. If native async I/O requires C runtime additions, those
> are implemented here.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.114.0
**Delta review:** No
**Full panel:** No (v4.120.0)
**Estimated work:** 1 sprint
**Theme:** Prove async I/O works natively, not just through the Python bootstrap.

---

## Scope

Async in Mapanare has been tested through golden tests (55-57) that exercise `async fn`, `await`, `block_on`, and channel communication. Those tests verify the scheduling and control flow. What has never been demonstrated is an async program that performs real I/O: reading a file, writing a file, or making a network connection. The v4.99.0 panel flagged this gap explicitly.

This release writes two example programs:

1. **`examples/async_file_io.mn`** -- an async function that reads a file, processes the content (word count, line count), and writes a summary to an output file. Uses `async fn`, `await`, `block_on`.

2. **`examples/async_http_demo.mn`** -- an async TCP connect + read (or HTTP GET if the net stdlib is available natively). Demonstrates async networking at the native binary level.

Both programs must compile through mnc-stage1, link against `libmapanare_rt.a`, and produce correct output when run as native binaries. This is cooperative async with real I/O wrappers -- not full suspension, which is a v5.x feature.

## Phase 1 -- Async file I/O example

- [ ] Write `examples/async_file_io.mn`:
  - `async fn read_and_process(path: String) -> Result<String, String>` -- reads the file, counts words and lines
  - `async fn write_summary(path: String, summary: String) -> Result<(), String>` -- writes the summary to a file
  - `fn main()` -- uses `block_on` to run the async pipeline
- [ ] Verify it compiles through the Python bootstrap: `mapanare emit-llvm examples/async_file_io.mn`
- [ ] Verify the emitted IR is valid: `llvm-as <output>.ll -o /dev/null`
- [ ] Compile through mnc-stage1: `./mapanare/self/mnc-stage1 examples/async_file_io.mn`
- [ ] Link: `clang <output>.ll -o async_file_io -lmapanare_rt -lm -lpthread`
- [ ] Run: `./async_file_io <test_input_file>` -- verify output file is created with correct word/line counts

## Phase 2 -- Compile + link + run verification

- [ ] Create a test input file: `examples/async_file_io_input.txt` (100+ lines, known word/line count)
- [ ] Run the native binary against the test input
- [ ] Verify output matches expected word count and line count
- [ ] Run through the full integration pipeline: `llvm-as -> opt -O2 -> llc -> clang -> run`
- [ ] Verify the binary works at -O2 (not just -O0)
- [ ] Record: compiles? links? runs? correct output at -O0? correct output at -O2?

## Phase 3 -- Async TCP/HTTP example

- [ ] Assess native net stdlib availability: check if `stdlib/net/` functions compile through mnc-stage1
- [ ] If net stdlib is available natively:
  - Write `examples/async_http_demo.mn` -- async HTTP GET to a known URL, print response status + body length
- [ ] If net stdlib is NOT available natively:
  - Write `examples/async_tcp_demo.mn` -- async TCP connect to localhost:80 (or a test server), read response, print bytes received
  - Use C runtime TCP functions (`mapanare_tcp_connect`, `mapanare_tcp_read`) via extern
- [ ] Compile through mnc-stage1, link, run
- [ ] Verify the program makes a real network connection (not mocked)

## Phase 4 -- C runtime additions (if needed)

- [ ] If Phase 1 or 3 reveals missing C runtime functions for async I/O:
  - Implement `mapanare_file_read_async(path, callback)` in `runtime/native/mapanare_runtime.c`
  - Implement `mapanare_file_write_async(path, data, len, callback)` in `runtime/native/mapanare_runtime.c`
  - Rebuild `libmapanare_rt.a` with the new exports
- [ ] If no additions are needed, document why (e.g., existing synchronous C runtime functions are sufficient for cooperative async)
- [ ] Verify the rebuilt library passes existing golden tests (no regressions)

## Phase 5 -- Async guide

- [ ] Write `docs/guides/async.md`:
  - What async means in Mapanare (cooperative inline-resume, not preemptive)
  - `async fn`, `await`, `block_on` syntax and semantics
  - File I/O example with explanation
  - Network I/O example with explanation
  - What works natively vs what requires the Python bootstrap
  - Limitations: no full suspension (v5.x), no multi-threaded async scheduler yet
- [ ] Verify all code examples in the guide compile and run

## Phase 6 -- LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.115.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (8 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `examples/async_file_io.mn` compiles through mnc-stage1 | build log |
| 2 | File I/O demo links and runs as a native binary | binary execution output |
| 3 | Output is correct (word count, line count match expected) | diff against expected output |
| 4 | Async TCP/HTTP example compiles, links, runs | binary execution output |
| 5 | Real I/O occurs (not mocked) | strace or output verification |
| 6 | `docs/guides/async.md` written with native examples | file exists |
| 7 | All code examples in the guide compile | compilation log |
| 8 | No regressions in golden tests or existing async tests | test log |

---

## What this release does NOT do

- **Implement full suspension** -- that is v5.x. This is cooperative async: the runtime resumes the coroutine when the I/O completes, but does not preempt it.
- **Build an async scheduler** -- the existing `block_on` + event loop is sufficient for these demos.
- **Implement async iterators or async streams** -- those build on top of the primitives demonstrated here.
- **Touch the optimizer** -- no changes to `mir_opt.py` or `optimizer.py`.
- **Run a panel** -- Phase E has no panel. The next panel is v4.120.0.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Async I/O requires C runtime additions not scoped in this release | medium | medium | Phase 4 explicitly handles this. Budget 1-2 new functions. |
| TCP demo fails because no server is listening | low | low | Use a well-known public endpoint or localhost echo server. Document the requirement. |
| Cooperative async model cannot express real I/O without blocking | low | high | The C runtime already has non-blocking file I/O. Async wraps it with callback or polling. If truly impossible, document the gap honestly. |
| New C runtime functions break ABI for existing binaries | low | medium | New functions are additive. Existing symbols unchanged. Rebuild libmapanare_rt.a. |
| Guide examples drift from actual working code | medium | medium | Phase 5 explicitly verifies every example compiles and runs. |

---

## After v4.115.0

v4.116.0 is the documentation batch: README update with Phase C benchmark numbers, SPEC sync, cookbook refresh, debugging guide, and getting started guide. v4.117.0 hardens the test suite with ASan/TSan CI gates and a flaky test audit.
