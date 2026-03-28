# Mapanare v2.0.1 — "Trust Restoration"

> A [7-reviewer code review](../../../.reviews/v2.0.0/README.md) scored v2.0.0 at
> **7.86/10 median** and identified 40 issues across correctness, security, memory
> safety, toolchain hygiene, and spec compliance. Two additional meta-reviews
> ([Codex](../../../.reviews/v2.0.0/08-codex.md), [Gemini](../../../.reviews/v2.0.0/09-gemini.md))
> converged on the same three trust-breaking items as the top priorities.
>
> v2.0.1 is a surgical patch release. No new features. Every item here protects
> correctness, security, or toolchain honesty. Deeper engineering debt (drop glue,
> monomorphization, self-hosted parity) is deferred to v2.1.0.
>
> Core theme: **Fix anything that makes the compiler lie to the user.**

---

## Scope Rules

1. **No new language features** — syntax and semantics are frozen at v1.0
2. **No new backends or targets** — WASM, GPU, and mobile ship as-is minus bugs
3. **Each patch is shippable independently** — no cross-patch dependencies
4. **Every patch must leave all tests green** — no regressions
5. **Review item numbers reference** the [v2.0.0 code review findings](../../../.reviews/v2.0.0/README.md)

---

## Status Tracking

| Icon | Meaning |
|------|---------|
| `[ ]` | Not started |
| `[~]` | In progress |
| `[x]` | Done |
| `[!]` | Skipped (reason noted) |

---

## Patch Overview

| Patch | Theme | Status | Effort | Review Items |
|-------|-------|--------|--------|--------------|
| P1 | WASM Correctness | `Not started` | Small | #10 |
| P2 | GPU Security | `Not started` | Medium | #4 |
| P3 | Toolchain Honesty | `Not started` | Small | #7, #16, #25 |
| P4 | Silent Failure Elimination | `Not started` | Small | #13, #14, #23, #24 |
| P5 | Runtime Safety Fixes | `Not started` | Small | #18, #20, #22 |
| P6 | Release Hygiene | `Not started` | Trivial | — |

---

## P1 — WASM Correctness

> The headline v2.0.0 feature produces wrong output. Every WASM program that
> converts an integer to a string gets reversed digits. This is the single
> highest-priority fix.

**Reported by:** Boa (H1), Cobra (H4), Rattler (H3)
**Effort:** Small

### Fix `str(int)` digit reversal

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Fix digit extraction loop to write digits in correct order | `[ ]` | `emit_wasm.py:738-790` | Reverse the buffer after extraction, or write from end of buffer backward |
| 2 | Add WASM-specific `str(int)` tests for edge cases | `[ ]` | `tests/wasm/` | `str(0)`, `str(-1)`, `str(123)`, `str(-2147483648)`, `str(9)` |
| 3 | Test `str(int)` inside `println` (end-to-end) | `[ ]` | `tests/wasm/` | This is the most common user path |

---

## P2 — GPU Security

> `system()` in the SPIR-V compilation path is a command injection vector.
> It also blocks mobile deployment where `system()` is unavailable or sandboxed.

**Reported by:** Mamba (C1)
**Effort:** Medium

