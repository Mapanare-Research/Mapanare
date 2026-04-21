# Mapanare v4.74.0 — Stream Async Iterator + `for await`

> **Arc 9 release 3.** Adds `for await chunk in stream { ... }`
> syntax. `Stream<T>` gains an async iterator interface via
> `next() -> Future<Option<T>>`. Delta review mandatory (new
> syntactic form).

**Status:** DONE (2026-04-13)
**Session log:** for await grammar, AST, parser, semantic, lowering. 5 new tests. Delta review PASS (Rattler + Coral).
**Decisions taken:** for await is sugar (desugars to for loop). No cancellation on break (v5.x). Stream close via None in Option. Inline-resume model from v4.73.0 handles async producers.
**Breaking:** No
**Prerequisite:** v4.73.0 (scheduler + `block_on` + basic coroutines runnable)
**Delta review:** **YES** — new syntax (`for await`). Rattler primary.
**Full panel:** No (v4.76.0)
**Estimated work:** 1.5 sprints
**Theme:** Streams become async-aware. The v4.47.0 `chat_stream` demo from arc 4 becomes real streaming instead of blocking per chunk.

---

## Scope

### Syntax

```mapanare
async fn process_stream(s: Stream<Int>) {
    for await x in s {
        print(x)
    }
}
```

Equivalent to:
```mapanare
async fn process_stream(s: Stream<Int>) {
    loop {
        match await s.next() {
            Some(x) => print(x),
            None => break,
        }
    }
}
```

### Stream API addition

`Stream<T>` gains:
- `next() -> Future<Option<T>>` — returns the next element, or `Option::None` if the stream has ended

---

## Phase 1 — Grammar

- [ ] `mapanare/mapanare.lark`:
  ```
  for_await_stmt: "for" "await" pattern "in" expression block
  ```
- [ ] Alternative to existing `for_stmt`. Disambiguate by the `await` keyword after `for`.

## Phase 2 — AST

- [ ] `mapanare/ast_nodes.py`:
  ```python
  @dataclass
  class ForAwait(Stmt):
      pattern: Pattern
      iterable: Expr
      body: Block
      span: Span
  ```

## Phase 3 — Parser

- [ ] `mapanare/parser.py` — `for_await_stmt` transformer constructs `ForAwait`

## Phase 4 — Semantic

- [ ] `mapanare/semantic.py` `check_for_await(node: ForAwait) -> None`:
  - Enclosing function must be async (same as `await`)
  - `iterable` must be `Stream<T>` for some T
  - Pattern must be compatible with T
  - Body is type-checked in a scope with the pattern bindings

## Phase 5 — Lowering

- [ ] `mapanare/lower.py` `_lower_for_await(node: ForAwait) -> None`:
  - Desugars to:
    ```
    %stream = lower(iterable)
    loop_header:
      %future = call stream.next()
      %result = await %future  ; emits coro save + suspend + resume
      match %result {
        Some(x) => bind pattern, run body, continue
        None => break
      }
    ```
  - Reuses the v4.34.0 match lowering + v4.72.0 await lowering

## Phase 6 — Stream runtime extension

- [ ] `runtime/native/mapanare_core.c` — extend `MnStream<T>` with a `next_async` operation:
  - Returns a `Future<Option<T>>` immediately
  - The scheduler drives the future to readiness when the next element is available
  - Implementation: backed by the existing `Stream<T>` ring-buffer + condition variable; `next_async` creates a future that becomes ready when the ring has data or the stream closes
- [ ] `__mn_stream_next_async(stream_ptr) -> Future<Option<T>>` runtime function

## Phase 7 — Stdlib Stream update

- [ ] Existing `Stream<T>` primitive exposes `.next_async()` as a method. All user code calling it should get back a `Future<Option<T>>`.
- [ ] Backwards-compat: existing `Stream<T>` synchronous operations (`map`, `filter`, etc.) keep working; `for` loop over a stream without `await` still works synchronously.

## Phase 8 — `chat_stream` upgrade

- [ ] `stdlib/ai/llm.mn` — `chat_stream` was written in v4.47.0 as a sync-blocking-per-chunk stream. v4.74.0 rewrites it as a real async stream.
- [ ] Update the v4.50.0 `chat_agent.mn` demo to use `for await chunk in stream`:
  ```mapanare
  async fn handle_user_message(self: Chatbot, msg: String) -> String {
      self.history.push(llm::Message::user(msg))
      let stream = self.client.chat_stream(self.history)
      let mut response = String::new()
      for await chunk in stream {
          response.push_str(chunk.content)
      }
      self.history.push(llm::Message::assistant(response))
      return response
  }
  ```
- [ ] This is the v4.50.0 demo working the way it always should have.

## Phase 9 — Self-hosted mirror

- [ ] Grammar, AST, parser, semantic, lowering all mirrored
- [ ] Fixed-point diff still 0

## Phase 10 — Delta review

- [ ] Rattler primary (lowering + emitter)
- [ ] Coral secondary (syntax)
- [ ] File: `.reviews/deltas/v4.74.0-for-await.md`

## Phase 11 — Tests

- [ ] `tests/parser/test_for_await.py` — parse cases
- [ ] `tests/semantic/test_for_await.py` — semantic rules
- [ ] `tests/llvm/test_for_await_lowering.py` — IR inspection
- [ ] `tests/runtime/test_stream_async_iterator.py` — end-to-end: create a stream, push 10 items, iterate with `for await`, verify all 10 received
- [ ] `tests/stdlib/ai/test_chat_stream_async.py` — the v4.50.0 chat_stream demo now works with real async

## Phase 12 — LOW sweep

2 items.

## Phase 13 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.74.0
- [ ] `CHANGELOG.md [4.74.0]` — `for await` + Stream async iterator
- [ ] SESSION_REPORT

---

## Exit criteria (14 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Grammar accepts `for await x in s` | parser test |
| 2 | `ForAwait` AST node real | grep |
| 3 | Semantic rejects `for await` outside async fn | test |
| 4 | Semantic rejects `for await` on non-Stream | test |
| 5 | Lowering desugars to loop+await+match | IR inspection |
| 6 | `Stream<T>.next_async()` returns Future<Option<T>> | compile test |
| 7 | Runtime scheduler drives stream futures | runtime test |
| 8 | Empty stream handled (break immediately) | `test_empty_stream` |
| 9 | 10-item stream iterated correctly | `test_stream_async_iterator` |
| 10 | Upgraded `chat_stream` demo runs async | integration log |
| 11 | Delta review PASS | `.reviews/deltas/v4.74.0-for-await.md` |
| 12 | Fixed-point diff still 0 | verify |
| 13 | Self-hosted mirror compiles | rebuild |
| 14 | Standard closeout clean | CI |

---

## What v4.74.0 does NOT do

- **Async `map`/`filter`/`take` on streams** — sync versions still exist; async versions are v5.x
- **Stream combinators across coroutine boundaries** — v5.x
- **Stream cancellation** — v5.x

---

## Reference

- [`v4.47.0/PLAN.md`](../v4.47.0/PLAN.md) — the chat_stream v4.47.0 version
- [`v4.50.0/PLAN.md`](../v4.50.0/PLAN.md) — the chat_agent demo v4.74.0 upgrades

---

## After v4.74.0

v4.75.0 is the final integration release: end-to-end async golden test, `http_fanout` demo, updated cookbook chapter.
