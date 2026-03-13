# Mapanare v0.8.0 — "Native Parity"

> v0.7.0 completed the self-hosted compiler pipeline and shipped developer tools.
> v0.8.0 must **close the gap between Python and LLVM backends** so that every core
> feature works natively. No more "Yes on Python, No on LLVM."
>
> Core theme: **LLVM backend completeness and C runtime expansion.**

---

## Scope Rules

1. **LLVM parity** — every feature that works on Python must work on LLVM
2. **C runtime expansion** — add networking and I/O primitives needed for v0.9.0 stdlib
3. **No new language syntax** — v0.8.0 is about the backends, not the grammar
4. **No new stdlib modules** — stdlib rewrite happens in v0.9.0; this version lays the C foundation
5. **Test on both backends** — every test must pass on Python AND LLVM
6. **Honesty** — fix the README feature table to reflect actual state

---

## Status Tracking

| Icon | Meaning |
|------|---------|
| `[ ]` | Not started |
| `[~]` | In progress |
| `[x]` | Done |
| `[!]` | Skipped (reason noted) |

---

## Phase Overview

| Phase | Name | Status | Estimated Effort |
|-------|------|--------|-----------------|
| 1 | LLVM Map/Dict Codegen | `Not Started` | Large — new C runtime data structure + both emitters |
| 2 | LLVM Signal Reactivity | `Not Started` | Large — dependency graph in C runtime |
| 3 | LLVM Stream Operators | `Not Started` | Large — stream runtime in C + MIR emitter |
| 4 | LLVM Closure Capture | `Not Started` | Medium — environment structs + arena integration |
| 5 | Remaining LLVM Gaps | `Not Started` | Medium — string methods, pipes, builtins |
| 6 | C Runtime Expansion | `Not Started` | Large — TCP, TLS, file I/O, event loop |
| 7 | Validation & Release | `Not Started` | Medium — cross-backend tests, README, docs |

---

## Phase 1 — LLVM Map/Dict Codegen
**Priority:** CRITICAL — Maps are a core data type; currently raises NotImplementedError

Maps are the last core collection type missing from the LLVM backend. The Python backend
uses Python dicts; the LLVM backend needs a hash table in the C runtime.

### C Runtime (`runtime/native/`)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Implement hash table in C runtime (`__mn_map_*` family) | `[ ]` | Open addressing with Robin Hood hashing; arena-allocated |
| 2 | `__mn_map_new(key_size, val_size) -> MapPtr` | `[ ]` | Initial capacity 16, load factor 0.75 |
| 3 | `__mn_map_set(map, key_ptr, val_ptr)` | `[ ]` | Insert or update; grow on load threshold |
| 4 | `__mn_map_get(map, key_ptr) -> ValPtr or NULL` | `[ ]` | Returns NULL for missing keys |
| 5 | `__mn_map_del(map, key_ptr) -> Bool` | `[ ]` | Tombstone deletion |
| 6 | `__mn_map_len(map) -> i64` | `[ ]` | Current entry count |
| 7 | `__mn_map_iter_new(map) -> IterPtr` | `[ ]` | Iterator over entries |
| 8 | `__mn_map_iter_next(iter) -> {key_ptr, val_ptr} or NULL` | `[ ]` | Advance iterator |
| 9 | `__mn_map_contains(map, key_ptr) -> Bool` | `[ ]` | Key existence check |
| 10 | Hash functions: `__mn_hash_int`, `__mn_hash_str`, `__mn_hash_float` | `[ ]` | FNV-1a or SipHash |
| 11 | C runtime tests with AddressSanitizer | `[ ]` | Catch memory bugs early |

### LLVM Emitters

