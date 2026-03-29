# Mapanare v2.1.0 — "Python Independence"

> The Python transpiler backends are deprecated since v2.0.0, but the Python
> *compiler* still runs every test. 4,400+ tests invoke the Python lexer, parser,
> semantic checker, MIR lowerer, and LLVM emitter. The test harness is just the
> thin wrapper — the bottleneck is the compiler code itself, not pytest.
>
> v2.1.0 closes that gap. The self-hosted compiler reaches fixed-point, tests
> migrate to call the native binary, and the test infrastructure scales to match.
>
> Core theme: **The compiler compiles itself. Tests call native code. Python is optional.**

---

## Current State (start of v2.1.0)

Before planning, here's what's actually true right now:

### Already solved (from v1.0.x / v2.0.x work)

- **llvmlite bypassed** — `build_stage1.py` defaults to the text emitter + clang -O2,
  not llvmlite. The text emitter generates alloca/load/store IR and relies on clang's
  mem2reg pass. No llvmlite truncation bugs in this path.
- **Enum boxing** — enums use `{i64, i8*}` (heap-allocated payload), not inline buffers.
  Eliminates the old 272-byte enum corruption.
- **Linkage fix** — `define internal` → `define` prevents LLVM -O1 from stripping
  functions with sret calling conventions.
- **`mnc-stage1` binary exists** — built and on disk at `mapanare/self/mnc-stage1`.
- **15/15 golden tests pass** — `mnc-stage1` compiles all golden test programs correctly.
- **Stage2 IR: 9/15 valid** — `mnc-stage1` generates valid LLVM IR for 9/15 golden tests.
  6 still fail (struct init, enum match, list types, string methods, result types, closures).
- **Large struct threshold: 1024 bytes** — raised from 56 to avoid most truncation edge cases.

### What's actually still broken

1. **`lower.mn` control flow bug** — `return` inside `if`/`match` blocks doesn't
   terminate the block. Control falls through to the merge block. This blocks 6/15
   stage2 tests. See [`ENUM_PAYLOAD_FIX_PLAN.md`](../ENUM_PAYLOAD_FIX_PLAN.md).

2. **MIR copy aliasing** — `let copy = list` creates a new alloca that doesn't
   track pushes to the original. Lists appear empty after copy+push sequences.

3. **Self-compilation untested** — `mnc-stage1` compiles golden tests (small programs)
   but has not been verified compiling its own 8,288-line source (`mnc_all.mn`).
   Previous attempts (03/20) crashed on `parser.mn`, `semantic.mn`, `lower.mn`,
   `emit_llvm.mn` due to LowerState (680 bytes). This may be resolved now that
   the text emitter + clang -O2 path is in place — needs retesting.

4. **`mn_checked_mul` visibility** — declared `static` in `mapanare_core.c` but
   called from `mapanare_runtime.c`. Causes gcc compilation failure on Windows.

### LowerState struct (the 680-byte problem)

```mapanare
struct LowerState {             // mapanare/self/lower.mn:399
    module: MIRModule,          // large — contains function list, type list, etc.
    current_fn: Option<MIRFunction>,
    current_block_idx: Int,
    tmp_counter: Int,
    block_counter: Int,
    vars: List<VarInfo>,
    scope_stack: List<List<VarInfo>>,
    impl_methods: List<ImplEntry>,
    struct_fields: List<StructFieldInfo>,
    enum_variants: List<EnumVariantNames>,
    lambda_vars: List<LambdaEntry>
}
```

Every `lower_*` function takes `LowerState` and returns `LowerResult { value, state }`.
This means 680 bytes copied on every call. With clang -O2 + mem2reg this may now
work (previous crashes were with llvmlite -O1 and clang -O0). **Must retest before
assuming restructuring is needed.**

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

| Phase | Name | Status | Effort | Impact |
|-------|------|--------|--------|--------|
| 0 | Quick Fixes (gcc, test parallelism) | `Done` | Small | Unblocks dev.ps1, 4-6x test speed |
| 1 | Retest Self-Compilation | `Done` | Small | 7/15 stage2, 4/7 modules, 3 crash on copy aliasing |
| 2 | Control Flow Fix (`lower.mn`) | `Not started` | Medium-Large | 7/15 stage2 → 15/15 |
| 3 | LowerState Restructure (CRITICAL) | `In Progress` | Medium | Copy aliasing crashes block self-compilation |
| 4 | Fixed-Point Verification | `Not started` | Medium | Python independence achieved |
| 5 | Native Test Migration | `Not started` | X-Large | 10-50x test speed |
| 6 | Go Test Harness (optional) | `Not started` | Large | Only if measurements justify |

---

## Phase 0 — Quick Fixes
**Status:** `In Progress`
**Effort:** Small

