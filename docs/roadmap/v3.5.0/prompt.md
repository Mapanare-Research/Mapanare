# v3.5.0 — Real Programs — Continuation Prompt

> Fix the compiler bugs. Compile all stdlib. Build a native test runner.
> No more workarounds — fix root causes.
> Read CLAUDE.md for project context.
> Track progress in `docs/roadmap/v3.5.0/PLAN.md`.
> Commit at each milestone. Make decisions autonomously.

## MANDATORY: Use Culebra for ALL IR debugging

```bash
# Wrap ALL gcc/clang/llvm-as commands through Culebra
~/.cargo/bin/culebra wrap -- clang -c -O2 output.ll -o output.o
~/.cargo/bin/culebra wrap -- llvm-as output.ll -o /dev/null

# Scan for IR pathologies
~/.cargo/bin/culebra scan output.ll
~/.cargo/bin/culebra triage output.ll --brief

# Track progress
~/.cargo/bin/culebra journal add "description" --action fix --tags "v3.5.0"
~/.cargo/bin/culebra journal add "description" --action milestone
~/.cargo/bin/culebra journal show
```

## MANDATORY: Validate locally before commit

```bash
# Full validation — mirrors CI exactly
black --check --target-version py311 .
ruff check .
python3 -m mypy mapanare/ runtime/ --ignore-missing-imports
gcc -O2 -Wall -Wextra -Werror -pthread tests/native/test_c_runtime.c \
    runtime/native/mapanare_core.c runtime/native/mapanare_runtime.c \
    -o /tmp/test_c_runtime && /tmp/test_c_runtime

# WASM validation (wat2wasm installed at ~/.local/bin/)
for f in examples/wasm/hello.mn examples/wasm/wasi_app.mn; do
    python3 -m mapanare emit-wasm "$f" -o /tmp/t.wat && wat2wasm /tmp/t.wat -o /dev/null
    python3 -m mapanare emit-wasm --wasi "$f" -o /tmp/t.wat && wat2wasm /tmp/t.wat -o /dev/null
done

# Bootstrap
bash scripts/build_from_seed.sh --verify

# Golden tests
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# pytest (run by directory to avoid OOM)
python3 -m pytest tests/bootstrap/ tests/stdlib/ tests/self_hosted/ \
    tests/test_doc_links.py -q --tb=no
```

---

## Context

v3.4.0 added module imports, Map type, extern "C" fn, and compiled
10 stdlib modules (252 functions). Three end-to-end programs run
natively: math, file I/O, JSON parse+encode.

