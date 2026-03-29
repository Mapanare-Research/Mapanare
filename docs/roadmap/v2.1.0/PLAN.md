# Mapanare v2.1.0 — "Python Independence"

> The Python transpiler backends are deprecated since v2.0.0, but the Python
> *compiler* still runs every test. 4,400+ tests invoke the Python lexer, parser,
> semantic checker, MIR lowerer, and LLVM emitter — the test harness is just the
> thin wrapper. Rewriting tests in Go or Rust would not help: the bottleneck is
> the compiler code itself, not pytest.
>
> v2.1.0 closes that gap. The self-hosted compiler reaches fixed-point, tests
> migrate to call the native binary, and the test infrastructure scales to match.
>
> Core theme: **The compiler compiles itself. Tests call native code. Python is optional.**

---

## Scope Rules

1. **No new language features** — syntax and semantics are frozen at v1.0
2. **Self-hosted parity is the gate** — `mnc` must compile itself before tests migrate
3. **Each phase is shippable independently** — immediate wins first, compiler fixes second
4. **Every phase must leave all tests green** — no regressions
5. **Python bootstrap stays for reference** — it becomes the oracle, not the product

---

## Status Tracking

| Icon | Meaning |
|------|---------|
| `[ ]` | Not started |
| `[~]` | In progress |
| `[x]` | Done |
| `[!]` | Skipped (reason noted) |

---

## Phase Overview

| Phase | Name | Status | Effort | Speedup |
|-------|------|--------|--------|---------|
| 1 | Immediate Test Parallelism | `Not started` | Small | 4-6x |
| 2 | Self-Hosted Compiler: Control Flow Fix | `Not started` | Large | — |
| 3 | Self-Hosted Compiler: Large Struct Codegen | `Not started` | Large | — |
| 4 | Fixed-Point Verification | `Not started` | Medium | — |
| 5 | Native Test Migration | `Not started` | X-Large | 10-50x |
| 6 | Go Test Harness (optional) | `Not started` | Large | 2-3x on top of Phase 5 |

---

## Phase 1 — Immediate Test Parallelism
**Status:** `Not started`
**Effort:** Small
**Expected speedup:** 4-6x (no code changes to tests)

The tests are independent — no shared global state, no database, no filesystem
contention. `pytest-xdist` can distribute them across CPU cores immediately.

### Tasks

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Add `pytest-xdist` to dev dependencies | `[ ]` | `pyproject.toml` | `pip install pytest-xdist` |
| 2 | Add `-n auto` to default pytest invocation | `[ ]` | `pyproject.toml`, `Makefile` | `addopts = "-n auto"` in `[tool.pytest.ini_options]` |
| 3 | Fix any tests that accidentally share state | `[ ]` | `tests/` | Unlikely but audit — look for temp files with fixed names, global singletons |
| 4 | Update CI to use parallel execution | `[ ]` | `.github/workflows/ci.yml` | `pytest tests/ -v -n auto` |
| 5 | Measure before/after wall-clock time | `[ ]` | — | Record in this plan |
| 6 | Add `pytest --durations=50` to CI for ongoing bottleneck visibility | `[ ]` | `.github/workflows/ci.yml` | Shows the 50 slowest tests per run |

**Done when:** CI runs 4x faster. No test failures from parallelism.

---

## Phase 2 — Self-Hosted Compiler: Control Flow Fix
**Status:** `Not started`
**Effort:** Large
**Depends on:** Nothing (can run in parallel with Phase 1)

The self-hosted compiler (`mnc-stage1`) compiles 6/15 golden tests correctly.
The remaining 9 fail because **`return` inside `if`/`match` blocks does not
actually return** — control flow falls through to the merge block.

This is the single biggest blocker to self-hosted parity. See
[`ENUM_PAYLOAD_FIX_PLAN.md`](../ENUM_PAYLOAD_FIX_PLAN.md) for the full diagnosis.

### Root Cause

`lower.mn`'s `lower_if` creates separate blocks for then/else/merge. A `Return`
in the then-block becomes the block's last instruction, but the merge block still
gets emitted and falls through. The terminator is lost.

### Fix Options

| Approach | Complexity | Risk |
|----------|-----------|------|
| A. Fix `lower_if` in `lower.mn` to detect `Return` and skip merge block emission | Medium | Low — surgical fix at the source |
| B. Add a post-pass in `lower.mn` that removes unreachable blocks after `Return` | Medium | Low — catch-all but harder to debug |
| C. Fix the Python bootstrap `lower.py` to generate better MIR that `emit_llvm.mn` can handle | Small | Medium — may mask the real bug |

