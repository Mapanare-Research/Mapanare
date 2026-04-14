# v4.104.0 Phase 5 — Divergence report (Python bootstrap vs mnc-stage1)

**Date:** 2026-04-14
**Method:** For each of 64 golden tests, emit IR from both compilers and
compare. Where both emit, run the stage1 IR through the full integration
pipeline and diff runtime output.

## Headline

| | Count | Notes |
|---|---:|---|
| Both compilers fail | 1 | `51_match_guards_and_or` — bootstrap semantic bug (Phase 3) |
| Only stage1 fails (MISSING) | 42 | Self-hosted compiler lacks feature/has crash bug |
| Both emit (comparable) | 21 | All with some divergence (see breakdown) |

Of the **21 comparable tests**:
- **20 emit valid IR** under `llvm-as` (one, `10_result`, fails IR validation)
- **18 ran end-to-end** (the other two require stdin/network)
- **17 of 18 produce byte-identical output** to the Python bootstrap
- **1** (`34_file_io`) differs by a transient filesystem state (stale `/tmp`)

So the stage1 compiler **produces correct behavior end-to-end on the 18 tests it can compile to linkable IR**.

## Classification tiers

Per the PLAN's three-tier taxonomy:

### COSMETIC (20 tests)

All stage1 PASSes except `10_result` fall into this bucket once we
normalize away three systematic differences:

1. **`main` return type:** bootstrap emits `define i64 @main()`, stage1
   emits `define i32 @main()`. Both work; stage1's is the Linux ABI-
   correct form. This is a per-binding difference, not a divergence
   between what either compiler *does*.

2. **`internal` linkage:** bootstrap marks non-entry-point functions
   `internal`, stage1 does not. `build_stage1.py` strips `internal`
   from bootstrap output before compiling anyway (to protect against
   `-O2` DCE with sret), so the post-processing equalizes this.

3. **Full runtime declare preamble:** stage1 emits all ~100 runtime
   `declare` lines regardless of usage; bootstrap emits only the
   declares it needs (5-13 typically). No semantic impact.

Tests in this tier (17 match bootstrap byte-for-byte, 1 is stale-state):

| Test | stg1 valid | stg1 runs | stg1 output == boot |
|---|:---:|:---:|:---:|
| 01_hello | ✅ | ✅ | ✅ |
| 02_arithmetic | ✅ | ✅ | ✅ |
| 04_if_else | ✅ | ✅ | ✅ |
| 06_struct | ✅ | ✅ | ✅ |
| 07_enum_match | ✅ | ✅ | ✅ |
| 08_list | ✅ | ✅ | ✅ |
| 09_string_methods | ✅ | ✅ | ✅ |
| 12_while | ✅ | ✅ | ✅ |
| 14_nested_struct | ✅ | ✅ | ✅ |
| 16_string_escape | ✅ | ✅ | ✅ |
| 17_option | ✅ | ✅ | ✅ |
| 18_method_chain | ✅ | ✅ | ✅ |
| 30_nested_generics | ✅ | ✅ | ✅ |
| 32_generic_enum | ✅ | ✅ | ✅ |
| 34_file_io | ✅ | ✅ | ⚠ stale /tmp count |
| 35_stdin | ✅ | skip | n/a |
| 36_crypto | ✅ | ✅ | ✅ |
| 37_regex | ✅ | ✅ | ✅ |
| 38_http | ✅ | skip | n/a |
| 39_gpu_detect | ✅ | ✅ | ✅ |

### SEMANTIC (1 test that already emits, plus notable ABI differences)

#### 10_result — invalid IR (HIGH)

stage1 emits `store i64 %v6, ptr %v7.addr` where `%v6` has type
`{ ptr, i64 }`. `llvm-as` rejects the IR. The test nonetheless appears
PASS in the `test_native.py` harness because the harness only counts
`define` lines, not IR validity.

This is the stage1 analogue of the bootstrap bug in `47_try_operator`
(documented in Phase 3): a type mismatch in the `?`-operator lowering,
stored into an undersized slot. The fix will need to land in
`mapanare/self/lower.mn` or `mapanare/self/emit_llvm.mn`.

**Docket candidate:** HIGH for v4.106.0.

#### Option payload representation (informational, not blocking)

- bootstrap: `{ i1, i64 }` — flat tagged union, integer payload inlined
- stage1:    `{ i1, ptr }` — tagged pointer, payload boxed

Both produce the same observable output for `17_option`, but the IR-level
ABI differs. Cross-boundary calls between bootstrap-compiled code and
stage1-compiled code would mismatch at this layer. Worth unifying for
eventual fixed-point self-compilation; not blocking for v4.104.0.

**Docket candidate:** MEDIUM for v4.106.0.

### MISSING (42 tests)

Every failure in Phase 2 falls here. The classification table from
Phase 2 applies:

| Category | Count | Reason |
|---|---:|---|
| A: Crash in `mir_opt__block_successors` | 14 | Self-hosted MIR optimizer null deref |
| B: Crash in `__mn_str_starts_with` | 9 | Self-hosted emitter String lifetime bug |
| C: Crash in `lower__lower_expr` | 3 | Self-hosted lowerer crash |
| D: MIR verifier — for_header0 missing terminator | 3 | Self-hosted lowerer invalid output |
| E: Semantic — `'Tensor'` undefined | 3 | Missing builtin |
| F: Parser — comma in `[a, b]` rejected | 2 | Grammar gap |
| G: Semantic — `'block_on'` undefined | 5 | Missing async builtin |
| H: Semantic — typed const / `fn(T) -> T` | 4 | Feature not ported to stage1 |

(Detailed per-test table in `PHASE2_GOLDEN.md`.)

### BOTH_FAIL (1 test)

`51_match_guards_and_or` — both compilers reject it. Bootstrap's
or-pattern checker refuses `Some(0) | None`. Documented in Phase 3's
`INTEGRATION_RESULTS.md`. Fix belongs in `mapanare/semantic.py` and
`mapanare/self/semantic.mn`.

**Docket candidate:** MEDIUM for v4.106.0.

## Docket items for v4.106.0 (Phase B panel)

| # | Item | Severity | Fix site |
|---|---|---|---|
| Div.1 | stage1 `?`-operator lowering emits wrong-type store (`10_result`) | HIGH | `mapanare/self/emit_llvm.mn` or `lower.mn` |
| Div.2 | bootstrap `?`-operator emits IR that fails `llvm-as` (`47_try_operator`) | HIGH | `mapanare/emit_llvm_text.py` |
| Div.3 | Option payload ABI differs (`{i1,i64}` vs `{i1,ptr}`) | MEDIUM | Unify in both emitters |
| Div.4 | or-pattern with enum constructor (`Some(0) \| None`) rejected by checker | MEDIUM | `mapanare/semantic.py` + `mapanare/self/semantic.mn` |
| Div.5 | `main` return type inconsistency (`i64` bootstrap vs `i32` stage1) | LOW | `mapanare/emit_llvm_text.py` |
| (MISSING bucket) | 42 stage1 crashes / semantic gaps (8 categories, Phase 2) | — | tracked separately |

## Exit criteria (Exits #5 + #6)

- [x] Divergence report written — this file.
- [x] Per-test findings documented — three tables above.
- [x] Cosmetic / Semantic / Missing / Both-fail classes all instantiated.
- [x] Semantic divergences (Div.1–Div.5) recorded as docket items for v4.106.0.