But v3.4.0 required **50+ workarounds** instead of fixing root causes:
- Renamed `input`, `agent`, `di` variables (keywords used as names)
- Replaced ~50 list concat `a + [x]` with `.push(x)`
- Stubbed `append_file`, `list_dir` (C ABI uses raw pointers)
- Gutted WASM examples (emitter can't do if/else)
- xfailed 23 tests (legacy AST emitter can't resolve cross-module calls)

v3.5.0 fixes the actual bugs so users don't hit these.

---

## Inherited State (from v3.4.0)

| Component | Status |
|-----------|--------|
| Self-hosted compiler | Fixed point, 25/25 golden, imports work |
| Seed binary | v3.4.0 with Map + imports + extern C |
| Bootstrap | `bash scripts/build_from_seed.sh --verify` (no Python) |
| Stdlib compiled | 10/37 modules (math, fs, time, log, crypto, string_utils, json, csv, sql, text) |
| Stdlib running | math (42 fns), fs (30 fns), json (33 fns) verified end-to-end |
| Map type | #{} literals, get, set, cada..en iteration |
| CI | 1453 pass, 0 fail, 23 xfail (legacy AST emitter) |
| C tests | 52/52 |
| WASM | wat2wasm passes, but examples are gutted (no control flow) |

---

## Attack Order

### Phase 1: Fix Compiler Bugs

#### 1.1 Keyword-as-variable resolution
**Problem:** The lexer turns `input`, `agent`, `di`, `si` into keywords
even in variable position. We renamed ~20 variables across stdlib.

**Fix:** In the parser, when a keyword token appears after `let`/`pon`,
as a function parameter name, or on the left side of `=`, treat it as
a NAME. This is contextual keyword resolution — Rust/Go do this.

**Files:** `mapanare/self/parser.mn` (parse_param, parse_let_stmt),
possibly `mapanare/self/lexer.mn`

**Test:** `let input: String = "hello"` should parse. `si input == "x"`
should work (si is if, input is variable).

#### 1.2 WASM structured control flow
**Problem:** The WASM emitter translates MIR basic blocks into WAT
blocks, but WAT requires structured control flow (if/else blocks must
have matching return types). The emitter generates invalid block nesting.

**Fix:** Implement a Relooper or Stackifier in `mapanare/emit_wasm.py`.
Reference: Emscripten's Relooper algorithm.

**Files:** `mapanare/emit_wasm.py`

**Test:** `examples/wasm/hello.mn` with fibonacci (if/else + recursion)
should pass `wat2wasm`.

#### 1.3 Cross-module return type resolution
**Problem:** When `kv.mn` calls `embedded_get()` from `embedded_kv.mn`,
the lowerer doesn't know the return type → defaults to `unknown` → IR
type mismatch.

**Fix:** During import resolution in `main.mn`, after parsing imported
modules, register ALL function return types from imported definitions
in the lowerer's `lambda_vars` registry (the `__ret__fn_name` pattern).

**Files:** `mapanare/self/main.mn` (resolve_imports), `mapanare/self/lower.mn`

**Test:** `stdlib/db/kv.mn` compiles without stubs.

#### 1.4 Retire legacy AST emitter from tests
**Problem:** 23 tests use `emit_llvm.py` (AST-based) which can't handle
cross-module functions. These are xfailed.

**Fix:** Remove the `[emit_llvm]` parametrize variant from bootstrap
tests. Keep `[main]` and `[mnc_all]` which use the MIR pipeline.

**Files:** `tests/bootstrap/test_bootstrap_stage1.py`,
`tests/bootstrap/test_bootstrap_stage2.py`,
`tests/bootstrap/test_verification.py`

---

### Phase 2: Native Test Runner

Build `stdlib/test/runner.mn` — a test framework written in Mapanare.

```mapanare
import stdlib::test::runner

@test
fn test_addition() {
    assert_eq(1 + 1, 2)
}

@test
fn test_json_roundtrip() {
    let src: String = "{\"x\": 1}"
    let parsed: Result<JsonValue, JsonError> = decode(src)
    match parsed {
        Ok(v) => { assert_eq(encode(v), "{\"x\":1}") },
        Err(e) => { fail("parse failed: " + e.message) }
    }
}
```

**Functions needed:**
- `assert(cond: Bool)` / `assert_msg(cond: Bool, msg: String)`
- `assert_eq(a: Int, b: Int)` / `assert_eq_str(a: String, b: String)`
- `assert_ne(a: Int, b: Int)`
- `assert_contains(haystack: String, needle: String)`
- `fail(msg: String)`

**CLI:** `./mnc test file.mn` — compile + run, report pass/fail.

**Priority tests to port:**
1. `stdlib/math.mn` — trig, stats, rounding
2. `stdlib/encoding/json.mn` — parse + encode roundtrip
3. `stdlib/fs.mn` — write, read, exists, remove

---

### Phase 3: Compile All 37 Stdlib Modules

| Module | Status | Blocker |
|--------|--------|---------|
| math.mn | DONE | — |
| fs.mn | DONE (stubbed append/listdir) | Raw pointer ABI |
| time.mn | DONE | — |
| log.mn | DONE | — |
| crypto.mn | DONE | — |
| text/string_utils.mn | DONE | — |
| text/text.mn | DONE | — |
| encoding/json.mn | DONE | — |
| encoding/csv.mn | DONE | — |
| db/sql.mn | DONE | — |
| encoding/toml.mn | COMPILES | Needs runtime testing |
| encoding/yaml.mn | COMPILES | Needs runtime testing |
| db/kv.mn | 1 error | Cross-module return types (Phase 1.3) |
| db/sqlite.mn | 1 error | Cross-module return types |
| db/pool.mn | 1 error | Cross-module return types |
| db/embedded_kv.mn | Untested | — |
| db/postgres.mn | Untested | Needs TCP extern C |
| db/redis.mn | Untested | Needs TCP extern C |
| db/migrate.mn | Untested | — |
| net/http.mn | Untested | TCP + TLS extern C |
| net/http/server.mn | Untested | — |
| net/http/auth.mn | Untested | — |
| net/http/cookie.mn | Untested | — |
| net/http/config.mn | Untested | — |
| net/http/body.mn | Untested | — |
| net/http/ratelimit.mn | Untested | — |
| net/http/session.mn | Untested | — |
| net/http/sse.mn | Untested | — |
| net/http/template.mn | Untested | — |
| net/websocket.mn | Untested | — |
| ai/llm.mn | Untested | JSON + HTTP |
| ai/embedding.mn | COMPILES | Needs runtime testing |
| ai/rag.mn | Untested | — |
| gpu/device.mn | Untested | @cuda decorator |
| gpu/kernel.mn | Untested | @cuda decorator |
| gpu/tensor.mn | Untested | @cuda decorator |
| wasm/bridge.mn | Untested | WASM-specific |
| wasm/runtime.mn | Untested | WASM-specific |

---

### Phase 4: Package Compilation

```bash
./mnc build program.mn -o program    # compile + link + produce binary
./mnc test tests/                    # run all .mn test files
```

---

## Known Issues to Expect

1. **`pub` visibility** — imports merge all definitions. Need to respect
   `pub` vs private when importing (only pub symbols visible).

2. **Name mangling** — when two imported modules define the same function
   name, they collide. Need module-prefix mangling (like Python's
   `multi_module.py` does with `math__sin`).

3. **Circular imports** — the guard exists but hasn't been stress-tested.

4. **Large module compilation** — the 2000-iteration for-loop limit in
   the lowerer may need increasing for large modules.

5. **`cada ... en` on lists** — for-each over lists isn't implemented
   (only maps and ranges). Need list iteration support.

6. **String interpolation** — `f"hello {name}"` syntax not in
   self-hosted parser yet.

---

## Verification Commands

```bash
# Rebuild compiler
python3 scripts/concat_self.py
python3 scripts/build_stage1.py --skip-check

# Build from seed (no Python)
bash scripts/build_from_seed.sh --verify

# Compile a stdlib module
./mapanare/self/mnc-stage1 stdlib/math.mn > /tmp/math.ll
~/.cargo/bin/culebra wrap -- llvm-as /tmp/math.ll -o /dev/null

# Compile + link + run
./mapanare/self/mnc-stage1 program.mn > /tmp/prog.ll
clang -c -O2 /tmp/prog.ll -o /tmp/prog.o
gcc /tmp/prog.o runtime/native/mapanare_core.c \
    -I runtime/native -o /tmp/prog -no-pie -rdynamic -lm -lpthread
/tmp/prog

# Stdlib scorecard
for mod in stdlib/math.mn stdlib/fs.mn stdlib/time.mn stdlib/log.mn \
    stdlib/crypto.mn stdlib/text/string_utils.mn stdlib/text/text.mn \
    stdlib/encoding/json.mn stdlib/encoding/csv.mn stdlib/db/sql.mn; do
    echo -n "$(basename $mod .mn): "
    ./mapanare/self/mnc-stage1 "$mod" > /tmp/t.ll 2>/dev/null && \
        llvm-as /tmp/t.ll -o /dev/null 2>/dev/null && \
        echo "OK ($(grep -c '^define ' /tmp/t.ll) fns)" || echo "FAIL"
done

# Culebra diagnostics
~/.cargo/bin/culebra scan /tmp/prog.ll
~/.cargo/bin/culebra journal show
```