### Tasks

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Create minimal `.mn` reproducer: function with `if { return X }` that falls through | `[ ]` | `tests/golden/` | Smallest program that triggers the bug |
| 2 | Trace MIR block graph for the reproducer — identify missing terminator | `[ ]` | — | Use `--emit-mir` to inspect |
| 3 | Fix `lower_if` in `lower.mn`: detect `Return` in then/else and mark merge block unreachable | `[ ]` | `mapanare/self/lower.mn` | Approach A |
| 4 | Fix `lower_match` in `lower.mn`: same terminator propagation for match arms | `[ ]` | `mapanare/self/lower.mn` | Same pattern |
| 5 | Fix nested conditionals: `if { if { return } }` must propagate through both levels | `[ ]` | `mapanare/self/lower.mn` | Recursive case |
| 6 | Rebuild `mnc-stage1` with the fix | `[ ]` | — | `python scripts/build_stage1.py` |
| 7 | Verify 15/15 golden tests produce valid IR | `[ ]` | — | `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v` |
| 8 | Verify the 9 previously-failing tests now pass | `[ ]` | — | struct, loop, enum, string, closure, result tests |

**Done when:** `mnc-stage1` compiles all 15 golden tests to correct, runnable LLVM IR.

---

## Phase 3 — Self-Hosted Compiler: Large Struct Codegen
**Status:** `Not started`
**Effort:** Large
**Depends on:** Phase 2 (control flow must work before large modules compile)

Even after the control flow fix, `mnc-stage1` crashes on its own large modules
(`parser.mn`, `semantic.mn`, `lower.mn`, `emit_llvm.mn`) due to large-struct
codegen issues at the 680-byte `LowerState` scale.

### Known Issues

From v1.0.x final results:
- llvmlite truncates large by-value load/store (>128 bytes) — partially fixed
  with `llvm.memcpy` in `_emit_enum_init` for large enums (v1.0.11)
- LowerState (680 bytes) triggers remaining edge cases in struct pass-by-value
- Self-hosted emitter's type resolution: `List<Int>` had kind `"unknown"` instead
  of `"list"` — partially fixed by checking method name before type kind

### Tasks

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Profile `mnc-stage1` crash on `parser.mn` — capture crash location and IR state | `[ ]` | — | `mnc-stage1 mapanare/self/parser.mn 2>&1` |
| 2 | Identify all struct types > 128 bytes in the self-hosted compiler | `[ ]` | `mapanare/self/*.mn` | LowerState, ParseState, SemanticState, EmitState |
| 3 | Ensure all large structs use pointer-based passing (sret/byptr) consistently | `[ ]` | `mapanare/emit_llvm_mir.py` | The v1.0.11 fix may be incomplete for self-referential patterns |
| 4 | Fix type resolution for nested generic types (`List<StructInit>`, `Map<String, MIRType>`) | `[ ]` | `mapanare/emit_llvm_mir.py`, `mapanare/self/emit_llvm.mn` | The "unknown" kind fallback |
| 5 | Test: `mnc-stage1` compiles `parser.mn` without crash | `[ ]` | — | Largest module (1,721 lines) |
| 6 | Test: `mnc-stage1` compiles `semantic.mn` without crash | `[ ]` | — | Second largest (1,607 lines) |
| 7 | Test: `mnc-stage1` compiles `lower.mn` without crash | `[ ]` | — | Largest (2,629 lines), heaviest struct usage |
| 8 | Test: `mnc-stage1` compiles `emit_llvm.mn` without crash | `[ ]` | — | 1,497 lines |
| 9 | Test: `mnc-stage1` compiles `mnc_all.mn` (all 7 modules concatenated) | `[ ]` | — | The full self-compilation input |

**Done when:** `mnc-stage1` compiles its own source code into `mnc-stage2` without crashing.

---

## Phase 4 — Fixed-Point Verification
**Status:** `Not started`
**Effort:** Medium
**Depends on:** Phase 3 (mnc-stage1 must compile itself first)

Three-stage bootstrap: `mnc-stage1` (built from Python) compiles itself into
`mnc-stage2`, which compiles itself into `mnc-stage3`. If `stage2 == stage3`
(byte-identical IR), the compiler has reached a fixed point and Python is no
longer needed for compilation.

