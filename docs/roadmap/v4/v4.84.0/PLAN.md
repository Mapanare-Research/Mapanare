# Mapanare v4.84.0 — Function Attributes + Aliasing Hints

> **Arc 11 release 3.** Second IR quality pass. Annotates functions
> and parameters with `noalias`, `nonnull`, `readonly`, `readnone`,
> `willreturn`, and `nounwind`. These attributes let LLVM inline more
> aggressively, hoist invariant loads out of loops, and eliminate
> redundant null checks.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.83.0
**Delta review:** No
**Full panel:** No (v4.86.0)
**Estimated work:** 1 sprint
**Theme:** Tell LLVM what we already know about our functions.

---

## Scope

v4.83.0 annotated the IR at the instruction level (nsw, TBAA,
inbounds). v4.84.0 annotates at the function and parameter level.
These are the attributes that LLVM's inliner, LICM (loop-invariant
code motion), and interprocedural optimizer use to make cross-function
decisions.

### noalias

Two uses:
1. **sret parameters** -- every function that returns a struct by
   pointer uses an `sret` parameter. That pointer doesn't alias any
   other argument. Adding `noalias` lets LLVM treat the output buffer
   as exclusive, enabling store forwarding.
2. **Allocation returns** -- `malloc`, `__mn_arena_alloc`, and all
   Mapanare allocation builtins return fresh memory that doesn't alias
   anything else.

### nonnull

Pointers that are structurally never null:
- `self` parameter in method calls (the receiver is always a valid object)
- Non-optional reference parameters (`&T` where `T` is not `Option`)
- Struct field pointers obtained from a valid struct (guaranteed by construction)

Adding `nonnull` lets LLVM eliminate redundant null checks and fold
conditional branches.

### readonly / readnone

- **`readonly`** -- functions that only read their arguments and global
  state: `len()`, field accessors, `is_some()`, `is_ok()`, string
  methods that return new strings without mutating the original.
- **`readnone`** -- pure computation functions that don't read or
  write memory at all: math builtins (`abs`, `min`, `max`, `pow`),
  hash functions, type conversion functions.

These let LLVM hoist calls out of loops (LICM), eliminate redundant
calls (CSE), and merge identical calls (GVN).

### willreturn + nounwind

- **`willreturn`** -- functions guaranteed to terminate: all Mapanare
  user functions (no infinite loops by default), all builtins, all
  runtime helpers.
- **`nounwind`** -- functions that don't throw exceptions: all
  Mapanare functions (the language uses `Result<T,E>`, not exceptions).

Together, these let LLVM assume functions don't have side effects
beyond their explicit reads/writes, enabling more aggressive dead
code elimination and inlining.

---

## Phase 1 -- noalias on sret and allocations

- [ ] `mapanare/emit_llvm_text.py`: identify all `sret` parameter emissions
- [ ] Add `noalias` attribute to every `sret` pointer parameter
- [ ] Identify all allocation return sites (`malloc`, `__mn_arena_alloc`, `__mn_string_new`, etc.)
- [ ] Add `noalias` return attribute to allocation functions
- [ ] Verify: `grep -c 'noalias' output.ll` shows annotations

## Phase 2 -- nonnull on non-optional pointers

- [ ] `mapanare/emit_llvm_text.py`: identify all pointer parameter emissions
- [ ] Add `nonnull` to:
  - `self` parameter in all method calls
  - Non-optional pointer parameters (where the type is `&T`, not `Option<&T>`)
  - Return values from allocation functions (allocation failure is a panic, not a null return)
- [ ] Do NOT add `nonnull` to:
  - Option-typed parameters (they may be null/none)
  - C interop function parameters (external code may pass null)
  - Raw pointer parameters from unsafe blocks
- [ ] Verify: `grep -c 'nonnull' output.ll`

## Phase 3 -- readonly / readnone on pure functions

- [ ] Audit all builtin functions in `mapanare/types.py` `BUILTIN_FUNCTIONS`:
  - `len`, `str`, `int`, `float` -- `readonly` (read argument, no side effects)
  - Math builtins (`abs`, `min`, `max`, `pow`, etc.) -- `readnone` (pure computation)
  - `print`, `println` -- neither (side effects: writes to stdout)
  - `Some`, `Ok`, `Err` -- `readnone` (constructors, pure)
