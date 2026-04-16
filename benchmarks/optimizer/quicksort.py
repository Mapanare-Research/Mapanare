"""Benchmark 2: Quicksort — Python equivalent."""


def lcg_next(seed):
    return (seed * 1103515245 + 12345) % 2147483648


def partition(arr, lo, hi):
    pivot = arr[hi]
    i = lo
    for j in range(lo, hi):
        if arr[j] < pivot:
            arr[i], arr[j] = arr[j], arr[i]
            i += 1
    arr[i], arr[hi] = arr[hi], arr[i]
    return i


def qsort(arr, lo, hi):
    if lo < hi:
        p = partition(arr, lo, hi)
        qsort(arr, lo, p - 1)
        qsort(arr, p + 1, hi)


import sys

sys.setrecursionlimit(100000)

arr = []
seed = 42
for _ in range(10000):
    seed = lcg_next(seed)
    arr.append(seed % 100000)

qsort(arr, 0, 9999)
checksum = sum(arr[:10])
print(f"checksum = {checksum}")
