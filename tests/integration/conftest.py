"""Integration test fixtures — full LLVM pipeline for Mapanare golden tests.

Pipeline stages:
  emit-llvm → llvm-as → opt -O2 → llc -filetype=obj → clang link → execute
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
GOLDEN_DIR = ROOT / "tests" / "golden"
EXPECTED_DIR = ROOT / "tests" / "integration" / "expected"
RUNTIME_DIR = ROOT / "runtime" / "native"
RUNTIME_LIB = RUNTIME_DIR / "libmapanare_rt.a"

STAGES = ("emit", "llvm-as", "opt", "llc", "link", "run", "stdout")


@dataclass
class PipelineResult:
    """Result of running a golden test through the full pipeline."""

    source: pathlib.Path
    stage_reached: str = "none"
    exit_code: int = -1
    stdout: str = ""
    stderr: str = ""
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.stage_reached == "stdout"


def _run(cmd: list[str], timeout: int = 30, **kwargs) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        **kwargs,
    )


def _ensure_runtime() -> None:
    """Build the C runtime if the static library doesn't exist."""
    if RUNTIME_LIB.exists():
        return
    result = _run(["make", "build-rt"], cwd=str(ROOT), timeout=120)
    if result.returncode != 0:
        pytest.skip(f"Cannot build C runtime: {result.stderr[:200]}")


def _find_tool(name: str) -> str:
    """Find an LLVM/clang tool, trying versioned names on CI."""
    for candidate in [name, f"{name}-18", f"{name}-17", f"{name}-16"]:
        path = shutil.which(candidate)
        if path:
            return path
    pytest.skip(f"{name} not found on PATH")
    return ""  # unreachable


def compile_mn(source: pathlib.Path, out_dir: pathlib.Path) -> pathlib.Path:
    """Emit LLVM IR from a .mn source file via the Python bootstrap."""
    ll_path = out_dir / f"{source.stem}.ll"
    result = _run(
        ["python3", "-m", "mapanare", "emit-llvm", str(source), "-o", str(ll_path)],
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"emit-llvm failed:\n{result.stderr[:500]}")
    return ll_path


def assemble_ll(ll_path: pathlib.Path, out_dir: pathlib.Path) -> pathlib.Path:
    """Validate and assemble .ll to .bc via llvm-as."""
    bc_path = out_dir / f"{ll_path.stem}.bc"
    tool = _find_tool("llvm-as")
    result = _run([tool, str(ll_path), "-o", str(bc_path)])
    if result.returncode != 0:
        raise RuntimeError(f"llvm-as failed:\n{result.stderr[:500]}")
    return bc_path


def optimize_bc(bc_path: pathlib.Path, out_dir: pathlib.Path) -> pathlib.Path:
    """Run opt -O2 on a .bc file."""
    opt_path = out_dir / f"{bc_path.stem}.opt.bc"
    tool = _find_tool("opt")
    result = _run([tool, "-O2", str(bc_path), "-o", str(opt_path)])
    if result.returncode != 0:
        raise RuntimeError(f"opt -O2 failed:\n{result.stderr[:500]}")
    return opt_path


def codegen_obj(bc_path: pathlib.Path, out_dir: pathlib.Path) -> pathlib.Path:
    """Generate an object file via llc."""
    obj_path = out_dir / f"{bc_path.stem}.o"
    tool = _find_tool("llc")
    result = _run(
        [tool, "-filetype=obj", "-relocation-model=pic", str(bc_path), "-o", str(obj_path)]
    )
    if result.returncode != 0:
        raise RuntimeError(f"llc failed:\n{result.stderr[:500]}")
    return obj_path


