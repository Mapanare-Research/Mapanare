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
| 1 | Python text emitter opaque pointers | `Done` | Large | Eliminates ALL typed-pointer type mismatches |
| 2 | Fix stage2 errors | `In progress` | Medium | 7/8 fixed, 1 remaining (list element type) |
| 3 | Build mnc-stage2 binary | `Not started` | Small | First native-compiled native compiler |
| 4 | Fixed-point verification | `Not started` | Medium | stage2 == stage3 → Python independence |
| 5 | Fix Python lowerer control flow bugs | `Not started` | Medium | Enables clean .mn code without workarounds |
| 6 | Native test migration | `Not started` | X-Large | 10-50x test speed |

---

## Phase 1 — Python Text Emitter Opaque Pointers
**Status:** `Done`
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
| 1 | Change `PTR = "ptr"`, `STR = "{ptr, i64}"`, `LIST = "{ptr, i64, i64, i64}"` | `[x]` | Single-point constants |
| 2 | Add `_is_ptr(ty)` predicate, replace `endswith("*")` | `[x]` | 13 locations |
| 3 | Replace `f"{TYPE}*"` with `"ptr"` in store/load/GEP | `[x]` | 83 locations |
| 4 | Remove pointer-to-pointer bitcasts | `[x]` | ~50 bitcasts eliminated |
| 5 | Update byref/sret to use `ptr` | `[x]` | |
| 6 | Run full test suite | `[x]` | 4248+ passing |
| 7 | Rebuild mnc-stage1 with opaque-pointer main.ll | `[x]` | 111K lines IR, 1.8MB binary |
| 8 | Verify 15/15 golden | `[x]` | |

**Done when:** `main.ll` uses zero typed pointers. All tests pass.

---

## Phase 2 — Fix Stage2 Errors
**Status:** `In progress`
**Effort:** Medium
**Depends on:** Phase 1

### Fixed errors
1. **Nested if-Phi type mismatch** in `check_pipe_stages` — refactored to helper fns
2. **Option<String/List> type inconsistency** — universal Option type erasure ({i1, ptr})
3. **struct/enum name mismatch** — emit_enum_tag/emit_enum_payload now use resolve_type
4. **Nested match in lower_if** — extracted else_clause handling to helper fns
5. **lower_pipe nested match** — extracted to lower_pipe_call/lower_pipe_with_call

### Remaining (1 error)
`MatchBuildResult` 5-field struct init: the self-hosted emitter drops fields 3-4
when generating insertvalue chains for large struct literals. Root cause is in the
self-hosted emitter's struct init handling, not the .mn source.

### Tasks

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Run `ir_doctor stage2` after Phase 1 | `[x]` | TypeInfo phi mismatch |
| 2 | Fix nested if-phi in check_pipe_stages | `[x]` | Refactored to helpers |
| 3 | Fix Option type erasure inconsistency | `[x]` | Universal {i1, ptr} |
| 4 | Fix struct/enum name mismatch | `[x]` | resolve_type in tag/payload |
| 5 | Fix nested match in lower_if | `[x]` | Extracted else helpers |
| 6 | Fix MatchBuildResult struct init | `[x]` | Root cause: parse_struct_fields_to_list hardcoded to 3 fields. Fixed with loop. |
| 7 | Fix multi-field enum destructuring | `[x]` | AgentSend(a,ch,v) workaround: simplified format_instruction to avoid >1 binding |
| 8 | Fix List<TypeExpr> element type | `[ ]` | IndexGet on List<enum> defaults to i64 — need emitter type resolution fix |
| 9 | Verify `llvm-as` accepts all stage2 IR | `[ ]` | 1 error remaining (TypeExpr list element type) |

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

---

## Groundwork for Phase 3: Industrialization

> Mapanare is being built to compete with Go, Rust, and Python as a
> production-grade language. Once the bootstrapping phase (v2.2.0) is
> complete, the next architectural goals shift from "can the compiler
> compile itself" to "can the language ship real software safely."

### 1. Formalize the Memory & Concurrency Model

The current COW list system and opaque pointer representation must be
proven safe for concurrent use by the native Agent/Signal runtime:

- **COW + Agents**: When `__mn_agent_spawn` copies state into a new
  agent, the COW refcount must be atomically incremented. The current
  `mn_list_detach` uses non-atomic operations — safe for single-threaded
  lowering/emission, but a data race under the agent scheduler's
  cooperative thread pool.

- **Signal reactivity**: `__mn_signal_set` triggers subscriber callbacks
  that may read shared lists. The COW magic header check
  (`mn_list_has_magic`) is a read on shared memory — needs acquire
  semantics under concurrency.

- **Opaque pointer + arena lifetime**: With type-erased `ptr` payloads
  in Options and enum variants, the arena allocator must guarantee that
  pointed-to memory outlives all references. The current arena is
  function-scoped (freed at return) — needs extension to compilation-unit
  scope for the self-hosted compiler's state threading.

**Deliverable**: A formal memory model document (`docs/MEMORY_MODEL.md`
update) that specifies ownership, borrowing, and lifetime rules for COW
lists, opaque pointers, and agent-spawned state. This document becomes
the reference for all future runtime and codegen work.

### 2. Consolidate the Toolchain

The current developer workflow depends on Python scripts (`ir_doctor.py`,
`build_stage1.py`, `concat_self.py`, `rebuild.sh`, `test_native.py`,
`mir_trace.py`). Once the self-hosted compiler reaches fixed-point, these
should be rewritten in Mapanare to create a unified, self-hosted CLI —
analogous to `cargo` (Rust), `go` (Go), or `dotnet` (C#).

**Target CLI**:
```
mapanare build              # compile .mn → native binary
mapanare test               # run test suite
mapanare golden             # golden test validation (replaces ir_doctor golden)
mapanare stage2             # stage2 self-compilation check
mapanare audit file.ll      # IR pathology detection
mapanare doctor file.mn     # valgrind + structmap crash analysis
mapanare fmt                # auto-format .mn files
mapanare lint               # lint .mn files
mapanare bench              # run benchmarks
mapanare init               # scaffold new project
mapanare doc                # generate documentation
```

**Migration path**:
1. Phase 4 (fixed-point) proves `mapanare` can compile arbitrary `.mn` files
2. Port `concat_self.py` → `mapanare concat` (simplest, validates I/O)
3. Port `ir_doctor.py golden` → `mapanare golden` (validates subprocess + IR parsing)
4. Port `build_stage1.py` → `mapanare bootstrap` (validates end-to-end pipeline)
5. Eventually: `mapanare` compiles itself without any Python in the loop

### 3. Performance & Safety Standards

All code written during v2.2.0 must meet these standards, even for
"temporary" workarounds:

- **No O(n²) patterns** — every list operation must be O(1) amortized
  or O(n) total. The 57GB OOM from string concat must never recur.

- **Valgrind-clean on all golden tests** — zero uninitialised reads,
  zero invalid accesses. Use `/valgrind-map` to verify.

- **No silent type coercion in the emitter** — if a type mismatch
  exists, the emitter must either fix it explicitly (bitcast, alloca
  reinterpret) or reject it with a diagnostic. No implicit `i64`
  fallbacks.

- **Deterministic output** — same input must produce byte-identical IR.
  Counter resets, label numbering, and string interning must be
  deterministic. This is a prerequisite for fixed-point verification.
