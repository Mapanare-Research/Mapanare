# Mapanare v2.2.0 — "Fixed Point"

> v2.1.0 achieved self-compilation: the self-hosted compiler compiles its own
> 10,120-line source in 0.8s / 200MB, producing 53K lines of stage2 IR with
> 1 error remaining. 15/15 golden tests pass. 1,775 pytest tests pass.
>
> v2.2.0 closes the loop. The Python text emitter migrates to opaque pointers,
> the last stage2 error is eliminated, and fixed-point verification proves
> the compiler compiles itself identically across generations.
>
> Core theme: **stage2 == stage3. The compiler is self-sustaining.**

---

## Inherited from v2.1.0

### What works
- 15/15 golden tests
- Self-compilation: 0.8s, 200MB, 53K lines stage2 IR
- Byref optimization (_BYREF_BYTES=64), selective COW cloning
- Opaque pointers in self-hosted emitter (emit_llvm_ir.mn, emit_llvm.mn)
- Type erasure for Option<Struct/Enum> = {i1, ptr}
- Per-module function resolution, closure support, builtin return types
- ir_doctor: golden, stage2, valgrind-map, audit, diff-all

### What's broken (1 stage2 error)
Nested if-expression Phi: inner `%if_result` produces `i64` (both arms unknown),
outer match-Phi expects `%struct.TypeInfo`. Root cause: MIR loses type info for
function calls, and the single-pass emitter can't backward-propagate types from
consumers to producers. See `docs/ARCHITECTURE_DECISIONS.md`.

### Known Python lowerer bugs (workarounds documented)
- `return` inside `if` drops subsequent code
- `break` inside `if` inside `for` is swallowed
- `<=` operator silently dropped
- `&&` may not compile correctly in all contexts

---

## Scope Rules

1. **No new language features** — syntax frozen at v1.0
2. **Fixed-point is the gate** — stage2.ll == stage3.ll before anything else
3. **Every phase must leave 15/15 golden and 1,775+ tests green**
4. **Python bootstrap stays for reference** — oracle, not product

---

## Phase Overview

| Phase | Name | Status | Effort | Impact |
|-------|------|--------|--------|--------|
| 1 | Python text emitter opaque pointers | `Not started` | Large | Eliminates ALL typed-pointer type mismatches |
| 2 | Fix last stage2 error | `Not started` | Small | 0 stage2 errors → can build mnc-stage2 |
| 3 | Build mnc-stage2 binary | `Not started` | Small | First native-compiled native compiler |
| 4 | Fixed-point verification | `Not started` | Medium | stage2 == stage3 → Python independence |
| 5 | Fix Python lowerer control flow bugs | `Not started` | Medium | Enables clean .mn code without workarounds |
| 6 | Native test migration | `Not started` | X-Large | 10-50x test speed |

---

## Phase 1 — Python Text Emitter Opaque Pointers
**Status:** `Not started`
**Effort:** Large
**Files:** `mapanare/emit_llvm_text.py`

Migrate the Python text emitter from typed pointers (`i8*`, `TYPE*`) to LLVM 18
opaque pointers (`ptr`). This eliminates the entire class of bitcast/type-mismatch
errors that blocked stage2 validation.

### Changes needed (from the v2.1.0 audit)

| Category | Count | Action |
|----------|-------|--------|
| `PTR = "i8*"` constant | 1 | Change to `PTR = "ptr"` |
| `STR`, `LIST`, `CLOS` constants | 3 | Replace `i8*` with `ptr` |
| `endswith("*")` pointer checks | 13 | Replace with `_is_ptr(ty)` predicate |
| `f"{TYPE}*"` concatenations | 83 | Replace with `"ptr"` |
| `bitcast TYPE* to TYPE*` | 50 | Remove (ptr-to-ptr is identity) |
| `getelementptr TYPE, TYPE*` | 13 | Change base to `ptr` |
| `store TYPE, TYPE*` / `load TYPE, TYPE*` | 20+ | Change pointer operand to `ptr` |
| byref/sret parameter handling | Lines 518-781 | Pointer types become `ptr` |

### Tasks

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Change `PTR = "ptr"`, `STR = "{ptr, i64}"`, `LIST = "{ptr, i64, i64, i64}"` | `[ ]` | Single-point constants |
| 2 | Add `_is_ptr(ty)` predicate, replace `endswith("*")` | `[ ]` | 13 locations |
| 3 | Replace `f"{TYPE}*"` with `"ptr"` in store/load/GEP | `[ ]` | 83 locations |
| 4 | Remove pointer-to-pointer bitcasts | `[ ]` | 50 locations |
| 5 | Update byref/sret to use `ptr` | `[ ]` | |
| 6 | Run full test suite | `[ ]` | Must stay 1,775+ passing |
| 7 | Rebuild mnc-stage1 with opaque-pointer main.ll | `[ ]` | |
| 8 | Verify 15/15 golden | `[ ]` | |

