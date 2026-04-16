"""Benchmark: Closure-like pattern — Python equivalent."""


def compute(a, b, c, x):
    return x + a + b + c


def main():
    s = 0
    for i in range(10_000):
        a, b, c = i, i * 2, i * 3
        s += compute(a, b, c, i)
    print(f"checksum = {s}")


if __name__ == "__main__":
    main()
