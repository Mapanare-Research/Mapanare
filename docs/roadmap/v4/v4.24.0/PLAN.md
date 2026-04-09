# Mapanare v4.24.0 — async/await Runtime Wiring

> async fn returns a Stream. await consumes cooperatively. Backpressure built in.

**Status:** DONE (single-threaded inline model — async fn runs synchronously, await unwraps result)
**Breaking:** No
**Prerequisite:** v4.23.0

---

## The Problem

v4.19.0 added `async`/`await` as grammar keywords but no runtime behavior.
The keywords parse and the AST nodes exist, but:
- `async fn` doesn't create a stream or spawn a task
- `await` doesn't consume from a stream
- No cooperative scheduling integration
- No backpressure via ring buffers

This version wires the syntax to the existing runtime infrastructure:
streams, agents, and SPSC ring buffers.

---

## Phase 1: MIR lowering for async fn

- [ ] `async fn` lowers to: create SPSC ring buffer → spawn cooperative task → return Stream
- [ ] The task body is the original function body, pushing results to the channel
- [ ] Add `AsyncSpawn` MIR instruction (or reuse AgentSpawn)
- [ ] Update `mapanare/lower.py` to handle `@async` decorator on FnDef

## Phase 2: MIR lowering for await

- [ ] `await stream_expr` lowers to: call `__mn_stream_next(stream)` → cooperative yield
- [ ] Add `AwaitExpr` handling in `_lower_expr` in `mapanare/lower.py`
- [ ] Type: `await Stream<T>` has type `T`

## Phase 3: LLVM emission

- [ ] Emit ring buffer allocation: `call @__mn_spsc_create(elem_size)`
- [ ] Emit task spawn: `call @__mn_agent_spawn_task(fn_ptr, channel)`
- [ ] Emit await: `call @__mn_stream_next(stream)` with cooperative yield
- [ ] Emit backpressure: if buffer full, producer yields before pushing

## Phase 4: Self-hosted compiler

- [ ] Add `async fn` handling in self-hosted parser (already recognizes keyword)
- [ ] Add AwaitExpr lowering in self-hosted lower.mn
- [ ] Rebuild + golden + stage2

## Phase 5: Golden tests

- [ ] `tests/golden/46_async_stream.mn` — async fn produces stream, consumer awaits
- [ ] `tests/golden/47_async_pipeline.mn` — producer | transform | consumer
- [ ] All tests run natively via lli or compiled binary

---

## Exit Criteria

| Check | Required |
|-------|----------|
| async fn creates stream backed by ring buffer | YES |
| await consumes from stream cooperatively | YES |
| Backpressure works (full buffer yields) | YES |
| Golden tests for async patterns | YES |
| 47/47+ golden | YES |
| 11/11 stage2 | YES |
