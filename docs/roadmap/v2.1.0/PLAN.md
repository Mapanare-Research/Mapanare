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

## Current State (2026-03-29, updated)

### What works

- **15/15 golden tests pass** — `mnc-stage1` compiles all golden test programs to valid LLVM IR.
- **Self-compilation succeeds** — `mnc-stage1` compiles `mnc_all.mn` (10,120 lines, 460 functions) in **~0.8s** using **~200 MB**. Produces 53,260 lines of stage2 IR.
- **Stage2 IR: 1 error** — nested if-expression Phi type mismatch (`i64` vs `%struct.TypeInfo`). See [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md) for full analysis.
- **Opaque pointer migration (partial)** — self-hosted emitter uses `ptr` throughout. Python text emitter still uses typed pointers (Phase 2).
- **Byref optimization** — structs >64 bytes pass by pointer with pre-zeroed sret buffers. Eliminated 57GB OOM → 200MB.
- **Selective COW cloning** — clone list fields on struct copy EXCEPT append-only lists (`lines`, `str_globals`). Maintains correctness without OOM.
- **Type erasure for Options** — `Option<Struct/Enum>` = `{i1, ptr}` with alloca boxing in WrapSome, ptr dereference in EnumPayload.
- **State-aware type resolution** — `resolve_type(st, ty)` corrects struct→enum misclassification at emit time.
- **Cross-module function resolution** — per-module cumulative fn_maps. Prevents `fresh_tmp`, `is_comparison_op` collisions.
- **Closure support** — parser extracts lambda params, lowerer lifts captured vars, emitter handles function pointer constants.
- **Builtin return types** — `print`, `println`, `int`, `float`, `str`, `len` produce correctly typed MIR values.
- **Debugging tools** — `ir_doctor stage2` (automated stage2 validation), `ir_doctor valgrind-map` (crash analysis with struct field mapping).
- **1,775 tests pass** — full pytest suite, 0 failures.

### What's still broken

1. **Stage2 IR: 1 error** — nested if-expression Phi produces `i64` but downstream match-Phi expects `%struct.TypeInfo`. Requires multi-pass type inference or Phase 2 opaque pointer migration. See [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md).
2. **Individual module compilation** — 9/10 modules produce invalid stage2 IR due to cross-module `%struct.X` types not being defined. Only matters for module-by-module workflow, not for Phase 4.

### Key metrics

| Metric | Value |
|--------|-------|
| Golden tests | 15/15 |
| Self-compilation | 0.19s, 86 MB, 51,807 lines IR |
| LowerState size | 240 bytes (11 fields) |
| Byref threshold | 64 bytes |
| Total pytest | 1,775 passed |

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
| 1 | Retest Self-Compilation | `Done` | Small | Confirmed 15/15 golden, identified OOM |
| 2 | Control flow + type recovery fixes | `Done` | Medium-Large | 15/15 golden, self-compilation works |
| 3 | Byref optimization + OOM fix | `Done` | Medium | Architectural fix — structs by pointer, O(n) join |
| 4 | Fixed-Point Verification | `In Progress` | Medium | 1 stage2 type error remaining |
| 5 | Native Test Migration | `Not started` | X-Large | 10-50x test speed |
| 6 | Go Test Harness (optional) | `Not started` | Large | Only if measurements justify |

---

## Phase 0 — Quick Fixes
**Status:** `Done`

All tasks completed: pytest-xdist, dev.ps1 validate, mn_checked_mul visibility.

---

## Phase 1 — Retest Self-Compilation
**Status:** `Done`

**Findings:** 15/15 golden pass. Self-compilation identified two blockers: function resolution collision (`fresh_tmp`) and O(n²) string concat in emitter.

---

## Phase 2 — Control Flow & Type Recovery
**Status:** `Done`
**Summary:** 15/15 golden, opaque pointer migration (partial), type erasure for Options, 20+ emitter fixes

### Fixes applied (cumulative from v1.0.x through v2.0.x sessions)

**Lowerer (`lower.mn`):**
1. `lower_match` Phi collection — skip terminated arms
2. `lower_if` Phi collection — track then/else terminated
3. Enum namespace resolution — verify variant belongs to correct enum
4. String method return types
5. Function return type registry
6. Signal vs field `.value` dispatch
7. Struct field type tracking
8. Two-pass declaration registration
9. State-aware type resolver
10. Full generic type resolution
11. Lambda param parsing (`parser.mn`) — extract from left expression
12. Closure by parameter lifting — captured vars as extra function params
13. Lambda registration — `lower_let` updates `lambda_vars` entry

**Emitter (`emit_llvm.mn`):**
14. `resolve_variant_index` — was stub returning 0
15. Enum zero-init — `store zeroinitializer`
16. `emit_builtin_len` / `emit_index_get` — alloca+store before pointer-expecting calls
17. `emit_const` for function type — `bitcast void ()* @name to i8*`
18. `emit_mir_return` — use `current_ret_type` instead of value's MIR type
19. `emit_mir_module` — O(n) `join("\n", st.lines)` replaces O(n²) string concat

