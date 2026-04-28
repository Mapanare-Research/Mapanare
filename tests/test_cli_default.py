"""Smoke test: native CLI default-command behavior.

v5.9.1 DX.5. Verifies the v5.9.0 -> v5.9.1 behavior change:

  pre-v5.9.1: ``mnc file.mn`` emits LLVM IR
  v5.9.1+:    ``mnc file.mn`` runs the program; ``mnc emit-llvm`` emits IR

Catches drift between the dispatch in ``mapanare/self/main.mn::mn_main``
and the documented user-facing surface.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MNC = REPO_ROOT / "mapanare" / "self" / "mnc-stage1"

HELLO_MN = 'fn main() { print("hello dx5") }\n'


@pytest.fixture
def hello_mn_path(tmp_path: Path) -> Path:
    p = tmp_path / "dx5_hello.mn"
    p.write_text(HELLO_MN)
    return p


@pytest.mark.skipif(not MNC.exists(), reason="mnc-stage1 not built")
def test_default_runs_program(hello_mn_path: Path) -> None:
    r = subprocess.run([str(MNC), str(hello_mn_path)], capture_output=True, text=True)
    assert r.returncode == 0, f"exit={r.returncode}; stdout={r.stdout!r}; stderr={r.stderr!r}"
    assert "hello dx5" in r.stdout
    # IR markers should NOT be on stdout
    assert "target triple" not in r.stdout
    assert "target datalayout" not in r.stdout
    assert "define i64" not in r.stdout


@pytest.mark.skipif(not MNC.exists(), reason="mnc-stage1 not built")
def test_default_silent_after_v5_11_0(hello_mn_path: Path) -> None:
    """v5.11.0 Pk.2: the v5.9.1 implicit-run deprecation note was removed
    after the v5.10.0 soak window."""
    r = subprocess.run([str(MNC), str(hello_mn_path)], capture_output=True, text=True)
    assert "now runs the program" not in r.stderr
    assert "implicit 'run'" not in r.stderr


@pytest.mark.skipif(not MNC.exists(), reason="mnc-stage1 not built")
def test_emit_llvm_subcommand_to_stdout(hello_mn_path: Path) -> None:
    r = subprocess.run([str(MNC), "emit-llvm", str(hello_mn_path)], capture_output=True, text=True)
    assert r.returncode == 0
    assert "target triple" in r.stdout or "target datalayout" in r.stdout
    assert "@main" in r.stdout or "@mn_main" in r.stdout
    # Deprecation note must NOT appear on the explicit path
    assert "implicit 'run'" not in r.stderr
    assert "now runs the program" not in r.stderr


@pytest.mark.skipif(not MNC.exists(), reason="mnc-stage1 not built")
def test_emit_llvm_to_file(hello_mn_path: Path, tmp_path: Path) -> None:
    out = tmp_path / "dx5_hello.ll"
    r = subprocess.run(
        [str(MNC), "emit-llvm", str(hello_mn_path), "-o", str(out)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    assert out.exists()
    content = out.read_text()
    assert "target triple" in content or "target datalayout" in content
    # stdout should be silent when -o is used
    assert r.stdout.strip() == ""


@pytest.mark.skipif(not MNC.exists(), reason="mnc-stage1 not built")
def test_non_mn_file_errors_with_hint(tmp_path: Path) -> None:
    nonmn = tmp_path / "Makefile"
    nonmn.write_text("all:\n\techo hi\n")
    r = subprocess.run([str(MNC), str(nonmn)], capture_output=True, text=True)
    assert r.returncode != 0
    assert "not a .mn file" in r.stderr
    assert "emit-llvm" in r.stderr  # migration hint surfaced


@pytest.mark.skipif(not MNC.exists(), reason="mnc-stage1 not built")
def test_help_lists_emit_llvm() -> None:
    r = subprocess.run([str(MNC), "--help"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "emit-llvm" in r.stdout