| # | Task | Status | Notes |
|---|------|--------|-------|
| 12 | Define LLVM map type: `{ i8* data, i64 len, i64 cap, i64 key_size, i64 val_size }` | `[ ]` | Or opaque pointer to C struct |
| 13 | `emit_llvm.py`: Implement `_emit_map_literal()` — create map, insert each k/v pair | `[ ]` | Replace current NotImplementedError |
| 14 | `emit_llvm.py`: Map indexing — `map[key]` calls `__mn_map_get()` | `[ ]` | Returns `Option<V>` or crashes on missing |
| 15 | `emit_llvm.py`: Map assignment — `map[key] = value` calls `__mn_map_set()` | `[ ]` | |
| 16 | `emit_llvm_mir.py`: `MapInit` instruction — create and populate map | `[ ]` | Replace current stub |
| 17 | `emit_llvm_mir.py`: Map get/set/del via Call instructions | `[ ]` | |
| 18 | `emit_llvm_mir.py`: Map iteration in `for` loops | `[ ]` | Lower to iter_new + iter_next + branch |
| 19 | Tests: map creation, lookup, insertion, deletion, iteration, nested maps | `[ ]` | Both AST and MIR emitters |

**Done when:** `let m: Map<String, Int> = {"a": 1, "b": 2}; println(m["a"])` compiles
and runs via LLVM backend. All existing Python-backend map tests pass on LLVM.

---

## Phase 2 — LLVM Signal Reactivity
**Priority:** CRITICAL — Signals are a headline feature; LLVM has only get/set (no reactivity)

The Python runtime (`runtime/signal.py`) has full reactive signals: dependency tracking,
computed signals, subscriber notification, batched updates. The LLVM backend currently
has opaque pointer get/set — no graph, no reactivity.

### C Runtime

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Design signal dependency graph data structure | `[ ]` | Array of subscriber pointers per signal |
| 2 | `__mn_signal_new(initial_value_ptr, val_size) -> SignalPtr` | `[ ]` | Arena-allocated signal node |
| 3 | `__mn_signal_get(signal) -> ValuePtr` | `[ ]` | Read current value + register dependency if in computed context |
| 4 | `__mn_signal_set(signal, value_ptr)` | `[ ]` | Write value + trigger subscriber notification |
| 5 | `__mn_signal_computed(compute_fn, deps, n_deps) -> SignalPtr` | `[ ]` | Lazy recomputation on dependency change |
| 6 | `__mn_signal_subscribe(signal, callback_fn)` | `[ ]` | Add subscriber to notification list |
| 7 | `__mn_signal_batch_begin()` / `__mn_signal_batch_end()` | `[ ]` | Defer propagation until batch end |
| 8 | `__mn_signal_unsubscribe(signal, callback_fn)` | `[ ]` | Remove subscriber |
| 9 | Topological sort for propagation order | `[ ]` | Prevent glitches (stale reads) |
| 10 | Tests: dependency tracking, computed, batch, diamond dependency | `[ ]` | |

### LLVM Emitters

| # | Task | Status | Notes |
|---|------|--------|-------|
| 11 | Update `SignalInit` to call `__mn_signal_new()` with proper size | `[ ]` | |
| 12 | Update `SignalGet` to call `__mn_signal_get()` with dependency tracking | `[ ]` | |
| 13 | Update `SignalSet` to call `__mn_signal_set()` with notification | `[ ]` | |
| 14 | Add `SignalComputed` instruction handling | `[ ]` | |
| 15 | Add `SignalSubscribe` instruction handling | `[ ]` | |
| 16 | Tests: signal reactivity end-to-end on LLVM backend | `[ ]` | |

**Done when:** `let a = signal(1); let b = computed(fn() { a.get() * 2 }); a.set(5); assert b.get() == 10`
works on LLVM backend with automatic recomputation.

---

## Phase 3 — LLVM Stream Operators
**Priority:** HIGH — Streams + pipe operator are a language differentiator

The Python runtime (`runtime/stream.py`) has full streams: cold/hot, operators
(map/filter/take/skip/collect/fold/etc.), backpressure, fusion. The MIR LLVM emitter
has a pass-through stub.