**Infrastructure (`emit_llvm_text.py` + `multi_module.py`):**
20. Byref optimization (`_BYREF_BYTES = 64`) — structs >64B by pointer, pre-zeroed sret
21. Per-module function resolution — fixes `fresh_tmp` collision
22. Removed `_clone_list_fields` from `_do_copy` — COW handles aliasing, clone was causing 57GB OOM
23. `ir_doctor.py` — `RET_TYPE_MISMATCH` fix for struct return types, `stage2` command

---

## Phase 3 — Byref Optimization
**Status:** `Done`
**Summary:** Byref optimization (_BYREF_BYTES=64), selective COW cloning, O(n) join. 57GB->200MB.

### Problem
LowerState (240B), LowerResult (248B), EmitState (240B) passed by value through 632 call sites. Every copy triggered `_clone_list_fields` (list cloning). With growing lists, caused O(n²) memory → 57GB OOM on self-compilation.

### Solution (architectural — replaces all previous clone/restructure approaches)

**Byref pass-by-reference** (`emit_llvm_text.py`):
- `_BYREF_BYTES = 64` threshold
- Function params >64B: `{T}* %name.byref` pointer; callee loads into pre-zeroed local alloca
- Function returns >64B: sret — caller allocates zeroed buffer, passes `{T}* sret({T})`
- Call sites: args stored to allocas, sret buffers zeroed before call

**COW replaces clone** (`_do_copy`):
- Removed `_clone_list_fields` — the C runtime's `__mn_list_push`/`__mn_list_set` call `mn_list_detach()` (COW) before mutation
- Explicit cloning was redundant and caused 57GB allocations

**O(n) string join** (`emit_llvm.mn`):
- `join("\n", st.lines)` replaces `result = result + line + "\n"` loop
- Self-compilation: 57GB/killed → 86MB/0.19s

---

## Phase 4 — Fixed-Point Verification
**Status:** `In Progress`
**Effort:** Medium
**Depends on:** Phase 2/3 (done)
**Summary:** Self-compilation works (0.8s, 200MB, 53K lines). 1 stage2 error remaining (nested if-Phi type). Blocked on Phase 2 Python emitter opaque pointer migration.

### Current state

Self-compilation produces 53,260 lines of stage2 IR with **1 error** — a nested if-expression Phi type mismatch (`i64` vs `%struct.TypeInfo`). The lowerer emits `i64` for one branch of a nested if-expression, but downstream pattern matching expects the full struct type.

This is blocked on completing the opaque pointer migration in the Python text emitter (Phase 2 leftover). The typed-pointer vs opaque-pointer mismatch causes the lowerer to misresolve variable types in certain nested control flow paths.

### Remaining work

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Fix extractvalue on non-aggregate (field access type tracking) | `[ ]` | Same fix pattern as ret type — use declared type |
| 2 | `mnc-stage1` compiles `mnc_all.mn` → valid stage2 IR | `[~]` | 1 error remaining |
| 3 | Compile stage2 IR to binary: `clang -O2 stage2.ll -o mnc-stage2` | `[ ]` | |
| 4 | `mnc-stage2` compiles `mnc_all.mn` → stage3 IR | `[ ]` | |
| 5 | Diff: `diff stage2.ll stage3.ll` | `[ ]` | Must be identical |
| 6 | If not identical: analyze diff, fix determinism issues | `[ ]` | |
| 7 | Update `scripts/verify_fixed_point.sh` | `[ ]` | |
| 8 | CI: gate on fixed-point verification | `[ ]` | |

**Done when:** `verify_fixed_point.sh` passes. CI gates on it.

---

## Phase 5 — Native Test Migration
**Status:** `Not started`
**Depends on:** Phase 4

Migrate tests from Python compiler to native `mnc` binary. 10-50x speedup expected.

---

## Phase 6 — Go Test Harness (Optional)
**Status:** `Not started`
**Decision gate:** Measure after Phase 5.

---

## Debugging Tools

```bash
# Stage 1: golden test validation (15/15)
python scripts/ir_doctor.py golden

# Stage 2: self-hosted module compilation + validation
python scripts/ir_doctor.py stage2

# Stage 2 with longer timeout
python scripts/ir_doctor.py stage2 --timeout 60

# Audit specific IR file
python scripts/ir_doctor.py audit /tmp/stage2_full.ll

# Compare bootstrap vs stage1 output
python scripts/ir_doctor.py diff tests/golden/07_enum_match.mn

# Per-function metrics
python scripts/ir_doctor.py table mapanare/self/main.ll

# Struct layout inspector
python scripts/ir_doctor.py structmap LowerState

# Valgrind crash analysis with struct field mapping
python scripts/ir_doctor.py valgrind-map mapanare/self/main.ll
```

---

## Bootstrap Path

```
mnc_all.mn ──[Python text emitter]──> main.ll ──[clang -O2]──> mnc-stage1
                                                                    │
mnc_all.mn ──────────────[mnc-stage1]──────────> stage2.ll ──[clang]──> mnc-stage2
                                                                    │
mnc_all.mn ──────────────[mnc-stage2]──────────> stage3.ll    (== stage2.ll? → fixed point)
```

No llvmlite in any step. After fixed-point, Python is only needed for disaster recovery.

---

## References

- `scripts/ir_doctor.py` — IR diagnostics, golden tests, stage2 validation
- `scripts/build_stage1.py` — bootstrap build (text emitter + clang)
- `scripts/verify_fixed_point.sh` — three-stage verification
- `scripts/test_native.py` — golden test harness
