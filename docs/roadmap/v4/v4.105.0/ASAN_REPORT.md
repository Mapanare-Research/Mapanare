# v4.105.0 Phase 2 — AddressSanitizer report (64 golden tests)

**Date:** 2026-04-14
**Tool:** clang 18.1.3 AddressSanitizer at `-O1 -fno-omit-frame-pointer`
**Target:** `./mapanare/self/mnc-stage1-asan <test>.mn`
**Flags:** `ASAN_OPTIONS=detect_leaks=0:halt_on_error=1:symbolize=1`
**Wall time:** 21 s (65× faster than valgrind — sanitizers are the
right choice for CI, valgrind for deep investigation.)

Leak detection is disabled because Phase 1 already documented the
intentional "don't free at shutdown" design.

## Headline

| Class | Count |
|---|---:|
| **CLEAN** (no ASan findings) | **21** |
| **ASAN_ERROR** (UAF / overflow caught) | **17** |
| **CRASH_NO_ASAN** (compiler exits nonzero but ASan is silent) | **26** |

The 26 CRASH_NO_ASAN are the semantic / parser / MIR-verifier failures
from Phase 2 — ASan only fires on memory errors, so semantic rejections
pass through unchanged.

## Per-class breakdown

### CLEAN (21 — compiler runs to completion with no ASan error)

```
01_hello, 02_arithmetic, 04_if_else, 06_struct, 07_enum_match, 08_list,
09_string_methods, 12_while, 14_nested_struct, 16_string_escape,
17_option, 18_method_chain, 30_nested_generics, 32_generic_enum,
34_file_io, 35_stdin, 36_crypto, 37_regex, 38_http, 39_gpu_detect,
40_gpu_tensor
```

This is the 21 Phase 2 passers, plus `40_gpu_tensor` which Phase 2
marked FAIL (no IR emitted) but which ASan runs to completion without
detecting a memory error — the underlying lowerer error is semantic,
not memory-related.

### ASAN_ERROR (17, clustered by bug class)

| Error kind | Count | Top frame |
|---|---:|---|
| `heap-use-after-free` | **12** | `mn_list_rc` (7), `MemcmpInterceptorCommon` (3 via `__mn_str_eq` `bcmp`), 2 others |
| `global-buffer-overflow` | **5** | `StrtolFixAndCheck` → `strtoll` called on non-null-terminated global string |

#### 12× heap-use-after-free in `__mn_list_free` → `mn_list_rc` (HIGH)

```
READ of size 8 at 0x50d000003ac0
  #0 mn_list_rc   at mapanare_core.c:976
  #1 __mn_list_free at mapanare_core.c:1192
  #2 emit_llvm__emit_mir_call

freed by thread T1 here:
  #0 free
  #1 __mn_free at mapanare_core.c:109
  #2 __mn_list_free at mapanare_core.c:1196
  #3 emit_llvm__emit_mir_call

previously allocated by:
  #0 calloc
  #1 __mn_alloc at mapanare_core.c:83
  #2 mn_list_alloc_buf at mapanare_core.c:993
  #3 __mn_list_push at mapanare_core.c:1095
  #4 emit_llvm__emit_mir_function
```

A `MnList` whose buffer was free'd by a previous `__mn_list_free` is
free'd again — `data` still points at the released block, so
`mn_list_rc` at `mapanare_core.c:976` reads `header[0]` (the
`MN_COW_MAGIC` check) out of freed memory. The current guard at line
974 (`if (!list->data || !list->managed) return NULL`) is insufficient
because `data` survives the first free on a second `MnList` that shared
the buffer (list copied without COW accounting).

Affected tests (12): 13_fib, 20_recursion, 23_multi_return,
24_enum_methods, 47_try_operator, 49_match_guards, 50_match_or_patterns,
63_else_sino, plus 3 `MemcmpInterceptorCommon` crashes (10_result,
19_nested_match, 43_module_let_math, 48_match_nested_exhaustive).

Full sample: `artifacts/asan-samples/13_fib-heap-uaf.err`.

#### 5× global-buffer-overflow in `strtoll` (HIGH)

