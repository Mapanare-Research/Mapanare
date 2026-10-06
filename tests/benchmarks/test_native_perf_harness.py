"""Benchmark failures must not appear as fast, correct measurements."""

import subprocess
import sys

import pytest

from benchmarks.compile_time import measure
from benchmarks.cross_language.run_benchmarks import (
    LangResult,
    SingleRun,
    _compute_geomean_ratios,
)


def test_failed_sample_disqualifies_result():
    result = LangResult(
        "example",
        "Mapanare O2",
        runs=[
            SingleRun(wall_time_s=0.1, output="checksum = 42"),
            SingleRun(output="TIMEOUT"),
        ],
    )
    result.aggregate("checksum = 42")
    assert not result.correct


def test_checksum_prefix_is_not_a_match():
    result = LangResult(
        "example",
        "Mapanare O2",
        runs=[
            SingleRun(wall_time_s=0.1, output="checksum = 420"),
        ],
    )
    result.aggregate("checksum = 42")
    assert not result.correct


def test_ratios_use_actual_label_and_only_correct_runs():
    entries = [
        {"benchmark": "good", "language": "Mapanare O2", "wall_median_ms": 2, "correct": True},
        {"benchmark": "good", "language": "C", "wall_median_ms": 1, "correct": True},
        {"benchmark": "bad", "language": "Mapanare O2", "wall_median_ms": 0.01, "correct": False},
        {"benchmark": "bad", "language": "C", "wall_median_ms": 1, "correct": True},
    ]
    assert _compute_geomean_ratios({"results": entries}) == {"C": 2.0}


def test_compile_measurement_rejects_failure():
    with pytest.raises(subprocess.CalledProcessError):
        measure([sys.executable, "-c", "raise SystemExit(3)"], 2)