### Tasks

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Add `pytest-xdist` to dev dependencies | `[x]` | `pyproject.toml` | |
| 2 | Add `-n auto` to `dev.ps1` and CI (with graceful fallback) | `[x]` | `dev.ps1`, `.github/workflows/ci.yml`, `Makefile` | Auto-detects xdist |
| 3 | Make `dev.ps1 validate` run once and exit (not watch) | `[x]` | `dev.ps1` | `-Watch` flag for old behavior |
| 4 | Fix `mn_checked_mul` visibility: move from `static` to non-static, add declaration to header | `[x]` | `runtime/native/mapanare_core.c`, `mapanare_core.h` | Removed `static` from both `mn_checked_mul` and `mn_checked_add`, added declarations to header |
| 5 | Install `pytest-xdist` and verify parallel execution | `[x]` | — | Installed with mapanare dev deps |
| 6 | Measure baseline test time (sequential vs parallel) | `[~]` | — | Running... |

**Done when:** `dev.ps1 validate` runs green with parallel tests.

---

## Phase 1 — Retest Self-Compilation (WSL)
**Status:** `Not started`
**Effort:** Small (just running commands and observing)

Before writing any fix code, test what actually works NOW. The text emitter +
clang -O2 path may have fixed the old LowerState crashes that happened under
llvmlite -O1 and clang -O0. **Don't fix what isn't broken.**

### Tasks

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Rebuild `mnc-stage1`: `python scripts/build_stage1.py` | `[x]` | — | 82,010 lines IR, 918KB binary, clang -O2 |
| 2 | Run golden test harness | `[x]` | — | **15/15 pass** in 1.6s |
| 3 | Test stage2 IR validity | `[x]` | — | **7/15 VALID** (was 9/15). Invalid: for_loop, struct, enum_match, list, result, closure, nested_struct |
| 4 | Test self-compilation: `./mnc-stage1 mapanare/self/mnc_all.mn` | `[x]` | — | **SEGFAULT** in `lookup_var` → `__mn_str_eq` (corrupted string pointer) |
| 5 | Test individual modules | `[x]` | — | ast✓ lexer✓ semantic✓ main✓ / parser(double-free) lower(segfault) emit_llvm(segfault) |
| 6 | Document results and decide path | `[x]` | — | See findings below |

**Findings (2026-03-28):**

Stage2 IR errors fall into two categories:
1. **Control flow** (07_enum_match): unterminated block before merge label → Phase 2
2. **Type emission** (struct/list/result/closure/for_loop): wrong types in emitted IR → Phase 2

Self-compilation crashes (parser/lower/emit_llvm) are all **memory corruption**:
- `parser.mn`: double-free in `__mn_list_push` during `lower_let` — list data pointer aliased after copy
- `lower.mn`: SIGSEGV in `__mn_str_eq` during `lookup_var` — stale string pointer after list realloc
- `emit_llvm.mn`: same pattern

**Root cause:** LowerState (680 bytes) is passed by value. Its list fields (vars, scope_stack, etc.)
get shallow-copied. When the copy's list grows (realloc moves the data), the original's data pointer
becomes dangling. This is the classic copy-aliasing bug.

**Decision:** Phase 3 (LowerState restructure) is the critical path. Phase 2 (control flow) fixes
stage2 IR quality but doesn't unblock self-compilation. Execute Phase 3 first, then Phase 2.

---

## Phase 2 — Control Flow Fix (`lower.mn`)
**Status:** `Not started`
**Effort:** Medium-Large
**Depends on:** Phase 1 results (skip if stage2 already produces 15/15 valid IR)

The self-hosted `lower.mn` has a known bug: `return` inside `if`/`match` blocks
doesn't terminate the block — control falls through to the merge block. This was
identified in the 03/21 chat session and confirmed by the ENUM_PAYLOAD_FIX_PLAN.

### Root Cause

`lower_if` creates then/else/merge blocks. A `Return` in the then-block becomes
the block's last instruction, but the merge block is still emitted with a phi node
that references the then-block's "value" — even though the then-block already
returned and should never reach the merge.

### Fix Strategy

Fix in the self-hosted `lower.mn` source (not the Python `lower.py`):

1. After lowering the then-block body, check if the last instruction is `Return`
2. If so, don't emit a branch to the merge block from that arm
3. If BOTH arms return, don't emit the merge block at all
4. Same logic for `lower_match` arms

