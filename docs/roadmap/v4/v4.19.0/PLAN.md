# Mapanare v4.19.0 — Reactive Async (async/await + Streams)

> async/await tied to Streams. No separate futures. Backpressure built in.

**Status:** DONE (syntax + parsing, runtime wiring deferred)
**Breaking:** No
**Prerequisite:** v4.18.0

---

## The Goal

Mapanare's async model is unique: **Streams ARE the async primitive.** There
are no separate Future or Promise types. An `async fn` returns a `Stream`,
and `await` consumes from it. Backpressure comes from the ring buffer
semantics already implemented in the C runtime's SPSC channels.

This design unifies three existing features:
- **Streams** (map/filter/take/skip/collect/fold — already on LLVM)
- **Agents** (cooperative scheduling, message passing — already on LLVM)
- **Ring buffers** (lock-free SPSC with backpressure — in C runtime)

The new syntax makes these accessible without manually wiring agents and
channels.

---

## Phase 1: async/await keywords

- [ ] Add `async` and `await` keywords to grammar (`mapanare.lark`)
- [ ] `async fn fetch(url: String) -> Stream<String>` — declares an async function
- [ ] `let result = await some_stream` — consumes next value from stream
- [ ] `await` on a non-Stream type is a compile-time error
- [ ] Parser produces `AsyncFnDef` and `AwaitExpr` AST nodes
- [ ] Rebuild + golden

## Phase 2: Semantic analysis

- [ ] `async fn` return type must be `Stream<T>` for some `T`
- [ ] `await` is only valid inside `async fn` (not in regular fn)
- [ ] Nested `await` is allowed (await inside async fn that awaits another)
- [ ] Type inference: `await stream_of_int` has type `Int`
- [ ] Add tests: `tests/semantic/test_async.py`

## Phase 3: MIR lowering

- [ ] `async fn` lowers to:
  1. Create a ring buffer (SPSC channel)
  2. Spawn a cooperative task on the agent scheduler
  3. The task runs the function body, pushing results into the channel
  4. Return the channel's read end as a `Stream`
- [ ] `await expr` lowers to:
  1. Evaluate `expr` to get a Stream
  2. Call `stream_next()` — blocks cooperatively (yields to scheduler)
  3. Result is the next value from the stream
- [ ] Use existing `MIRInstruction` types where possible
- [ ] Add new MIR instructions only if strictly necessary
- [ ] Rebuild + golden

## Phase 4: LLVM emission

- [ ] Emit ring buffer allocation via C runtime (`__mn_spsc_create`)
- [ ] Emit task spawn via agent scheduler (`__mn_agent_spawn_task`)
- [ ] Emit cooperative yield in `await` (`__mn_agent_yield`)
- [ ] Emit stream consumption via `__mn_stream_next`
- [ ] Wire backpressure: if ring buffer is full, producer yields
- [ ] Rebuild + golden + stage2

## Phase 5: Self-hosted compiler support

- [ ] Add `async` and `await` to self-hosted lexer (`lexer.mn`)
- [ ] Add AST nodes to self-hosted parser (`parser.mn`)
- [ ] Add lowering to self-hosted compiler (`lower.mn`)
- [ ] Rebuild + golden + stage2 + fixed-point

## Phase 6: Examples and tests

- [ ] `examples/async/fetch.mn` — async HTTP fetch (uses existing TCP/TLS)
- [ ] `examples/async/pipeline.mn` — producer | transform | consumer
- [ ] `tests/golden/43_async_basic.mn` — basic async/await
- [ ] `tests/golden/44_async_pipeline.mn` — stream pipeline with backpressure
- [ ] All examples compile and run natively

---

## Exit Criteria

| Check | Required |
|-------|----------|
| async fn syntax parsed and type-checked | YES |
| await syntax parsed and type-checked | YES |
| async fn returns Stream backed by ring buffer | YES |
| await consumes from stream cooperatively | YES |
| Backpressure works (full buffer causes yield) | YES |
| Self-hosted compiler supports async/await | YES |
| Golden tests for async patterns | YES |
| 40/40+ golden (new tests added) | YES |
| 11/11 stage2 | YES |
| Fixed-point preserved | YES |