### C Runtime

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Design native stream representation | `[ ]` | Iterator-based: `{ next_fn, state_ptr, done_flag }` |
| 2 | `__mn_stream_from_list(list_ptr) -> StreamPtr` | `[ ]` | Create stream from list |
| 3 | `__mn_stream_map(stream, map_fn) -> StreamPtr` | `[ ]` | Lazy transform |
| 4 | `__mn_stream_filter(stream, pred_fn) -> StreamPtr` | `[ ]` | Lazy filter |
| 5 | `__mn_stream_take(stream, n) -> StreamPtr` | `[ ]` | First N elements |
| 6 | `__mn_stream_skip(stream, n) -> StreamPtr` | `[ ]` | Skip N elements |
| 7 | `__mn_stream_collect(stream) -> ListPtr` | `[ ]` | Terminal: consume into list |
| 8 | `__mn_stream_fold(stream, init, fold_fn) -> ValuePtr` | `[ ]` | Terminal: reduce |
| 9 | `__mn_stream_next(stream) -> {value_ptr, done}` | `[ ]` | Pull next element |
| 10 | `__mn_stream_bounded(stream, capacity) -> StreamPtr` | `[ ]` | Backpressure via bounded buffer |
| 11 | Stream fusion: collapse adjacent map/filter in MIR optimizer | `[ ]` | |
| 12 | Tests: stream creation, operators, collect, backpressure | `[ ]` | |

### LLVM Emitters

| # | Task | Status | Notes |
|---|------|--------|-------|
| 13 | Replace `StreamOp` stub with real stream instruction dispatch | `[ ]` | |
| 14 | Pipe operator (`\|>`) targets stream operations when RHS is stream op | `[ ]` | |
| 15 | `for x in stream { ... }` → `stream_next` loop | `[ ]` | |
| 16 | Tests: stream pipelines end-to-end on LLVM | `[ ]` | |

**Done when:** `[1, 2, 3, 4, 5] |> stream() |> filter(fn(x) { x > 2 }) |> map(fn(x) { x * 10 }) |> collect()`
returns `[30, 40, 50]` on LLVM backend.

---

## Phase 4 — LLVM Closure Capture
**Priority:** HIGH — closures are fundamental; currently no variable capture

The LLVM backend emits anonymous functions but does NOT capture free variables.
Any lambda that references outer scope variables will fail.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Design closure representation: `{ fn_ptr, env_ptr }` | `[ ]` | Environment is a struct of captured values |
| 2 | Analyze lambda body for free variables | `[ ]` | Walk AST/MIR, find references outside lambda scope |
| 3 | Generate environment struct type per lambda | `[ ]` | `{ captured_var_1: T1, captured_var_2: T2, ... }` |
| 4 | Allocate environment on arena, populate with captured values | `[ ]` | Copy values into env struct |
| 5 | Modify lambda function signature: add `env_ptr` as first param | `[ ]` | Lambda becomes `fn(env_ptr, params...) -> ret` |
| 6 | At call site: extract `fn_ptr` and `env_ptr`, call with env | `[ ]` | Indirect call through function pointer |
| 7 | Handle mutable captures (capture by reference vs by value) | `[ ]` | By value default; `mut` captures get pointer in env |
| 8 | MIR emitter: closure capture in `emit_llvm_mir.py` | `[ ]` | |
| 9 | AST emitter: closure capture in `emit_llvm.py` | `[ ]` | |
| 10 | Tests: capture immutable, capture mutable, nested closures | `[ ]` | |
| 11 | Test: closure passed as argument, closure returned from function | `[ ]` | |

**Done when:** `let x = 10; let f = fn(y: Int) -> Int { x + y }; assert f(5) == 15`
works on LLVM backend.

---

## Phase 5 — Remaining LLVM Gaps
**Priority:** MEDIUM — completeness sweep

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | String method: `.contains(needle)` | `[ ]` | `__mn_str_contains()` in C runtime |
| 2 | String method: `.split(delimiter)` | `[ ]` | Returns `List<String>` |
| 3 | String method: `.trim()` / `.trim_start()` / `.trim_end()` | `[ ]` | |
| 4 | String method: `.to_upper()` / `.to_lower()` | `[ ]` | |
| 5 | String method: `.replace(old, new)` | `[ ]` | |
| 6 | Pipe definitions: `pipe Transform { A \|> B \|> C }` on LLVM | `[ ]` | Compile to agent spawn chain |
| 7 | `while` loop with `break`/`continue` on LLVM | `[ ]` | Verify both emitters handle this |
| 8 | Nested pattern matching (match inside match) | `[ ]` | |
| 9 | String interpolation on LLVM backend | `[ ]` | Verify `InterpConcat` MIR instruction works |
| 10 | `?` operator (Result/Option early return) on LLVM | `[ ]` | Verify unwrap + branch emitted correctly |
| 11 | Verify all 25 TypeKind variants handled in LLVM type mapping | `[ ]` | |
| 12 | Cross-backend consistency test suite | `[ ]` | Run identical .mn files on both backends, diff outputs |

