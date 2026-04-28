"""Tests for the self-hosted main.mn module.

Validates that main.mn:
1. Wires the full pipeline: parse → check → lower → emit_llvm
2. Imports all required modules including lower.mn
3. Has compile and compile_and_print functions
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SELF_DIR = REPO_ROOT / "mapanare" / "self"
MAIN_MN = SELF_DIR / "main.mn"
VERSION_FILE = REPO_ROOT / "VERSION"
MNC_STAGE1 = SELF_DIR / "mnc-stage1"


@pytest.fixture
def main_mn_source() -> str:
    """Read the main.mn source file."""
    assert MAIN_MN.exists(), f"main.mn not found at {MAIN_MN}"
    return MAIN_MN.read_text(encoding="utf-8")


class TestMainMnStructure:
    """Validate the structure of main.mn."""

    def test_file_exists(self) -> None:
        assert MAIN_MN.exists()

    def test_imports_all_modules(self, main_mn_source: str) -> None:
        """main.mn should import all 5 compiler modules."""
        assert "import self::ast" in main_mn_source
        assert "import self::parser" in main_mn_source
        assert "import self::semantic" in main_mn_source
        assert "import self::lower" in main_mn_source
        assert "import self::emit_llvm" in main_mn_source

    def test_has_compile_fn(self, main_mn_source: str) -> None:
        assert "fn compile(source: String, filename: String) -> CompileResult" in main_mn_source

    def test_has_compile_and_print_fn(self, main_mn_source: str) -> None:
        assert "fn compile_and_print" in main_mn_source

    def test_has_version_fn(self, main_mn_source: str) -> None:
        assert "fn version()" in main_mn_source

    def test_has_format_error_fn(self, main_mn_source: str) -> None:
        assert "fn format_error" in main_mn_source


class TestMainMnPipeline:
    """Validate the pipeline wiring in main.mn."""

    def test_calls_lower(self, main_mn_source: str) -> None:
        """compile() should call lower() to produce MIR."""
        assert "lower(resolved" in main_mn_source or "lower(program" in main_mn_source

    def test_calls_emit(self, main_mn_source: str) -> None:
        """compile() should call emit_mir_module()."""
        assert "emit_mir_module(" in main_mn_source

    def test_pipeline_order(self, main_mn_source: str) -> None:
        """Pipeline should be: parse → resolve → lower → emit_mir_module."""
        src = main_mn_source
        parse_pos = src.index("parse(source")
        lower_pos = src.index("lower(")
        emit_pos = src.index("emit_mir_module(")
        assert parse_pos < lower_pos < emit_pos

    def test_version_calls_runtime_export(self, main_mn_source: str) -> None:
        """``version()`` must call ``__mn_version_string()`` (v5.9.0 DX.2).

        Replaced the v4.28.0 ``__MN_VERSION__`` build-time placeholder with
        a C-runtime export baked at C-compile time via ``-DMAPANARE_VERSION``.
        Same dispatch shape as ``__mn_host_is_windows()`` (v5.8.6 We.1).
        Guards against any edit that re-introduces a literal in the body.
        """
        assert "__mn_version_string()" in main_mn_source, (
            "version() must call __mn_version_string() — the build pipeline "
            "bakes the version into the C runtime via -DMAPANARE_VERSION. "
            "A literal would re-open the staleness class that v4.28.0 closed "
            "and v5.9.0 DX.2 made structural."
        )

    def test_version_string_is_not_hardcoded(self, main_mn_source: str) -> None:
        """No hardcoded ``mapanare X.Y.Z`` literal may appear in ``version()``.

        Guards against a future edit that replaces the runtime call with a
        fresh hardcoded literal.
        """
        import re

        # Split the source into lines and only look at the body of version().
        lines = main_mn_source.splitlines()
        in_version_fn = False
        hardcoded_hits: list[tuple[int, str]] = []
        for i, line in enumerate(lines, start=1):
            if "fn version()" in line:
                in_version_fn = True
                continue
            if in_version_fn:
                if line.strip().startswith("}"):
                    break
                if re.search(r'"mapanare\s+\d+\.\d+\.\d+"', line):
                    hardcoded_hits.append((i, line.strip()))
        assert not hardcoded_hits, (
            f"Hardcoded version literal found in version() body: {hardcoded_hits}. "
            f"Call __mn_version_string() and let the C runtime supply the value."
        )

    @pytest.mark.skipif(
        not MNC_STAGE1.exists(),
        reason="mnc-stage1 not built; run scripts/build_stage1.py first",
    )
    def test_mnc_stage1_version_matches_version_file(self) -> None:
        """Built ``mnc-stage1`` must print the live VERSION from ``mnc version``.

        This is the real regression test: it runs the binary and asserts
        the output. If this fails, either the build-time substitution is
        broken or the placeholder didn't land in the IR.
        """
        expected_version = VERSION_FILE.read_text(encoding="utf-8").strip()
        result = subprocess.run(
            [str(MNC_STAGE1), "version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"mnc-stage1 version failed:\n"
            f"  stdout: {result.stdout}\n"
            f"  stderr: {result.stderr}"
        )
        expected_line = f"mapanare {expected_version}"
        assert expected_line in result.stdout, (
            f"Expected {expected_line!r} in mnc-stage1 output.\n"
            f"Got: {result.stdout!r}\n"
            f"VERSION file: {expected_version!r}"
        )


class TestMainMnCompileResult:
    """Validate the CompileResult struct."""

    def test_has_compile_result(self, main_mn_source: str) -> None:
        assert "struct CompileResult" in main_mn_source

    def test_compile_result_has_success(self, main_mn_source: str) -> None:
        assert "success: Bool" in main_mn_source

    def test_compile_result_has_ir_text(self, main_mn_source: str) -> None:
        assert "ir_text: String" in main_mn_source

    def test_compile_result_has_errors(self, main_mn_source: str) -> None:
        assert "errors: List<SemanticError>" in main_mn_source
