# v4.150.0 E6 IR/Source Diff — Async Agent Scheduler

## 1. Lever A — empty-wake sem_post

**Go (buffered channel send path):**
```go
// runtime/chan.go::chansend (simplified)
func chansend(c *hchan, ep unsafe.Pointer) {
    lock(&c.lock)
    // ...enqueue element to buffer...
    if sg := c.recvq.dequeue(); sg != nil {
        // A goroutine is waiting to receive — wake it
        goready(sg.g, 3)   // ← only wakes when a receiver is parked
    }
    unlock(&c.lock)
}
```
Go only calls `goready` (the wake primitive) when there's a goroutine
*actually blocked* in the receive queue. If the receiver hasn't parked
yet, no wake is issued — the receiver finds the value in the buffer on
its next poll.

**Mapanare (current — unconditional sem_post):**
```c
// runtime/native/mapanare_runtime.c::mapanare_agent_send (lines 643-656)
int mapanare_agent_send(mapanare_agent_t *agent, void *msg) {
    mapanare_mutex_lock(&agent->inbox_producer_lock);
    int rc = mapanare_ring_push(&agent->inbox, msg);
    mapanare_mutex_unlock(&agent->inbox_producer_lock);
    if (rc == 0) {
        mapanare_bp_increment(&agent->bp);
        mapanare_sem_post(&agent->inbox_ready);   // ← EVERY send, unconditional
        trace_emit(MAPANARE_TRACE_SEND, agent, msg, 0);
    }
    return rc;
}
```
Every send performs `sem_post` even when the worker is still running
(processing a previous message or in the `ring_pop → dispatch → loop`
cycle). For sequential agents that process one message and exit, the
worker thread is almost never in `sem_wait` when send is called — the
spawn itself starts the worker, which finds the inbox empty and blocks.
The first send wakes it, but for multi-message workloads subsequent
sends waste an atomic increment on the semaphore.

**Missing check:** Snapshot ring emptiness before push. If the ring was
non-empty pre-push, the worker is either dispatching or about to
loop back to `ring_pop` — no wake needed.

---

## 2. Lever B — inline small-message payload

**Go (buffered channel — value copy to ring slot):**
```go
// runtime/chan.go::chansend (buf path)
// Element is memcopied directly into the circular buffer slot.
// No heap allocation for small values (int, pointer, small struct).
typedmemmove(c.elemtype, qp, ep)  // value → buf[sendx]
```
Go channels store values *inline* in the ring buffer. For `chan int`,
each slot is 8 bytes — no pointer indirection, no malloc per send.

**Mapanare (current — heap envelope via void*):**
```c
// The ring stores void* pointers. The emitter allocates a message on
// the heap for every agent send:
//   %msg = call ptr @malloc(i64 8)
//   store i64 %value, ptr %msg
//   call i32 @mapanare_agent_send(%agent, ptr %msg)
// Worker handler receives (void *msg), casts to payload type.
// mapanare_agent_destroy calls free() on each remaining message.
```
Every send allocates, every recv frees. For a 100-message sequential
chain, that's 100 malloc + 100 free — O(n) heap overhead that Go
avoids entirely with inline buffer slots.

**Threshold candidate:** Messages ≤ 16 bytes (covers Int, Float, Bool,
single-field structs) could be stored inline in the ring slot via a
tagged union: `{ uint8_t kind; union { uint8_t buf[16]; void *ptr; }; }`.

---

## 3. Lever C — spin-before-park

**Go (findRunnable spin state):**
```go
// runtime/proc.go::findRunnable (simplified)
// Before parking the M (OS thread), Go spins briefly:
if !_g_.m.spinning && 2*atomic.Load(&sched.nmspinning) >= ... {
    // spin: check local queue, global queue, netpoll
    for i := 0; i < active_spin_cnt; i++ {
        procyield(active_spin)   // PAUSE instruction
        if gp := runqget(_p_); gp != nil { return gp }
    }
}
schedule()  // park after spin fails
```
Go's scheduler spins for ~4 iterations of 30 PAUSE instructions before
parking the OS thread. This catches the common case where a goroutine
becomes runnable within microseconds of the spin start.

**Mapanare (current — unconditional sem_wait):**
```c
// runtime/native/mapanare_runtime.c::agent_thread_fn (lines 556-558)
} else {
    /* No message — wait on semaphore instead of polling */
    mapanare_sem_wait(&agent->inbox_ready);
}
```
When the ring is empty, the worker immediately parks via `sem_wait`.
No spin window. If a message arrives 100ns after the worker parks,
the full wake path (sem_post → futex_wake → context switch → resume)
adds ~1-5 µs of latency that a 64-iteration PAUSE spin would have
avoided.

**Insertion point:** Between the failed `ring_pop` and `sem_wait`, add
a short spin loop (64 iterations of `__builtin_ia32_pause()` + retry
`ring_pop`).