**Done when:** No feature in the README table says "No" or "Partial" for LLVM
when the Python backend says "Yes" (except planned experimental features).

---

## Phase 6 — C Runtime Expansion
**Priority:** HIGH — foundation for v0.9.0 native stdlib

v0.9.0 writes stdlib modules in `.mn`, but they need low-level primitives in the C runtime
to talk to the OS. This phase adds those primitives. No Mapanare-level API yet — just
the C functions that `net/http.mn` and `encoding/json.mn` will call in v0.9.0.

### Networking

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | `__mn_tcp_connect(host, port) -> fd` | `[ ]` | DNS resolution + connect |
| 2 | `__mn_tcp_listen(host, port, backlog) -> fd` | `[ ]` | Bind + listen |
| 3 | `__mn_tcp_accept(listen_fd) -> fd` | `[ ]` | Accept incoming connection |
| 4 | `__mn_tcp_send(fd, buf, len) -> bytes_sent` | `[ ]` | |
| 5 | `__mn_tcp_recv(fd, buf, len) -> bytes_received` | `[ ]` | |
| 6 | `__mn_tcp_close(fd)` | `[ ]` | |
| 7 | `__mn_tcp_set_timeout(fd, ms)` | `[ ]` | SO_RCVTIMEO / SO_SNDTIMEO |
| 8 | Cross-platform: Winsock on Windows, POSIX sockets on Unix | `[ ]` | `#ifdef _WIN32` |

### TLS (via OpenSSL FFI)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 9 | `__mn_tls_init()` — initialize OpenSSL | `[ ]` | One-time global init |
| 10 | `__mn_tls_connect(fd, hostname) -> tls_ctx` | `[ ]` | SNI + certificate verification |
| 11 | `__mn_tls_read(tls_ctx, buf, len) -> bytes` | `[ ]` | |
| 12 | `__mn_tls_write(tls_ctx, buf, len) -> bytes` | `[ ]` | |
| 13 | `__mn_tls_close(tls_ctx)` | `[ ]` | |
| 14 | Link against OpenSSL/LibreSSL at build time | `[ ]` | `-lssl -lcrypto` |

### File I/O (extended)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 15 | `__mn_file_open(path, mode) -> fd` | `[ ]` | Modes: read, write, append, create |
| 16 | `__mn_file_read(fd, buf, len) -> bytes` | `[ ]` | |
| 17 | `__mn_file_write(fd, buf, len) -> bytes` | `[ ]` | |
| 18 | `__mn_file_close(fd)` | `[ ]` | |
| 19 | `__mn_file_stat(path) -> {size, mtime, is_dir}` | `[ ]` | |
| 20 | `__mn_dir_list(path) -> entries` | `[ ]` | |

### Event Loop

| # | Task | Status | Notes |
|---|------|--------|-------|
| 21 | `__mn_event_loop_new() -> loop_ptr` | `[ ]` | |
| 22 | `__mn_event_loop_add_fd(loop, fd, events, callback)` | `[ ]` | |
| 23 | `__mn_event_loop_remove_fd(loop, fd)` | `[ ]` | |
| 24 | `__mn_event_loop_run(loop)` | `[ ]` | Blocks until no more fds |
| 25 | `__mn_event_loop_run_once(loop, timeout_ms)` | `[ ]` | Single iteration |
| 26 | Platform backends: `epoll` (Linux), `kqueue` (macOS), `IOCP` (Windows) | `[ ]` | |

### Tests