### Tasks

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Create minimal reproducer and trace the MIR blocks | `[ ]` | — | `fn f(x: Int) -> Int { if x > 0 { return 1 } return 0 }` |
| 2 | Fix `lower_if` in `lower.mn`: skip merge when arm returns | `[ ]` | `mapanare/self/lower.mn` | ~line 2126 |
| 3 | Fix `lower_match` in `lower.mn`: same pattern | `[ ]` | `mapanare/self/lower.mn` | ~line 2235 |
| 4 | Handle nested case: `if { if { return } }` | `[ ]` | `mapanare/self/lower.mn` | Must propagate through nesting |
| 5 | Rebuild mnc-stage1 and test 15/15 golden stage2 | `[ ]` | — | |
| 6 | Fix copy aliasing if it blocks remaining tests | `[ ]` | `mapanare/self/lower.mn` or `emit_llvm.mn` | List copy + push = stale alloca |

**Done when:** `mnc-stage1` produces valid LLVM IR for all 15 golden tests (stage2).

---

## Phase 3 — LowerState Restructure (if needed)
**Status:** `Not started`
**Effort:** Medium
**Depends on:** Phase 1 (only needed if self-compilation still crashes on large modules)

If `mnc-stage1` compiles golden tests but crashes on its own source due to
LowerState (680 bytes), restructure the struct to avoid large-value passing.

### Option A: Split LowerState (preferred)

Break LowerState into a small core + heap-allocated context:

```mapanare
struct LowerCtx {                    // heap-allocated, passed by pointer
    module: MIRModule,
    vars: List<VarInfo>,
    scope_stack: List<List<VarInfo>>,
    impl_methods: List<ImplEntry>,
    struct_fields: List<StructFieldInfo>,
    enum_variants: List<EnumVariantNames>,
    lambda_vars: List<LambdaEntry>
}

struct LowerState {                  // small, safe to pass by value
    ctx: LowerCtx,                   // single pointer
    current_fn: Option<MIRFunction>,
    current_block_idx: Int,
    tmp_counter: Int,
    block_counter: Int
}
```

This reduces LowerState to ~80 bytes (5 scalars + 1 pointer). All the heavy
collections live behind a single pointer.

### Option B: Thread state through mutable reference

Change `lower_*` functions to take `LowerState` by mutable reference instead of
by value + return. This eliminates all copies but requires changing every
function signature in `lower.mn` (2,629 lines, ~100+ functions).

### Tasks

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Confirm Phase 1 crash is LowerState-related (not control flow) | `[ ]` | — | Check crash location |
| 2 | Choose Option A or B based on change scope | `[ ]` | — | A is smaller change |
| 3 | Implement restructure in `lower.mn` | `[ ]` | `mapanare/self/lower.mn` | |
| 4 | Update all callers in `lower.mn` | `[ ]` | `mapanare/self/lower.mn` | |
| 5 | Rebuild and test self-compilation | `[ ]` | — | `mnc-stage1 mapanare/self/mnc_all.mn` |

**Done when:** `mnc-stage1` compiles `mnc_all.mn` without crashing.

---

## Phase 4 — Fixed-Point Verification
**Status:** `Not started`
**Effort:** Medium
**Depends on:** Phase 2/3 (mnc-stage1 must compile itself)

Three-stage bootstrap:
1. Python bootstrap compiles `mnc_all.mn` → `mnc-stage1` (already done)
2. `mnc-stage1` compiles `mnc_all.mn` → `mnc-stage2` IR
3. `mnc-stage2` compiles `mnc_all.mn` → `mnc-stage3` IR
4. If stage2 IR == stage3 IR → **fixed point. Python is no longer needed.**

### Tasks

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | `mnc-stage1` compiles `mnc_all.mn` → stage2 IR | `[ ]` | — | |
| 2 | Compile stage2 IR to binary: `clang -O2 stage2.ll -o mnc-stage2` | `[ ]` | — | |
| 3 | `mnc-stage2` compiles `mnc_all.mn` → stage3 IR | `[ ]` | — | |
| 4 | Diff: `diff stage2.ll stage3.ll` | `[ ]` | — | Must be identical |
| 5 | If not identical: analyze diff, fix determinism issues | `[ ]` | — | Counter resets, label numbering, etc. |
| 6 | Update `scripts/verify_fixed_point.sh` | `[ ]` | `scripts/verify_fixed_point.sh` | |
| 7 | CI: remove `continue-on-error: true` from fixed-point job | `[ ]` | `.github/workflows/ci.yml` | Make it a hard gate |
| 8 | Document in ROADMAP.md | `[ ]` | `docs/roadmap/ROADMAP.md` | **Milestone: Python bootstrap optional** |

**Done when:** `verify_fixed_point.sh` passes. CI gates on it.

---

## Phase 5 — Native Test Migration
**Status:** `Not started`
**Effort:** X-Large
**Depends on:** Phase 4
**Expected speedup:** 10-50x (native compilation in microseconds vs Python in milliseconds)

Migrate tests from `from mapanare.parser import ...` (Python compiler) to calling
the native `mnc` binary. Python bootstrap becomes the oracle for differential
testing, not the primary test target.

### Strategy

