# Mapanare v4.107.0 — Add Go + C to Cross-Language Benchmark Suite

> **Phase C release 1.** v4.98.0 benchmarks compared Mapanare against
> Python and Rust only. Go was not installed. C was never planned.
> That leaves a gaping hole: we don't know where Mapanare sits on the
> full spectrum from C (fastest possible) to Python (slowest). This
> release adds Go and C programs for all 6 benchmark workloads and
> publishes the complete 6-language comparison. No code changes to
> Mapanare. Pure measurement.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.106.0
**Delta review:** No
**Full panel:** No (numbers speak for themselves)
**Estimated work:** 1 sprint
**Theme:** Measure against the full spectrum: C, Rust, Go, Mapanare, Python.

---

## Scope

The v4.98.0 `FINAL_REPORT.md` has two columns where Go should be: "Go not installed." C was explicitly deferred: "C/C++ can be added in v5.x." That was a mistake. Without C and Go, we cannot answer the question "how fast is Mapanare?" honestly.

C represents the theoretical performance ceiling. Rust represents the practical ceiling. Go represents the nearest competitor in the "modern compiled language" space. Python represents the floor. Mapanare's position relative to all four tells the full story.

This release writes 12 new benchmark programs (6 Go, 6 C), updates the harness to compile and run them, and publishes a single comprehensive comparison table. No Mapanare code is modified. No optimizations. Pure measurement.

### Benchmark programs

The 6 workloads from v4.98.0 that have cross-language equivalents:

1. `fib_recursive` -- recursive Fibonacci(35), pure integer compute
2. `quicksort` -- sort 10,000 random integers
3. `struct_alloc` -- allocate 100,000 small structs
4. `enum_match` -- dispatch over 100,000 tagged values
5. `prime_sieve` -- Sieve of Eratosthenes to 100,000
6. `string_concat` -- concatenate 10,000 strings in a loop

---

## Phase 1 -- Write Go equivalents

- [ ] Create `benchmarks/cross_language/go/fib_recursive.go` -- recursive fib(35), print result + `__BENCH_METRICS__` block (wall time, CPU time, peak memory via `runtime.ReadMemStats`)
- [ ] Create `benchmarks/cross_language/go/quicksort.go` -- Lomuto partition quicksort on 10K random ints, print sorted checksum
- [ ] Create `benchmarks/cross_language/go/struct_alloc.go` -- allocate 100K structs with 4 fields (int, float, string, bool), sum a field, print checksum
- [ ] Create `benchmarks/cross_language/go/enum_match.go` -- tagged union via interface or `iota` switch, dispatch 100K values through 10 variants
- [ ] Create `benchmarks/cross_language/go/prime_sieve.go` -- Sieve of Eratosthenes to 100,000, print count of primes
- [ ] Create `benchmarks/cross_language/go/string_concat.go` -- `s += chunk` in a loop for 10,000 iterations, print final length
- [ ] Verify all 6 compile with `go build -o <binary>` and produce correct output
- [ ] Verify checksums match Mapanare/Python/Rust equivalents where applicable

## Phase 2 -- Write C equivalents

- [ ] Create `benchmarks/cross_language/c/fib_recursive.c` -- recursive fib(35), `clock_gettime` for wall time, `getrusage` for peak RSS
- [ ] Create `benchmarks/cross_language/c/quicksort.c` -- Lomuto partition quicksort on 10K random ints, same seed as other languages
- [ ] Create `benchmarks/cross_language/c/struct_alloc.c` -- `malloc` 100K structs, sum field, free, print checksum
- [ ] Create `benchmarks/cross_language/c/enum_match.c` -- tagged union with enum discriminant + union payload, switch dispatch 100K values
- [ ] Create `benchmarks/cross_language/c/prime_sieve.c` -- Sieve of Eratosthenes to 100,000, print count
- [ ] Create `benchmarks/cross_language/c/string_concat.c` -- `realloc` + `memcpy` loop for 10K iterations (idiomatic C string concat), print final length
- [ ] Verify all 6 compile with `gcc -O2 -o <binary>` and `clang -O2 -o <binary>`
- [ ] Verify checksums match other languages
- [ ] Verify both gcc and clang produce correct output (no UB, no warnings with `-Wall -Wextra`)

## Phase 3 -- Update benchmark harness

- [ ] Read `benchmarks/cross_language/run_benchmarks.py` -- understand current runner architecture
- [ ] Add `run_c_gcc(c_file, n_runs)` function: compile with `gcc -O2`, run binary, parse `__BENCH_METRICS__` block
- [ ] Add `run_c_clang(c_file, n_runs)` function: compile with `clang -O2`, same structure
- [ ] Add `run_go_compiled(go_file, n_runs)` function: `go build -o <tmpdir>/bench`, run binary, parse metrics
- [ ] Update `BENCHMARKS` list to include all 6 workloads that have cross-language equivalents
- [ ] Update `_print_summary()` to include C (gcc), C (clang), and Go columns
- [ ] Update the expressiveness table to include C and Go LOC counts
- [ ] Read `benchmarks/optimizer/run_baseline.py` -- update its `bench_cross_language()` to include C targets if appropriate
- [ ] Verify the updated harness runs end-to-end with `--only fib_recursive` before running the full suite