### Tasks

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Stage 2: `mnc-stage1` compiles `mnc_all.mn` -> `mnc-stage2` IR | `[ ]` | — | First self-compilation |
| 2 | Stage 3: `mnc-stage2` compiles `mnc_all.mn` -> `mnc-stage3` IR | `[ ]` | — | Second self-compilation |
| 3 | Binary diff: `mnc-stage2` IR == `mnc-stage3` IR | `[ ]` | — | THIS is the fixed point |
| 4 | Update `scripts/verify_fixed_point.sh` if needed | `[ ]` | `scripts/verify_fixed_point.sh` | |
| 5 | Fixed-point CI job passes (remove `continue-on-error: true`) | `[ ]` | `.github/workflows/ci.yml` | Make it a hard gate |
| 6 | Document the achievement in ROADMAP.md | `[ ]` | `docs/roadmap/ROADMAP.md` | Milestone: Python bootstrap is no longer required |

**Done when:** `verify_fixed_point.sh` passes. CI gates on it. The compiler sustains itself.

---

## Phase 5 — Native Test Migration
**Status:** `Not started`
**Effort:** X-Large
**Depends on:** Phase 4 (fixed-point must pass — otherwise tests would use an incorrect compiler)
**Expected speedup:** 10-50x over Python pipeline (native compilation in microseconds vs milliseconds)

Migrate tests from calling the Python compiler pipeline (`from mapanare.parser import ...`)
to invoking the native `mnc` binary via subprocess. The Python bootstrap becomes the
oracle for differential testing, not the primary test target.

### Strategy

Tests fall into three categories:

| Category | Count | Migration Path |
|----------|-------|----------------|
| **Compilation tests** (parse + semantic + emit, verify IR) | ~3,500 | Call `mnc` binary, check IR output |
| **Runtime behavior tests** (compile + execute, check stdout) | ~500 | Call `mnc` to compile, `lli` to execute, check stdout |
| **Python-specific tests** (Python emitter, bootstrap, FFI) | ~400 | Keep as-is (deprecated backend, reference only) |

### Tasks

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Create `tests/conftest.py` with `mnc_binary` fixture that locates `mnc-stage1` | `[ ]` | `tests/conftest.py` | Skip tests if binary not found |
| 2 | Create `tests/helpers/native.py` with `compile_mn(source) -> ir`, `run_mn(source) -> stdout` | `[ ]` | `tests/helpers/native.py` | Thin subprocess wrapper |
| 3 | Migrate `tests/llvm/` — LLVM IR validation tests (19 files) | `[ ]` | `tests/llvm/` | Highest value: most tests, all check IR output |
| 4 | Migrate `tests/mir/` — MIR tests (4 files) | `[ ]` | `tests/mir/` | Need `mnc --emit-mir` flag |
| 5 | Migrate `tests/semantic/` — type checking tests (3 files) | `[ ]` | `tests/semantic/` | Need `mnc check` to report errors |
| 6 | Migrate `tests/parser/` — syntax tests (2 files) | `[ ]` | `tests/parser/` | Need `mnc --parse-only` or similar |
| 7 | Migrate `tests/e2e/` — end-to-end tests (7 files) | `[ ]` | `tests/e2e/` | `mnc build` + execute |
| 8 | Migrate `tests/wasm/` — WASM emitter tests (4 files) | `[ ]` | `tests/wasm/` | `mnc emit-wasm` |
| 9 | Migrate `tests/stdlib/` — stdlib compilation tests (21 files) | `[ ]` | `tests/stdlib/` | `mnc build` with stdlib imports |
| 10 | Keep Python-only tests tagged with `@pytest.mark.python_backend` | `[ ]` | `tests/` | Bootstrap, FFI, Python emitter tests |
| 11 | Add `--backend=native` / `--backend=python` test selector | `[ ]` | `tests/conftest.py` | Run both for differential testing |
| 12 | Measure before/after wall-clock time | `[ ]` | — | Record in this plan |

**Done when:** >80% of tests call the native binary. Full suite is faster than Phase 1 baseline.

---

## Phase 6 — Go Test Harness (Optional)
**Status:** `Not started`
**Effort:** Large
**Depends on:** Phase 5 (only makes sense when tests call a native binary)

Once tests shell out to `mnc`, the Python test runner adds overhead: process
startup, GIL, subprocess management. A Go test harness would eliminate that:
`go test -parallel` with native subprocess management, zero warmup, built-in
benchmarking.

This phase is optional. It only makes sense if Phase 5 shows that pytest
subprocess overhead is a measurable bottleneck (>20% of wall-clock time).

### Decision Criteria

