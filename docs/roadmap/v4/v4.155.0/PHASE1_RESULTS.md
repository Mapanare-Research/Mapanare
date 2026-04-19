# Phase 1 Results — What Works Today

Tested at v4.155.0 before any code changes.

## Transpile (Python → .mn source)

| Script | transpile | valid .mn |
|---|---|---|
| fibonacci.py | OK | params untyped (`fn fibonacci(n)` — parser rejects) |
| collatz.py | OK | OK (has type annotations) |
| primes.py | OK | OK (has type annotations) |
| fibonacci_bench.py | OK | OK (has type annotations) |

## Build (LLVM backend → native binary)

| Script | compile (.o) | link | run | output matches python3 |
|---|---|---|---|---|
| fibonacci.py | FAIL (parse error: untyped param) | — | — | — |
| collatz.py | OK | FAIL (`__mn_intern_destroy` undefined) | — | — |
| primes.py | OK | FAIL (`__mn_intern_destroy` undefined) | — | — |
| fibonacci_bench.py | OK | FAIL (`__mn_intern_destroy` undefined) | — | — |

## Run (C backend)

| Script | run | output matches python3 |
|---|---|---|
| fibonacci.py | FAIL (parse error: untyped param) | — |
| collatz.py | OK | yes |
| primes.py | OK | yes |
| fibonacci_bench.py | OK | yes |

## Root causes

1. **TRANSPILER**: Untyped params when Python has no type annotations → `fn foo(n)` → parser error.
   - Fix: infer param types from body usage (arithmetic/comparison → Int/Float).

2. **COMPILE**: `cmd_build` linker doesn't include `libmapanare_rt.a`, `-lm`, `-lpthread`.
   - Fix: add runtime library to host linker commands (same pattern as `cmd_deploy`).

## After Phase 2 fixes

| Script | transpile | build | run | output matches |
|---|---|---|---|---|
| fibonacci.py | OK | OK | OK | yes |
| collatz.py | OK | OK | OK | yes |
| primes.py | OK | OK | OK | yes |
| fibonacci_bench.py | OK | OK | OK | yes |
