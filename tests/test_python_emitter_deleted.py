"""v4.58.0 regression gate: verify the Python emitter is fully removed.

These tests ensure no code in the tree still references the deleted
``mapanare/emit_python_mir.py`` module. If any of these fail, the deletion
was incomplete.
"""

from __future__ import annotations

import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestPythonEmitterDeleted:
    """The Python emitter file must not exist and must not be importable."""

    def test_emit_python_mir_file_absent(self) -> None:
        path = os.path.join(REPO_ROOT, "mapanare", "emit_python_mir.py")
        assert not os.path.exists(path), f"emit_python_mir.py still exists at {path}"

    def test_import_raises_importerror(self) -> None:
        result = subprocess.run(
            [sys.executable, "-c", "import mapanare.emit_python_mir"],
            capture_output=True,
            text=True,
        )
        assert (
            result.returncode != 0
        ), "import mapanare.emit_python_mir should fail with ImportError"

    def test_no_references_in_mapanare_package(self) -> None:
        """grep mapanare/*.py for stale references."""
        result = subprocess.run(
            [
                "grep",
                "-rn",
                "emit_python_mir\\|PythonMIREmitter",
                os.path.join(REPO_ROOT, "mapanare"),
            ],
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip() == "", f"Stale references found in mapanare/:\n{result.stdout}"

    def test_no_references_in_tests(self) -> None:
        """grep tests/*.py for stale references."""
        result = subprocess.run(
            [
                "grep",
                "-rn",
                "emit_python_mir\\|PythonMIREmitter\\|_compile_source",
                os.path.join(REPO_ROOT, "tests"),
                "--include=*.py",
            ],
            capture_output=True,
            text=True,
        )
        # Allow this very file to reference the strings
        lines = [
            ln
            for ln in result.stdout.strip().split("\n")
            if ln and "test_python_emitter_deleted.py" not in ln
        ]
        assert len(lines) == 0, f"Stale references found in tests/:\n{''.join(lines)}"


class TestCLINoPythonBackend:
    """CLI must not expose any Python backend commands."""

    def test_no_compile_subcommand(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "mapanare", "compile", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "'mapanare compile' should not exist"

    def test_no_repl_subcommand(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "mapanare", "repl", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "'mapanare repl' should not exist"
