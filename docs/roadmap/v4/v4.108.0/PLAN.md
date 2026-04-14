# Mapanare v4.108.0 — String Concat Fix: Auto-StringBuilder

> **Phase C release 2.** string_concat is 2.2x slower than Python
> (95.2ms vs 43.7ms) and 136x slower than Rust (0.7ms). This is the
> single most embarrassing number in the benchmark suite. The cause
> is known: `__mn_str_concat` allocates a new string on every `+`,
> making loop concatenation O(n^2). The fix: a `StringBuilder` in
> the C runtime with exponential buffer growth, plus a MIR optimizer
> pass that auto-detects `s = s + x` patterns in loops and rewrites
> them to use the builder. Target: faster than Python (< 43ms).

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.107.0
**Delta review:** No
**Full panel:** No (numbers speak for themselves)
**Estimated work:** 1 sprint
**Theme:** Fix the one embarrassing benchmark. String concat must beat Python.

---

## Scope

The `__mn_str_concat` function in `runtime/native/mapanare_core.c` allocates a new `MnString` for every concatenation: `malloc(len_a + len_b + 1)`, `memcpy` both sides, return new string. In a loop of 10,000 iterations, this means 10,000 allocations, each copying the growing result -- classic O(n^2) Schlemiel the Painter's algorithm.

Python beats Mapanare because CPython has a special optimization: when a string's refcount is 1 and it's being concatenated, CPython `realloc`s in place. Rust beats both because `String::push_str` uses an exponentially-growing buffer (Vec<u8> with amortized O(1) push).

The fix has two parts:

1. **C runtime**: Add `mapanare_string_builder_t` with exponential growth (start 64B, double on overflow). Functions: `mn_sb_create`, `mn_sb_append`, `mn_sb_to_string`, `mn_sb_destroy`.

2. **MIR optimizer**: Detect `var = var + expr` inside loop bodies. Replace with: create builder before loop, append inside loop, finalize after loop. This makes the optimization automatic -- users don't need to change their code.

