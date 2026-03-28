"""mapanare.math -- numeric and statistical utilities."""

from __future__ import annotations

import math as _math
from typing import Sequence

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PI: float = _math.pi
E: float = _math.e
TAU: float = _math.tau
INF: float = _math.inf
NAN: float = _math.nan


# ---------------------------------------------------------------------------
# Basic numeric functions
# ---------------------------------------------------------------------------


def abs(x: float) -> float:
    """Absolute value."""
    return _math.fabs(x)


def clamp(x: float, lo: float, hi: float) -> float:
    """Clamp x to [lo, hi]."""
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b by factor t."""
    return a + (b - a) * t


def remap(x: float, in_lo: float, in_hi: float, out_lo: float, out_hi: float) -> float:
    """Remap x from [in_lo, in_hi] to [out_lo, out_hi]."""
    t = (x - in_lo) / (in_hi - in_lo)
    return lerp(out_lo, out_hi, t)


# ---------------------------------------------------------------------------
# Power and roots
# ---------------------------------------------------------------------------


def sqrt(x: float) -> float:
    return _math.sqrt(x)


def pow(base: float, exp: float) -> float:
    return _math.pow(base, exp)


def log(x: float, base: float | None = None) -> float:
    if base is not None:
        return _math.log(x, base)
    return _math.log(x)


def log2(x: float) -> float:
    return _math.log2(x)


def log10(x: float) -> float:
    return _math.log10(x)


# ---------------------------------------------------------------------------
# Trigonometry
# ---------------------------------------------------------------------------


def sin(x: float) -> float:
    return _math.sin(x)


def cos(x: float) -> float:
    return _math.cos(x)


def tan(x: float) -> float:
    return _math.tan(x)


def asin(x: float) -> float:
    return _math.asin(x)


def acos(x: float) -> float:
    return _math.acos(x)


def atan(x: float) -> float:
    return _math.atan(x)


def atan2(y: float, x: float) -> float:
    return _math.atan2(y, x)


def degrees(radians: float) -> float:
    return _math.degrees(radians)


def radians(degrees: float) -> float:
    return _math.radians(degrees)


# ---------------------------------------------------------------------------
# Rounding
# ---------------------------------------------------------------------------


def floor(x: float) -> int:
    return _math.floor(x)


def ceil(x: float) -> int:
    return _math.ceil(x)


def round_to(x: float, decimals: int = 0) -> float:
    """Round x to the given number of decimal places."""
    factor = 10.0**decimals
    return _math.floor(x * factor + 0.5) / factor


# ---------------------------------------------------------------------------
# Statistical utilities
# ---------------------------------------------------------------------------


def sum(values: Sequence[float]) -> float:
    """Sum of values."""
    total = 0.0
    for v in values:
        total += v
    return total


def mean(values: Sequence[float]) -> float:
    """Arithmetic mean."""
    n = len(values)
    if n == 0:
        raise ValueError("mean requires at least one value")
    return sum(values) / n


def median(values: Sequence[float]) -> float:
    """Median value."""
    n = len(values)
    if n == 0:
        raise ValueError("median requires at least one value")
    s = sorted(values)
    mid = n // 2
    if n % 2 == 0:
        return (s[mid - 1] + s[mid]) / 2.0
    return s[mid]


def variance(values: Sequence[float], population: bool = True) -> float:
    """Variance (population by default, sample if population=False)."""
    n = len(values)
    if n == 0:
        raise ValueError("variance requires at least one value")
    m = mean(values)
    ss = 0.0
    for v in values:
        ss += (v - m) ** 2
    divisor = n if population else (n - 1)
    if divisor == 0:
        raise ValueError("sample variance requires at least two values")
    return ss / divisor


def stddev(values: Sequence[float], population: bool = True) -> float:
    """Standard deviation."""
    return sqrt(variance(values, population=population))


def min_val(values: Sequence[float]) -> float:
    """Minimum value."""
    if len(values) == 0:
        raise ValueError("min_val requires at least one value")
    result = values[0]
    for v in values[1:]:
        if v < result:
            result = v
    return result


def max_val(values: Sequence[float]) -> float:
    """Maximum value."""
    if len(values) == 0:
        raise ValueError("max_val requires at least one value")
    result = values[0]
    for v in values[1:]:
        if v > result:
            result = v
    return result


def percentile(values: Sequence[float], p: float) -> float:
    """p-th percentile (0–100)."""
    if len(values) == 0:
        raise ValueError("percentile requires at least one value")
    if not 0 <= p <= 100:
        raise ValueError(f"percentile must be 0–100, got {p}")
    s = sorted(values)
    k = (p / 100.0) * (len(s) - 1)
    f = _math.floor(k)
    c = _math.ceil(k)
    if f == c:
        return s[int(k)]
    return s[f] * (c - k) + s[c] * (k - f)
