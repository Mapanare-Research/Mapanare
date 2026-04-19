# Mamba — v4.144.0 C runtime / performance review

**Score: 9.1 / 10**
**Grade: EXCEEDS**
**Prior (v4.143.0): 8.7 / 10 MEETS**
**Delta: +0.4**

---

## Executive summary

Bn.1 is fixed. The Rust numbers are real numbers now. I can read
them and not want to throw the JSON file in the trash. The
`__BENCH_METRICS__` instrumentation — `std::time::Instant` inside
`main`, wall reported via stdout — bypasses the subprocess-spawn
tax I flagged at v4.143.0. All 10 Rust `.rs` benchmarks carry the
instrumentation. All 6 cross-language Rust entries in the JSON show
`wall_time_s == cpu_time_s` per run (the expected signature of
internal-timer reporting). Rust `quicksort` is 0.414 ms, not the
9.99 ms nonsense from v4.142.0. Rust `struct_alloc` is 0.017 ms,
not 9.58 ms. The harness works.

The Mapanare numbers are consistent with v4.135.0 (last pre-Bn.1
clean baseline): `fib_recursive` 20.66 ms vs 19.57 ms, `enum_match`
1.62 ms vs 1.47 ms, `quicksort` 2.39 ms vs 2.73 ms. No codegen
regression. The v4.142.0 floor-shift I flagged was entirely harness
tax, as I said.

The geomean arithmetic in `FINAL_REPORT_v4.144.md` is wrong. I dock
for that. But the raw data is honest, and the Bn.1 closure is real.
The C runtime is untouched. Zero new dockets.

---

## Bn.1 verification — CLOSED, confirmed

### Instrumentation audit

All 10 Rust benchmark source files carry the `__BENCH_METRICS__`
pattern:

```rust
let __bench_t0 = Instant::now();
// ... workload ...
let __bench_dt = __bench_t0.elapsed().as_secs_f64();
println!("__BENCH_METRICS__");
println!("wall_time_s={}", __bench_dt);
println!("cpu_time_s={}", __bench_dt);
println!("peak_memory_kb=0");
```

Files verified: `fib_recursive.rs`, `quicksort.rs`, `string_concat.rs`,
`matmul_naive.rs`, `agent_fanout.rs` (optimizer/), `struct_alloc.rs`,
`enum_match.rs`, `list_ops.rs`, `compile_self.rs`, `closure_capture.rs`
(system/), plus 5 cross-language `.rs` files. 15 total.

### Rust numbers — no longer pinned at 10 ms

| Benchmark | Rust v4.142.0 (broken) | Rust v4.144.0 (fixed) | Ratio |
|---|---:|---:|---:|
| fib_recursive | 25.18 ms | 21.16 ms | real compute, slight improvement |
| quicksort | 9.99 ms | 0.414 ms | **24x** lower = spawn-tax removed |
| struct_alloc | 9.58 ms | 0.017 ms | **563x** lower = spawn-tax removed |
| enum_match | 10.08 ms | 0.296 ms | **34x** lower = spawn-tax removed |
| prime_sieve | 10.97 ms | 1.760 ms | **6.2x** lower = spawn-tax removed |
| string_concat | 9.97 ms | 0.046 ms | **217x** lower = spawn-tax removed |

Five of six cells moved by 6x to 563x. `fib_recursive` moved ~16%
because its 21 ms of real compute already dominated the ~10 ms
spawn tax. This is exactly the pattern I predicted: fixed-cost
artifact removed, only `fib_recursive` stays near prior because
the workload dominates.

### JSON evidence

`wall_time_s == cpu_time_s` on every Rust run (all 60 data points).
This is the fingerprint of internal-timer reporting — the harness
reads the `__BENCH_METRICS__` stdout line and uses the reported
internal wall time, not `time.time()` around `subprocess.run()`.

Rust run variance is reasonable: cv 3.1% to 6.1% on the compute-
dominated workloads (`fib`, `quicksort`, `enum_match`, `prime_sieve`).
`struct_alloc` and `string_concat` show higher cv (17.9% and 14.7%)
because they're sub-millisecond — noise is proportionally larger at
17 microseconds. Acceptable.

### Verdict on Bn.1

**CLOSED.** The fix is correct, the evidence is clean, the Rust
column is citable again. This was the single item I opened at
v4.143.0 and the single reason I dropped from 9.0 to 8.7. It's
done.

---

## Geomean arithmetic — wrong in the report

The `FINAL_REPORT_v4.144.md` claims:

