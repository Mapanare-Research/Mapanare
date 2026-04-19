# Write Python, Compile Native

Mapanare can compile your existing Python scripts to native binaries, running **33x-239x faster** than CPython with zero code changes.

## Quickstart

```bash
mapanare build your_script.py -o your_script
./your_script
```

That's it. Mapanare transpiles your Python to Mapanare source, compiles it through the LLVM backend, and links a native binary.

## What Python features work

The transpiler handles the core compute patterns that dominate data processing and numerical code:

- **Functions** with type annotations (`def foo(n: int) -> int:`)
- **Functions without annotations** — types are inferred from usage
- **Loops** — `for i in range(n)`, `while` loops, `break`, `continue`
- **Conditionals** — `if`/`elif`/`else`, ternary expressions
- **Arithmetic** — `+`, `-`, `*`, `/`, `//`, `%`, `**`, bitwise ops
- **Comparisons** — `==`, `!=`, `<`, `<=`, `>`, `>=`
- **Augmented assignment** — `+=`, `-=`, `*=`, etc.
- **Type conversions** — `int()`, `float()`, `str()`
- **Print** — `print(value)`, including multi-argument `print(a, b, c)`
- **String methods** — `.upper()`, `.lower()`, `.strip()`, `.split()`, `.replace()`, etc.
- **Booleans** — `True`, `False`, `and`, `or`, `not`
- **f-strings** — translated to string concatenation

## What doesn't work (yet)

- **`import` statements** — stdlib and third-party imports are not mapped
- **Classes with inheritance** — class definitions transpile to structs, but no inheritance
- **Decorators** — ignored
- **`try`/`except`** — exception handling is commented out (use Result types in Mapanare)
- **`*args`, `**kwargs`** — variadic arguments not supported
- **List comprehensions** — rewrite as `for` loops
- **Generators** — `yield` not supported
- **`with` statements** — context managers not supported
- **Anything that calls C extensions** — numpy, pandas, etc. cannot be transpiled

## Tips for best results

1. **Add type annotations.** The transpiler infers types from usage, but explicit annotations (`def foo(n: int) -> int:`) produce the best results.

2. **Use simple data structures.** `int`, `float`, `bool`, `str` work best. Lists of primitives work. Nested data structures may need adjustments.

3. **Avoid imports.** Write self-contained scripts. If you need math functions, use arithmetic instead of `import math`.

4. **Rewrite comprehensions as loops.** `[x*2 for x in range(n)]` should become a `for` loop with `.append()`.

5. **Keep it pure-compute.** The transpiler excels at numerical code, data processing loops, and algorithm implementations — exactly the code that's slowest in Python.

## Benchmark results

Median of 10 runs per script on Linux x86_64:

| Script | Python 3 | Mapanare (native) | Speedup |
|---|---:|---:|---:|
| numerical_compute (10M iterations) | 2,557 ms | 10.7 ms | **239x** |
| collatz_explorer (5M range) | 30,636 ms | 446.8 ms | **69x** |
| prime_sieve (2M range) | 3,832 ms | 108.8 ms | **35x** |
| fibonacci(40) | 8,220 ms | 193.7 ms | **42x** |
| primes (500K) | 995 ms | 30.6 ms | **33x** |

All outputs verified identical between Python and compiled binary.

## FAQ

**Why not Cython?** Cython requires rewriting Python with type declarations in a different syntax (`.pyx` files), plus a C compiler toolchain, plus understanding Cython's type system. Mapanare compiles unmodified `.py` files.

**Why not PyPy?** PyPy is a JIT — it needs warm-up time and doesn't produce standalone binaries. Mapanare produces a native binary you can deploy anywhere, with no runtime dependency.

**Why not Numba?** Numba requires `@jit` decorators and only works on numerical code using numpy arrays. Mapanare handles general Python (loops, strings, conditionals) and produces a standalone binary.

**What about accuracy?** Integer arithmetic is identical (64-bit). Float arithmetic may differ in the last few decimal places due to different ordering of operations, but the results are numerically equivalent.

## See also

- Demo scripts: `examples/python_to_native/`
- Existing transpile examples: `examples/transpile/`
- Benchmark harness: `benchmarks/python_vs_native/run_benchmarks.py`
