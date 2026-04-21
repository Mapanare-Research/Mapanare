# Mapanare v4.4.0 — Thread Safety (Concurrency Hardening)

> Concurrent agents don't corrupt shared state.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.3.0 (memory ownership must be clear before adding concurrency)

---

## The Core Problems

1. `__mn_signal_free` frees subscriber/dependency arrays without holding the
   signal mutex. Another thread propagating signals iterates a freed array.
2. Memory profiling counters (`mn_alloc_count`, etc.) are plain `int64_t` —
   racy under concurrent allocation.
3. Arena allocator has no synchronization — fine for per-function arenas but
   dangerous if agent arenas are shared.
4. COW nested list corruption (known, worked around in `mnc_all.mn:6944`).
5. Agent arena and agent lifecycle are disconnected — emitter must call both.
6. In-flight messages leak when an agent dies.

---

## Phase 1: Signal Safety

### 1A. Signal free under lock

- [ ] In `mapanare_core.c`, modify `__mn_signal_free` to:
  1. Acquire `mn_signal_lock()`
  2. Unsubscribe from all dependencies
  3. Null out the signal's subscriber/dependency arrays
  4. Release `mn_signal_unlock()`
  5. Free the arrays and the signal struct outside the lock
- [ ] Write a test: two threads — one propagating signals, one freeing a signal.
      Must not crash under TSan.
- [ ] Run C runtime TSan tests: full matrix

### 1B. Signal propagation snapshot safety

- [ ] Verify the existing subscriber snapshot approach (line ~1984) is correct
      when combined with 1A
- [ ] Ensure the snapshot copy is made under the lock and propagation happens
      outside the lock (this may already be the case — verify)

**Files:** `runtime/native/mapanare_core.c`

---

## Phase 2: Atomic Counters

### 2A. Memory profiling counters

- [ ] Change `mn_alloc_count`, `mn_alloc_bytes`, `mn_alloc_live`, `mn_alloc_peak`
      from `static int64_t` to `static _Atomic int64_t`
- [ ] Replace `++`/`--`/`+=` with `atomic_fetch_add` / `atomic_fetch_sub`
- [ ] Use `memory_order_relaxed` (counters are informational, don't need ordering)
- [ ] Test: `MN_PROFILE_MEM=1` with multi-agent program under TSan

### 2B. COW statistics counters

- [ ] Change `cow_shares`, `cow_fallbacks`, `cow_detaches` to `_Atomic int64_t`
- [ ] Same relaxed ordering

### 2C. Fix `__mn_free` profiling

- [ ] Add `MN_PROFILE_FREE` tracking to `__mn_free` (currently missing —
      `mn_alloc_live` drifts because frees aren't counted)

**Files:** `runtime/native/mapanare_core.c`

---

## Phase 3: Arena Thread Safety

### 3A. Per-agent arena guarantee

- [ ] Document and enforce: arenas are per-thread, never shared between agents
- [ ] If agent arenas ARE shared (check emitter), add a mutex to `MnArena`
- [ ] If agent arenas are per-agent (verify), document the invariant with a comment

### 3B. Tie arena to agent lifecycle

- [ ] Modify `mapanare_agent_destroy` to call `mn_agent_arena_destroy` if the
      agent has an associated arena
- [ ] Add `arena` field to the agent struct (or use thread-local lookup)
- [ ] Verify with valgrind: agent spawn + complete + destroy frees arena

**Files:** `runtime/native/mapanare_core.c`, `runtime/native/mapanare_runtime.c`

---

## Phase 4: COW Correctness

### 4A. Audit struct-copy paths

- [ ] Search for all paths where `MnList` is copied by value (C level):
  - Function argument passing (by value)
  - Struct field assignment
  - Return value copy
- [ ] For each path, verify `__mn_list_clone` is called (increments refcount)
- [ ] If any path does a raw struct copy without clone: fix it

### 4B. Fix nested list corruption

- [ ] Identify the root cause of the `mnc_all.mn:6944` workaround
- [ ] If it's a missing clone on nested list copy, add the clone
- [ ] If it's a deeper issue (e.g., list of lists where inner list is mutated
      through outer), document the limitation or fix the COW model

### 4C. Test

- [ ] Write a C runtime test: clone a list, mutate the clone, verify original
      unchanged
- [ ] Write a C runtime test: clone a list of lists, mutate inner list through
      clone, verify original's inner list unchanged
- [ ] Run under TSan

**Files:** `runtime/native/mapanare_core.c`

---

## Phase 5: Agent Message Ownership

### 5A. Define policy

- [ ] Decision: when an agent dies, what happens to in-flight messages?
  - Option A: Agent destroy drains and frees all messages (simple but loses data)
  - Option B: Messages are transferred to a supervisor (complex, needs supervision tree)
  - Recommended: Option A for now, document limitation
- [ ] Implement the chosen policy in `mapanare_agent_destroy`

### 5B. Agent restart cleanup

- [ ] Verify that restarted agents (via restart policy) properly destroy old
      state before reinitializing
- [ ] If not: add destroy-before-reinit to the restart path

**Files:** `runtime/native/mapanare_runtime.c`

---

## Phase 6: Verification

- [ ] `.\dev.ps1 validate` — full validation passes
- [ ] `/golden` — 40/40 pass
- [ ] Run C runtime under TSan: `make test-tsan` or equivalent
- [ ] Run C runtime under ASan: `make test-asan` or equivalent
- [ ] Run multi-agent golden test under valgrind
- [ ] `/rebuild` + `/stage2` — self-hosted still works

---

## Exit Criteria

| Check | Required |
|-------|----------|
| `__mn_signal_free` acquires lock before touching arrays | YES |
| All profiling counters are `_Atomic int64_t` | YES |
| `__mn_free` tracks MN_PROFILE_FREE | YES |
| Arena thread safety documented or enforced | YES |
| Agent destroy calls arena destroy | YES |
| COW nested list audit complete (all copy paths verified) | YES |
| Agent message ownership policy implemented | YES |
| Agent restart cleans up old state | YES |
| TSan clean on multi-agent program | YES |
| ASan clean on all C runtime tests | YES |
| All 40 golden tests pass | YES |
| Self-hosted rebuild + fixed point maintained | YES |
