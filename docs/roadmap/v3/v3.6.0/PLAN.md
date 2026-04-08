# Mapanare v3.6.0 — Type System + Native Programs

> Fix the type system. Compile the last stdlib module. Run real programs.
> The compiler must handle parameterized generics, nested match types,
> and produce runnable binaries — not just validated IR.

**Status:** COMPLETE
**Author:** Juan Denis
**Date:** April 2026
**Breaking:** No

---

## The Goal

v3.5.0 reached 34/35 stdlib modules (1,086 functions) by fixing PHI
ordering, list concat, Map return types, circular import dedup, and
Result parameterization. But the compiler still has type-tracking gaps
that block the last module and prevent real programs from running.

v3.6.0 fixes the type system root causes and makes Mapanare programs
actually run end-to-end — compile, link, execute, get output.

---

## Inherited State (from v3.5.0)

| Component | Status |
|-----------|--------|
| Self-hosted compiler | 25/25 golden (2 fail: closure, enum_methods) |
| Seed binary | v3.5.0 with all fixes |
| Bootstrap | `bash scripts/build_from_seed.sh --verify` (no Python) |
| Stdlib compiled | 34/35 modules, 1,086 functions |
| Stdlib failing | encoding/toml.mn (nested match loses Map type) |
| Native tests | math 12/12, json 6/6, fs 6/6 = 24/24 |
| CI | 1,455 pass, 0 fail, 2 skip, 1 xfail |
| C runtime | 52/52, includes FS functions (exists, remove, size, etc.) |
| WASM | if/else + recursion work, for-loops need __mn_range builtins |

---

## Phase 1: Fix Type System Root Causes

### 1.1 Enum payload type tracking through nested match

**Problem:** When `match val { TTable(sub) => ... }` extracts a
`Map<String, TomlValue>` payload inside a nested context (match-inside-
for-inside-match), the lowerer loses the Map type and defaults to i64.

**Root cause:** `infer_variant_payload_type` returns the correct type,
but the subject value's `.ty` field is `i64` (unknown) instead of
`enum:TomlValue` by the time it reaches the inner match. Type info is
lost when values pass through for-loop PHI nodes.

**Fix:** In the lowerer's for-loop codegen, propagate the iteration
variable's type through the PHI node. In `lower_for`, the loop variable
should carry the collection element type, not default to i64.

**Files:** `mapanare/self/lower.mn` (lower_for, bind_arm_pattern)

**Test:** `encoding/toml.mn` compiles → 35/35 stdlib.

**Verification:** `culebra scan` + `culebra baseline diff` after fix.

### 1.2 MIR type parameterization in lambda_vars

**Problem:** Function return types are encoded as `"result:Result"` in
lambda_vars, losing generic parameters. The decoder reconstructs
`mir_result()` without args → wrong LLVM type.

**Current workaround:** v3.5.0 looks up the full MIRType from
`module.functions` for result-returning calls. This works but adds O(n)
lookup per call.

**Fix:** Encode full type info: `"result:Result:ok_kind:ok_name:err_kind:err_name"`.
Decode back with args. Remove the module.functions fallback.

**Files:** `mapanare/self/lower.mn` (register_definition, lower_call_by_name)

### 1.3 Struct constructor field ordering

**Problem:** When complex expressions (enum variant constructors, sret
function calls) are used inline in struct constructors, the lowerer
generates ghost intermediate values that shift field indices.

**Current workaround:** v3.5.0 extracts expressions into local variables.

**Fix:** In the emitter's `__new_*` handler, match constructor args to
fields by NAME (from FieldInit), not by position. Requires the parser
to generate Construct AST nodes instead of Call.

**Files:** `mapanare/self/parser.mn`, `mapanare/self/lower.mn`,
`mapanare/self/emit_llvm.mn`

**Note:** Attempted in v3.5.0 but Construct AST node caused crashes in
large modules. Investigate why and fix properly.

---

## Phase 2: Golden Test Completeness

### 2.1 Fix 11_closure (closure capture)

**Problem:** `lambda1` function is missing from stage1 output. The
self-hosted compiler doesn't emit closure/lambda capture support.

**Files:** `mapanare/self/emit_llvm.mn` (closure emission),
`mapanare/self/lower.mn` (closure lowering)

### 2.2 Fix 24_enum_methods (impl methods on enums)

**Problem:** Stage1 produces 0 lines for enum method programs. The
lowerer doesn't handle `impl` methods on enum types.

**Files:** `mapanare/self/lower.mn` (register_impl, method dispatch)

**Goal:** 25/25 golden tests pass through both bootstrap and stage1.

---

## Phase 3: `./mnc test` CLI

### 3.1 Test command in compiler driver

Add `test` subcommand to the self-hosted compiler:
```bash
./mnc test tests/native/test_math.mn     # compile + link + run
./mnc test tests/native/                 # run all .mn test files
```

**Implementation:** In `main.mn`, detect `test` as argv[1]. Compile
the source, write to /tmp, invoke clang + gcc, run the binary, report
pass/fail from the exit code.

**Files:** `mapanare/self/main.mn`

### 3.2 Port more tests to native

Write native .mn tests for:
- `stdlib/encoding/csv.mn`
- `stdlib/crypto.mn` (base64 encode/decode)
- `stdlib/text/string_utils.mn`
- `stdlib/db/kv.mn` (embedded store CRUD)

---

## Phase 4: Run Real Programs

### 4.1 End-to-end binary compilation

```bash
./mnc build program.mn -o program    # compile + link → executable
./program                            # run it
```

Currently the compiler only outputs IR. Add the compile+link step.

### 4.2 WASM for-loop runtime

Implement `__mn_range`, `__iter_has_next`, `__iter_next` as WASM
built-in functions so for-loops work in WebAssembly.

**Files:** `mapanare/emit_wasm.py` (built-in function emission)

### 4.3 Demo programs

Write 3 real-world programs that compile and run natively:
1. JSON config reader — read config.json, extract fields, print
2. HTTP health checker — GET a URL, check status code
3. File word counter — read file, split by spaces, count

---

## Success Criteria

- [x] 35/35 stdlib modules compile (toml fixed)
- [x] 25/25 golden tests pass through stage1 (closures + enum methods)
- [x] `./mnc test` CLI command works
- [x] `./mnc build` produces runnable binaries
- [ ] WASM for-loops work (with range iterator builtins) — deferred to v3.7.0
- [x] 3 demo programs compile + link + run natively
- [ ] Native test suite: 30+ assertions across 6+ modules — deferred to v3.7.0

---

## Non-Goals

- Package registry / dependency manager
- IDE integration / LSP
- Debugger support
- New language features beyond what stdlib needs
