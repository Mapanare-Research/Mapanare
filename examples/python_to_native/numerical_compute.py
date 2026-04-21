# Monte Carlo pi estimation — 10M iterations of pure math.
# Valid Python 3. Compile with: mapanare build numerical_compute.py -o pi
#
# Deterministic PRNG so output matches across runs.
# Prints the count of points inside the circle (integer) for exact match.


def estimate_pi(n: int) -> int:
    inside = 0
    sx = 12345
    sy = 67890
    i = 0
    while i < n:
        sx = (sx * 1103515245 + 12345) % 2147483648
        sy = (sy * 1103515245 + 12345) % 2147483648
        xn = float(sx) / 2147483648.0
        yn = float(sy) / 2147483648.0
        if xn * xn + yn * yn <= 1.0:
            inside = inside + 1
        i = i + 1
    return inside


count = estimate_pi(10000000)
print(count)
