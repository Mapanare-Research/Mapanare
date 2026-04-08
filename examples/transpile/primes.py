def is_prime(n: int) -> bool:
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


def count_primes(limit: int) -> int:
    count = 0
    n = 2
    while n < limit:
        if is_prime(n):
            count += 1
        n += 1
    return count


result = count_primes(500000)
print(result)
