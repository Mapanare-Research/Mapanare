# Mapanare v4.155.0 — "Write Python, Compile Native"

> **The adoption release.** Wire `mapanare build file.py` end-to-end,
> prove 50-100x speedup on real data-processing scripts, publish the
> demo that makes people try Mapanare for the first time.
>
> The transpiler (`from_python.py`, 937 lines) and the CLI wiring
> (`_read_source()` at `cli.py:40`) already exist. This release is
> verification + demo + benchmarks — not a rewrite.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.154.0 shipped (perf panel complete)
**Estimated work:** 1-2 sessions
**Theme:** "Same Python code, 100x faster, zero changes."

---

## Why this release exists

Mapanare is 168x faster than Python on pure compute. The perf arc
proved the compiler is real. But nobody outside the project has a reason
to *try* it — there's no on-ramp.

The on-ramp is: take an existing Python script, compile it with
Mapanare, get a native binary that runs 50-100x faster. No rewrite.
No new language to learn. Just `mapanare build your_script.py`.

This is the release that turns the perf story into an adoption story.

---

## What already works

| Component | File | Lines | Status |
|---|---|---:|---|
| Python transpiler (bootstrap) | `mapanare/from_python.py` | 937 | Complete |
| Python transpiler (self-hosted) | `mapanare/self/from_python.mn` | 578 | Complete |
| CLI `.py` detection | `mapanare/cli.py:40-48` | 8 | Wired into `_read_source()` |
| `mapanare build` (LLVM backend) | `mapanare/cli.py:520` | — | Uses `_read_source()` |
| `mapanare run` (C backend) | `mapanare/cli.py:288` | — | Uses `_read_source()` |
| `mapanare transpile` (output .mn) | `mapanare/cli.py:1233` | — | Standalone command |
| Example scripts | `examples/transpile/*.py` | 4 files | fibonacci, collatz, primes, fibonacci_bench |
| Transpiler tests | `tests/python_compat/` | — | Basic coverage |
| Dato DataFrame lib | `dato/src/*.mn` | 2,637 | read_csv, groupby, agg, join, reshape |

**Key insight:** `mapanare build file.py` should *already* work via the
`_read_source()` chain. The transpiler intercepts `.py`, produces `.mn`
source, and feeds it to the normal compile pipeline. The question is
what breaks in practice.

---

## The 5 phases

### Phase 1 — Verify existing pipeline (~1 hour)

Test what works today without any code changes:

```bash
# Does the transpiler produce valid .mn?
mapanare transpile examples/transpile/fibonacci.py -o /tmp/fib.mn
cat /tmp/fib.mn

# Does build accept .py directly?
mapanare build examples/transpile/fibonacci.py -o /tmp/fib
/tmp/fib

# Does run work?
mapanare run examples/transpile/primes.py

# Try all 4 example scripts
for f in examples/transpile/*.py; do
    echo "=== $f ==="
    mapanare build "$f" -o "/tmp/$(basename $f .py)" 2>&1 && echo OK || echo FAIL
done
```

Record what works, what fails, and why. Categorize failures:
- **Transpiler bug**: produces invalid .mn syntax
- **Type inference gap**: transpiled code has unresolved types
- **Feature gap**: uses Python feature the transpiler doesn't handle
- **Compile bug**: valid .mn but LLVM emitter chokes

### Phase 2 — Fix pipeline breaks (~2-4 hours)

Fix whatever Phase 1 finds. Expected issues:

1. **Type annotation gaps** — Python transpiler may not infer all types;
   the `.mn` output may need type annotations the LLVM emitter requires.
   Fix in `from_python.py` type inference or add a post-pass.

2. **`main()` wrapping** — top-level Python statements need wrapping in
   `fn main()`. The transpiler may or may not do this. Verify at
   `from_python.py` and fix if missing.

3. **`range()` lowering** — `for i in range(n)` must produce a bounded
   `mien` (while) loop. Check if the transpiler handles this.

4. **List comprehensions** — may not be supported. If so, document the
   limitation, don't block the release.

5. **String methods** — `from_python.py` maps `upper`→`to_upper`,
   `find`→`index_of`, etc. Verify the mappings compile.

6. **`print()` with multiple args** — `print(a, b)` must map to
   `print(str(a) + " " + str(b))` or equivalent.

### Phase 3 — Build the demo scripts (~2-3 hours)

Create 3 compelling demo scripts in `examples/python_to_native/`:

**Demo 1: `row_processing.py`** (the pitch script)
```python
# Pure Python row-by-row data processing — the pattern every
# data scientist writes and every Python expert warns against.
# Mapanare compiles it to native code, 50-100x faster.

def process_sales(records):
    results = []
    for record in records:
        region = record[0]
        revenue = record[1]
        cost = record[2]
        if region == "LATAM":
            margin = (revenue - cost) / revenue
            if margin > 0.3:
                results.append(margin)
    return results

# Generate 1M synthetic records
data = []
for i in range(1000000):
    region = "LATAM" if i % 3 == 0 else "NA"
    data.append([region, 100.0 + (i % 50), 40.0 + (i % 30)])

result = process_sales(data)
print(len(result))
```

