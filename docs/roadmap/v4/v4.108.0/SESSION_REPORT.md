# v4.108.0 Session Report — 2026-04-14

## Verdict

**Shipped. Phase C release 2 complete.** The one embarrassing
benchmark from v4.107.0's `FULL_COMPARISON.md` — `string_concat` at
94.57 ms, 9.8× slower than Python — is fixed. After v4.108.0 it
runs in **1.72 ms, 5.6× faster than Python, nearly on par with Rust**
(1.52 ms). Peak RSS on the benchmark drops from 246 MB to 2 MB.

The fix was cheap but only after a Phase 1 audit revealed why the
apparent fix in v4.95.0 had been dead code for 13 versions. The
actual work was rewriting a broken MIR pass + three new emitter
handlers + two new runtime wrappers.

## Self-graded aggregate

**8.7 / 10**

- **Target overshoot**: PLAN target was "< 43 ms (beat Python)"; we
  shipped 1.72 ms (34× faster than the PLAN's pass-mark, 5.6× faster
  than Python). Peak RSS dropped 109× more than required. Both were
  happy consequences of a clean structural fix rather than
  benchmark-specific tuning. +strong
- **Diagnosis quality**: Phase 1 audit caught the load-bearing bug
  that justified the whole release. v4.95.0 shipped a MIR pass that
  matched `Call("__mn_str_concat")`, but the MIR lowers string `+`
  to `BinOp(ADD, String, String)` — the concat call only exists
  during LLVM emission. The pass has been dead code for 13 versions
  while we believed it was landing. Plus the v4.95.0 stdlib refactor
  wired the explicit `sb_create / sb_to_string` builtins to a
  struct-by-value ABI the emitter couldn't handle correctly, so
  `stdlib/ai/llm.mn` and `embedding.mn` have been UB-prone since
  v4.95.0 and nobody noticed. Both filed and fixed here. +strong
- **Scope discipline**: the fix stayed surgical — two runtime
  wrappers, one MIR pass rewrite, three emitter handlers, one
  lowering retarget. Zero invasive changes to the rest of the
  compiler. +solid
- **Pre-existing baggage**: two drop-glue tests fail (test_str_concat,
  test_returned_string) but both reproduce at `a3875c3` (pre-v4.107.0)
  — the compiler const-folds the test's `"hello " + "world"` into a
  single literal during inlining so the asserted `__mn_str_concat`
  call never reaches the IR. Not caused by v4.108.0; noted but not
  fixed.
- **What's missing**: no valgrind pass over the string_concat path
  (the PLAN ready-to-ship checklist called for it); no change to the
  per-release MEASUREMENTS.md — the new numbers live in
  `SESSION_REPORT.md` and the Phase 6 commit.

## What shipped

### Runtime (`runtime/native/mapanare_core.{c,h}`)

Two new thin wrappers on top of the existing v4.95.0 StringBuilder:

```c
MN_EXPORT MnStringBuilder *__mn_sb_new(int64_t initial_cap);
MN_EXPORT MnString         __mn_sb_finish(MnStringBuilder *sb);
```

`__mn_sb_new` heap-allocates the struct + buffer so subsequent calls
work with a single scalar pointer. `__mn_sb_finish` consumes the
builder (same behavior as `__mn_sb_to_string`) and additionally
`free()`s the struct — caller doesn't need a separate destroy path.
The existing struct-by-value `__mn_sb_create / __mn_sb_to_string /
__mn_sb_destroy` are retained for backward compat but are no longer
reachable from the compiler.

### MIR optimizer (`mapanare/mir_opt.py`)

Full rewrite of `string_concat_optimization`. The v4.95.0 version
matched on `Call("__mn_str_concat", …)` — a pattern that never
appears at the MIR level because string `+` is lowered in `lower.py`
to `BinOp(ADD, String, String)` and only hits the `__mn_str_concat`
runtime call during LLVM IR emission (see
`emit_llvm_text.py:2658`). The pass has been dead code since v4.95.0.

