"""Retained aliases must keep live map counts bounded during long loops."""

import os
import subprocess
from pathlib import Path

import pytest

from mapanare.cli import _compile_to_llvm_ir
from mapanare.mir_opt import MIROptLevel
from tests.integration.test_retained_map_ownership import CASES
from tests.integration.test_retained_map_views import CASES as VIEW_CASES

pytest_plugins = ["tests.integration.test_map_return_ownership"]
ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("opt", list(MIROptLevel))
@pytest.mark.parametrize("case", ["retain-first", "saved-value", "saved-key"])
def test_live_map_count_stays_bounded(
    case: str, opt: MIROptLevel, instrumented_core: Path, tmp_path: Path
) -> None:
    source, expected = (CASES if case == "retain-first" else VIEW_CASES)[case]
    source = source.replace("0..100:", "0..100000:")
    ir = tmp_path / "bounded.ll"
    ir.write_text(_compile_to_llvm_ir(source, "bounded.mn", opt_level=opt))
    executable = tmp_path / "bounded"
    build = subprocess.run(
        [
            "clang",
            "-O1",
            "-g",
            "-fsanitize=address,undefined",
            "-fno-sanitize-recover=all",
            "-no-pie",
            "-I",
            str(ROOT / "runtime/native"),
            str(ir),
            str(instrumented_core),
            str(ROOT / "tests/native/fixtures/map_owner_bound.c"),
            "-Wl,--wrap=__mn_map_new",
            "-Wl,--wrap=__mn_map_retain",
            "-Wl,--wrap=__mn_map_free_deep",
            "-lm",
            "-lpthread",
            "-ldl",
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert build.returncode == 0, build.stderr
    result = subprocess.run(
        [str(executable)],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1"},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == expected
    assert "map peak:" in result.stderr
