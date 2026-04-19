# Prime counting via trial division — count primes up to 2M.
# Valid Python 3. Compile with: mapanare build prime_sieve.py -o primes


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d = d + 2
    return True


def count_primes(limit: int) -> int:
    count = 0
    n = 2
    while n < limit:
        if is_prime(n):
            count = count + 1
        n = n + 1
    return count


total = count_primes(2000000)
print(total)
