"""Benchmark: Prime sieve — Python equivalent."""

def is_prime(n):
    if n < 2: return False
    if n < 4: return True
    if n % 2 == 0: return False
    d = 3
    while d * d <= n:
        if n % d == 0: return False
        d += 2
    return True

def main():
    count = 0
    for i in range(100_000):
        if is_prime(i):
            count += 1
    print(f"primes = {count}")

if __name__ == "__main__":
    main()