| Category | ~Count | Migration |
|----------|--------|-----------|
| Compilation tests (IR validation) | ~3,500 | `mnc source.mn`, check IR output |
| Runtime behavior (compile + execute) | ~500 | `mnc build` + execute binary |
| Python-only (bootstrap, FFI, Python emitter) | ~400 | Keep in pytest as-is |

### Tasks

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Add `mnc_binary` fixture to `tests/conftest.py` | `[ ]` | `tests/conftest.py` | Skip if binary not found |
| 2 | Create `tests/helpers/native.py` — thin subprocess wrapper | `[ ]` | `tests/helpers/native.py` | `compile_mn(source) -> ir`, `run_mn(source) -> stdout` |
| 3 | Migrate `tests/llvm/` (19 files, highest value) | `[ ]` | `tests/llvm/` | |
| 4 | Migrate `tests/semantic/` (3 files) | `[ ]` | `tests/semantic/` | |
| 5 | Migrate `tests/parser/` (2 files) | `[ ]` | `tests/parser/` | |
| 6 | Migrate `tests/e2e/` (7 files) | `[ ]` | `tests/e2e/` | |
| 7 | Migrate `tests/wasm/` (4 files) | `[ ]` | `tests/wasm/` | |
| 8 | Migrate `tests/stdlib/` (21 files) | `[ ]` | `tests/stdlib/` | |
| 9 | Tag remaining Python-only tests: `@pytest.mark.python_backend` | `[ ]` | `tests/` | |
| 10 | Measure wall-clock improvement | `[ ]` | — | Record here |

**Done when:** >80% of tests call native binary. Full suite faster than Phase 0 baseline.

---

## Phase 6 — Go Test Harness (Optional)
**Status:** `Not started`
**Effort:** Large
**Depends on:** Phase 5 measurements

Only justified if pytest subprocess overhead is >20% of wall-clock time after
Phase 5. Go's `testing` package has built-in parallelism and zero-overhead
subprocess management. Rust is also viable but Go's test ergonomics are better
for string-heavy IR validation.

**Decision gate:** Measure after Phase 5. If CI < 5 min with pytest, skip this.

---

## Execution Order

```
Phase 0 (quick fixes) ──── Immediate: gcc fix, parallel tests
     │
Phase 1 (retest) ───────── WSL: rebuild mnc-stage1, test self-compilation
     │
     ├── if self-compilation works → Phase 4
     │
     ├── if stage2 IR fails → Phase 2 (control flow fix)
     │
     └── if crash on large modules → Phase 3 (LowerState restructure)
                                          │
                                     Phase 4 (fixed-point) ── Python independence
                                          │
                                     Phase 5 (test migration) ── 10-50x speed
                                          │
                                     Phase 6 (Go harness) ── measure first
```

**Key insight:** Phase 1 (just running tests) tells us how much work remains.
Don't write fix code until we know what's actually broken with the current
text emitter + clang -O2 pipeline.

---

## Bootstrap Path (no llvmlite anywhere)

```
mnc_all.mn ──[Python text emitter]──> main.ll ──[clang -O2]──> mnc-stage1
                                                                    │
mnc_all.mn ──────────────[mnc-stage1]──────────> stage2.ll ──[clang]──> mnc-stage2
                                                                    │
mnc_all.mn ──────────────[mnc-stage2]──────────> stage3.ll    (== stage2.ll? → fixed point)
```

No llvmlite in any step. The Python text emitter generates alloca-based IR as
plain strings. clang handles optimization. After fixed-point, Python is only
needed if you want to rebuild from scratch (disaster recovery).

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Phase 1 reveals new crashes not seen before | Medium | Text emitter + clang -O2 is a different path — may have new bugs, but unlikely to have the old llvmlite bugs |
| Control flow fix breaks working stage2 tests | High | Run golden harness after every change |
| LowerState restructure touches 100+ functions | High | Option A (split struct) is smaller; Option B (mutable ref) is cleaner but larger |
| Fixed-point IR not byte-identical (non-determinism) | Medium | Diff-based debugging; counter/label normalization pass |
| Test migration reveals `mnc` bugs not in golden tests | Medium | Differential testing: run both Python and native, compare |

---

## References

- [v1.0.x Plan](../v1.0.x/PLAN.md) — self-hosted compiler progress through v1.0.11
- [Enum Payload Fix Plan](../ENUM_PAYLOAD_FIX_PLAN.md) — control flow bug diagnosis (03/21)
- [v2.0.1 Plan](../v2.0.1/PLAN.md) — defers self-hosted parity to v2.1.0
- [Chat logs](../../../.reviews/chats/) — 03/19-03/22 debugging sessions
- `scripts/build_stage1.py` — current bootstrap build (text emitter + clang)
- `scripts/verify_fixed_point.sh` — three-stage verification script
- `scripts/test_native.py` — golden test harness
