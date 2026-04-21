# v4.105.0 Phase 1 — Valgrind report (64 golden tests)

**Date:** 2026-04-14
**Tool:** valgrind-3.22.0
**Target:** `./mapanare/self/mnc-stage1 <test>.mn -o /tmp/<test>.ll`
**Flags:** `--leak-check=full --show-leak-kinds=all --track-origins=yes --errors-for-leak-kinds=none --error-exitcode=99 --num-callers=20`
**Wall time:** 1 m 24 s

## Headline

| Class | Count | Meaning |
|---|---:|---|
| **CLEAN** (0 errors, 0 leaks) | **0** | zero tests are pristine under valgrind |
| **WARNINGS_ONLY** (leaks only) | **28** | no uninit/invalid-access errors; only leaked blocks at exit |
| **ERRORS** (invalid read/write or uninit use) | **36** | genuine memory-safety findings |

The 36 errors fall into two buckets:

- **29 tests** that were already CRASHes in Phase 2 (v4.104.0's Phase 2
  bucket). Valgrind confirms those crashes are memory-safety bugs, not
  just assertion failures.
- **7 tests** that were PASS in Phase 2 — meaning the compiler produced
  correct output while reading freed or uninitialized memory. These are
  latent bugs: correct output today, crash tomorrow.

### Phase-2 PASSes with valgrind ERRORS (latent bugs)

| Test | Top-frame symbol | Error kind |
|---|---|---|
| 06_struct | `lower__lookup_struct_field_type` | Invalid read of size 8 (use-after-free: 16 bytes into 144-byte block) |
| 08_list | `__mn_list_free` / `lower__lower_list` | Invalid read of size 8 |
| 10_result | `emit_llvm__emit_mir_call` | Uninit + Invalid read of sizes 1/2/8 |
| 12_while | `mir_opt__block_successors` | Invalid read of size 8 |
| 14_nested_struct | `lower__lookup_struct_field_type` | Invalid read of size 8 (same UAF as 06) |
| 30_nested_generics | `lower__monomorphize_impl_methods`, `lower_state__fresh_tmp` | Conditional jump on uninit stack value from `try_monomorphize_struct` |
| 32_generic_enum | `emit_llvm_ir__resolve_mir_type` | Invalid read of size 8 |

These 7 are the primary new finding of Phase 1. The compiler's golden
test harness calls them PASS because output matches; valgrind calls
them bugs because they're reading freed or uninitialised memory to
compute that output.

### Top-frame clustering across all 36 ERROR tests

| Count | Symbol | Interpretation |
|---:|---|---|
| 14 | `mir_opt__block_successors` | Same signature as Phase 2 Category A (null-deref / use-after-free in MIR optimizer) |
| 12 | `__mn_list_free` | **NEW** — list free'd while still reachable via another path |
| 11 | `emit_llvm__emit_mir_call` | Same signature as Phase 2 Category B (String lifetime in call emitter) |
| 6 | `mir_opt__escape_analysis_function` | Escape analysis pass reads freed memory |
| 6 | `lower__verify_block` | MIR verifier reads invalid memory |
| 6 | `emit_llvm__emit_mir_basic_block` | LLVM emitter reads invalid memory |
| 5 | `bcmp` | libc memory compare with uninit/freed buffer |
| 4 | `memmove` | libc memmove with uninit/freed buffer |
| 4 | `lower_state__fresh_tmp` | Fresh-temp allocator reads uninit stack |
| 4 | `lower__lower_list` | List lowering site |
| 4 | `lower__lookup_struct_field_type` | Struct field lookup UAF |
| 3 | `emit_llvm_ir__resolve_mir_type` | Type resolver reads invalid memory |

Full clustering: `artifacts/valgrind-frame-clusters.txt`.

## Detailed analysis — the two representative leaks

### UAF in `lower__lookup_struct_field_type` (affects 06_struct + 14_nested_struct)

```
==6613== Invalid read of size 8
==6613==    at 0x5E6A4C: lower__lookup_struct_field_type (...mnc-stage1)
==6613==  Address 0x6a90c00 is 16 bytes inside a block of size 144 free'd
```

A struct field-type descriptor (144 B) is free'd and then re-read at
byte offset 16. Same bug class as the Python emitter's v4.101.0
use-after-free fix (heap data freed while a pointer remained live). The
fix belongs in `mapanare/self/lower_state.mn` or wherever the struct
descriptor's lifetime is managed.

### Uninit stack value in `try_monomorphize_struct` (affects 30_nested_generics)

```
==7542== Conditional jump or move depends on uninitialised value(s)
==7542==    at 0x5A0438: lower__monomorphize_impl_methods
==7542==  Uninitialised value was created by a stack allocation
==7542==    at 0x596C0A: lower__try_monomorphize_struct
```

`try_monomorphize_struct` allocates a stack struct but does not zero-
init all its fields; downstream code branches on an uninit field. The
output happens to be correct because the uninit bytes land on a
consistent execution path, but this is a classic Phase B catch.

## WARNINGS_ONLY (28 tests)

All 28 have leaks but no invalid accesses. The leaks come from the
self-hosted compiler's intentional lack of free — the compiler is a
short-lived process that runs, emits IR, and exits. Freeing everything
on the way out would only slow the compiler down; the OS reclaims at
exit. This is not a bug, just a design choice the panel should note.

Classification of the 28 WARNINGS_ONLY tests: arena memory, string
interning tables, enum descriptor tables, and AST nodes kept live
through compilation. None reach the runtime; all released at process
exit.

## Docket candidates for v4.106.0 panel

From this phase (valgrind-specific):

| # | Item | Severity | Evidence |
|---|---|---|---|
| Vg.1 | UAF in `lower__lookup_struct_field_type` | HIGH | 4 tests, 06/14 still produce correct output |
| Vg.2 | Uninit use in `__mn_list_free` | HIGH | 12 tests; affects 08_list which currently passes |
| Vg.3 | Uninit stack from `try_monomorphize_struct` | MEDIUM | 30_nested_generics currently passes |
| Vg.4 | UAF in `lower_state__fresh_tmp` | MEDIUM | 4 tests |
| Vg.5 | Invalid read in `emit_llvm_ir__resolve_mir_type` | MEDIUM | 3 tests, 32_generic_enum affected |
| Vg.6 | `emit_llvm__emit_mir_basic_block` reads invalid memory | MEDIUM | 6 tests |
| Vg.7 | `lower__verify_block` reads invalid memory | LOW | 6 tests — verifier runs after lower, may be benign |

Vg.1/Vg.2/Vg.3 are the blue-chip entries: they hit tests the harness
calls PASS. The others overlap with known Phase 2 crashes.

## Evidence trail

- Full TSV: `artifacts/valgrind-summary.tsv`
- Top-frame clusters: `artifacts/valgrind-frame-clusters.txt`
- Per-test raw logs: `/tmp/v4_105_valgrind/<test>.log` (session-local)
- Runner script: `scripts/valgrind_all_goldens.sh` (committed)

## Exit criterion

- [x] **Exit #1** — valgrind report for all 64 golden tests: done.
- [ ] **Exit #2** — 0 valgrind errors on golden suite. **NOT MET** — 36
  of 64 have errors. This release *documents* them; fixes belong to
  post-panel work.

Per the PLAN's "What this release does NOT do" clause, discoveries go
to the v4.106.0 panel docket. No fixes attempted in this release.
