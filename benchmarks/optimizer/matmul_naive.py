"""Benchmark 3: Naive matrix multiply — Python equivalent."""

n = 64
n2 = n * n
a = [(i * 3 + 7) % 100 for i in range(n2)]
b = [(i * 5 + 13) % 100 for i in range(n2)]
c = [0] * n2

for i in range(n):
    for j in range(n):
        s = 0
        for k in range(n):
            s += a[i * n + k] * b[k * n + j]
        c[i * n + j] = s

cs = c[0] + c[n - 1] + c[(n - 1) * n] + c[n2 - 1]
print(f"checksum = {cs}")