## Phase 4 -- Run ALL benchmarks

- [ ] Run full suite: `python benchmarks/cross_language/run_benchmarks.py --runs 10`
- [ ] Targets: Mapanare (mnc-stage1 + opt -O2), Python 3.12, Go, Rust, C (gcc -O2), C (clang -O2)
- [ ] Same hardware, same environment, 10 runs each, median of middle 8 reported
- [ ] Verify correctness: all programs produce expected checksums
- [ ] Save raw results to `benchmarks/cross_language/v4.107.0-results.json`

## Phase 5 -- Publish FULL_COMPARISON.md

- [ ] Create `benchmarks/cross_language/FULL_COMPARISON.md`:
  - **Methodology**: hardware, OS, compiler versions (gcc, clang, go, rustc, python, LLVM), run count, median method
  - **Table 1: Wall-clock time (ms)** -- 6 columns: C (gcc -O2), C (clang -O2), Rust -O, Go, Mapanare O2, Python 3.12. All 6 benchmarks.
  - **Table 2: Peak memory (KB)** -- same 6 columns, same 6 benchmarks
  - **Table 3: Binary size (KB)** -- C (gcc), C (clang), Rust, Go, Mapanare (excludes Python)
  - **Table 4: Lines of code** -- all 6 languages, all 6 benchmarks
  - **Table 5: Speedup vs C (gcc)** -- ratio for each language: time / C_gcc_time. Shows where each language sits relative to the floor.
  - **Analysis**: where Mapanare sits on the C -> Rust -> Go -> Mapanare -> Python spectrum for each workload category
  - **Reproducibility**: exact commands to reproduce every number

## Phase 6 -- LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.107.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (9 items)

| # | Check | Evidence |
|---|---|---|
| 1 | 6 Go programs exist, compile, produce correct output | `benchmarks/cross_language/go/*.go` compile clean |
| 2 | 6 C programs exist, compile with both gcc and clang | `benchmarks/cross_language/c/*.c` compile clean with `-Wall -Wextra` |
| 3 | Harness updated to run Go, C (gcc), C (clang) | diff of `run_benchmarks.py` |
| 4 | All 6 benchmarks run on all 6 language configs | `v4.107.0-results.json` has 6 x 6 = 36 entries |
| 5 | Checksums match across languages for each benchmark | verified in harness output |
| 6 | `FULL_COMPARISON.md` published with all 5 tables | file exists, tables present |
| 7 | Numbers reproducible via documented commands | methodology section in report |
| 8 | 10 runs per config, median reported | JSON shows run count |
| 9 | Standard closeout clean | CI green |

---

## What this release does NOT do

- **Change Mapanare compiler or runtime** -- zero modifications to any `.py`, `.mn`, `.c`, or `.h` file in `mapanare/` or `runtime/`. Pure measurement.
- **Optimize anything** -- no tuning benchmark programs for any language. Standard idiomatic code in every language.
- **Add async benchmarks** -- async linking is still blocked. Only the 6 workloads with fully working cross-language equivalents are measured.
- **Compare debug vs release** -- all compiled languages are measured at their standard release optimization level only.
- **Run a panel** -- Phase C has no panel. Numbers speak for themselves.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Go not installable in WSL environment | low | high | `sudo apt install golang-go` or `snap install go`; if unavailable, document and note |
| C programs have UB that makes numbers meaningless | medium | high | Compile with `-fsanitize=undefined` in addition to `-O2`; fix any UB before measuring |
| Algorithm mismatch across languages inflates/deflates ratios | low | high | Code review each implementation; same algorithm, same data size, same RNG seed where applicable |
| Benchmark variance too high for sub-2ms benchmarks | medium | medium | 10 runs helps; for sub-1ms results, report "below measurement threshold" rather than fake precision |
| C -O2 triggers auto-vectorization that other languages don't match | medium | low | Document; this is expected -- C with SIMD is the theoretical ceiling. Report it honestly. |

---

## After v4.107.0

Now we know exactly where Mapanare stands against the full spectrum: C (fastest) -> Rust -> Go -> Mapanare -> Python (slowest). The one embarrassing number -- string_concat 2.2x slower than Python -- is the target for v4.108.0. The optimizer ROI question ("why did Arcs 11-12 produce zero delta at O2?") is v4.109.0. v4.110.0 re-measures everything after fixes land.