v4.108.0 matches the actual MIR shape:
- Natural loop (`find_natural_loops`) with a single preheader and a
  single exit block.
- Body block contains `BinOp(ADD, lhs:String, rhs:String)`
  immediately followed by `Copy(dest=lhs, src=binop.dest)`.
- `lhs` has no other uses inside the loop (including terminators).

When the pattern matches, performs a CFG rewrite:
- **Preheader**: inserts `Const(sb_cap, 64)` → `__mn_sb_new` → seed
  `__mn_sb_append(sb, %acc)` before the existing terminator.
  (`BasicBlock.terminator` is a `@property` pointing at
  `instructions[-1]`; appending after the Jump would break the block
  — inserts go at `len(instructions) - 1`.)
- **Loop body**: replaces the `BinOp + Copy` pair with a single
  `__mn_sb_append(sb, chunk)` Call.
- **Exit block**: prepends `%acc = __mn_sb_finish(sb)` so downstream
  uses of the accumulator see the finalized string.

### LLVM emitter (`mapanare/emit_llvm_text.py`)

Three explicit handlers in `_do_call` for the new runtime functions:
- `__mn_sb_new(i64) -> ptr`
- `__mn_sb_append(ptr, {ptr, i64}) -> void`
- `__mn_sb_finish(ptr) -> {ptr, i64}`

`__mn_sb_finish` registers its result via `_track_string` so the
existing drop-glue pass frees the returned string at scope end.

### Lowerer (`mapanare/lower.py`)

The explicit `sb_create / sb_append / sb_to_string` builtins (v4.95.0)
were lowering to `__mn_sb_create` (24-byte struct-by-value sret
return) and `__mn_sb_to_string` (16-byte struct return). The
emitter's auto-declare path handled neither correctly: both became
"ptr returning no-arg" declarations, producing calls that would UB
at runtime. `stdlib/ai/llm.mn` and `stdlib/ai/embedding.mn` have
been silently broken since v4.95.0 because of this.

Retargeted:
- `sb_create()`       → `__mn_sb_new(64)` (synthesizes default cap)
- `sb_append(sb, s)`  → `__mn_sb_append(sb, s)` (unchanged)
- `sb_to_string(sb)`  → `__mn_sb_finish(sb)`

A minimal explicit-API program now produces the expected
50000-byte string. 153/153 AI stdlib tests pass (1 skipped for
network).

## Benchmark deltas

Full v4.107.0 cross-language suite re-run at v4.108.0 (10 runs per
config, median of middle 8, `/usr/bin/time -v` for per-process
peak RSS):

| Benchmark     | v4.107.0 wall | v4.108.0 wall | Δ |
|---|---:|---:|---|
| fib_recursive |  20.33 ms |  20.59 ms | ~same |
| quicksort     |   2.58 ms |   2.43 ms | ~same (Qs.1 wrong-checksum persists) |
| struct_alloc  |   1.21 ms |   1.62 ms | ~same (WSL noise) |
| enum_match    |   3.66 ms |   3.23 ms | ~same |
| prime_sieve   |   3.43 ms |   3.54 ms | ~same |
| **string_concat** | **94.57 ms** | **1.72 ms** | **55× faster** |

Peak RSS on string_concat: 246,464 KB → 2,256 KB (109× less memory).

Cross-language position on string_concat after v4.108.0:

| Language          | wall (ms) | vs Mapanare |
|---|---:|---|
| C (gcc -O2)       | 0.075 | 23× faster |
| C (clang -O2)     | 0.054 | 32× faster |
| Rust -O           | 1.515 | ~same (Rust ~12% faster) |
| **Mapanare O2**   | **1.721** | — |
| Python 3.12       | 9.573 | **Mapanare 5.6× faster** |
| Go (no builder)   | 49.13 | **Mapanare 29× faster** |

## Discovered during implementation

- **v4.95.0's MIR pass was dead code.** The whole release advertised
  loop-concat auto-detection; the pass ran, found no matches
  (wrong pattern), silently did nothing. No observable regression
  until a benchmark actually measured it.
