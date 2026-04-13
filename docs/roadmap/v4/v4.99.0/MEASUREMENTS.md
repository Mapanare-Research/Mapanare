# v4.99.0 Measurements — Current State of Mapanare

> Snapshot as of 2026-04-13 on `dev` branch.

## Codebase Size

| Component | Lines |
|-----------|-------|
| Self-hosted compiler (`mapanare/self/*.mn`) | 38,824 |
| Python bootstrap (`mapanare/*.py`) | 38,526 |
| C runtime (`runtime/native/*.c + *.h`) | 14,243 |
| Tests (`tests/**/*.py`) | 57,852 |
| **Total project** | **~150,000+** |

## Test Coverage

| Suite | Count |
|-------|-------|
| pytest (total collected) | 5,374 |
| Golden test programs (`tests/golden/*.mn`) | 61 |
| System benchmark programs (`benchmarks/system/*.mn`) | 5 |
| Optimizer benchmark programs (`benchmarks/optimizer/*.mn`) | 5 |
| Cross-language equivalents (`.py` + `.rs`) | 18 |

## Benchmark Headlines (v4.98.0, O2, AMD Ryzen 9 7950X)

| Benchmark | Mapanare (ms) | Python (ms) | Rust (ms) | vs Python | vs Rust |
|-----------|--------------|-------------|-----------|-----------|---------|
| fib(35) | 19.6 | 799.7 | 17.4 | 41x faster | 1.1x slower |
| quicksort 10K | 2.0 | 48.9 | 1.0 | 24x faster | 2.0x slower |
| struct_alloc 100K | 0.6 | 72.9 | 0.8 | 122x faster | faster |
| enum_match 100K | 2.3 | 49.6 | 1.1 | 22x faster | 2.1x slower |
| prime_sieve 100K | 3.0 | 91.0 | 2.6 | 30x faster | 1.2x slower |
| string_concat 10K | 95.2 | 43.7 | 0.7 | **2.2x slower** | 136x slower |

## Self-Hosted Compiler (mir_opt.mn)

| Pass | Status |
|------|--------|
| Constant folding | Implemented |
| Constant propagation | Implemented |
| Dead block elimination | Implemented |
| Strength reduction (v4.97.0) | Implemented |
| Function inlining (v4.97.0) | Implemented |
| LICM (v4.97.0) | Implemented |
| Escape analysis (v4.97.0) | Framework only |

## IR Quality (emit_llvm.mn + emit_llvm_ir.mn)

| Feature | Status |
|---------|--------|
| `nsw` on add/sub/mul | Yes |
| `nsw` on negation | Yes (v4.97.0) |
| `inbounds` on all GEPs | Yes |
| `nounwind willreturn` on user functions | Yes (v4.97.0) |
| `noalias` on sret | Yes (v4.97.0) |
| TBAA metadata | Declared (v4.97.0) |

## Known Blockers (v5 readiness)

| # | Issue | Severity | Status |
|---|-------|----------|--------|
| 1 | **mnc-stage1 binary corruption** — tagged pointer UB in `mapanare_core.c` (`mn_tag_heap` sets bit 0 of `char*`). LLVM exploits this UB at -O2. Binary produces garbled output. | **CRITICAL** | Open |
| 2 | **List indexing bug** — `data[j]` returns garbage in certain contexts despite working in quicksort. Context-dependent emitter issue. | HIGH | Open |
| 3 | **Async can't link** — `__mn_coro_scheduler_*` functions not in `libmapanare_rt.a`. 5 async benchmarks compile to IR but can't produce binaries. | HIGH | Open |
| 4 | **String concat 2.2x slower than Python** — `__mn_str_concat` allocates per call. Python's `+=` optimization and Rust's `String::push_str` are fundamentally faster. | MEDIUM | Open (StringBuilder exists but not auto-applied) |
| 5 | **Golden test regression** — 0/61 golden tests pass through mnc-stage1 (binary corruption). 19/61 passed with a previous binary. | HIGH | Open (blocked by #1) |
| 6 | **Fixed-point unverifiable** — Can't compare stage1-from-Python vs stage1-from-self because the binary can't run. | MEDIUM | Blocked by #1 |
