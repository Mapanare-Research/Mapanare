"""Tests for the built-in Mapanare test runner (mapanare test)."""

from __future__ import annotations

import os
import subprocess
import sys

from mapanare.ast_nodes import AssertStmt, BinaryExpr
from mapanare.parser import parse
from mapanare.semantic import check_or_raise
from mapanare.test_runner import (
    TestResult,
    TestSuite,
    discover_test_files,
    discover_tests,
    format_results,
    run_test_file,
    run_tests,
)

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
SAMPLE_FILE = os.path.join(FIXTURES, "sample_tests.mn")
FAILING_FILE = os.path.join(FIXTURES, "failing_test.mn")
NO_TESTS_FILE = os.path.join(FIXTURES, "no_tests.mn")


# ---------------------------------------------------------------------------
# Grammar / Parser: assert statement
# ---------------------------------------------------------------------------


class TestAssertParsing:
    def test_assert_basic(self) -> None:
        ast = parse("fn f() { assert 1 == 1 }", filename="test.mn")
        body = ast.definitions[0].body.stmts  # type: ignore[attr-defined]
        assert len(body) == 1
        stmt = body[0]
        assert isinstance(stmt, AssertStmt)
        assert isinstance(stmt.condition, BinaryExpr)
        assert stmt.message is None

    def test_assert_with_message(self) -> None:
        ast = parse('fn f() { assert 1 == 2, "msg" }', filename="test.mn")
        body = ast.definitions[0].body.stmts  # type: ignore[attr-defined]
        stmt = body[0]
        assert isinstance(stmt, AssertStmt)
        assert stmt.message is not None

    def test_assert_semantic_check(self) -> None:
        src = "fn f() { assert 1 + 1 == 2 }"
        ast = parse(src, filename="test.mn")
        check_or_raise(ast, filename="test.mn")  # Should not raise


# ---------------------------------------------------------------------------
# @test decorator recognition
# ---------------------------------------------------------------------------


class TestDecorator:
    def test_test_decorator_parsed(self) -> None:
        ast = parse("@test\nfn test_x() { assert 1 == 1 }", filename="test.mn")
        fn = ast.definitions[0]
        assert hasattr(fn, "decorators")
        assert any(d.name == "test" for d in fn.decorators)

    def test_test_decorator_semantic(self) -> None:
        src = "@test\nfn test_x() { assert 1 == 1 }"
        ast = parse(src, filename="test.mn")
        check_or_raise(ast, filename="test.mn")  # Should not raise


# ---------------------------------------------------------------------------
# Test discovery
# ---------------------------------------------------------------------------


class TestDiscovery:
    def test_discover_test_files_single(self) -> None:
        files = discover_test_files(SAMPLE_FILE)
        assert len(files) == 1
        assert files[0] == SAMPLE_FILE

    def test_discover_test_files_directory(self) -> None:
        files = discover_test_files(FIXTURES)
        assert len(files) >= 3
        assert all(f.endswith(".mn") for f in files)

    def test_discover_test_files_nonexistent(self) -> None:
        files = discover_test_files("nonexistent.mn")
        assert files == []

    def test_discover_tests_in_source(self) -> None:
        with open(SAMPLE_FILE, encoding="utf-8") as f:
            source = f.read()
        names = discover_tests(source, SAMPLE_FILE)
        assert "test_add" in names
        assert "test_comparison" in names
        assert "test_assert_message" in names
        assert "add" not in names  # Regular fn, not a test

    def test_discover_tests_no_tests(self) -> None:
        with open(NO_TESTS_FILE, encoding="utf-8") as f:
            source = f.read()
        names = discover_tests(source, NO_TESTS_FILE)
        assert names == []


# ---------------------------------------------------------------------------
# Test execution
# ---------------------------------------------------------------------------