After the fix, string_concat should drop from 95ms to well under 43ms (Python's time), ideally under 10ms.

---

## Phase 1 -- Audit current string concatenation

- [ ] Read `runtime/native/mapanare_core.c` -- find `__mn_str_concat` implementation
- [ ] Read `runtime/native/mapanare_core.h` -- find `MnString` struct definition
- [ ] Understand the allocation pattern: how many bytes are allocated per concat? Does the arena allocator help or hurt?
- [ ] Read `mapanare/emit_llvm_text.py` -- find where string concatenation is emitted (the call to `__mn_str_concat`)
- [ ] Read `mapanare/mir.py` and `mapanare/lower.py` -- find where string `+` is lowered to MIR
- [ ] Document the full path: `.mn` source -> AST -> MIR -> LLVM IR -> C runtime call

## Phase 2 -- Implement StringBuilder in C runtime

- [ ] Check if `mapanare_string_builder_t` or similar already exists (v4.95.0 may have added one)
- [ ] If not, implement in `runtime/native/mapanare_core.c`:
  ```c
  typedef struct {
      char *buf;
      size_t len;
      size_t cap;
  } mapanare_string_builder_t;

  mapanare_string_builder_t *mn_sb_create(size_t initial_cap);
  void mn_sb_append(mapanare_string_builder_t *sb, const char *data, size_t len);
  MnString mn_sb_to_string(mapanare_string_builder_t *sb);
  void mn_sb_destroy(mapanare_string_builder_t *sb);
  ```
- [ ] Growth strategy: start at 64 bytes, double when capacity exceeded
- [ ] `mn_sb_to_string`: transfer ownership of the buffer to an MnString (no copy -- just wrap the pointer)
- [ ] Add function declarations to `runtime/native/mapanare_core.h`
- [ ] Verify it compiles: `gcc -c -O2 runtime/native/mapanare_core.c`
- [ ] Write a minimal C test: create builder, append 10K times, verify output length and content

## Phase 3 -- MIR optimizer: auto-detect loop string concat

- [ ] Read `mapanare/mir_opt.py` -- understand the existing pass infrastructure
- [ ] Read `mapanare/mir.py` -- understand MIR instructions (specifically `MIRCall`, `MIRBinOp`, `MIRAssign`)
- [ ] Implement a new pass `optimize_string_concat_loops`:
  - Identify loops (using existing natural loop detection from v4.88.0)
  - Inside each loop body, find assignments of the form `%var = call __mn_str_concat(%var, %other)`
  - Replace with:
    - Before loop: `%sb = call mn_sb_create(64)`
    - Inside loop: `call mn_sb_append(%sb, %other.data, %other.len)` (replacing the concat)
    - After loop: `%var = call mn_sb_to_string(%sb)`
  - Handle the initial value: if `%var` had a value before the loop, append it first
- [ ] Register the pass in the O1/O2 pipeline
- [ ] Add MIR-level test: verify the transform fires on a simple loop concat pattern
- [ ] Add MIR-level test: verify the transform does NOT fire on single-expression concat (no loop)

## Phase 4 -- LLVM emitter support

- [ ] Update `mapanare/emit_llvm_text.py` to emit calls to `mn_sb_create`, `mn_sb_append`, `mn_sb_to_string`, `mn_sb_destroy`
- [ ] Declare the builder functions as `extern` in the emitted LLVM IR module
- [ ] Ensure the StringBuilder struct type is defined in the emitted IR (opaque pointer is fine)
- [ ] Verify the emitted IR validates with `llvm-as`

## Phase 5 -- Fix AI stdlib string building

- [ ] Read `stdlib/ai/llm.mn` -- find string concatenation patterns used for JSON body building
- [ ] Read `stdlib/ai/embedding.mn` -- same
- [ ] If these files use `s = s + chunk` patterns, refactor to use explicit `StringBuilder` type (if exposed) or verify the auto-optimizer handles them
- [ ] If a `StringBuilder` stdlib type is warranted, create `stdlib/string/builder.mn` as a thin wrapper
- [ ] Run existing AI stdlib tests to verify no regressions

## Phase 6 -- Re-run string_concat benchmark

- [ ] Compile `benchmarks/optimizer/string_concat.mn` with the updated compiler
- [ ] Run 10 times, median of middle 8
- [ ] **Target: < 43ms** (beat Python's 43.7ms)
- [ ] **Stretch target: < 10ms** (approach Rust's 0.7ms -- unlikely due to remaining runtime overhead but worth measuring)
- [ ] Compare against v4.98.0 baseline (95.2ms)
- [ ] Run the full optimizer benchmark suite to verify no regressions on other benchmarks
- [ ] Run the full golden test suite: `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`

## Phase 7 -- LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.108.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (9 items)

| # | Check | Evidence |
|---|---|---|
| 1 | StringBuilder implemented in C runtime | `mn_sb_create`/`mn_sb_append`/`mn_sb_to_string`/`mn_sb_destroy` in `mapanare_core.c` |
| 2 | StringBuilder compiles cleanly | `gcc -c -O2 runtime/native/mapanare_core.c` succeeds |
| 3 | MIR auto-detection pass implemented or explicit type available | diff of `mir_opt.py` or stdlib type |
| 4 | string_concat benchmark < 43ms (beats Python) | benchmark output showing median time |
| 5 | Other benchmarks show no regression | full suite output |
| 6 | Golden tests pass | `test_native.py` output |
| 7 | LLVM emitter supports StringBuilder calls | `llvm-as` validates emitted IR |
| 8 | AI stdlib string building addressed | diff of `llm.mn` / `embedding.mn` or note that auto-optimizer handles them |
| 9 | Standard closeout clean | CI green |

---

## What this release does NOT do

- **Fix all string performance issues** -- only loop concatenation. Single-expression `a + b + c` is not a bottleneck (it's O(n) already).
- **Implement a GC** -- the StringBuilder transfers buffer ownership to MnString. No garbage collection needed.
- **Change the language syntax** -- `+` still means string concatenation. The optimization is invisible to the user.
- **Make Mapanare match Rust on strings** -- Rust's `String::push_str` with SIMD `memcpy` and no bounds checking is a different tier. Beating Python is the realistic target.
- **Run a panel** -- Phase C has no panel.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| MIR auto-detection is too fragile (misidentifies patterns) | medium | high | Conservative matching: only fire on exact `var = concat(var, other)` in a natural loop body. Require the variable to be the same SSA value on both sides. |
| StringBuilder introduces memory leaks (builder not destroyed on exception/early return) | medium | high | `mn_sb_destroy` is a no-op on NULL. Emit destroy in all exit paths. Valgrind on golden tests. |
| The optimization doesn't fire on the benchmark program (pattern doesn't match) | medium | medium | If auto-detection is too complex, fall back to explicit StringBuilder type. The benchmark can be updated to use it. |
| Arena allocator interferes with StringBuilder's realloc strategy | low | medium | StringBuilder uses `malloc`/`realloc` (heap), not the arena. The finalized string can be arena-allocated if needed. |
| Regressions on non-string benchmarks from new MIR pass | low | medium | The pass only touches string concat in loops. Run full benchmark suite to confirm. |

---

## After v4.108.0

String concat should now beat Python. v4.109.0 investigates why the optimizer work from Arcs 11-12 (nsw/nuw/TBAA/inlining/LICM) produced zero measurable delta at -O2. Was it already redundant? Did the passes not fire? v4.110.0 re-measures everything.
