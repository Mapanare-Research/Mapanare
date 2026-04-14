"""Tests for the mapa CLI (Phase 2.5)."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from mapanare.cli import __version__, _format_mapanare, build_parser

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _run_cli(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run mapa CLI as a subprocess."""
    return subprocess.run(
        [sys.executable, "-m", "mapanare.cli", *args],
        capture_output=True,
        text=True,
        cwd=cwd or str(_PROJECT_ROOT),
    )


def _write_ax(content: str, suffix: str = ".mn") -> str:
    """Write Mapanare source to a temp file, return path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


HELLO_AX = """\
fn main() {
    print("hello mapanare")
}
"""

SIMPLE_FN = """\
fn add(a: Int, b: Int) -> Int {
    return a + b
}

fn main() {
    let result = add(1, 2)
    print(result)
}
"""

BAD_SYNTAX = """\
fn {{{ broken
"""

BAD_SEMANTIC = """\
fn main() {
    let x = undefined_var
}
"""


# ---------------------------------------------------------------------------
# --version and --help
# ---------------------------------------------------------------------------


class TestVersionAndHelp:
    def test_version_flag(self) -> None:
        result = _run_cli("--version")
        assert result.returncode == 0
        assert __version__ in result.stdout

    def test_help_flag(self) -> None:
        result = _run_cli("--help")
        assert result.returncode == 0
        assert "mapanare" in result.stdout
        assert "compile" in result.stdout
        assert "check" in result.stdout
        assert "run" in result.stdout
        assert "fmt" in result.stdout

    def test_no_args_shows_help(self) -> None:
        result = _run_cli()
        assert result.returncode == 1
        assert "mapanare" in result.stdout or "mapanare" in result.stderr


# ---------------------------------------------------------------------------
# mapa compile (REMOVED in v3.x — Python emitter retired; transpile is the
# inverse direction .py/.php → .mn). The five TestCompile cases that
# round-tripped Mapanare to Python output have been deleted in v4.121.0
# because they exercised a feature that no longer exists. The negative-path
# behaviour (missing file, syntax error) and source-validity behaviour
# remain covered by TestCheck below; the CLI surface is covered by
# TestArgparse and TestOptLevelFlags.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# mapa check
# ---------------------------------------------------------------------------


class TestCheck:
    def test_check_valid_file(self) -> None:
        src = _write_ax(HELLO_AX)
        try:
            result = _run_cli("check", src)
            assert result.returncode == 0
            assert "OK" in result.stdout
        finally:
            os.unlink(src)

    def test_check_syntax_error(self) -> None:
        src = _write_ax(BAD_SYNTAX)
        try:
            result = _run_cli("check", src)
            assert result.returncode == 1
        finally:
            os.unlink(src)

    def test_check_does_not_emit_file(self) -> None:
        src = _write_ax(HELLO_AX)
        try:
            _run_cli("check", src)
            out_path = src.replace(".mn", ".py")
            assert not os.path.isfile(out_path)
        finally:
            os.unlink(src)

    def test_check_missing_file(self) -> None:
        result = _run_cli("check", "/nonexistent/file.mn")
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# mapa run
# ---------------------------------------------------------------------------


class TestRun:
    def test_run_hello(self) -> None:
        src = _write_ax(HELLO_AX)
        try:
            result = _run_cli("run", src)
            assert result.returncode == 0
            assert "hello mapanare" in result.stdout
        finally:
            os.unlink(src)

    def test_run_syntax_error(self) -> None:
        src = _write_ax(BAD_SYNTAX)
        try:
            result = _run_cli("run", src)
            assert result.returncode == 1
        finally:
            os.unlink(src)

    def test_run_missing_file(self) -> None:
        result = _run_cli("run", "/nonexistent/file.mn")
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# mapa fmt
# ---------------------------------------------------------------------------


class TestFmt:
    def test_format_removes_trailing_whitespace(self) -> None:
        result = _format_mapanare("fn main() {   \n    print(1)  \n}\n")
        lines = result.split("\n")
        for line in lines:
            if line:  # skip empty lines
                assert line == line.rstrip()

    def test_format_normalizes_blank_lines(self) -> None:
        result = _format_mapanare("fn a() {\n}\n\n\n\n\nfn b() {\n}\n")
        # No more than 2 consecutive blank lines
        count = 0
        for line in result.split("\n"):
            if line == "":
                count += 1
            else:
                assert count <= 2
                count = 0

    def test_format_tabs_to_spaces(self) -> None:
        result = _format_mapanare("fn main() {\n\tprint(1)\n}\n")
        assert "\t" not in result
        assert "    print(1)" in result

    def test_format_single_trailing_newline(self) -> None:
        result = _format_mapanare("fn main() {\n}\n\n\n")
        assert result.endswith("\n")
        assert not result.endswith("\n\n")

    def test_fmt_command_writes_file(self) -> None:
        src = _write_ax("fn main() {   \n    print(1)  \n}\n")
        try:
            result = _run_cli("fmt", src)
            assert result.returncode == 0
            content = Path(src).read_text(encoding="utf-8")
            for line in content.split("\n"):
                if line:
                    assert line == line.rstrip()
        finally:
            os.unlink(src)

    def test_fmt_syntax_error(self) -> None:
        src = _write_ax(BAD_SYNTAX)
        try:
            result = _run_cli("fmt", src)
            assert result.returncode == 1
        finally:
            os.unlink(src)

    def test_fmt_missing_file(self) -> None:
        result = _run_cli("fmt", "/nonexistent/file.mn")
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# argparse structure
# ---------------------------------------------------------------------------


class TestArgparse:
    def test_build_parser_returns_parser(self) -> None:
        parser = build_parser()
        assert parser.prog == "mapanare"

    def test_compile_subcommand_parsed(self) -> None:
        """v4.121.0: ``compile`` was removed; ``build`` is the .mn → native
        binary command. The argparse contract under test is that the source
        positional binds and the output flag is unset by default."""
        parser = build_parser()
        args = parser.parse_args(["build", "test.mn"])
        assert args.command == "build"
        assert args.source == "test.mn"
        assert args.o is None

    def test_compile_with_output(self) -> None:
        """v4.121.0: ``-o`` argparse contract on the surviving ``build``
        subcommand (was previously asserted on the removed ``compile``)."""
        parser = build_parser()
        args = parser.parse_args(["build", "test.mn", "-o", "out.bin"])
        assert args.o == "out.bin"

    def test_check_subcommand_parsed(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["check", "test.mn"])
        assert args.command == "check"

    def test_run_subcommand_parsed(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["run", "test.mn"])
        assert args.command == "run"

    def test_fmt_subcommand_parsed(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["fmt", "test.mn"])
        assert args.command == "fmt"

    def test_init_subcommand_parsed(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["init"])
        assert args.command == "init"
        assert args.path == "."

    def test_init_with_path(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["init", "myproject"])
        assert args.path == "myproject"

    def test_init_with_name(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["init", "--name", "cool"])
        assert args.name == "cool"

    def test_install_subcommand_parsed(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["install", "mypkg"])
        assert args.command == "install"
        assert args.package == "mypkg"

    def test_install_with_git(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["install", "mypkg", "--git", "https://example.com/pkg.git"])
        assert args.git == "https://example.com/pkg.git"

    def test_install_with_branch(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["install", "mypkg", "--branch", "dev"])
        assert args.branch == "dev"

    def test_publish_subcommand_parsed(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["publish"])
        assert args.command == "publish"


# ---------------------------------------------------------------------------
# mapa init (integration)
# ---------------------------------------------------------------------------


class TestInitCommand:
    def test_init_creates_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = os.path.join(tmpdir, "testproj")
            result = _run_cli("init", project_dir, "--name", "testproj")
            assert result.returncode == 0
            assert "initialized" in result.stdout
            assert os.path.isfile(os.path.join(project_dir, "mapanare.toml"))
            assert os.path.isfile(os.path.join(project_dir, "main.mn"))


# ---------------------------------------------------------------------------
# mapa publish (stub)
# ---------------------------------------------------------------------------


class TestPublishCommand:
    def test_publish_requires_manifest(self) -> None:
        result = _run_cli("publish")
        assert result.returncode == 1
        assert "mapanare.toml" in result.stderr.lower() or "error" in result.stderr.lower()


# ---------------------------------------------------------------------------
# Optimization level flags (-O0 through -O3)
# ---------------------------------------------------------------------------


class TestOptLevelFlags:
    """v4.121.0: argparse-level coverage of ``-O0``..``-O3`` on the
    surviving subcommands. Was previously asserted on the removed
    ``compile`` subcommand; rewritten against ``build`` (the .mn →
    native binary command, which exposes the same opt-level flags) and
    ``run``. The two ``test_compile_with_o*_runs`` cases that
    subprocessed ``mapanare compile <file> -O*`` were dropped because
    they exercised a removed command; equivalent end-to-end -O coverage
    is provided by ``tests/integration/test_pipeline_hardening.py`` and
    the cross-language benchmark harness."""

    def test_compile_default_opt_level(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["build", "test.mn"])
        assert args.opt_level == 2

    def test_compile_o0(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["build", "test.mn", "-O0"])
        assert args.opt_level == 0

    def test_compile_o1(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["build", "test.mn", "-O1"])
        assert args.opt_level == 1

    def test_compile_o2(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["build", "test.mn", "-O2"])
        assert args.opt_level == 2

    def test_compile_o3(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["build", "test.mn", "-O3"])
        assert args.opt_level == 3

    def test_run_o0(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["run", "test.mn", "-O0"])
        assert args.opt_level == 0

    def test_run_o3(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["run", "test.mn", "-O3"])
        assert args.opt_level == 3

    def test_compile_with_o0_runs(self) -> None:
        """v4.121.0: was a subprocess-running compile test; now an
        argparse-level smoke check that ``build … -O0`` parses to opt
        level 0 with the source positional bound. Spawning a real build
        requires clang on PATH and is covered by the integration harness."""
        parser = build_parser()
        args = parser.parse_args(["build", "x.mn", "-O0"])
        assert args.opt_level == 0
        assert args.source == "x.mn"

    def test_compile_with_o3_runs(self) -> None:
        """v4.121.0: argparse smoke for ``build … -O3`` (see sibling
        ``test_compile_with_o0_runs`` for the rationale)."""
        parser = build_parser()
        args = parser.parse_args(["build", "x.mn", "-O3"])
        assert args.opt_level == 3
        assert args.source == "x.mn"
