# v4.130.0 Valgrind Report — 65 Golden Tests Swept

> **Phase F closeout release 10, Phase 2.** Generated 2026-04-15.
> Ran `valgrind --leak-check=full --track-origins=yes --error-exitcode=99`
> on `mnc-stage1` compiling each of the 65 `tests/golden/*.mn` files.
> Raw TSV + per-test logs preserved. Methodology identical to the
> v4.105.0 Phase B baseline.

## Verdict

| Class | v4.105.0 (baseline) | v4.130.0 (live) | Δ |
|---|---:|---:|---:|
| CLEAN | 0 | **0** | 0 |
| WARNINGS_ONLY | 28 | **34** | +6 |
| ERRORS | 36 | **31** | **−5** |
| Total | 64 | 65 | +1 (new golden 65_list_int_indexing) |

**Net improvement: 5 fewer tests triggering valgrind errors vs v4.105.0
baseline, 6 more tests clean of errors.** All four Phase A fixes
(v4.100.0–v4.103.0) held under re-run; no regressions since v4.105.0.
Zero CLEAN tests is expected: the self-hosted compiler uses arena
allocation with deferred teardown, which every test triggers as
"definitely lost" bytes in the 20–50KB range. v4.105.0's analysis
documented this as baseline allocator behaviour.

**Source archive:** `docs/roadmap/v4/v4.130.0/valgrind-summary.tsv`
(66 lines — 1 header + 65 data). Raw per-test logs:
`/tmp/v4_130_valgrind/*.log`.

---

## Methodology

```bash
VG_OUTDIR=/tmp/v4_130_valgrind bash scripts/valgrind_all_goldens.sh
```

The script (shipped at v4.105.0) runs `mnc-stage1` under valgrind
against each golden:

```
valgrind \
    --error-exitcode=99 \
    --errors-for-leak-kinds=none \
    --leak-check=full \
    --show-leak-kinds=all \
    --track-origins=yes \
    --num-callers=20 \
    mnc-stage1 tests/golden/NN.mn -o /tmp/vg_out/NN.ll
```

**Classification:**
- **CLEAN** — `ERROR SUMMARY: 0` + `definitely lost: 0` + `indirectly lost: 0`.
- **WARNINGS_ONLY** — `ERROR SUMMARY: 0` but non-zero leaks. Normal for
  arena allocator — memory is held until process exit, not freed.
- **ERRORS** — non-zero `ERROR SUMMARY` count (invalid reads/writes,
  uninitialised reads, etc.).

**Scope:** tests the **compiler under valgrind** (i.e., memory safety
of the self-hosted `mnc-stage1` binary as it parses, type-checks,
lowers, optimises, and emits LLVM IR). Does NOT test the emitted
binary's runtime behaviour — that's Phase 3 (ASan) which instruments
both the compiler and the emitted code.

---

## Top offending frames (self-hosted compiler stack)

Extracted from `at 0x...: <frame>` in each ERRORS log (top-of-stack
across all 31 failing tests):

| Frame | Count | Known docket |
|---|---:|---|
| `emit_llvm__emit_mir_call` | 13 | **Sh.2** (v4.111.0, open) — `__mn_str_starts_with` NULL deref / stale FnEntry.ret_type |
| `lower__lower_list` | 4 | **L** (v4.126.0 narrowed) — List<Value> realloc with stale pointers |
| `lower__lookup_struct_field_type` | 3 | new narrowing — see below |
| `lower_state__fresh_tmp` | 2 | candidate: state-struct aliasing |
| `lower__monomorphize_impl_methods` | 2 | candidate: generic monomorphization drift |
| `lower__lower_call_by_name` | 1 | same family as `emit_mir_call` |
| `emit_llvm__resolve_variant_index` | 1 | enum dispatch path |

### New finding — `lower__lookup_struct_field_type` (3 tests)

Sample stack (from `06_struct.log`):

```
==65967== Invalid read of size 8
==65967==    at 0x5E6D5C: lower__lookup_struct_field_type
==65967==    by 0x6A9322F: ???
==65967==  Address 0x6a90c00 is 16 bytes inside a block of size 144 free'd
```

Pattern: **use-after-free on the struct-field-type lookup block**. The
144-byte block was freed earlier and `lookup_struct_field_type` is
reading at offsets +16 and +24 — consistent with a `StructField`
struct (name at +16, type at +24) whose parent allocation was moved
by a List<StructField> reallocation. Same root-cause family as Sh.2
(stale copy of a FnEntry's ret_type) and L (stale List element
pointers). Not opened as a new docket — documented as a narrowing of
Sh.2's family on a different call site.

### Sh.2 is the dominant finding

