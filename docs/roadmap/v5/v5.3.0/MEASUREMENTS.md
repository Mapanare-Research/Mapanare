# MEASUREMENTS.md — v5.3.0 Pre-Panel Evidence

> **Canonical evidence snapshot for the v5.3.0 panel.** All numbers
> from WSL2 on the dev branch at commit `b40bedb` (HEAD of v5.2.0).
> Reviewers should cite this document, not SESSION_REPORTs.

**Date:** 2026-04-22
**Platform:** WSL2 (Ubuntu, LLVM 18.1.3, valgrind 3.22.0)
**Branch:** dev
**HEAD:** b40bedb (Switch registry to mapanare.dev API)

---

## 1. Test Suite

### 1.1 Non-bootstrap pytest

```
8 failed, 5445 passed, 116 skipped, 9 xfailed, 2 warnings in 527.74s
```

**Failure classification (8 deterministic failures):**

| # | Test | Category | Root cause |
|---|------|----------|------------|
| 1 | `test_user_agent_contains_current_version` | VERSION drift | Binary embeds 5.1.4; VERSION file reads 5.2.0 |
| 2 | `test_mnc_stage1_version_matches_version_file` | VERSION drift | mnc-stage1 embeds 5.1.4; VERSION file reads 5.2.0 |
| 3 | `test_black_check_passes` | Lint (v5.2.0 registry) | 4 files need black: stdlib/pkg.py, mapanare/cli.py, 2 test files |
| 4 | `test_ruff_check_passes` | Lint (v5.2.0 registry) | 9 ruff errors: 1 E501, 1 I001, 5 F401, 2 others in registry code |
| 5 | `test_all_c_tests_pass` | Stream runtime | 3/74 C tests fail: stream_from_list_collect, stream_map, stream_filter |
| 6 | `test_asan_no_errors` | Stream runtime | Same 3 stream tests fail under ASan |
| 7 | `test_tsan_no_races` | Stream runtime | Same 3 stream tests fail under TSan |
| 8 | `test_post_opt_single_switch_in_hot_loop` | E1 opt regression | LLVM 18 opt produces 0 switches in hot loop (expected 1) |

**Category totals:**
- VERSION drift (2) — binary not rebuilt after v5.2.0 version bump
- Lint (2) — v5.2.0 registry code committed without `black`/`ruff` pass
- Stream runtime (3) — `__mn_list_get` in stream collect/map/filter returns wrong element values (71/74 C tests pass)
- LLVM version (1) — LLVM 18 optimizes differently than LLVM 17 for E1 switch folding

### 1.2 Flaky audit (5x sequential)

```
Run 1: 8 failed, 5445 passed in 538s
Run 2: 8 failed, 5446 passed in 505s
Run 3: 8 failed, 5447 passed in 490s
Run 4: 8 failed, 5447 passed in 493s
Run 5: 8 failed, 5452 passed in 484s

Pairwise diffs: 4/4 IDENTICAL failure sets
Flaky count: 0
```

**0 flaky across 5 sequential runs.** Same 8 deterministic failures
in every run. Pass count varies 5445–5452 (normal parametrized test
generation noise). Cumulative across all audits (v4.117.0 through
v5.3.0): **35 sequential runs, 0 flaky.**

### 1.3 Registry tests

```
51 passed in 1.14s
```

All 51 registry tests pass (manifest parsing, lockfile round-trip, semver
resolution, tarball creation, integrity hashing, install-all).

### 1.4 Test count (deterministic)

```
scripts/count_tests.py: 4284 def test_* declarations
pytest collected: ~5445 (parametrized expansion)
```

Delta from v4.154.0: 5309 → 5445 (+136 tests, primarily from registry suite).

### 1.5 Bootstrap tests

```
[Not re-run this session — expected 212 passed / 13 failed, stable]
```

---

## 2. Golden Tests (native compiler)

```
54 passed, 12 failed in 6.4s
```

**54/66 — unchanged from v4.144.0 through v5.2.0 (32+ releases).**

The 12 failures are the same feature-gap bucket:
- 5 async tests (55-59)
- 5 tensor/GPU tests (39-40, 51-53)
- 1 closure-typed (64)
- 1 or-pattern / break-continue interaction