**Demo 2: `string_processing.py`** (ETL cleaning)
```python
def clean_records(lines):
    cleaned = []
    for line in lines:
        parts = line.split(",")
        if len(parts) >= 3:
            name = parts[0].strip().upper()
            value = int(parts[1].strip())
            if value > 0:
                cleaned.append(name + ":" + str(value))
    return cleaned
```

**Demo 3: `numerical_compute.py`** (Monte Carlo / math)
```python
def estimate_pi(n):
    inside = 0
    x = 0.1
    y = 0.7
    for i in range(n):
        # Simple PRNG (not real randomness, but deterministic)
        x = (x * 1103515245 + 12345) % 2147483648
        y = (y * 1103515245 + 12345) % 2147483648
        xn = x / 2147483648.0
        yn = y / 2147483648.0
        if xn * xn + yn * yn <= 1.0:
            inside += 1
    return 4.0 * inside / n

print(estimate_pi(10000000))
```

Each demo must:
- Be valid Python that runs with `python3`
- Compile with `mapanare build demo.py -o demo`
- Produce identical output in both
- Be large enough to measure (>100ms in Python)

### Phase 4 — Benchmark and measure (~1-2 hours)

Create `benchmarks/python_vs_native/run_benchmarks.py`:

```bash
# For each demo script:
# 1. Run with python3, measure wall time (10 runs, median)
# 2. Compile with mapanare build, run binary, measure wall time
# 3. Report speedup factor

python3 benchmarks/python_vs_native/run_benchmarks.py
```

Expected output:
```
Python vs Mapanare-compiled (median of 10 runs)

  row_processing    Python: 2,340 ms    Mapanare: 23 ms    Speedup: 102x
  string_processing Python: 890 ms      Mapanare: 12 ms    Speedup: 74x
  numerical_compute Python: 4,560 ms    Mapanare: 31 ms    Speedup: 147x
```

Also benchmark against the existing examples:
```
  fibonacci(35)     Python: 3,200 ms    Mapanare: 19 ms    Speedup: 168x
  primes(500000)    Python: 8,900 ms    Mapanare: 52 ms    Speedup: 171x
```

### Phase 5 — Document and polish (~1 hour)

1. **README section** — "Write Python, Compile Native" with the
   benchmark table and a 3-line quickstart:
   ```bash
   pip install mapanare
   mapanare build your_script.py -o your_script
   ./your_script   # 100x faster
   ```

2. **`docs/guides/python_to_native.md`** — full guide with:
   - What Python features are supported
   - What isn't supported (classes, imports, decorators — document honestly)
   - The benchmark methodology
   - FAQ: "Why not just use Cython/PyPy/Numba?"

3. **Limitations doc** — honest list of what doesn't transpile:
   - `import` statements (stdlib not mapped)
   - Class inheritance
   - Decorators
   - `try`/`except`
   - `*args`, `**kwargs`
   - List comprehensions (if not fixed in Phase 2)
   - Anything that calls C extensions (numpy, pandas)

---

## What this release does NOT do

- Replace pandas/numpy (that's a Dato integration story, v5.x)
- Support `import` of arbitrary Python packages
- Handle classes with inheritance
- Guarantee 100% Python compatibility (it's a transpiler, not CPython)
- Change the compiler or runtime (transpiler + docs + benchmarks only)

---

## Exit criteria

| # | Check | Required |
|---|---|---|
| 1 | `mapanare build examples/transpile/fibonacci.py -o /tmp/fib && /tmp/fib` works | yes |
| 2 | `mapanare build examples/transpile/primes.py -o /tmp/primes && /tmp/primes` works | yes |
| 3 | At least 2 of 3 new demo scripts compile + run + match Python output | yes |
| 4 | Benchmark report with measured speedup factors | yes |
| 5 | `docs/guides/python_to_native.md` written | yes |
| 6 | Limitations documented honestly | yes |
| 7 | All existing tests still pass (`pytest tests/ --ignore=tests/bootstrap -q`) | yes |
| 8 | No regressions in golden tests (54/66) | yes |

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Transpiler produces .mn that doesn't compile | high | medium | Fix in Phase 2; scope to pure-compute Python (no imports/classes) |
| Type inference insufficient for LLVM backend | medium | high | Add explicit type annotations in post-pass; document as "type-annotated Python compiles best" |
| Demo scripts too simple to be compelling | low | high | Use 1M-row data processing — nobody dismisses a 100x speedup on real-looking code |
| Speedup is less than 50x on some demos | medium | low | Honest numbers. Even 30x is compelling. The fib benchmark already shows 168x. |
| `range()` or list ops don't lower correctly | medium | medium | These are the core Python patterns; fix is highest priority in Phase 2 |

---

## After v4.155.0

The demo opens three paths:

1. **Blog post**: "I took my Python script and made it 100x faster
   without changing a line" — HN / Reddit / Twitter material
2. **Dato integration** (v5.x): `import dato as pd` in transpiled code
   maps to the native DataFrame lib — the pandas replacement story
3. **Type inference improvements** (v5.x): infer more types from Python
   context so fewer annotations are needed
