# v4.24.0 — async/await Runtime Wiring — Continuation Prompt

> Wire async/await to streams, agents, and ring buffers.
> You are in WSL. Rebuild + golden + stage2 after every change.
> Run lint before every commit. The golden test must show ACTUAL async
> behavior — not just keyword parsing.

---

## Context

v4.19.0 added `async`/`await` as grammar keywords. The parser produces:
- `async fn` → `FnDef` with `@async` decorator
- `await expr` → `AwaitExpr` AST node

But neither does anything at runtime. This version connects them to the
existing runtime infrastructure that ALREADY works:

| Infrastructure | Where | Status |
|---------------|-------|--------|
| Stream type (map/filter/take/skip/collect/fold) | `mapanare/lower.py`, `emit_llvm_text.py` | Working on LLVM |
| Agent cooperative scheduler | `runtime/native/mapanare_runtime.c` | Working |
| SPSC ring buffer (lock-free, backpressure) | `runtime/native/mapanare_core.c` | Working |
| `__mn_agent_spawn` / `__mn_agent_send` / `__mn_agent_sync` | `runtime/native/mapanare_runtime.c` | Declared in emitter |
| `StreamOp` MIR instruction | `mapanare/mir.py` | Exists |
| `StreamInit` MIR instruction | `mapanare/mir.py` | Exists |

The approach: `async fn` creates a stream backed by the SPSC ring buffer.
The function body runs in a spawned cooperative task. `await` calls
`__mn_agent_sync` to consume the next value.

## The Design

```
async fn produce(n: Int) -> Stream<Int> {
    for i in 0..n {
        yield i        // pushes to ring buffer
    }
}

fn main() {
    let s: Stream<Int> = produce(10)
    let val: Int = await s   // blocks cooperatively until value available
    print(val)
}
```

For v4.24.0, we implement a simpler model:
- `async fn foo(args) -> T` lowers to: spawn a task that runs `foo(args)`,
  push the return value to a ring buffer, return the buffer as a stream-like
  handle.
- `await handle` consumes the value from the handle (blocks cooperatively).

This is essentially a one-shot future over the existing agent infrastructure.

## Key Files

| File | What Changes |
|------|-------------|
| `mapanare/lower.py:780-810` | `_lower_definition` — detect `@async` decorator, lower differently |
| `mapanare/lower.py:1470-1485` | `_lower_identifier` — handle `await` in expression lowering |
| `mapanare/lower.py:1035-1060` | `_lower_stmt` — handle `AwaitExpr` as statement |
| `mapanare/mir.py` | May need `AsyncSpawn` instruction or reuse `Call` |
| `mapanare/emit_llvm_text.py` | Emit `__mn_agent_spawn` + `__mn_agent_sync` calls |
| `mapanare/semantic.py` | Validate `await` only in async context, type of `await Stream<T>` is `T` |
| `mapanare/self/lower.mn` | Self-hosted: handle `@async` + `await` |
| `mapanare/self/emit_llvm.mn` | Self-hosted: emit spawn + sync |
| `runtime/native/mapanare_runtime.c` | Already has `__mn_agent_spawn`, `__mn_agent_sync` |

## The Golden Test (must show real behavior)

```mapanare
// tests/golden/46_async_stream.mn
async fn compute(x: Int) -> Int {
    return x * 2
}

fn main() {
    let result: Int = await compute(21)
    print(result)  // must print 42
}
```

This test MUST:
1. Compile through the Python bootstrap
2. Compile through mnc-stage1
3. Run via `lli` or compiled binary
4. Print `42` (not crash, not print nothing)

If this can't work with lli (which lacks threading), an alternative:
inline the async function (since it's single-threaded anyway) and test
the lowering/emission path. But the test must show the value flows through.

## Commands

```bash
# After every change
bash scripts/rebuild.sh

# Test the async golden test specifically
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 --filter 46_async

# All golden
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# Stage2
python3 scripts/ir_doctor.py stage2 --timeout 60

# Run the async test via lli (if available)
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 --run --filter 46_async

# Lint
black --check . && ruff check . && mypy mapanare/
```

## Rules

- Python lowerer FIRST (lower.py + emit_llvm_text.py), then self-hosted (.mn)
- The golden test must produce correct output (not just compile)
- If lli can't run async (no threads), use single-threaded inline as fallback
- Do NOT just add syntax — the value must flow from async fn to await site
- Test with BOTH Python bootstrap and stage1

## Exit Criteria with Proof Commands

| Criterion | Proof Command |
|-----------|---------------|
| async fn compiles | `python3 -m mapanare emit-llvm tests/golden/46_async_stream.mn` succeeds |
| await expr compiles | Same as above |
| Golden test passes | `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 --filter 46` |
| Value flows through | Golden test output contains expected value |
| Stage2 valid | `python3 scripts/ir_doctor.py stage2 --timeout 60` → "11/11" |
| Lint clean | `black --check . && ruff check . && mypy mapanare/` |
