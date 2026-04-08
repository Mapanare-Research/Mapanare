# Mapanare v3.43.0 — "Mapanare" (Agent Runtime Native)

> Agents work from native binaries with real OS threads.
> spawn, send (<-), sync — the core concurrency model.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v3.42.0 (network native)

---

## The Problem

The agent runtime (`mapanare_runtime.c`) has a thread pool, lock-free ring
buffers, agent lifecycle management, and graceful shutdown. None of it is
linked into native binaries. Agents only work in the Python interpreter.

---

## Checklist

### 1. Link Agent Runtime

- [ ] `scripts/build_stage1.py`: compile + link `mapanare_runtime.c`
- [ ] Link flags: `-lpthread` (already implied by mapanare_runtime.c)
- [ ] Verify with `nm mnc-stage1 | grep __mn_agent` — symbols present

### 2. LLVM Emitter — Agent IR

- [ ] Declare all agent functions in `emit_llvm_text.py`:
  - `__mn_agent_create`, `__mn_agent_start`, `__mn_agent_stop`
  - `__mn_agent_send`, `__mn_agent_recv`, `__mn_agent_sync`
  - `__mn_ring_new`, `__mn_ring_push`, `__mn_ring_pop`
  - `__mn_threadpool_create`, `__mn_threadpool_submit`, `__mn_threadpool_destroy`
- [ ] `spawn Agent()` → `__mn_agent_create` + `__mn_agent_start`
- [ ] `agent.input <- value` → `__mn_agent_send`
- [ ] `sync agent.output` → `__mn_agent_sync`

### 3. Golden Tests

- [ ] `40_agent_basic.mn` — spawn, send message, sync response
- [ ] `41_agent_pipeline.mn` — 3-stage pipeline with typed channels
- [ ] `42_agent_concurrent.mn` — fan-out: spawn 4 workers, collect results

### 4. Culebra Validation

- [ ] `culebra scan` on agent IR — check for race patterns
- [ ] `culebra triage` — zero critical

---

## Exit Criteria

```mn
agent Counter {
    input increment: Int
    output total: Int
    state count: Int = 0

    fn handle(n: Int) -> Int {
        count += n
        return count
    }
}

fn main() {
    let c = spawn Counter()
    c.increment <- 5
    c.increment <- 3
    let result = sync c.total
    print("Total: " + str(result))  // Total: 8
}
```
