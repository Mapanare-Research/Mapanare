# Mapanare v3.34.0 — "Cachicamo" (Zero-Python Compiler Driver)

> Kill the Python dependency for end users. `mnc` becomes the default compiler
> binary. `mapanare run hello.mn` goes through the native compiler, not Python.
> Target: hello.mn compiles in <100ms.

**Status:** DONE
**Estimated scope:** Medium-Large (2-3 sessions)
**Breaking:** No (Python bootstrap still works, just not the default path)
**Prerequisite:** v3.33.0

---

## Motivation

Right now `mapanare run hello.mn` spawns Python, imports 13+ modules (~200-300ms),
does <5ms of actual work, then shells out to gcc/clang. The user waits 400ms+ for
a 3-line program. That's unacceptable for a compiled language.

The self-hosted compiler (`mnc-stage1`) already works. It compiles 20K lines of
itself. But the user-facing CLI still goes through Python. This version makes `mnc`
the default driver.

---

## Items

### 1. `mnc` as Default Compiler Binary [HIGH]

**Files:** `mapanare/cli.py`, `scripts/install.sh`, `Makefile`

The install process should produce a `mnc` binary (or `mapanare` symlink).
When the user runs `mapanare run hello.mn`, it should:
1. Check if `mnc` binary exists in PATH or known location
2. If yes → exec `mnc run hello.mn` (native, no Python)
3. If no → fall back to Python pipeline (development mode)

`mnc` is the compiled self-hosted compiler. No Python interpreter involved.

### 2. `mnc run` Subcommand [HIGH]

**File:** `mapanare/self/main.mn`

Add `run` subcommand to the native compiler:
1. Parse source → AST
2. Semantic check
3. Lower → MIR
4. Emit LLVM IR to temp file
5. Exec `clang -O2 <temp>.ll -o <temp> -lm -lpthread && <temp>`

All in one binary. No Python. Target: <100ms for hello.mn (native parse + clang).

### 3. `mnc build` Subcommand [HIGH]

**File:** `mapanare/self/main.mn`

```
mnc build hello.mn              # → hello (or hello.exe on Windows)
mnc build hello.mn -o myapp     # → myapp
mnc build --release hello.mn    # → optimized binary (-O2)
mnc build myproject/            # → build all .mn files in directory
```

### 4. `mnc compile` for Transpiler Languages [MEDIUM]

**File:** `mapanare/self/main.mn`, `mapanare/self/from_python.mn`, `mapanare/self/from_php.mn`

```
mnc compile main.py             # Python → native (via from_python.mn)
mnc compile app.php             # PHP → native (via from_php.mn)
```

Detect by file extension, route to the appropriate front-end module.
All native. Zero Python.

### 5. Precompiled C Runtime [MEDIUM]

**Files:** `scripts/install.sh`, `Makefile`

Pre-compile `mapanare_core.c` + `mapanare_runtime.c` into a static library
(`libmapanare_rt.a` / `mapanare_rt.lib`) during install. Then `mnc` links
against the prebuilt `.a` instead of compiling C source every time.

Saves ~30-50ms per compilation.

### 6. Startup Time Benchmark [LOW]

**File:** `tests/bench/bench_startup.sh` (new)

Measure and track:
- `time mnc run tests/golden/01_hello.mn` — must be <100ms
- `time mnc build tests/golden/01_hello.mn` — must be <150ms
- `time mnc compile tests/python_compat/test_basic_types.py` — must be <200ms

Add to CI as a regression gate.

### 7. Python CLI Becomes Dev-Only [LOW]

**File:** `mapanare/cli.py`

Add deprecation notice when running through Python:
```
[dev mode] Using Python bootstrap compiler. Install mnc for native speed.
```

Keep Python CLI for development/debugging but it's no longer the user-facing path.

---

## Verification

- [ ] `mnc run tests/golden/01_hello.mn` prints "hello" in <100ms
- [ ] `mnc build tests/golden/01_hello.mn -o /tmp/hello && /tmp/hello` works
- [ ] `mnc compile tests/python_compat/test_basic_types.py` works (no Python)
- [ ] `time mnc run hello.mn` consistently under 100ms
- [ ] Precompiled runtime linked correctly on Linux + Windows
- [ ] `/golden` — all pass through both `mnc` and Python bootstrap
- [ ] Python CLI shows dev-mode notice
- [ ] CI startup benchmark passes
