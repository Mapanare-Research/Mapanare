# Perf Arc Experiments — v4.144.0 → v4.154.0

Running ledger of performance experiments. Each row is one E-release.
"Win" means the patch was kept; "dead end" means it was rolled back.

| ID | Hypothesis | Result | Δ enum_match | Δ geomean | Files changed | Release |
|---|---|---|---:|---:|---|---|
| E1 | Unified-return for inline-enum returns prevents aggregate PHI → LLVM merges redundant switches | **WIN** | −8.4% (10M amplified) | n/a (only enum_match affected) | `mapanare/emit_llvm_text.py` (~30 LOC) | v4.145.0 |
| E2 | fib_recursive: nsw flags + pure-fn attrs + noundef on scalar params | **DEAD END** | −0.8% fib (noise) | n/a (no bench affected) | `mapanare/emit_llvm_text.py` (~52 LOC hygiene) | v4.146.0 |
| E3 | noalias on non-aliasing params via MIR escape analysis | **DEAD END** | 0% (binary identical) | 0% (binary identical) | `mapanare/mir_opt.py` +134 LOC, `mapanare/mir.py` +1 LOC, `mapanare/emit_llvm_text.py` +4 LOC | v4.147.0 |
| E4 | string_concat: StringBuilder realloc + benchmark methodology fix | **WIN** | −30% string_concat (internal), 2.04× Rust (was 33× artifact) | methodology fix reveals true geomean 1.13× Rust | `runtime/native/mapanare_core.c` ~20 LOC, `benchmarks/cross_language/mn_bench_main.c` NEW, `run_benchmarks.py` ~40 LOC | v4.148.0 |
| E5 | ABI.1: per-target sret for aggregates > 16B (SysV) / > 8B (Win64) | **WIN (correctness)** | +0.6% enum_match (neutral), sret 0 → 57 | neutral (no bench affected) | `mapanare/abi.py` NEW 97 LOC, `mapanare/emit_llvm_text.py` ~15 LOC | v4.149.0 |
| E6a | Agent runtime: empty-wake sem_post (only sem_post when ring empty pre-push) | **NEUTRAL** | n/a | −2.0% async (noise); async benchmarks use coroutine scheduler, not agent runtime | `runtime/native/mapanare_runtime.c` ~6 LOC | v4.150.0 |
| E6b | Agent runtime: inline small-message payload (tagged union in ring slot) | **NOT ATTEMPTED** | n/a | n/a — async benchmarks don't use agent runtime | — | v4.150.0 |
| E6c | Agent runtime: spin-before-park (64 PAUSE iters before sem_wait) | **NOT ATTEMPTED** | n/a | n/a — async benchmarks don't use agent runtime | — | v4.150.0 |
| E6* | Async scheduler: MAPANARE_ASYNC_THREADS env var (thread pool size control) | **WIN** | n/a | −50.1% async geomean (2.28 → 1.14 ms); Mapanare 0.85× Go with ASYNC_THREADS=2 | `runtime/native/mapanare_runtime.c` ~8 LOC | v4.150.0 |