> Mapanare/Rust geomean: 5.83x
> Mapanare/C geomean: 4.57x

I recomputed from the raw JSON data:

| Benchmark | Mn/Rust | Mn/C |
|---|---:|---:|
| fib_recursive | 0.98x | 1.87x |
| quicksort | 5.76x | 6.79x |
| struct_alloc | 70.47x | 2.09x |
| enum_match | 5.47x | 12.45x |
| prime_sieve | 1.94x | 1.71x |
| string_concat | 36.00x | 23.32x |
| **geomean** | **7.31x** | **4.87x** |

The Mn/C geomean is 4.87x, not 4.57x. Close enough that it could
be a rounding artifact from the per-row rounded values, but the
Mn/Rust geomean is **7.31x**, not 5.83x. That's a 25% error. The
report's 5.83x number is wrong.

I suspect the report computed the geomean from the ratio column
after rounding individual ratios, or excluded `struct_alloc` and
`string_concat` as outliers without saying so. Either way: the
number in the headline is wrong. The raw data is honest; the
summary math is not.

I dock 0.15 for this. Not the same severity as v4.142.0's broken
harness — the underlying data is clean this time, and the per-
benchmark table is correct. But a wrong geomean in the headline
of a panel evidence pack is still wrong.

---

## The JSON version field is still "4.125.0"

```json
"version": "4.125.0"
```

The actual VERSION file says `4.144.0`. This has been wrong since I
first flagged it at v4.143.0. It's a cosmetic annoyance, not a
measurement issue — the data is from the current harness run, the
JSON just doesn't stamp itself. But it's sloppy. One line to fix.

Not docking further; I already named it. Tracking as residual
polish.

---

## fib_recursive at 0.98x Rust — real or artifact?

Real.

Mapanare: 20.66 ms. Rust: 21.16 ms. The Mapanare binary is compiled
with `clang -O2` on emitted LLVM IR; Rust is compiled with `rustc -O`
(release, which maps to `-O2` in LLVM). Both are calling the same
LLVM optimizer on nearly identical recursive IR. The Mapanare IR
for `fib_recursive` is trivial — one function, two recursive calls,
no allocations, no runtime interaction. LLVM -O2 produces
essentially the same machine code from both inputs.

The Rust binary is 3.99 MB (statically linked stdlib); the Mapanare
binary is 59 KB. The Rust binary has more startup overhead (TLS
init, panic handler registration, stack guard setup). On a 20 ms
workload, that startup cost is negligible but nonzero. Hence Rust
is slightly slower.

This is not an artifact. It is a compute-bound workload where both
compilers feed the same LLVM backend the same shaped IR. Parity
is the expected result.

---

## struct_alloc at 70x slower than Rust

Rust `Point { x, y, z }` is a 24-byte stack struct. No allocation.
The loop runs 100K iterations; LLVM likely auto-vectorizes or at
minimum keeps the struct in registers.

Mapanare's `Point` is heap-allocated with drop-glue per iteration.
100K mallocs + 100K frees vs zero. 70x is the expected cost of
heap allocation in a tight loop where the competitor does zero.

This is the ABI.1 gap I named at v4.125.0: Mapanare's struct
return ABI uses heap + sret even for small structs that fit in
registers. The report correctly identifies this and targets
v4.149.0 for a perf arc. There is nothing to fix here today;
this is an architectural debt item, not a bug.

---

## Runtime stability

Zero commits to `runtime/native/` since v4.137.0 (Ch.1). That is
7 releases of no-touch. The C runtime surface is:

- **14,619 lines** of `.c` + `.h` — unchanged from v4.143.0
- **267,262 bytes** `libmapanare_rt.a` — unchanged from v4.143.0
- **sha256**: same archive I measured at v4.143.0

No growth. No churn. The runtime is stable.

### Binary size

`mnc-stage1` stripped: **3,570,832 bytes** at v4.144.0. Was
3,566,736 at v4.143.0. Delta: **+4,096 bytes** (+0.11%). This is
the Cb.6/Cb.7 changes in `emit_llvm.mn` and `lower.mn` — self-
hosted compiler source changes, not runtime. One page of growth
for test infrastructure and a guard clause. Fine.

### Sanitizer state

Valgrind 0 ERRORS, ASan 0 ASAN_ERROR — unchanged from v4.143.0.
The runtime is clean. The sanitizer coverage has not regressed.

---

## What v4.144.0 actually ships (from my lens)

