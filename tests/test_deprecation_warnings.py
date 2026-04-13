"""v4.57.0: Deprecation warning tests for the Python emitter removal (v4.58.0).

Verifies that all public entry points of the deprecated Python transpiler
backend emit DeprecationWarning, that CLI commands print stderr warnings,
and that the migration guide exists. Also confirms the emitter still works
(regression: warnings must not break functionality).
"""

from __future__ import annotations

import os
import subprocess
import sys
import warnings

import pytest

# ---------------------------------------------------------------------------
# Phase 1: Library-level warnings
# ---------------------------------------------------------------------------


class TestPythonEmitterInstantiationWarns:
    """PythonMIREmitter.__init__ must emit DeprecationWarning."""

    def test_instantiation_warns(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            from mapanare.emit_python_mir import PythonMIREmitter

            PythonMIREmitter()

        deprecation_msgs = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        assert any(
            "v4.58.0" in str(w.message) for w in deprecation_msgs
        ), "PythonMIREmitter() must warn about v4.58.0 removal"

    def test_emit_warns(self) -> None:
        """PythonMIREmitter.emit() must emit DeprecationWarning."""
        from mapanare.lower import lower as build_mir
        from mapanare.parser import parse
        from mapanare.semantic import check_or_raise

        source = 'fn main() { print("hello") }'
        ast = parse(source, filename="<test>")
        check_or_raise(ast, filename="<test>")
        mir_module = build_mir(ast, module_name="test")

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            from mapanare.emit_python_mir import PythonMIREmitter

            emitter = PythonMIREmitter()
            emitter.emit(mir_module)

        emit_warnings = [
            w
            for w in caught
            if issubclass(w.category, DeprecationWarning) and "emit()" in str(w.message)
        ]
        assert len(emit_warnings) >= 1, "PythonMIREmitter.emit() must warn about v4.58.0"

    def test_import_warns(self) -> None:
        """Importing mapanare.emit_python_mir must emit DeprecationWarning."""
        # Use subprocess to get a clean import (module-level warning fires once)
        result = subprocess.run(
            [
                sys.executable,
                "-W",
                "all::DeprecationWarning",
                "-c",
                "import mapanare.emit_python_mir",
            ],
            capture_output=True,
            text=True,
        )
        assert (
            "v4.58.0" in result.stderr
        ), f"import-time warning must mention v4.58.0, got: {result.stderr!r}"


# ---------------------------------------------------------------------------
# Phase 2: CLI warnings
# ---------------------------------------------------------------------------


class TestCLIWarnings:
    """CLI commands that use the Python backend must print stderr warnings."""

    @pytest.fixture()
    def sample_source(self, tmp_path: pytest.TempPathFactory) -> str:
        src = tmp_path / "hello.mn"
        src.write_text('fn main() { print("hello") }')
        return str(src)

    def test_compile_warns_stderr(self, sample_source: str) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "mapanare", "compile", sample_source],
            capture_output=True,
            text=True,
        )
        assert (
            "v4.58.0" in result.stderr
        ), f"'mapanare compile' must warn about v4.58.0 on stderr, got: {result.stderr!r}"


# ---------------------------------------------------------------------------
# Phase 3: Migration guide exists
# ---------------------------------------------------------------------------


class TestMigrationGuide:
    """The migration guide must exist at the documented path."""

    def test_migration_guide_exists(self) -> None:
        guide_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "docs",
            "migration",
            "v4.57-to-v4.58.md",
        )
        assert os.path.isfile(guide_path), f"Migration guide not found at {guide_path}"

    def test_migration_guide_mentions_key_topics(self) -> None:
        guide_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "docs",
            "migration",
            "v4.57-to-v4.58.md",
        )
        content = open(guide_path, encoding="utf-8").read()
        assert "PythonMIREmitter" in content
        assert "mapanare build" in content
        assert "mapanare emit-llvm" in content
        assert "v4.58.0" in content
        assert "v4.59.0" in content  # llvmlite timeline mention


# ---------------------------------------------------------------------------
# Phase 5 / Exit criterion 7: Python emitter still works (regression test)
# ---------------------------------------------------------------------------


class TestPythonEmitterStillWorks:
    """The Python emitter must still produce valid output despite the warnings."""

    def test_emitter_produces_valid_python(self) -> None:
        from mapanare.lower import lower as build_mir
        from mapanare.parser import parse
        from mapanare.semantic import check_or_raise

        source = 'fn main() { print("hello from deprecation test") }'
        ast = parse(source, filename="<test>")
        check_or_raise(ast, filename="<test>")
        mir_module = build_mir(ast, module_name="test")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from mapanare.emit_python_mir import PythonMIREmitter

            emitter = PythonMIREmitter()
            python_code = emitter.emit(mir_module)

        # The output must be valid Python that can be compiled
        compile(python_code, "<test>", "exec")

        # The output must contain the expected print call
        assert "hello from deprecation test" in python_code
