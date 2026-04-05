# Mapanare v3.5.0 — Real Programs

> Fix the compiler bugs, compile all stdlib, build a native test runner.
> No more workarounds.

**Status:** PLANNED
**Author:** Juan Denis
**Date:** April 2026
**Breaking:** No

---

## The Goal

v3.4.0 proved the self-hosted compiler can compile real stdlib modules
and run programs end-to-end. But it required 50+ workarounds (renamed
variables, stubbed functions, simplified WASM examples, xfailed tests).

v3.5.0 fixes the root causes and makes Mapanare self-sufficient: a
native test runner, all 37 stdlib modules compiling, and no Python in
the critical path.

---

## Phase 1: Fix Compiler Bugs (not workarounds)

### 1.1 Keyword-as-variable resolution
The lexer turns `input`, `agent`, `di`, `si` into keywords even when
used as variable names. Fix: the parser should allow keywords in
variable position (after `let`, as function params, in assignments).
This is how Rust/Go handle contextual keywords.

**Impact:** Unblocks all stdlib modules that use common names.

### 1.2 WASM structured control flow
The WASM emitter's block translation is broken — if/else and recursion
generate invalid WAT (block return type mismatches). Fix: implement
proper Relooper or Stackifier algorithm for MIR→WAT conversion.

**Impact:** WASM examples can use real programs (not gutted demos).

### 1.3 Cross-module return type resolution
When module A calls a function from module B, the return type is
sometimes `unknown` because the lowerer doesn't propagate types across
module boundaries. Fix: during import resolution, register all
imported function signatures in the lowerer's type registry.

**Impact:** kv.mn, sqlite.mn, pool.mn compile without stubs.

### 1.4 Retire legacy Python AST emitter
`emit_llvm.py` (AST-based) can't handle cross-module code and causes
23 xfailed tests. The MIR pipeline (`emit_llvm_mir.py`) is the real
emitter. Remove `emit_llvm.py` from the test matrix and delete the
23 xfail markers.

---

## Phase 2: Native Test Runner (`stdlib/test/`)

### 2.1 Core framework (`stdlib/test/runner.mn`)
```mapanare
import stdlib::test::runner

@test
fn test_addition() {
    assert_eq(1 + 1, 2)
    assert_ne(1 + 1, 3)
}

@test
fn test_string_ops() {
    let s: String = "hello"
    assert_eq(len(s), 5)
    assert(s.starts_with("hel"))
}
```

Functions:
- `assert(condition: Bool)` — fail with message if false
- `assert_eq(a, b)` — fail if a != b, show both values
- `assert_ne(a, b)` — fail if a == b
- `assert_contains(haystack, needle)`
- `run_tests()` — discover and run all `@test` functions

### 2.2 CLI integration
```bash
./mnc test stdlib/math.mn          # run tests in one file
./mnc test stdlib/                  # run all tests in directory
./mnc test --filter "test_add"     # filter by name
```

### 2.3 Mapanare stdlib tests
Rewrite the critical Python tests as native .mn tests:
- math.mn tests (trig, stats, rounding)
- json.mn tests (parse, encode, roundtrip)
- fs.mn tests (write, read, remove)
- string operations tests

---

## Phase 3: Compile All 37 Stdlib Modules

Work through the remaining modules systematically:

| Priority | Modules | Blocker |
|----------|---------|---------|
| High | net/http.mn | String concat in headers, extern C for TCP |
| High | ai/llm.mn | JSON + HTTP composition |
| Medium | db/sqlite.mn, db/pool.mn | Cross-module types |
| Medium | encoding/toml.mn, encoding/yaml.mn | Complex parsing |
| Low | net/websocket.mn | Needs HTTP first |
| Low | gpu/*.mn | Needs @cuda/@vulkan decorator support |

---

## Phase 4: Package Compilation

### 4.1 Build script for stdlib
```bash
./mnc build stdlib/ -o libmapanare.a    # compile all stdlib to archive
./mnc build myapp.mn -L stdlib/         # link against stdlib
```

### 4.2 Multi-module binary
Compile a program + its imports into a single binary:
```bash
./mnc build program.mn -o program       # resolves imports, links, produces binary
```

---

## Success Criteria

- [ ] No keyword-as-variable workarounds needed in stdlib
- [ ] WASM examples use real control flow (if/else, recursion)
- [ ] All 37 stdlib modules compile through `./mnc`
- [ ] Native test runner works for math, json, fs tests
- [ ] `./mnc test` CLI command runs .mn test files
- [ ] kv, sqlite, pool compile without stubs
- [ ] Legacy emit_llvm.py removed from test matrix

---

## Non-Goals

- Python test replacement (keep pytest for Python-level compiler tests)
- Package registry / dependency manager
- IDE integration updates
- New language features