| # | Task | Status | Notes |
|---|------|--------|-------|
| 27 | TCP echo server test (connect, send, receive, close) | `[ ]` | |
| 28 | TLS connection test (connect to HTTPS endpoint) | `[ ]` | |
| 29 | File I/O round-trip test (write, read, verify) | `[ ]` | |
| 30 | Event loop test (multi-fd, timeout, callback dispatch) | `[ ]` | |
| 31 | All tests with AddressSanitizer and ThreadSanitizer | `[ ]` | |

**Done when:** A `.mn` program can open a TCP socket, send/receive data, and close it
via the C runtime primitives. TLS connections work. File I/O works beyond stdio.

---

## Phase 7 — Validation & Release
**Priority:** MEDIUM — wrap up the release

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Run full test suite — both backends, confirm 100% pass rate | `[ ]` | |
| 2 | Update README feature status table to reflect reality | `[ ]` | Remove false claims, update all Partial/No entries |
| 3 | Remove REPL claim from README (doesn't exist) | `[ ]` | |
| 4 | Fix tensor status (no language integration) | `[ ]` | |
| 5 | Write CHANGELOG entry for v0.8.0 | `[ ]` | |
| 6 | Bump VERSION to 0.8.0 | `[ ]` | |
| 7 | Update SPEC.md with any new semantics (closures, maps on LLVM) | `[ ]` | |
| 8 | Update ROADMAP.md with v0.8.0 completion | `[ ]` | |
| 9 | Performance benchmarks: compare v0.7.0 → v0.8.0 native performance | `[ ]` | |
| 10 | Update `mapanare.dev` website with v0.8.0 release notes | `[ ]` | |

**Done when:** VERSION reads `0.8.0`. Every "Yes" on Python backend is "Yes" on LLVM
for core features. Feature table is honest. C runtime has networking primitives ready
for v0.9.0 stdlib.

---

## What v0.8.0 Does NOT Include

| Item | Deferred To | Reason |
|------|-------------|--------|
| Stdlib modules in .mn | v0.9.0 | Needs C runtime primitives from Phase 6 first |
| JSON/CSV/YAML parsers | v0.9.0 | Stdlib |
| HTTP client/server in .mn | v0.9.0 | Stdlib, needs TCP + TLS from Phase 6 |
| Cross-module LLVM compilation | v0.9.0 | Needed for stdlib imports, not core features |
| Self-hosted fixed-point | v1.0.0 | Needs cross-module compilation |
| New language syntax | v0.9.0+ | v0.8.0 is backends only |
| AI/LLM drivers | v1.1.0 | Needs HTTP client first |
| Database drivers | v1.2.0 | Needs stable stdlib first |

---

## Success Criteria for v0.8.0

v0.8.0 ships when ALL of the following are true:

1. **Maps work on LLVM:** Map literals, indexing, insertion, iteration compile and run natively.
2. **Signals are reactive on LLVM:** Computed signals auto-recompute when dependencies change.
3. **Streams work on LLVM:** `stream() |> map() |> filter() |> collect()` produces correct output natively.
4. **Closures capture on LLVM:** Lambdas can reference variables from enclosing scope.
5. **Feature table is honest:** README reflects actual implementation state on both backends.
6. **C runtime has networking:** TCP sockets, TLS, file I/O, and event loop primitives exist and are tested.
7. **Cross-backend tests:** A shared test suite runs the same `.mn` programs on both backends and verifies identical output.
8. **All existing tests pass:** No regressions from v0.7.0.

---

## Priority Order

If time is limited, ship in this order:

1. **Phase 1** (Maps — core data type, currently broken on LLVM)
2. **Phase 4** (Closures — fundamental language feature, blocks higher-order patterns)
3. **Phase 2** (Signals — headline feature, key differentiator)
4. **Phase 3** (Streams — headline feature, key differentiator)
5. **Phase 6** (C runtime expansion — unblocks v0.9.0)
6. **Phase 5** (Remaining gaps — completeness sweep)
7. **Phase 7** (Release — ceremonial once the rest lands)

---

*"A language with two backends where only one works isn't a choice — it's a trap."*
