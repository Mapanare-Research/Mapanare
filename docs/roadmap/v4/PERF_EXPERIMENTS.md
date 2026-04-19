# Perf Arc Experiments — v4.144.0 → v4.154.0

Running ledger of performance experiments. Each row is one E-release.
"Win" means the patch was kept; "dead end" means it was rolled back.

| ID | Hypothesis | Result | Δ enum_match | Δ geomean | Files changed | Release |
|---|---|---|---:|---:|---|---|
| E1 | Unified-return for inline-enum returns prevents aggregate PHI → LLVM merges redundant switches | **WIN** | −8.4% (10M amplified) | n/a (only enum_match affected) | `mapanare/emit_llvm_text.py` (~30 LOC) | v4.145.0 |
| E2 | fib_recursive: nsw flags + pure-fn attrs + noundef on scalar params | **DEAD END** | −0.8% fib (noise) | n/a (no bench affected) | `mapanare/emit_llvm_text.py` (~52 LOC hygiene) | v4.146.0 |
| E3 | noalias on non-aliasing params via MIR escape analysis | **DEAD END** | 0% (binary identical) | 0% (binary identical) | `mapanare/mir_opt.py` +134 LOC, `mapanare/mir.py` +1 LOC, `mapanare/emit_llvm_text.py` +4 LOC | v4.147.0 |
| E4 | string_concat: StringBuilder realloc + benchmark methodology fix | **WIN** | −30% string_concat (internal), 2.04× Rust (was 33× artifact) | methodology fix reveals true geomean 1.13× Rust | `runtime/native/mapanare_core.c` ~20 LOC, `benchmarks/cross_language/mn_bench_main.c` NEW, `run_benchmarks.py` ~40 LOC | v4.148.0 |
