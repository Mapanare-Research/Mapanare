"""Benchmark: Stream Pipeline Processing (1M items) -- Python baseline.

Same workload as Mapanare: for each x in 0..1M, compute x*3,
keep if even, accumulate sum.

Uses intermediate lists (typical Python pattern) to show
memory overhead vs Mapanare's single-pass approach.
"""

import time


def stream_pipeline(n: int) -> int:
    # Typical Python: create intermediate list, then filter, then sum
    mapped = [x * 3 for x in range(n)]
    total = sum(x for x in mapped if x % 2 == 0)
    return total


if __name__ == "__main__":
    start = time.perf_counter()
    result = stream_pipeline(1_000_000)
    elapsed = time.perf_counter() - start
    print(f"result = {result}")
    print(f"Time: {elapsed:.4f}s")
