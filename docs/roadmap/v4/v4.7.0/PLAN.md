# Mapanare v4.7.0 — Optimizer + Performance

> Better code generation. Fewer allocations. Measurable speedups.

**Status:** TODO
**Breaking:** No
**Prerequisite:** v4.6.0 (compiler must be correct before optimizing)

---

## The Core Problems

1. MIR optimizer runs O1 and O2 as separate fixpoint loops — O2 creates
   opportunities for O1 that are missed.
2. Self-hosted compiler does zero optimization — all deferred to LLVM.
3. Every `str(true)`, `str(42)` allocates a fresh heap buffer.
4. Strings have no COW — every copy/concat allocates fresh (lists have COW).

---

## Phase 1: Unified Fixpoint Loop

### 1A. Merge O1 and O2

- [ ] In `mapanare/mir_opt.py`, merge the O1 loop (constant folding +
      propagation) and O2 loop (copy propagation, branch simplification,
      unreachable block elimination, DCE, agent inlining) into one loop
- [ ] Run all passes in sequence per iteration
- [ ] Break when no pass reports a change
- [ ] Keep max 10 iterations

### 1B. Add convergence warning

- [ ] If the loop hits 10 iterations without converging, emit a warning:
      `"MIR optimizer: did not converge in 10 iterations for function <name>"`
- [ ] Include the function name so developers can investigate

### 1C. O3 in the loop (optional)

- [ ] Consider moving stream fusion into the main loop
- [ ] If it creates new dead code opportunities, it should be inside the loop
- [ ] If it's purely a final transform, leave it outside

### 1D. Test

- [ ] Run benchmarks before and after — measure any improvement
- [ ] `/golden` — all pass
- [ ] Verify: no test that previously passed now fails (optimizer is stronger,
      not weaker)

**Files:** `mapanare/mir_opt.py`

---

## Phase 2: Constant Propagation in Self-Hosted

### 2A. Basic constant folding

- [ ] In the self-hosted MIR pipeline, add a pass that evaluates constant
      `BinOp` instructions at compile time:
  - `Const(3) + Const(4)` → `Const(7)`
  - `Const("hello") + Const(" world")` → `Const("hello world")`
  - `Const(true) && Const(false)` → `Const(false)`
- [ ] This pass runs after lowering, before emission

### 2B. Constant propagation

- [ ] If a `Copy` instruction copies a `Const` value, replace all uses of the
      copy with the constant directly
- [ ] This enables further folding downstream

### 2C. Dead code elimination

- [ ] After constant folding removes branches, some basic blocks become unreachable
- [ ] Add a simple reachability pass: walk from entry block, mark reachable blocks,
      delete unreachable ones

### 2D. Rebuild and test

- [ ] `bash scripts/rebuild.sh`
- [ ] `/golden` — all pass
- [ ] Measure: compilation time of golden tests before and after
- [ ] `/stage2` — passes

**Files:** `mapanare/self/lower.mn` or new `mapanare/self/mir_opt.mn`

---

## Phase 3: String Allocation Reduction

### 3A. Pool common string conversions

- [ ] In `mapanare_core.c`, change `__mn_str_from_bool` to return constant
      strings (static `{ptr, 4}` for "true", `{ptr, 5}` for "false") instead
      of allocating via `__mn_alloc`
- [ ] Tag these as constant (bit 0 = 0) so `__mn_str_free` skips them
- [ ] Same for `__mn_str_from_int` for values -128 to 127 (small int pool)

### 3B. Verify no double-free

- [ ] Since these are now constant-tagged, `__mn_str_free` must skip them
- [ ] Test: call `str(true)` 1000 times, verify no leak and no crash
- [ ] Run under valgrind

**Files:** `runtime/native/mapanare_core.c`

---

## Phase 4: COW for Strings (Optional — Evaluate)

### 4A. Evaluate cost/benefit

- [ ] Strings currently use tag-bit ownership (constant vs heap). Adding COW
      would require:
  - Buffer layout: `[8-byte refcount][string data]`
  - Clone: increment refcount, share buffer
  - Mutate (concat, replace): detach if refcount > 1
  - Free: decrement refcount, free if 0
- [ ] Measure: what percentage of string operations are copy vs mutate?
- [ ] If most operations are concat (creates new buffer anyway), COW may not help

### 4B. Implement if worthwhile

- [ ] If analysis shows > 30% of string operations are pure copies, implement COW
- [ ] If not, skip this phase and document the decision

**Files:** `runtime/native/mapanare_core.c`

---

## Phase 5: Verification

- [ ] `.\dev.ps1 validate` — full validation
- [ ] `/golden` — 40/40
- [ ] Run benchmarks: compare against pre-v4.7.0 baseline
  - Fibonacci, stream pipeline, matrix multiply
  - Measure compilation time of golden tests
  - Measure runtime allocation count (MN_PROFILE_MEM)
- [ ] `/rebuild` + `/stage2`
- [ ] Verify fixed point maintained

---

## Exit Criteria

| Check | Required |
|-------|----------|
| O1/O2 merged into single fixpoint loop | YES |
| Convergence warning if max iterations hit | YES |
| Self-hosted constant folding for arithmetic/string/bool | YES |
| Self-hosted constant propagation (copy of const → inline) | YES |
| Self-hosted dead block elimination | YES |
| `str(true)` / `str(false)` returns constant (no alloc) | YES |
| Small int `str(N)` pooled for -128..127 | YES |
| COW strings evaluated (implemented if worthwhile) | EVALUATE |
| Benchmarks show no regression | YES |
| All 40 golden tests pass | YES |
| Self-hosted rebuild + fixed point maintained | YES |