**Done when:** `main.ll` uses zero typed pointers. All tests pass.

---

## Phase 2 — Fix Last Stage2 Error
**Status:** `Not started`
**Effort:** Small (should resolve automatically from Phase 1)
**Depends on:** Phase 1

With opaque pointers in the Python text emitter, the nested if-Phi type mismatch
should disappear because `Option<TypeInfo>` becomes `{i1, ptr}` everywhere —
no `{i1, %struct.TypeInfo}` vs `{i1, i8*}` conflicts.

### Tasks

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Run `ir_doctor stage2` after Phase 1 | `[ ]` | |
| 2 | If errors remain, diagnose with `ir_doctor audit` | `[ ]` | |
| 3 | Verify `llvm-as` accepts all stage2 IR | `[ ]` | 0 errors |

**Done when:** `llvm-as /tmp/stage2.ll` exits 0.

---

## Phase 3 — Build mnc-stage2 Binary
**Status:** `Not started`
**Effort:** Small
**Depends on:** Phase 2

Compile the valid stage2 IR to a native binary using clang.

### Tasks

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | `clang -O2 /tmp/stage2.ll runtime/native/mapanare_core.c -o mnc-stage2` | `[ ]` | Link with C runtime |
| 2 | Test: `./mnc-stage2 tests/golden/01_hello.mn` | `[ ]` | Basic smoke test |
| 3 | Run golden suite through mnc-stage2 | `[ ]` | |
| 4 | Run `ir_doctor golden --stage1 ./mnc-stage2` | `[ ]` | |

**Done when:** mnc-stage2 passes golden tests.

---

## Phase 4 — Fixed-Point Verification
**Status:** `Not started`
**Effort:** Medium
**Depends on:** Phase 3

Three-stage bootstrap:
1. Python compiles mnc_all.mn → mnc-stage1 (already done)
2. mnc-stage1 compiles mnc_all.mn → stage2.ll → mnc-stage2
3. mnc-stage2 compiles mnc_all.mn → stage3.ll
4. **If stage2.ll == stage3.ll → fixed point. Python is no longer needed.**

### Tasks

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | mnc-stage2 compiles mnc_all.mn → stage3.ll | `[ ]` | |
| 2 | `diff stage2.ll stage3.ll` | `[ ]` | Must be identical |
| 3 | If not identical: normalize counters/labels and re-diff | `[ ]` | |
| 4 | Update `scripts/verify_fixed_point.sh` | `[ ]` | |
| 5 | Add fixed-point check to CI | `[ ]` | Hard gate, not continue-on-error |
| 6 | Document in ROADMAP.md | `[ ]` | **Milestone: Python bootstrap optional** |

**Done when:** `verify_fixed_point.sh` passes. CI gates on it.

---

## Phase 5 — Fix Python Lowerer Control Flow Bugs
**Status:** `Not started`
**Effort:** Medium
**Depends on:** Phase 4 (optional — can be done anytime)

The Python lowerer (`mapanare/lower.py`) has known bugs that force workarounds
in the self-hosted .mn code. Once fixed-point is achieved, these can be fixed
without risk (the self-hosted compiler is the authority).

### Known bugs
1. `return` inside `if` blocks drops subsequent code
2. `break` inside `if` inside `for` loops is swallowed
3. `<=` operator silently dropped (workaround: `< N+1`)
4. `&&` operator may not compile in all contexts (workaround: nested `if`)

### Tasks

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Add regression tests for each bug | `[ ]` | |
| 2 | Fix return-inside-if in Python lowerer | `[ ]` | |
| 3 | Fix break-inside-if-inside-for | `[ ]` | |
| 4 | Fix <= operator compilation | `[ ]` | |
| 5 | Remove workarounds from .mn files | `[ ]` | |

---

## Phase 6 — Native Test Migration
**Status:** `Not started`
**Effort:** X-Large
**Depends on:** Phase 4

Migrate tests from Python compiler to native `mnc` binary. 10-50x speedup expected.
Same plan as v2.1.0 Phase 5 — deferred because fixed-point must come first.

---

## Debugging Tools (inherited from v2.1.0)

```bash
# Stage 1: golden test validation
python scripts/ir_doctor.py golden

# Stage 2: self-hosted module compilation + validation
python scripts/ir_doctor.py stage2
python scripts/ir_doctor.py stage2 --timeout 60

# Valgrind crash analysis with struct field mapping
python scripts/ir_doctor.py valgrind-map ./mapanare/self/mnc-stage1 file.mn
python scripts/ir_doctor.py valgrind-map --struct LowerState ./mnc file.mn

# IR audit, diff, structmap
python scripts/ir_doctor.py audit mapanare/self/main.ll
python scripts/ir_doctor.py diff tests/golden/07_enum_match.mn
python scripts/ir_doctor.py structmap LowerState
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

After fixed-point, Python is only needed for disaster recovery.
