# Mapanare v3.36.0 — "Cunaguaro II" (Compiler Performance + Release Prep)

> Final performance pass: optimize the compiler itself, shrink binary size,
> add compile-time benchmarks to CI, and prepare the ground for v4.0.0.
> After this version, v4.0.0 is purely docs, demos, and the quality gate.

**Status:** DONE
**Estimated scope:** Medium (1-2 sessions)
**Breaking:** No
**Prerequisite:** v3.35.0

---

## Motivation

v3.34.0 killed Python dependency. v3.35.0 added incremental compilation.
v3.36.0 optimizes the compiler's own code — making the native binary smaller,
reducing memory usage during compilation, and establishing performance baselines
that v4.0.0 will enforce.

---

## Items

### 1. Compiler Memory Optimization [HIGH]

**Files:** `mapanare/self/lower.mn`, `mapanare/self/emit_llvm.mn`

Profile memory usage during self-compilation. The compiler processes 20K lines
and generates 275K lines of IR — how much memory does it use?

Targets:
- Arena reuse between modules (don't allocate fresh arenas per module)
- String interning for common IR patterns (`i64`, `ptr`, `%struct.`, etc.)
- Release AST nodes after lowering (don't keep full AST in memory alongside MIR)

### 2. IR Output Size Reduction [HIGH]

**File:** `mapanare/self/emit_llvm.mn`

275K lines of IR for 20K lines of source is a 13.75x blowup. Targets:
- Deduplicate identical string constants (currently each `print("hello")` emits
  a separate `@.str.N` global even if the string is the same)
- Merge identical small functions (constructors that do the same thing)
- Eliminate dead function declarations (declared but never called)
- Target: <200K lines of IR (<10x blowup)

### 3. Binary Size Optimization [MEDIUM]

**Files:** Build scripts, `mapanare/self/emit_llvm.mn`

Current `mnc-stage1` binary size: ~50MB (estimate). Targets:
- Strip debug info from release builds (`-s` flag to linker)
- LTO (Link-Time Optimization) for release builds
- Dead code elimination at link time (`--gc-sections`)
- Target: <10MB release binary

### 4. Compile-Time Benchmark Suite [MEDIUM]

**File:** `tests/bench/bench_compile.sh` (new)

Tracked in CI, fails on regression:

| Benchmark | Target |
|-----------|--------|
| `mnc run hello.mn` | <100ms |
| `mnc build hello.mn` | <150ms |
| `mnc build` (11-module compiler, clean) | <15s |
| `mnc build` (11-module compiler, incremental, 1 file changed) | <2s |
| `mnc compile test.py` (100-line Python) | <200ms |
| Peak memory during self-compilation | <512MB |
| `mnc-stage1` binary size (stripped) | <10MB |

### 5. Error Message Performance [LOW]

**File:** `mapanare/self/semantic.mn`

Type errors in large files should not slow down. If the user has 50 errors,
don't spend time formatting all 50 — show the first 10 with a "and 40 more..."
message. Currently the compiler formats all errors even if it will only show 10.

### 6. LLVM Pass Pipeline Tuning [LOW]

**File:** `mapanare/self/main.mn`

When shelling out to clang, use the right optimization pipeline:
- `-O0` for debug builds (fastest compile)
- `-O2` for release builds (good perf, reasonable compile time)
- `-Os` for size-optimized builds (smallest binary)
- `-O2 -flto` for fully optimized release

Expose via `mnc build --release`, `mnc build --small`, `mnc build --debug`.

### 7. Warm-Up Profiling Data [LOW]

**File:** `mapanare/self/main.mn`

Support PGO (Profile-Guided Optimization) for the compiler itself:
1. `mnc build --profile` → build with instrumentation
2. Run the instrumented compiler on the test suite
3. `mnc build --pgo` → rebuild using the profile data

The compiler optimizes itself based on its own usage patterns. Meta.

---

## Verification

- [ ] IR output for self-compilation: <200K lines (down from 275K)
- [ ] `mnc-stage1` stripped binary: <10MB
- [ ] Peak memory during self-compilation: <512MB
- [ ] `mnc run hello.mn` consistently <100ms
- [ ] Incremental rebuild <2s after single-file change
- [ ] Compile-time benchmark suite passes in CI
- [ ] Error messages limited to 10 by default
- [ ] `-O0`/`-O2`/`-Os` flags work correctly
- [ ] `/golden` — all pass
- [ ] Fixed point maintained (stage3 == stage4)