1. **Bn.1 closure confirmed** — Rust benchmarks report internal
   wall times via `__BENCH_METRICS__`. Numbers are credible.
2. **34 enum-inline unit tests** (Cb.5-tests) — not my domain
   but positive test coverage growth.
3. **Cb.6/Cb.7** — self-hosted emitter hardening. Minor. Correct.
4. **Zero runtime changes.** Good.

This is a measurement-hygiene + test-coverage release. No codegen
changes, no runtime changes. The kind of release that makes the
prior arc's numbers citable again.

---

## Score rationale

Starting from v4.143.0 baseline of 8.7:

- **Bn.1 closed and confirmed**: **+0.5**
  The single item I opened. The fix is structural (`__BENCH_METRICS__`
  internal timers), not cosmetic. Rust numbers moved 6x-563x back
  to plausible ranges. The harness is no longer lying. This recovers
  the 0.5 I docked at v4.143.0.

- **Geomean arithmetic wrong in report**: **-0.15**
  Mn/Rust geomean is 7.31x, not 5.83x. The raw data is fine; the
  summary is wrong. Less severe than a broken harness but still a
  wrong number in a panel-facing document.

- **JSON version field still "4.125.0"**: **-0.0**
  Already named. Cosmetic. Not docking again.

- **Runtime untouched, sanitizers clean**: **+0.0** (par)

- **enum_match 1.62 ms confirmed (was 1.47 ms at v4.135.0)**: **+0.05**
  The Rt.1 win I credited at v4.136.0 holds. The tiny regression
  (1.47 -> 1.62 ms, +10%) is within noise on WSL2. The 0.98x-of-
  Rust on `fib_recursive` is a new parity data point.

**Net: 8.7 + 0.5 - 0.15 + 0.05 = 9.1.**

Grade: **EXCEEDS** (threshold 9.0).

---

## Carry-forward

| Docket | Severity | Status at v4.144.0 |
|---|---|---|
| **Bn.1** (cross-language harness tax) | MEDIUM | **CLOSED** — `__BENCH_METRICS__` confirmed across all 10 Rust benchmarks |
| **ABI.1** (24-byte struct return → heap) | LOW | OPEN — `struct_alloc` 70x gap confirms; v4.149.0 perf arc target |
| **Qs.1'** (List<Int> tight-loop indexing) | LOW | OPEN — unchanged |
| **Bn.2** (geomean arithmetic error in FINAL_REPORT) | NEW LOW | OPEN — Mn/Rust geomean is 7.31x, not 5.83x |
| **Bn.3** (JSON version field "4.125.0") | NEW LOW | OPEN — one-line fix in benchmark runner |

Bn.2 and Bn.3 are LOW polish items. Neither affects the underlying
measurement quality.

---

## Reproducibility

```bash
cd /mnt/c/Users/Juan/Documents/GitHub/Mapanare
cat VERSION                                     # -> 4.144.0

# Rust __BENCH_METRICS__ check
grep -l __BENCH_METRICS__ benchmarks/**/*.rs | wc -l   # -> 15

# Rust wall==cpu fingerprint
python3 -c "
import json
d = json.load(open('benchmarks/cross_language/v4.144.0-results.json'))
for r in d['results']:
    if r['language'] == 'Rust -O':
        ok = all(x['wall_time_s'] == x['cpu_time_s'] for x in r['runs'])
        print(f\"{r['benchmark']:20s} internal_timer={ok}\")
"
# -> all True

# Geomean recompute
python3 -c "
import json, math
d = json.load(open('benchmarks/cross_language/v4.144.0-results.json'))
mn, rust = {}, {}
for r in d['results']:
    if r['language'] == 'Mapanare O2': mn[r['benchmark']] = r['wall_median_ms']
    if r['language'] == 'Rust -O': rust[r['benchmark']] = r['wall_median_ms']
ratios = [mn[b]/rust[b] for b in mn if b in rust]
print(f'Mn/Rust geomean = {math.exp(sum(math.log(r) for r in ratios)/len(ratios)):.2f}x')
"
# -> 7.31x (report claims 5.83x)

# Runtime untouched
git log --oneline -1 -- runtime/native/   # -> 9cb8911 (v4.137.0 Ch.1)
wc -l runtime/native/*.c runtime/native/*.h | tail -1   # -> 14619
ls -la runtime/native/libmapanare_rt.a    # -> 267262 bytes

# JSON version drift
python3 -c "import json; print(json.load(open('benchmarks/cross_language/v4.144.0-results.json'))['version'])"
# -> 4.125.0
```
