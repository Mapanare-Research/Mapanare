# Collatz conjecture explorer — finds the starting number under 5M
# with the longest hailstone sequence.
# Valid Python 3. Compile with: mapanare build collatz_explorer.py -o collatz


def collatz_length(start: int) -> int:
    n = start
    steps = 0
    while n != 1:
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
        steps = steps + 1
    return steps


def find_longest(limit: int) -> int:
    best_n = 1
    best_len = 0
    n = 2
    while n < limit:
        length = collatz_length(n)
        if length > best_len:
            best_len = length
            best_n = n
        n = n + 1
    return best_n


winner = find_longest(5000000)
print(winner)
print(collatz_length(winner))