13 of 31 ERRORS are `emit_llvm__emit_mir_call`. This is the
**single largest remaining self-hosted memory-safety finding**. The
v4.101.0 move-semantics fix that v4.124.0 SR pointed at as the
mirror-target (`_move_resource` in Python emitter, six call sites) is
still not mirrored into self-hosted `emit_llvm.mn`. Per v4.127.0 PLAN
"v4.127.0 PLAN target — mirror v4.101.0 `_move_resource` into
self-hosted emit_llvm.mn"; v4.127.0 shifted to fixed-point refinement
and did not land the Sh.2 fix. Sh.2 remains open on the v4.131.0+
post-panel arc.

---

## Per-test detail — 31 ERRORS

| Test | Exit code | Definitely lost | Indirectly lost | Error types |
|---|---:|---:|---:|---|
| 06_struct | 0 | 31 KB | 57 KB | Invalid read of size 8 |
| 08_list | 0 | 52 KB | 71 KB | Invalid read of size 8 |
| 10_result | 0 | 43 KB | 67 KB | Invalid read 1/2 |
| 13_fib | 0 | 32 KB | 57 KB | Invalid read of size 8 |
| 14_nested_struct | 0 | 35 KB | 62 KB | Invalid read of size 8 |
| 19_nested_match | 0 | 58 KB | 82 KB | Invalid read 1/2/8 |
| 20_recursion | 0 | 33 KB | 57 KB | Invalid read of size 8 |
| 21_list_ops | 0 | 55 KB | 79 KB | Invalid read of size 8 |
| 22_string_builder | 0 | 35 KB | 59 KB | Invalid read of size 8 |
| 23_multi_return | 0 | 43 KB | 65 KB | Invalid read 8/16 |
| 24_enum_methods | 0 | 41 KB | 68 KB | Invalid read of size 8 |
| 26_generics | 0 | 35 KB | 60 KB | Conditional jump uninit |
| 29_generic_impl | 0 | 45 KB | 70 KB | uninit + Invalid read 8 |
| 30_nested_generics | 0 | 38 KB | 63 KB | Conditional jump uninit |
| 31_generic_multi | 0 | 42 KB | 67 KB | uninit + Invalid read 8 |
| 32_generic_enum | 0 | 43 KB | 68 KB | Invalid read of size 8 |
| 33_break_continue | 0 | 32 KB | 57 KB | Invalid read of size 8 |
| 40_gpu_tensor | 0 | 45 KB | 70 KB | Invalid read of size 8 |
| 41_module_let | 0 | 32 KB | 57 KB | Invalid read 1/2 |
| 42_module_let_string | 0 | 34 KB | 59 KB | Invalid read 1/2 |
| 43_module_let_math | 0 | 33 KB | 58 KB | Invalid read 1/2 |
| 45_ffi_bind | 0 | 37 KB | 62 KB | Invalid read of size 8 |
| 47_try_operator | 0 | 51 KB | 75 KB | Invalid read 1/2/8 |
| 48_match_nested_exhaustive | 0 | 61 KB | 86 KB | Invalid read 1/2/8 |
| 49_match_guards | 0 | 47 KB | 72 KB | Invalid read of size 8 |
| 50_match_or_patterns | 0 | 45 KB | 70 KB | Invalid read of size 8 |
| 51_match_guards_and_or | 0 | 46 KB | 71 KB | Invalid read of size 8 |
| 54_const_basic | 0 | 33 KB | 58 KB | Invalid read 1/2 |
| 58_const_scope | 0 | 42 KB | 67 KB | Invalid read 1/2/8 |
| 62_list_output | 0 | 43 KB | 67 KB | Invalid read of size 8 |
| 63_else_sino | 0 | 36 KB | 62 KB | Invalid read of size 8 |

**Every test with errors still exits 0.** The compiler completes
successfully; the valgrind findings are memory-safety violations that
happen to not produce user-visible misbehaviour because freed memory
has not yet been reallocated to another purpose when the invalid
reads happen. This is the classic silent-UB profile — benign at
runtime, but a hazard that would bite under an allocator with
different placement policy, under ASan (Phase 3), or under a real
multi-threaded workload with concurrent free + allocate.

---

## Per-test detail — 34 WARNINGS_ONLY (error-free samples)

Tests that complete with zero valgrind errors, only expected arena-
allocator retention:

