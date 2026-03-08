"""Benchmark: Matrix Multiplication — Python baseline (no numpy)."""

import time


def matrix_mul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    n = len(a)
    c = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            s = 0.0
            for k in range(n):
                s += a[i][k] * b[k][j]
            c[i][j] = s
    return c


if __name__ == "__main__":
    size = 100
    a = [[1.0] * size for _ in range(size)]
    b = [[2.0] * size for _ in range(size)]

    start = time.perf_counter()
    c = matrix_mul(a, b)
    elapsed = time.perf_counter() - start

    print(f"c[0][0] = {c[0][0]}")
    print(f"Time: {elapsed:.4f}s")
