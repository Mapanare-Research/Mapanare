# Perf Arc Experiments — v4.144.0 → v4.154.0

Running ledger of performance experiments. Each row is one E-release.
"Win" means the patch was kept; "dead end" means it was rolled back.

| ID | Hypothesis | Result | Δ enum_match | Δ geomean | Files changed | Release |
|---|---|---|---:|---:|---|---|
| E1 | Unified-return for inline-enum returns prevents aggregate PHI → LLVM merges redundant switches | **WIN** | −8.4% (10M amplified) | n/a (only enum_match affected) | `mapanare/emit_llvm_text.py` (~30 LOC) | v4.145.0 |
| E2 | fib_recursive: nsw flags + pure-fn attrs + noundef on scalar params | **DEAD END** | −0.8% fib (noise) | n/a (no bench affected) | `mapanare/emit_llvm_text.py` (~52 LOC hygiene) | v4.146.0 |
