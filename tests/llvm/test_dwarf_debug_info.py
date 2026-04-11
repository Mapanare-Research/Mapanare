"""Tests for the ``-g`` / ``--debug`` CLI flag and MIR source-span threading.

v4.29.0 (Path B — strike claim)
--------------------------------

Prior to v4.29.0 this file had six ``@pytest.mark.skip`` classes covering
roughly thirty tests for DWARF debug info emission (``!DICompileUnit``,
``!DISubprogram``, ``!DILocation``, ``!DILocalVariable``, ``DICompositeType``,
etc.). Those tests had been silently skipped since v4.2.0 — the ``debug=True``
flag was wired through the pipeline but the ``LLVMTextEmitter`` never emitted
a single DWARF metadata node.

The v4.26.0 seven-reviewer panel flagged this as a core hollow-feature case.
v4.29.0 strikes the claim: DWARF debug info emission is deferred to v5.x
(see ``docs/SPEC.md`` §21.3 and ``docs/roadmap/ROADMAP.md``). The 30-plus
skipped tests have been deleted because they test a feature that does not
exist; when DWARF lands, new tests will be written against the shipping
implementation rather than resurrected from a speculative skeleton.

What this file still covers
---------------------------

1. ``TestDebugCLIFlag`` — the ``-g`` / ``--debug`` flag is still accepted
   for forward compatibility. v4.29.0 made ``_resolve_debug`` print a
   stderr warning every time it is used, which is verified here.
2. ``TestNoDebugWhenDisabled`` — the current behaviour (no DWARF at all)
   is pinned: when ``debug=False`` the emitter must not leak any
   ``!DICompileUnit`` / ``!DISubprogram`` / ``!DILocation`` / ``!dbg``
   metadata. This is the regression gate that will fail the day DWARF
   lands without tests being updated alongside.
3. ``TestMIRSpanThreading`` — the MIR already threads source spans
   (``SourceSpan`` dataclass and per-instruction ``.span`` field). That
   plumbing is the foundation future DWARF will build on; the tests
   confirm it still works.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

try:
    from llvmlite import ir as llvm_ir  # noqa: F401

    HAS_LLVMLITE = True
except ImportError:
    HAS_LLVMLITE = False

from mapanare.lower import lower
from mapanare.mir import SourceSpan
from mapanare.parser import parse
from mapanare.semantic import check_or_raise

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _emit_without_debug(source: str, filename: str = "test.mn") -> str:
    """Parse, lower, and emit LLVM IR with debug info disabled."""
    from mapanare.emit_llvm_text import LLVMTextEmitter

    ast = parse(source, filename=filename)
    check_or_raise(ast, filename=filename)
    mir = lower(ast, module_name="test", source_file=filename, source_directory="/test")
    emitter = LLVMTextEmitter(module_name="test", debug=False)
    return emitter.emit(mir)


# ---------------------------------------------------------------------------
# -g / --debug CLI flag
# ---------------------------------------------------------------------------


class TestDebugCLIFlag:
    """Verify the ``-g`` / ``--debug`` flag is still accepted."""

    def test_debug_flag_exists(self) -> None:
        """The ``-g`` flag must be accepted by the argparse parser."""

        import argparse

        from mapanare.cli import _add_debug_flag

        parser = argparse.ArgumentParser()
        _add_debug_flag(parser)
        ns = parser.parse_args(["-g"])
        assert ns.debug is True

    def test_debug_flag_long_form(self) -> None:
        import argparse

        from mapanare.cli import _add_debug_flag

        parser = argparse.ArgumentParser()
        _add_debug_flag(parser)
        ns = parser.parse_args(["--debug"])
        assert ns.debug is True

    def test_no_debug_by_default(self) -> None:
        import argparse

        from mapanare.cli import _add_debug_flag

        parser = argparse.ArgumentParser()
        _add_debug_flag(parser)
        ns = parser.parse_args([])
        assert ns.debug is False


class TestDebugFlagDeferred:
    """v4.29.0: using ``-g`` prints a stderr warning naming v5.x."""

    def _run_with_g(self) -> subprocess.CompletedProcess[str]:
        fd = tempfile.NamedTemporaryFile(mode="w", suffix=".mn", delete=False, encoding="utf-8")
        fd.write('fn main() {\n    print("hello")\n}\n')
        fd.close()
        out = tempfile.NamedTemporaryFile(suffix=".ll", delete=False).name
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "mapanare.cli",
                "emit-llvm",
                fd.name,
                "-o",
                out,
                "-g",
            ],
            capture_output=True,
            text=True,
            cwd=str(_PROJECT_ROOT),
        )

    def test_warning_mentions_noop(self) -> None:
        result = self._run_with_g()
        assert "no-op" in result.stderr.lower()

    def test_warning_names_tracking_version(self) -> None:
        """The warning must say where the real feature is tracked."""
        result = self._run_with_g()
        assert "v5" in result.stderr.lower()

    def test_warning_written_to_stderr_not_stdout(self) -> None:
        result = self._run_with_g()
        assert "debug" in result.stderr.lower()
        # stdout can be empty or contain the IR; the warning must not leak
        # into it (would corrupt piped output).
        assert "debug info" not in result.stdout.lower()


# ---------------------------------------------------------------------------
# Regression gate: no DWARF metadata when debug is off
# ---------------------------------------------------------------------------


class TestNoDebugWhenDisabled:
    """The emitter must not leak DWARF metadata without ``-g``.

    This is the regression gate: the day DWARF emission lands, whoever
    wires it in will trip this test, which forces them to update the
    file rather than silently enable DWARF for every build.
    """

    def test_no_di_compile_unit(self) -> None:
        ir = _emit_without_debug("fn main() {}")
        assert "!DICompileUnit" not in ir

    def test_no_di_subprogram(self) -> None:
        ir = _emit_without_debug("fn main() {}")
        assert "!DISubprogram" not in ir

    def test_no_di_location(self) -> None:
        ir = _emit_without_debug("fn main() { let x: Int = 42 }")
        assert "!DILocation" not in ir

    def test_no_dbg_attachments(self) -> None:
        ir = _emit_without_debug("fn main() {}")
        for line in ir.split("\n"):
            if line.strip().startswith("!"):
                continue
            assert "!dbg" not in line, f"Unexpected !dbg on: {line}"


# ---------------------------------------------------------------------------
# MIR source-span threading (foundation for future DWARF)
# ---------------------------------------------------------------------------


class TestMIRSpanThreading:
    """Verify AST spans are preserved through MIR lowering."""

    def test_source_span_on_module(self) -> None:
        ast = parse("fn main() {}", filename="test.mn")
        check_or_raise(ast, filename="test.mn")
        mir = lower(ast, module_name="test", source_file="test.mn", source_directory="/src")
        assert mir.source_file == "test.mn"
        assert mir.source_directory == "/src"

    def test_source_line_on_function(self) -> None:
        ast = parse("fn main() {}", filename="test.mn")
        check_or_raise(ast, filename="test.mn")
        mir = lower(ast, module_name="test", source_file="test.mn")
        fn = mir.functions[0]
        assert fn.source_line == 1
        assert fn.source_file == "test.mn"

    def test_span_on_instructions(self) -> None:
        source = "fn main() { let x: Int = 42 }"
        ast = parse(source, filename="test.mn")
        check_or_raise(ast, filename="test.mn")
        mir = lower(ast, module_name="test", source_file="test.mn")
        fn = mir.functions[0]
        has_span = any(inst.span is not None for bb in fn.blocks for inst in bb.instructions)
        assert has_span, "No instructions have source spans"

    def test_source_span_dataclass(self) -> None:
        span = SourceSpan(line=10, column=5, end_line=10, end_column=20)
        assert span.line == 10
        assert span.column == 5
        assert span.end_line == 10
        assert span.end_column == 20


# ``pytest`` and ``HAS_LLVMLITE`` are retained for backward compatibility
# with other modules that may import from this file in the future.
__all__ = [
    "HAS_LLVMLITE",
    "TestDebugCLIFlag",
    "TestDebugFlagDeferred",
    "TestNoDebugWhenDisabled",
    "TestMIRSpanThreading",
]
_unused = pytest  # keep the import used
