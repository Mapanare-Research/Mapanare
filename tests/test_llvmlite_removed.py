"""v4.59.0 regression gate: verify llvmlite JIT is fully removed.

These tests ensure ``mapanare/jit.py`` is deleted, ``llvmlite`` is not
a dependency, and the ``jit`` CLI subcommand no longer exists.
"""

from __future__ import annotations

import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestLlvmliteRemoved:
    """llvmlite must not be a project dependency."""

    def test_jit_module_absent(self) -> None:
        path = os.path.join(REPO_ROOT, "mapanare", "jit.py")
        assert not os.path.exists(path), f"jit.py still exists at {path}"

    def test_import_raises_importerror(self) -> None:
        result = subprocess.run(
            [sys.executable, "-c", "import mapanare.jit"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "import mapanare.jit should fail"

    def test_llvmlite_not_in_pyproject(self) -> None:
        toml_path = os.path.join(REPO_ROOT, "pyproject.toml")
        content = open(toml_path, encoding="utf-8").read()
        assert "llvmlite" not in content, "llvmlite still referenced in pyproject.toml"

    def test_no_llvmlite_import_in_mapanare(self) -> None:
        result = subprocess.run(
            ["grep", "-rn", "import llvmlite", os.path.join(REPO_ROOT, "mapanare")],
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip() == "", f"Stale llvmlite imports in mapanare/:\n{result.stdout}"


class TestCLINoJit:
    """CLI must not expose jit or --release."""

    def test_no_jit_subcommand(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "mapanare", "jit", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "'mapanare jit' should not exist"