| Metric | Stay with pytest | Migrate to Go |
|--------|-----------------|---------------|
| pytest subprocess overhead | <20% of total time | >20% of total time |
| Test count growth | Stable | Growing fast (>6,000) |
| CI wall-clock time after Phase 5 | <5 min | >10 min |
| Team Go experience | Low | Comfortable |

### Tasks (if Go is chosen)

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Design Go test structure: `tests_go/compiler_test.go`, `tests_go/e2e_test.go` | `[ ]` | `tests_go/` | Mirror Python test categories |
| 2 | Implement `mnc` binary wrapper: `CompileMN(source) -> (ir string, err)` | `[ ]` | `tests_go/testutil/` | Reusable across all tests |
| 3 | Migrate golden tests first (15 tests, well-defined input/output) | `[ ]` | `tests_go/golden_test.go` | Validate approach |
| 4 | Migrate LLVM IR validation tests | `[ ]` | `tests_go/llvm_test.go` | Bulk of the suite |
| 5 | Migrate E2E tests | `[ ]` | `tests_go/e2e_test.go` | `mnc build` + execute |
| 6 | Parallel execution with `t.Parallel()` | `[ ]` | `tests_go/` | Built into Go's test runner |
| 7 | CI integration: `go test ./tests_go/... -v -count=1` | `[ ]` | `.github/workflows/ci.yml` | Alongside or replacing pytest |
| 8 | Keep pytest for Python-specific tests (bootstrap, FFI, Python backend) | `[ ]` | — | ~400 tests stay in Python |

### Why Go Over Rust

| Factor | Go | Rust |
|--------|-----|------|
| Test runner | Built-in, parallel, benchmarks | Needs `#[test]` + custom harness |
| Subprocess management | `exec.Command` — simple | `std::process::Command` — verbose |
| Compile time (tests themselves) | <2s | 10-30s for first build |
| String assertions | `strings.Contains`, `testing` | `assert!` macros, less ergonomic for string-heavy IR checks |
| Learning curve | Low | Medium-high |
| Binary size | Single `go test` binary | Single binary but slower to produce |

**Done when:** Go test suite covers the same ground as pytest. CI uses Go for native tests, pytest for Python-only tests.

---

## Execution Order

```
Phase 1 (parallelism) ─────────────────────────────────── Immediate 4-6x win
     │
Phase 2 (control flow fix) ── Phase 3 (large struct) ─── Compiler parity
                                        │
                                   Phase 4 (fixed-point) ── The milestone
                                        │
                                   Phase 5 (test migration) ── 10-50x win
                                        │
                                   Phase 6 (Go harness) ── Optional, measure first
```

Phase 1 is independent and should ship immediately. Phases 2-4 are the critical
path to self-hosted parity. Phase 5 is the payoff. Phase 6 is only justified by
measurements after Phase 5.

---

## Success Metrics

| Metric | Current (v2.0.1) | After Phase 1 | After Phase 5 | After Phase 6 |
|--------|------------------|---------------|---------------|---------------|
| Test suite wall-clock | ~TBD | ~TBD / 4-6x | ~TBD / 10-50x | ~TBD / 2-3x more |
| Python required at runtime | Yes (compiler) | Yes (compiler) | No (native `mnc`) | No |
| Self-compilation | Crashes on large modules | Crashes on large modules | Fixed-point achieved | Fixed-point achieved |
| Test count | 4,400+ | 4,400+ | 4,400+ | 4,400+ |

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Control flow fix in `lower.mn` breaks working tests | High | Run golden harness after every change |
| Large struct codegen has deeper issues than expected | High | Fall back to refactoring LowerState into smaller structs (<128 bytes) |
| Fixed-point produces different IR (not byte-identical) | Medium | Diff-based debugging, relax to semantic equivalence first |
| Native test migration reveals `mnc` bugs not caught by golden tests | Medium | Differential testing: run both Python and native, compare |
| Go harness not worth the effort | Low | Phase 6 is gated on measurements — skip if pytest is fast enough |

---

## References

- [v1.0.x Plan](../v1.0.x/PLAN.md) — v1.0.5/v1.0.6 self-hosted compiler status
- [Enum Payload Fix Plan](../ENUM_PAYLOAD_FIX_PLAN.md) — control flow bug diagnosis
- [v2.0.1 Plan](../v2.0.1/PLAN.md) — defers self-hosted parity to v2.1.0
- [SPEC.md](../../SPEC.md) — language specification (frozen at v1.0)
- [BOOTSTRAP.md](../../BOOTSTRAP.md) — self-hosted compiler architecture