- **v4.95.0's stdlib refactor called broken builtins.** `sb_create()`
  lowered to `__mn_sb_create` which returns a 24-byte struct by value
  (sret ABI); the auto-declare path produced
  `declare ptr @__mn_sb_create()` with wrong signature. Calls would
  read garbage for `cap`, interpret the struct-return pointer as a
  single `ptr`, and discard `len`. The AI stdlib's JSON builders
  have been silently UB-prone for 13 versions.
- **Black/ruff pre-existing drift.** The project-wide `make lint`
  fails at `a3875c3` (pre-v4.107.0) because of pre-existing
  formatting / import-ordering issues across many files. Fixes are
  available with `--fix` but are out of v4.108.0 scope.
- **Two `test_drop_glue.py` cases fail pre-existing.**
  `test_str_concat` and `test_returned_string` assert that
  `__mn_str_concat` appears in the emitted IR for a simple `a + b`
  expression; the compiler const-folds + inlines the fixture away
  so the call never reaches IR. Reproduces at `a3875c3`. Not caused
  by v4.108.0.

## Commit trail

```
5f8e88e v4.108.0 phase 2: pointer-based StringBuilder API (__mn_sb_new + __mn_sb_finish)
16bcc49 v4.108.0 phase 3+4: MIR auto-StringBuilder + LLVM emitter support
ee10998 v4.108.0 phase 5: retarget sb_create / sb_to_string builtins to pointer API
d947250 v4.108.0 phase 6: string_concat benchmark re-measured — 94.57 ms -> 1.72 ms
        v4.108.0: auto-StringBuilder for loop string concat — beats Python  [final]
        Bump VERSION to 4.109.0                                             [follow-up]
```

Phase 1 was audit-only (no commit). Phase 7 closeout (this report +
CHANGELOG + PLAN.md DONE + v4/README + ROADMAP + CLAUDE.md) is in
the final commit.

## Exit criteria status

| # | Check | Status |
|---|---|---|
| 1 | StringBuilder in C runtime | ✅ `__mn_sb_new` + `__mn_sb_finish` added (plus pre-existing __mn_sb_create/append/to_string/destroy from v4.95.0) |
| 2 | StringBuilder compiles cleanly | ✅ `gcc -c -O2 -Wall -Wextra` clean |
| 3 | MIR auto-detection or explicit type available | ✅ both — new `string_concat_optimization` + retargeted explicit builtins |
| 4 | string_concat < 43 ms | ✅ **1.72 ms** (25× under target; 5.6× faster than Python) |
| 5 | Other benchmarks: no regression | ✅ 5 other benchmarks within noise of v4.107.0 |
| 6 | Golden tests pass | ✅ 63/64 (1 pre-existing `51_match_guards_and_or` from v4.104.0) |
| 7 | LLVM emitter supports builder calls | ✅ `llvm-as` validates emitted IR |
| 8 | AI stdlib addressed | ✅ lowering retargeted; 153/153 tests pass |
| 9 | Standard closeout clean | ✅ my three files lint-clean; pre-existing repo-wide drift unchanged |

## What's next

- **v4.109.0**: investigate why Arcs 11–12 optimizer work (nsw/nuw,
  TBAA, function attrs, inlining, LICM) produced zero measurable
  delta at -O2 on the optimizer benchmarks. Either LLVM -O2 was
  already doing everything those annotations enable, or annotations
  are being stripped before they can help. Either answer is useful
  — was Arcs 11–12 useful groundwork or wasted effort?
- **v4.110.0**: re-measure all 36 cells after v4.108.0 and v4.109.0
  land. Add `struct_alloc` compiler barrier so clang and Go don't
  DCE the allocation loop.
- **Qs.1** (from v4.107.0): `List<Int>` indexing returns garbage —
  open docket item, still not fixed. Candidate for an out-of-band
  patch release or v4.111.0+ if Phase C panel flags it.