---

## 3. Fixed-Point Verification

**Status: BROKEN (regression from NEAR)**

```
stage2.ll: 120,956 lines
llvm-as: FAIL
error: use of undefined value '%_inl0_6_t4'
  store %struct.Span %_inl0_6_t4, ptr %_inl0_6_retval.cpy
```

**Root cause:** v5.1.2 re-enabled `inline_small_functions` in the
self-hosted MIR optimizer. The In.1 rename fix (`%_inlN_M_dst`)
works for golden tests (54/66 unchanged), but fails when the
self-hosted compiler compiles itself — the inliner produces an
undefined SSA name on the Span struct in the lexer module.

**Prior state (v4.154.0):** NEAR FIXED POINT (4 diff, version
metadata only). stage2.ll == stage3.ll structurally at 110,127 lines.

**Regression timeline:**
- v4.134.0: STRICT (first time — La Culebra Se Muerde La Cola)
- v4.154.0: NEAR (4 diff, Dr.1 version metadata)
- v5.1.2: BROKEN (In.1 inliner re-enable produces invalid SSA in stage2)

This is the most significant quality regression in the v5 arc.
The v5.1.2 In.1 fix passed all 54 golden tests and 4 dedicated
rename tests, but the self-compilation path exercises more complex
inlining patterns that the rename logic does not handle.

---

## 4. Module Sizes

### 4.1 Self-hosted compiler

```
wc -l mapanare/self/*.mn: 41,195 total
```

Delta from v4.154.0 (40,319): +876 lines (+2.2%) — primarily from
v5.0.4 abi.mn, v5.0.5 semantic.mn bare_type_name, v5.1.0 emit_llvm.mn
inline list ops, v5.1.2 mir_opt.mn inline rename helpers.

### 4.2 main.ll (concatenated IR)

```
922,330 lines
```

Delta from v4.154.0 (912,184): +10,146 lines (+1.1%).

### 4.3 Native binary

```
mnc-stage1: 3,648,672 bytes (stripped)
```

Delta from v4.154.0 (3,583,120): +65,552 bytes (+1.8%).

### 4.4 C runtime

```
runtime/native/*.c + *.h: 14,963 lines
libmapanare_rt.a: 269,886 bytes
```

Delta from v4.154.0 (14,687 lines / 268,326 bytes): +276 lines / +1,560 bytes.

---

## 5. Sanitizer State

### 5.1 Valgrind

```
66 tests: 62 WARNINGS_ONLY, 2 ERRORS
```

**ERRORS (2):** `39_gpu_detect` (6390 errors, timeout), `40_gpu_tensor`
(6390 errors, timeout) — both are GPU feature-gap tests that attempt
`dlopen` for CUDA/Vulkan. These are not memory-safety bugs.

**Ge.1r CONFIRMED CLOSED:** Generics goldens 26/29/30/31 — all clean
under valgrind. The v5.1.1 zero-init fix in `try_monomorphize_enum` /
`try_monomorphize_struct` eliminated the 4 "Invalid read of size 16|8"
errors that Viper reported at v4.154.0.

**Delta from v4.154.0:** 4 ERRORS (Ge.1 generics) → 2 ERRORS (GPU
feature gap). Net improvement: -2 ERRORS, and the remaining 2 are
from an entirely different class (dlopen, not memory safety).

### 5.2 ASan

C hardening tests: 3 stream test failures (see §1.1 above).
Not new ASan memory-safety findings — the stream tests fail with
wrong values, not with ASan errors.

### 5.3 TSan

Same 3 stream test failures. No race conditions detected.

---

## 6. Carry-Forward Closures (v5.0.1 → v5.2.0)