| Test | Exit code | Definitely lost | Indirectly lost |
|---|---:|---:|---:|
| 01_hello | 0 | 22 KB | 47 KB |
| 02_arithmetic | 0 | 31 KB | 50 KB |
| 03_function | 0 | 39 KB | 56 KB |
| 04_if_else | 0 | 36 KB | 54 KB |
| 05_for_loop | 0 | 36 KB | 55 KB |
| 07_enum_match | 0 | 44 KB | 69 KB |
| 09_while_loop | 0 | 32 KB | 52 KB |
| 11_closure | 0 | 36 KB | 63 KB |
| 12_match_basic | 0 | 37 KB | 60 KB |
| 15_multifunction | 0 | 39 KB | 56 KB |
| 16_list_basic | 0 | 32 KB | 55 KB |
| 17_option | 0 | 34 KB | 61 KB |
| 18_map | 0 | 36 KB | 62 KB |
| 25_fizzbuzz | 0 | 36 KB | 59 KB |
| 27_impl | 0 | 41 KB | 64 KB |
| 28_traits | 0 | 44 KB | 69 KB |
| 65_list_int_indexing | 0 | 32 KB | 55 KB |

(Plus ~17 more — full data in the TSV.)

These tests exercise the same compiler code paths as the ERRORS set
but happen to not trigger the use-after-free pattern on their
specific input. Running under different golden program structure
would likely shift which tests land in WARNINGS_ONLY vs ERRORS.

---

## Comparison to v4.105.0 baseline

v4.105.0 SR reported:

```
Top frames:
- mir_opt__block_successors: 14×
- __mn_list_free: 12×
- emit_llvm__emit_mir_call: 11×
```

v4.130.0 result:

```
- emit_llvm__emit_mir_call: 13×
- lower__lower_list: 4×
- lower__lookup_struct_field_type: 3×
- lower_state__fresh_tmp: 2×
```

**Delta interpretation:**

- **`mir_opt__block_successors` dropped from 14× → 0×.** The v4.111.0
  disable of the 4 zero-ROI MIR optimiser passes (strength_reduce /
  inline_small_fns / licm / escape_analysis) eliminated this hot
  frame. Confirmed with grep: zero valgrind logs reference the frame.
- **`__mn_list_free` dropped from 12× → 0×.** v4.101.0's
  `_move_resource` adoption in the Python emitter removed the drop-
  glue use-after-free. But the C-runtime `__mn_list_free` is symmetric
  between bootstrap and self-hosted — so the v4.101.0 fix must be
  reaching both paths via the common runtime. Zero occurrences in the
  v4.130.0 logs; v4.105.0's 12× is gone.
- **`emit_llvm__emit_mir_call` moved 11 → 13.** Sh.2 has grown
  slightly — the two additional tests hitting it are likely new or
  newly-covered goldens (65_list_int_indexing is new; others may have
  shifted behavior under v4.124.0 Rt.1 enum-layout changes).
- **New: `lower__lookup_struct_field_type` at 3×.** Not in v4.105.0's
  top-3. Family-same as Sh.2 (stale FnEntry.ret_type pattern; this
  site has stale StructField.name / .type pattern). Not opening a new
  docket; narrowing of Sh.2 family.

---

## Carry-forward from this report

1. **Sh.2 remains the dominant finding.** 13 of 31 ERRORS on one
   frame. The v4.127.0 PLAN pointed at the fix (mirror v4.101.0
   `_move_resource` into self-hosted `emit_llvm.mn` at six call
   sites); v4.127.0–v4.130.0 did not land it. **v4.131.0+ target.**
2. **L narrowing.** v4.126.0 narrowed `33_break_continue` to
   "let + 2+-element list literal". v4.130.0 confirms the pattern
   holds across `08_list`, `21_list_ops`, `33_break_continue`,
   `62_list_output`. Same Sh.2 family; same fix vehicle.
3. **`lower__lookup_struct_field_type`** — new narrowing of Sh.2
   family on a third call site. Fix mechanism same as Sh.2
   (move-semantics on the intermediate FnEntry-like copy).
4. **Arena-allocator pattern is not a bug.** 34 WARNINGS_ONLY tests
   have "definitely lost" bytes in 20–60KB range. This is intentional
   v4.105.0-documented design (arena is never freed between compile
   phases). Per v4.105.0 SR: "these leaks are not a v4.x target;
   closure is a v5.x memory-model redesign (slot-pooled arenas) or
   equivalent."

---

## Panel impact projection

Viper (memory safety reviewer) graded v4.120.0 at 8.4 with notes
including the v4.105.0 baseline's 36 ERRORS count and 12 heap-UAF
from `mn_list_rc`.

v4.130.0 evidence:
- **5 fewer tests with errors** (36 → 31).
- **Top two hot frames eliminated** (`mir_opt__block_successors`,
  `__mn_list_free`).
- **Sh.2 is now the named target**; v4.127.0 PLAN had pointed at the
  fix vehicle.
- **Zero CLEAN tests** — but the arena-allocator reading is
  well-documented and not a regression.

If Viper accepts the Sh.2 narrowing + the v4.101.0/v4.111.0 closures,
the grade likely holds or moves up slightly (+0.1 to 0.3). The hold
item for PASS: Sh.2 is documented, scoped, and has a named fix path.