def link_binary(obj_path: pathlib.Path, out_dir: pathlib.Path) -> pathlib.Path:
    """Link object file against the C runtime to produce an executable."""
    _ensure_runtime()
    binary_path = out_dir / obj_path.stem
    tool = _find_tool("clang")
    # v5.8.8: macOS needs Metal + Foundation frameworks linked. The
    # runtime archive includes ``mapanare_metal.o`` (Da.2 fix to
    # Makefile build-rt), and that .o calls into the Metal /
    # Foundation Objective-C runtimes — without -framework here the
    # link fails with "Undefined symbols for architecture arm64:
    # _mapanare_metal_available" etc.
    extra_link: list[str] = []
    if sys.platform == "darwin":
        extra_link += [
            "-framework",
            "Metal",
            "-framework",
            "Foundation",
            "-fobjc-arc",
        ]
    result = _run(
        [
            tool,
            str(obj_path),
            str(RUNTIME_LIB),
            "-lm",
            "-lpthread",
            "-ldl",
            *extra_link,
            "-o",
            str(binary_path),
        ]
    )
    if result.returncode != 0:
        raise RuntimeError(f"link failed:\n{result.stderr[:500]}")
    return binary_path


def run_binary(
    binary_path: pathlib.Path, timeout: int = 10, stdin_data: str | None = None
) -> tuple[int, str, str]:
    """Execute a compiled binary and return (exit_code, stdout, stderr)."""
    result = _run(
        [str(binary_path)],
        timeout=timeout,
        input=stdin_data,
    )
    return result.returncode, result.stdout, result.stderr


def full_pipeline(
    source: pathlib.Path,
    out_dir: pathlib.Path,
    stop_after: str | None = None,
    stdin_data: str | None = None,
) -> PipelineResult:
    """Run a .mn source through the full LLVM pipeline.

    stop_after: one of STAGES to halt early (e.g. "llvm-as" to only validate IR).
    """
    pr = PipelineResult(source=source)

    stages = [
        ("emit", lambda: compile_mn(source, out_dir)),
        ("llvm-as", lambda: assemble_ll(ll, out_dir)),
        ("opt", lambda: optimize_bc(bc, out_dir)),
        ("llc", lambda: codegen_obj(opt_bc, out_dir)),
        ("link", lambda: link_binary(obj, out_dir)),
        ("run", lambda: run_binary(binary, stdin_data=stdin_data)),
    ]

    ll = bc = opt_bc = obj = binary = None

    for stage_name, stage_fn in stages:
        try:
            result = stage_fn()
            if stage_name == "emit":
                ll = result
            elif stage_name == "llvm-as":
                bc = result
            elif stage_name == "opt":
                opt_bc = result
            elif stage_name == "llc":
                obj = result
            elif stage_name == "link":
                binary = result
            elif stage_name == "run":
                pr.exit_code, pr.stdout, pr.stderr = result
            pr.stage_reached = stage_name
        except (RuntimeError, subprocess.TimeoutExpired, OSError) as exc:
            pr.errors[stage_name] = str(exc)[:300]
            return pr

        if stop_after and stage_name == stop_after:
            return pr

    # Check stdout match
    expected_file = EXPECTED_DIR / f"{source.stem}.expected"
    if expected_file.exists():
        expected = expected_file.read_text()
        if pr.stdout == expected:
            pr.stage_reached = "stdout"
        else:
            pr.errors["stdout"] = (
                f"Output mismatch.\n"
                f"Expected:\n{textwrap.indent(expected[:200], '  ')}\n"
                f"Got:\n{textwrap.indent(pr.stdout[:200], '  ')}"
            )
    else:
        # No expected file — pass if binary ran successfully
        if pr.exit_code == 0:
            pr.stage_reached = "stdout"

    return pr


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--integration-stage",
        default=None,
        choices=list(STAGES),
        help="Stop pipeline after this stage (e.g. --integration-stage=llvm-as)",
    )


@pytest.fixture
def integration_stage(request: pytest.FixtureRequest) -> str | None:
    return request.config.getoption("--integration-stage")


@pytest.fixture
def pipeline_tmpdir(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path


def discover_golden_tests() -> list[pathlib.Path]:
    """Find all .mn files in tests/golden/."""
    tests = sorted(GOLDEN_DIR.glob("*.mn"))
    return tests


# Tests that require external resources (network, GPU, stdin, filesystem)
# and cannot run in a sandboxed CI environment.
EXTERNAL_RESOURCE_TESTS = {
    "34_file_io",  # filesystem operations
    "35_stdin",  # reads from stdin
    "36_crypto",  # may need runtime crypto support
    "37_regex",  # may need runtime regex support
    "38_http",  # network access
    "39_gpu_detect",  # GPU hardware
    "40_gpu_tensor",  # GPU hardware
}