- [ ] User-defined functions: analyze MIR for side effects
  - Functions with no `store` instructions and no `call` to side-effecting functions -> `readonly`
  - Functions with no `load`, no `store`, no `call` -> `readnone`
  - Conservative default: no attribute (safe; LLVM just can't optimize as well)
- [ ] Emit `readonly` / `readnone` as function attributes in the IR
- [ ] Verify: `grep -c 'readonly\|readnone' output.ll`

## Phase 4 -- willreturn + nounwind

- [ ] Add `willreturn` to:
  - All builtin functions
  - All user-defined functions (Mapanare has no infinite loops by default; explicit `loop {}` is the only exception)
  - All runtime helper functions
- [ ] Add `nounwind` to:
  - All Mapanare functions (the language doesn't use exceptions; errors are `Result<T,E>`)
  - All runtime helpers that don't call `longjmp` or `setjmp`
- [ ] Do NOT add `willreturn` to functions containing `loop {}` without a provable exit condition
- [ ] Do NOT add `nounwind` to C interop functions that may throw
- [ ] Verify: `grep -c 'willreturn\|nounwind' output.ll`

## Phase 5 -- Integration tests + benchmarks

- [ ] Run all 58 golden tests through `llvm-as -> opt -O2 -> llc -> run`
- [ ] Verify every golden produces correct output (no miscompilation from attributes)
- [ ] Run mnc-stage1 build -- still works
- [ ] Run `benchmarks/optimizer/run_baseline.py`
- [ ] Save results to `benchmarks/optimizer/v4.84.0-delta.json`
- [ ] Compute delta vs `v4.83.0-delta.json` and vs `v4.82.0-baseline.json` (cumulative)

## Phase 6 -- LOW sweep + closeout

- [ ] Grep for `TODO(v4.84)` or unfinished items
- [ ] Standard closeout: `VERSION`, `CHANGELOG.md`, `SESSION_REPORT.md`

---

## Exit criteria (9 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `noalias` on all `sret` parameters | grep |
| 2 | `noalias` on allocation return values | grep |
| 3 | `nonnull` on non-optional pointer parameters | grep |
| 4 | `readonly` on read-only builtins, `readnone` on pure builtins | grep |
| 5 | `willreturn` on all terminating functions | grep |
| 6 | `nounwind` on all non-throwing functions | grep |
| 7 | 58/58 golden tests pass at O2 | test log |
| 8 | mnc-stage1 builds and golden tests pass | `test_native.py` |
| 9 | Benchmark delta measured, `v4.84.0-delta.json` saved | file |

---

## What this release does NOT do

- **MIR-level optimization passes** -- that's Arc 12
- **Interprocedural analysis in the emitter** -- we mark builtins and obvious cases; a full side-effect analysis is future work
- **Link-time optimization (LTO)** -- v5.x
- **Profile-guided optimization (PGO)** -- v5.x
- **Self-hosted emitter mirror** -- deferred until Python bootstrap is proven

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| `noalias` on a parameter that actually aliases another | low | critical | sret is always exclusive by construction; audit other uses carefully |
| `nonnull` on a parameter that is null in some edge case | low | critical | Only annotate structurally-guaranteed non-null (self, non-optional); golden tests cover edge cases |
| `readonly` on a function that has a subtle side effect | medium | high | Conservative default: don't annotate unless MIR proves purity; builtins are known |
| `willreturn` on a function with `loop {}` | low | medium | Scan MIR for infinite loops; skip annotation if found |
| Attributes cause LLVM to inline too aggressively, bloating binary | low | low | Monitor binary sizes in benchmarks; LLVM's inliner has cost models |

---

## After v4.84.0

v4.85.0 is the benchmark refresh: re-run all 5 benchmarks, compute cumulative delta from v4.82.0 baseline, refresh cross-language comparison, publish `ARC11_RESULTS.md`. This is the payoff measurement.