class TestExecution:
    def test_run_passing_tests(self) -> None:
        results = run_test_file(SAMPLE_FILE)
        assert len(results) == 3
        assert all(r.passed for r in results)

    def test_run_failing_tests(self) -> None:
        results = run_test_file(FAILING_FILE)
        assert len(results) == 2
        passed = [r for r in results if r.passed]
        failed = [r for r in results if not r.passed]
        assert len(passed) == 1
        assert len(failed) == 1
        assert failed[0].name == "test_fail"
        assert "assertion failed" in failed[0].error

    def test_run_with_filter(self) -> None:
        results = run_test_file(SAMPLE_FILE, filter_pattern="test_add")
        assert len(results) == 1
        assert results[0].name == "test_add"
        assert results[0].passed

    def test_run_no_tests_file(self) -> None:
        results = run_test_file(NO_TESTS_FILE)
        assert results == []

    def test_run_tests_directory(self) -> None:
        suite = run_tests(FIXTURES)
        assert suite.total >= 5  # 3 passing + 2 mixed
        assert suite.passed >= 4
        assert suite.failed >= 1


# ---------------------------------------------------------------------------
# Test reporter
# ---------------------------------------------------------------------------


class TestReporter:
    def test_format_empty(self) -> None:
        suite = TestSuite()
        output = format_results(suite)
        assert "no tests found" in output

    def test_format_passing(self) -> None:
        suite = TestSuite(
            results=[TestResult(name="test_a", file="a.mn", passed=True, duration=0.001)],
            duration=0.01,
        )
        output = format_results(suite)
        assert "PASS" in output
        assert "test_a" in output
        assert "1 passed, 0 failed" in output

    def test_format_failing(self) -> None:
        suite = TestSuite(
            results=[
                TestResult(
                    name="test_b",
                    file="b.mn",
                    passed=False,
                    error="assertion failed",
                    duration=0.002,
                )
            ],
            duration=0.01,
        )
        output = format_results(suite)
        assert "FAIL" in output
        assert "assertion failed" in output
        assert "0 passed, 1 failed" in output


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------


class TestCLI:
    def test_cli_passing(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "mapanare.cli", "test", SAMPLE_FILE],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        )
        assert result.returncode == 0
        assert "3 passed" in result.stdout

    def test_cli_failing(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "mapanare.cli", "test", FAILING_FILE],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        )
        assert result.returncode == 1
        assert "1 failed" in result.stdout

    def test_cli_filter(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "mapanare.cli", "test", SAMPLE_FILE, "--filter", "test_add"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        )
        assert result.returncode == 0
        assert "1 passed" in result.stdout

    def test_cli_no_tests(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "mapanare.cli", "test", NO_TESTS_FILE],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        )
        assert result.returncode == 0
        assert "no tests found" in result.stdout


# ---------------------------------------------------------------------------
# Assert compilation (MIR path)
# ---------------------------------------------------------------------------


class TestAssertMIR:
    def test_assert_compiles_via_mir(self) -> None:
        from mapanare.emit_python_mir import PythonMIREmitter
        from mapanare.lower import lower as build_mir

        src = "fn f() { assert 1 == 1 }"
        ast = parse(src, filename="test.mn")
        check_or_raise(ast, filename="test.mn")
        mir = build_mir(ast, module_name="test")
        emitter = PythonMIREmitter()
        code = emitter.emit(mir)
        assert "AssertionError" in code or "assert" in code.lower()

    def test_assert_with_message_mir(self) -> None:
        from mapanare.emit_python_mir import PythonMIREmitter
        from mapanare.lower import lower as build_mir

        src = 'fn f() { assert 1 == 2, "bad" }'
        ast = parse(src, filename="test.mn")
        check_or_raise(ast, filename="test.mn")
        mir = build_mir(ast, module_name="test")
        emitter = PythonMIREmitter()
        code = emitter.emit(mir)
        assert "assertion failed" in code


# ---------------------------------------------------------------------------
# Assert compilation (legacy path)
# ---------------------------------------------------------------------------


class TestAssertLegacy:
    def test_assert_compiles_legacy(self) -> None:
        from mapanare.emit_python import PythonEmitter

        src = "fn f() { assert 1 == 1 }"
        ast = parse(src, filename="test.mn")
        check_or_raise(ast, filename="test.mn")
        emitter = PythonEmitter()
        code = emitter.emit(ast)
        assert "assert" in code

    def test_assert_with_message_legacy(self) -> None:
        from mapanare.emit_python import PythonEmitter

        src = 'fn f() { assert 1 == 2, "msg" }'
        ast = parse(src, filename="test.mn")
        check_or_raise(ast, filename="test.mn")
        emitter = PythonEmitter()
        code = emitter.emit(ast)
        assert "assert" in code
        assert "msg" in code