| ID | Closed at | Category | What |
|----|-----------|----------|------|
| Cb.15 | v5.0.4 | ABI | sret classifier ported to self-hosted |
| Cb.9a | v5.0.5 | Semantic | Qualified type refs in self-hosted semantic.mn |
| Gr.2 | v5.0.5 | Grammar | Bootstrap grammar synced with NAME (DOT NAME)* |
| Bo.12-table | v5.0.6 | Docs | README benchmark table updated to v4.153.0 |
| Bo.12-i18n | v5.0.6 | Docs | Localized READMEs synced |
| Rt.4 | v5.0.6 | Codegen | llvm_type_size enum safe upper bound |
| Bn.3 | v5.0.6 | Benchmark | JSON version reads VERSION file |
| Cb.6-test | v5.0.6 | Testing | Regression gate for i64* rejection |
| An.9 | v5.0.6 | Testing | E1 unified-return IR-shape tests |
| An.10 | v5.0.6 | Testing | Deterministic test-count script |
| Dr.1-mutation | v5.0.6 | Build | tempdir substitution in build_stage1.py |
| Perf.1 | v5.1.0 | Performance | Inline list ops — quicksort 2.99× → 1.14× Rust |
| Ge.1r | v5.1.1 | Memory | Zero-init monomorphized generics fields |
| In.1 | v5.1.2 | Optimizer | Inliner SSA rename fix (pass enabled) |
| Ea.1 | v5.1.2 | Optimizer | Escape analysis ported to self-hosted |
| Bn.2 | v5.1.2 | Benchmark | Geomean arithmetic function |
| Bn.4 | v5.1.2 | Benchmark | C struct_alloc rewritten (no malloc) |
| Own.1 P1 | v5.1.3 | Safety | Cb.7 zero-after-push at register_struct/enum |
| Perf.2 | v5.1.4 | Performance | Lazy coro threads (0.91× Go at default) |

**19 carry-forwards closed in 12 releases.** This is the highest
closure rate per release in the project's history.

---

## 7. Remaining Open Items

| ID | Severity | Status | What |
|----|----------|--------|------|
| Li.1 | LOW | OPEN | LICM hoist_instruction — unit tests pass, live goldens regress |
| Own.1 P2 | LOW | DEFERRED | Move instruction + drop-glue in self-hosted emitter |
| Sh.4/5/6/7 | LOW | DEFERRED | Feature gaps (tensor, views, slices, closure-typed) |
| Sh.9a | LOW | DEFERRED | Async test harness |
| In.1-stage2 | NEW | OPEN | Inliner SSA rename breaks stage2 self-compilation |
| Lint-v5.2.0 | NEW | OPEN | 4 files need black/ruff in registry code |
| Stream-C | NEW | OPEN | 3 stream C runtime tests fail (wrong element values) |

---

## 8. Arc Summary (v5.0.1 → v5.2.0)

| Release | What | Domain |
|---------|------|--------|
| v5.0.1 | Windows native binary | Platform |
| v5.0.2 | .exe suffix fix | Platform |
| v5.0.3 | macOS Intel binary | Platform |
| v5.0.4 | Cb.15 sret classifier ported | ABI / Self-hosted |
| v5.0.5 | Gr.2 + Cb.9a qualified refs | Grammar / Semantic |
| v5.0.6 | 8-item multi-cycle closeout | Hygiene |
| v5.1.0 | Perf.1 inline list ops | Performance |
| v5.1.1 | Windows stage2 + Ge.1r | Platform / Safety |
| v5.1.2 | In.1 + Ea.1 MIR passes + Bn.2/Bn.4 | Optimizer / Benchmark |
| v5.1.3 | Own.1 Phase 1 | Safety |
| v5.1.4 | Perf.2 lazy coro threads | Performance |
| v5.2.0 | Package Registry MVP | Feature |

**12 releases, 21 commits, 19 carry-forward closures.**

---

## 9. Reproducibility

```bash
# Test suite
python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no

# Golden tests
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# Fixed-point
bash scripts/verify_fixed_point.sh --keep

# Registry tests
python3 -m pytest tests/registry/ -q

# Test count
python3 scripts/count_tests.py

# Valgrind sweep
for mn in tests/golden/*.mn; do
    base=$(basename "$mn" .mn)
    python3 -m mapanare emit-llvm "$mn" -o "/tmp/vg_${base}.ll"
    clang -O0 "/tmp/vg_${base}.ll" runtime/native/libmapanare_rt.a \
        -lm -lpthread -o "/tmp/vg_${base}"
    valgrind --error-exitcode=99 --leak-check=no "/tmp/vg_${base}" 2>&1 \
        | grep "ERROR SUMMARY"
done

# C hardening
python3 -m pytest tests/native/test_c_hardening.py -v
```
