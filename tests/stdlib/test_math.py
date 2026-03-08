"""Tests for mapanare.math -- numeric and statistical utilities."""

from __future__ import annotations

import math

import pytest

from stdlib.math import (
    INF,
    NAN,
    PI,
    TAU,
    E,
    abs,
    acos,
    asin,
    atan,
    atan2,
    ceil,
    clamp,
    cos,
    degrees,
    floor,
    lerp,
    log,
    log2,
    log10,
    max_val,
    mean,
    median,
    min_val,
    percentile,
    pow,
    radians,
    remap,
    round_to,
    sin,
    sqrt,
    stddev,
    sum,
    tan,
    variance,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_pi(self) -> None:
        assert PI == math.pi

    def test_e(self) -> None:
        assert E == math.e

    def test_tau(self) -> None:
        assert TAU == math.tau

    def test_inf(self) -> None:
        assert INF == math.inf

    def test_nan(self) -> None:
        assert math.isnan(NAN)


# ---------------------------------------------------------------------------
# Basic numeric functions
# ---------------------------------------------------------------------------


class TestBasicNumeric:
    def test_abs_positive(self) -> None:
        assert abs(5.0) == 5.0

    def test_abs_negative(self) -> None:
        assert abs(-3.5) == 3.5

    def test_clamp_within(self) -> None:
        assert clamp(5.0, 0.0, 10.0) == 5.0

    def test_clamp_below(self) -> None:
        assert clamp(-1.0, 0.0, 10.0) == 0.0

    def test_clamp_above(self) -> None:
        assert clamp(15.0, 0.0, 10.0) == 10.0

    def test_lerp_zero(self) -> None:
        assert lerp(0.0, 10.0, 0.0) == 0.0

    def test_lerp_one(self) -> None:
        assert lerp(0.0, 10.0, 1.0) == 10.0

    def test_lerp_half(self) -> None:
        assert lerp(0.0, 10.0, 0.5) == 5.0

    def test_remap(self) -> None:
        assert remap(5.0, 0.0, 10.0, 0.0, 100.0) == 50.0


# ---------------------------------------------------------------------------
# Power and roots
# ---------------------------------------------------------------------------


class TestPowerRoots:
    def test_sqrt(self) -> None:
        assert sqrt(9.0) == 3.0

    def test_pow(self) -> None:
        assert pow(2.0, 10.0) == 1024.0

    def test_log_natural(self) -> None:
        assert math.isclose(log(E), 1.0)

    def test_log_base(self) -> None:
        assert math.isclose(log(100.0, 10.0), 2.0)

    def test_log2(self) -> None:
        assert math.isclose(log2(8.0), 3.0)

    def test_log10(self) -> None:
        assert math.isclose(log10(1000.0), 3.0)


# ---------------------------------------------------------------------------
# Trigonometry
# ---------------------------------------------------------------------------


class TestTrig:
    def test_sin_zero(self) -> None:
        assert sin(0.0) == 0.0

    def test_cos_zero(self) -> None:
        assert cos(0.0) == 1.0

    def test_tan_zero(self) -> None:
        assert tan(0.0) == 0.0

    def test_asin(self) -> None:
        assert math.isclose(asin(1.0), math.pi / 2)

    def test_acos(self) -> None:
        assert math.isclose(acos(1.0), 0.0)

    def test_atan(self) -> None:
        assert math.isclose(atan(1.0), math.pi / 4)

    def test_atan2(self) -> None:
        assert math.isclose(atan2(1.0, 1.0), math.pi / 4)

    def test_degrees(self) -> None:
        assert math.isclose(degrees(math.pi), 180.0)

    def test_radians(self) -> None:
        assert math.isclose(radians(180.0), math.pi)


# ---------------------------------------------------------------------------
# Rounding
# ---------------------------------------------------------------------------


class TestRounding:
    def test_floor(self) -> None:
        assert floor(3.7) == 3

    def test_ceil(self) -> None:
        assert ceil(3.2) == 4

    def test_round_to_zero(self) -> None:
        assert round_to(3.14159, 0) == 3.0

    def test_round_to_two(self) -> None:
        assert round_to(3.14159, 2) == 3.14


# ---------------------------------------------------------------------------
# Statistical utilities
# ---------------------------------------------------------------------------


class TestStatistics:
    def test_sum(self) -> None:
        assert sum([1.0, 2.0, 3.0]) == 6.0

    def test_sum_empty(self) -> None:
        assert sum([]) == 0.0

    def test_mean(self) -> None:
        assert mean([1.0, 2.0, 3.0]) == 2.0

    def test_mean_empty(self) -> None:
        with pytest.raises(ValueError):
            mean([])

    def test_median_odd(self) -> None:
        assert median([3.0, 1.0, 2.0]) == 2.0

    def test_median_even(self) -> None:
        assert median([1.0, 2.0, 3.0, 4.0]) == 2.5

    def test_median_empty(self) -> None:
        with pytest.raises(ValueError):
            median([])

    def test_variance_population(self) -> None:
        assert math.isclose(variance([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]), 4.0)

    def test_variance_sample(self) -> None:
        v = variance([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0], population=False)
        assert math.isclose(v, 4.571428571428571)

    def test_stddev(self) -> None:
        assert math.isclose(stddev([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]), 2.0)

    def test_min_val(self) -> None:
        assert min_val([5.0, 1.0, 3.0]) == 1.0

    def test_min_val_empty(self) -> None:
        with pytest.raises(ValueError):
            min_val([])

    def test_max_val(self) -> None:
        assert max_val([5.0, 1.0, 3.0]) == 5.0

    def test_max_val_empty(self) -> None:
        with pytest.raises(ValueError):
            max_val([])

    def test_percentile_50(self) -> None:
        assert percentile([1.0, 2.0, 3.0, 4.0, 5.0], 50) == 3.0

    def test_percentile_0(self) -> None:
        assert percentile([1.0, 2.0, 3.0], 0) == 1.0

    def test_percentile_100(self) -> None:
        assert percentile([1.0, 2.0, 3.0], 100) == 3.0

    def test_percentile_invalid(self) -> None:
        with pytest.raises(ValueError):
            percentile([1.0], 101)
