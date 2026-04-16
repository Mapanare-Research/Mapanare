"""Benchmark 1: Recursive Fibonacci — Python equivalent."""

import sys

sys.setrecursionlimit(100000)


def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)


r = fib(35)
print(f"fib(35) = {r}")
