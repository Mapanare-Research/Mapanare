"""Benchmark: Recursive Fibonacci — Python baseline."""

import time


def fib(n: int) -> int:
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)


if __name__ == "__main__":
    start = time.perf_counter()
    result = fib(35)
    elapsed = time.perf_counter() - start
    print(f"fib(35) = {result}")
    print(f"Time: {elapsed:.4f}s")