```
READ of size 2 at 0x0000008da521 thread T1
  #0 StrtolFixAndCheck(...) in asan_interceptors.cpp.o
  #1 strtoll
  #2 mir_opt__try_strength_reduce

0x0000008da521 is located 0 bytes after global variable '.str.1811'
    defined in '.../main.ll' (0x8da520) of size 1
```

The self-hosted MIR optimizer's strength-reduction pass calls the C
`strtoll` (via a runtime wrapper) on an `[N x i8]` string constant.
Mapanare string constants are **not null-terminated** — the
`MnString {ptr, len}` pair carries the length. `strtoll` reads byte
after byte looking for a terminator and walks past the allocated
global. The fix is to call `__mn_str_to_int` (which knows the
length) or to null-terminate the buffers.

Affected tests (5): 05_for_loop, 21_list_ops, 22_string_builder,
25_fizzbuzz, 33_break_continue.

Full sample: `artifacts/asan-samples/05_for_loop-gbo.err`.

### CRASH_NO_ASAN (26 — compiler exit nonzero, ASan silent)

- **11 with exit 139** (SIGSEGV): 03_function, 11_closure, 15_multifunction,
  26_generics, 27_impl, 28_traits, 29_generic_impl, 31_generic_multi,
  41_module_let, 42_module_let_string, 45_ffi_bind, 62_list_output.
  These match Phase 2's "mir_opt__block_successors" crash family. ASan
  doesn't catch them because the segfault comes from dereferencing a
  null pointer — not from a heap bounds violation.
- **15 with exit 1**: 49-59 semantic/parser errors (`Tensor`, `block_on`,
  tuple indexing, typed closures). Clean exits, no memory error —
  expected behavior for unsupported source constructs.

## Docket candidates for v4.106.0 panel

From this phase (ASan-specific):

| # | Item | Severity | Evidence |
|---|---|---|---|
| As.1 | `__mn_list_free` / `mn_list_rc` UAF on shared list buffer | HIGH | 12 tests; runtime bug in `mapanare_core.c:976,1192,1196` |
| As.2 | `strtoll` on non-null-terminated `[N x i8]` global | HIGH | 5 tests; `mir_opt__try_strength_reduce` calls `int()` on a string-constant slice |
| As.3 | `__mn_str_eq` → `bcmp` reads freed buffer | MEDIUM | 4 tests (merged with heap-UAF bucket; same kind) |

As.1 is **a runtime-level C bug**, not a self-hosted-compiler bug.
The `MnList` COW refcount machinery (`mapanare_core.c:970-1204`)
cannot tell "this list shares its buffer with another list I don't
know about." The fix probably requires an explicit `managed` clear on
the sibling, or a per-buffer doubly-linked sibling list. Significant
design work — not drive-by. Deferred.

As.2 is a known class: Mapanare strings are length-prefixed, not
NUL-terminated; calling C `strtoll` is a category error. Fix is
mechanical in the emitter.

## Build details

- Script: `scripts/build_asan.sh` (new in this release)
- Build time: 1 m 11 s (similar to normal `-O2` build)
- Binary size: 6,679,200 bytes (vs 3,501,200 stripped normal build)
- Runtime files compiled with ASan: 7 C runtime `.c` + `mnc_main.c` + `main.ll`

## Evidence trail

- Full TSV: `artifacts/asan-summary.tsv`
- Sample reports: `artifacts/asan-samples/` (13_fib UAF, 05_for_loop GBO, 10_result memcmp-UAF)
- Per-test raw logs: `/tmp/v4_105_asan/<test>.err` (session-local)
- Runner script: `scripts/run_asan_goldens.sh` (committed)
- Build script: `scripts/build_asan.sh` (committed)

## Exit criteria

- [x] **Exit #3** — ASan build of mnc-stage1 succeeds.
- [x] **Exit #4** — ASan report for all 64 golden tests.
- [ ] **Exit #5** — 0 ASan errors: **NOT MET** (17 errors). Per the
  PLAN, findings are docketed (As.1–As.3), not fixed here.