### Remove `system()` from GLSL→SPIR-V compilation

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Replace `system(cmd)` calls with `subprocess.run()` or C `popen()` with proper argument escaping | `[ ]` | `runtime/native/mapanare_gpu.c:822,835` | Two call sites: `glslc` primary, `glslangValidator` fallback |
| 2 | Use `execvp`-style argument arrays instead of string interpolation | `[ ]` | `runtime/native/mapanare_gpu.c` | Eliminates shell metacharacter injection entirely |
| 3 | Add error handling for compiler-not-found (return error code, don't crash) | `[ ]` | `runtime/native/mapanare_gpu.c` | Currently undefined behavior if glslc missing |
| 4 | Test: verify GPU SPIR-V compilation rejects filenames with shell metacharacters | `[ ]` | `tests/native/` | Regression test for the injection vector |

---

## P3 — Toolchain Honesty

> A no-op stub in the verification pipeline, stale version strings, and missing
> gitignore entries create false confidence. Fix the lies.

**Reported by:** Anaconda (C-1, H-1, H-2), Coral
**Effort:** Small

### Remove or implement `fix_ssa.py`

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Remove `fix_ssa.py` from the verification pipeline | `[ ]` | `scripts/fix_ssa.py` | Currently a documented no-op ("passes IR through unchanged"). Remove from pipeline scripts that invoke it; keep the file with a clear `NOT_IMPLEMENTED` header if future work is planned, or delete entirely |
| 2 | Audit `scripts/verify_fixed_point.sh` and `scripts/build_stage1.py` for references | `[ ]` | `scripts/` | Ensure no pipeline step depends on the stub |

### Version string alignment

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 3 | Update DWARF producer string to `"mapanare 2.0.1"` | `[ ]` | `emit_llvm_mir.py:666` | Currently frozen at `"mapanare 1.0.0"` |
| 4 | Update self-hosted compiler version to `"mapanare 2.0.1"` | `[ ]` | `mapanare/self/main.mn:29` | Currently returns `"mapanare 1.0.0"` |
| 5 | Read version from `VERSION` file instead of hardcoding | `[ ]` | `emit_llvm_mir.py`, `mapanare/self/main.mn` | Single source of truth; at minimum sync the hardcoded strings |

### Gitignore hygiene

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 6 | Add `mnc-stage2*` and `mnc-stage3*` patterns to `.gitignore` | `[ ]` | `.gitignore` | Only `mnc-stage1*` is currently listed |

---

## P4 — Silent Failure Elimination

> Several code paths silently swallow exceptions or emit warnings where errors
> are required. Users get green builds for broken programs.

**Reported by:** Boa (H1, M3), Cobra, Rattler (H3), Coral (H1)
**Effort:** Small

### Promote match exhaustiveness to error

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Change `_warning()` → `_error()` for non-exhaustive match | `[ ]` | `semantic.py:847` | Spec requires exhaustive matching; current implementation only warns |
| 2 | Update tests that expect warning to expect error | `[ ]` | `tests/semantic/` | |

### Fix blanket exception swallowing in AST emitter

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 3 | Replace `except Exception: continue` with specific exception types | `[ ]` | `emit_llvm.py:2444-2447` | Cross-module field access fallback; catch only `LLVMException` or `IndexError` |

### Add logging to agent exception handler

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 4 | Log exception message + traceback before incrementing error counter | `[ ]` | `runtime/agent.py:291-292` | Currently swallows silently with only a metrics counter |

### Surface `mapanare check` warnings

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 5 | Ensure `mapanare check` prints all warnings to stderr | `[ ]` | `cli.py` | Currently some warnings are dropped |

### Add deprecation notice to `mapanare compile` CLI

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 6 | Print runtime deprecation warning when `compile` subcommand is invoked | `[ ]` | `cli.py` | Docstring says deprecated but user sees no notice |

---

## P5 — Runtime Safety Fixes

> Small but important correctness and safety issues in the C runtime.

**Reported by:** Viper (H5), Mamba (H1, H2, H3), Cobra (M5)
**Effort:** Small

### Thread-safe GPU context initialization

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Add `pthread_once` or atomic flag guard to `mapanare_gpu_init()` | `[ ]` | `runtime/native/mapanare_gpu.c` | Race condition when multiple threads call init simultaneously |

### Fix checked arithmetic negative overflow

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 2 | Handle negative operands in `mn_checked_mul` / `mn_checked_add` | `[ ]` | `runtime/native/mapanare_runtime.c` | Currently bypasses overflow check for negative values |

### Fix constant folding `x - x` type assumption

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 3 | Preserve operand type when folding `x - x = 0` | `[ ]` | `mapanare/optimizer.py` or `mapanare/mir_opt.py` | Currently assumes Int result; wrong for Float |

---

## P6 — Release Hygiene

> Bump the version and ensure all release metadata is consistent.

**Effort:** Trivial

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Bump `VERSION` to `2.0.1` | `[ ]` | `VERSION` | |
| 2 | Update `pyproject.toml` version if present | `[ ]` | `pyproject.toml` | |
| 3 | Tag release after all patches land | `[ ]` | — | `git tag v2.0.1` |

---

## Deferred to v2.1.0

These items are real and important but require focused engineering time beyond
a patch release. Documented here for traceability.

| # | Issue | Review Source | Why Deferred |
|---|-------|-------------- |--------------|
| 1 | Re-enable drop glue with proper alloca strategy | Viper C1, Rattler H1 | Medium effort, needs careful alloca lifetime analysis to avoid double-free |
| 2 | Free closure environments on scope exit | Viper C2 | Coupled with drop glue — fix together |
| 3 | Signal value destructor for heap contents | Viper C3 | Needs type-aware destructor dispatch, not just memcpy |
| 4 | Range iterator cleanup on break/return | Viper M3 | Requires destructor emission at early-exit points |
| 5 | Thread-safe string interning table | Viper H4, Mamba M2 | Needs reader-writer lock or concurrent hash map |
| 6 | Thread-safe signal batching | Viper M1 | Global mutable state needs redesign |
| 7 | Add `-Wall -Wextra -Werror` to C compilation | Anaconda H-2 | Will surface many warnings in existing code; needs cleanup pass |
| 8 | Stack-allocate map Robin Hood swap buffer | Viper H2, Mamba H2 | Performance, not correctness |
| 9 | Per-function arenas | Mamba M1 | Large refactor of allocation strategy |
| 10 | WASM bump allocator freeing strategy | Cobra M2, Rattler M2 | Needs GC or region-based approach |
| 11 | Tensor shape overflow check | Mamba H3 | Needs safe multiplication in `mapanare_tensor_alloc` |
| 12 | Vulkan compute queue family selection | Viper M3, Mamba M3 | Hardcoded to 0; needs proper queue family query |

## Deferred to v2.2.0+

| # | Issue | Review Source | Why Deferred |
|---|-------|--------------|--------------|
| 1 | Generic monomorphization | Cobra C1 | Architecture work — type-erased generics functional but slow |
| 2 | Narrow `_coerce_arg` escape hatch | Cobra C2 | 130 lines, 30 call sites — needs systematic type coercion redesign |
| 3 | Ownership / borrow checking | Viper H1 | Major language feature — needs RFC |
| 4 | Self-hosted compiler feature parity | Coral C1, C2 | Large bootstrapping effort (scope_define, missing AST nodes) |
| 5 | Trait dispatch beyond Eq/Ord | Cobra M1 | Needs operator overloading design |
| 6 | MIR optimizer cross-pass fixed-point | Cobra M4 | Optimization quality, not correctness |
| 7 | Semantic checker generic arity validation | Cobra M3 | Rare edge case in current usage |

---

*Derived from the v2.0.0 code review panel (7 reviewers), Codex meta-review, and
Gemini meta-review. 2026-03-28.*
