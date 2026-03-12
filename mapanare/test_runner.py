"""Built-in test runner for Mapanare.

Discovers and runs @test-decorated functions in .mn source files.
Usage: mapanare test [path] [--filter pattern]
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field

from mapanare.ast_nodes import Decorator, Definition, DocComment, ExportDef, FnDef
from mapanare.parser import ParseError, parse
from mapanare.semantic import SemanticErrors, check_or_raise


@dataclass
class TestResult:
    """Result of a single test execution."""

    name: str
    file: str
    passed: bool
    duration: float = 0.0
    error: str = ""


@dataclass
class TestSuite:
    """Collection of test results."""

    results: list[TestResult] = field(default_factory=list)
    duration: float = 0.0

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def total(self) -> int:
        return len(self.results)


def discover_test_files(path: str) -> list[str]:
    """Find all .mn files under the given path."""
    if os.path.isfile(path):
        if path.endswith(".mn"):
            return [path]
        return []

    mn_files: list[str] = []
    for root, _dirs, files in os.walk(path):
        for f in sorted(files):
            if f.endswith(".mn"):
                mn_files.append(os.path.join(root, f))
    return mn_files


def _has_test_decorator(defn: Definition) -> bool:
    """Check if a definition has the @test decorator."""
    decorators: list[Decorator] = getattr(defn, "decorators", [])
    return any(d.name == "test" for d in decorators)


def _unwrap_definition(defn: Definition) -> Definition | None:
    """Unwrap DocComment and ExportDef wrappers."""
    if isinstance(defn, DocComment):
        return defn.definition
    if isinstance(defn, ExportDef):
        return defn.definition
    return defn


def discover_tests(source: str, filename: str) -> list[str]:
    """Parse a source file and return names of @test functions."""
    try:
        ast = parse(source, filename=filename)
    except ParseError:
        return []

    test_names: list[str] = []
    for defn in ast.definitions:
        inner = _unwrap_definition(defn)
        if inner is None:
            continue
        if isinstance(inner, FnDef) and _has_test_decorator(inner):
            test_names.append(inner.name)
    return test_names


def _compile_test_source(source: str, filename: str) -> str:
    """Compile a .mn file to Python, keeping @test functions."""
    from mapanare.emit_python_mir import PythonMIREmitter
    from mapanare.lower import lower as build_mir
    from mapanare.mir_opt import MIROptLevel
    from mapanare.mir_opt import optimize_module as mir_optimize
    from mapanare.modules import ModuleResolver

    resolver = ModuleResolver()
    ast = parse(source, filename=filename)
    check_or_raise(ast, filename=filename, resolver=resolver)

    module_name = os.path.splitext(os.path.basename(filename))[0]
    mir_module = build_mir(ast, module_name=module_name)
    mir_module, _ = mir_optimize(mir_module, MIROptLevel.O0)

    emitter = PythonMIREmitter()
    return emitter.emit(mir_module)


def run_test_file(filepath: str, filter_pattern: str | None = None) -> list[TestResult]:
    """Run all @test functions in a single .mn file."""
    source = _read_file(filepath)
    test_names = discover_tests(source, filepath)

    if filter_pattern:
        test_names = [n for n in test_names if filter_pattern in n]

    if not test_names:
        return []

    # Compile the file
    try:
        python_code = _compile_test_source(source, filepath)
    except (ParseError, SemanticErrors, Exception) as e:
        return [
            TestResult(name=n, file=filepath, passed=False, error=f"compile error: {e}")
            for n in test_names
        ]

    # Generate test harness that calls each test and reports results
    harness_lines = [python_code, "", "import sys, time, json", "", "_results = []"]
    for name in test_names:
        harness_lines.append("_t0 = time.perf_counter()")
        harness_lines.append("try:")
        harness_lines.append(f"    {name}()")
        harness_lines.append(
            f"    _results.append(dict(name={name!r}, passed=True,"
            f" duration=time.perf_counter() - _t0))"
        )
        harness_lines.append("except Exception as _e:")
        harness_lines.append(
            f"    _results.append(dict(name={name!r}, passed=False,"
            f" error=str(_e), duration=time.perf_counter() - _t0))"
        )
    harness_lines.append('print("__TEST_RESULTS__")')
    harness_lines.append("print(json.dumps(_results))")

    harness_code = "\n".join(harness_lines)

    # Write to temp file and run
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(harness_code)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )

        # Parse results from stdout
        import json

        results: list[TestResult] = []
        output = result.stdout
        if "__TEST_RESULTS__" in output:
            json_line = output.split("__TEST_RESULTS__\n", 1)[1].strip().split("\n")[0]
            raw_results = json.loads(json_line)
            for r in raw_results:
                results.append(
                    TestResult(
                        name=r["name"],
                        file=filepath,
                        passed=r["passed"],
                        duration=r.get("duration", 0.0),
                        error=r.get("error", ""),
                    )
                )
        else:
            # Process crashed — all tests fail
            stderr = result.stderr.strip()
            for name in test_names:
                results.append(
                    TestResult(
                        name=name,
                        file=filepath,
                        passed=False,
                        error=stderr or f"process exited with code {result.returncode}",
                    )
                )
        return results

    except subprocess.TimeoutExpired:
        return [
            TestResult(name=n, file=filepath, passed=False, error="timeout (60s)")
            for n in test_names
        ]
    finally:
        os.unlink(tmp_path)


def run_tests(path: str = ".", filter_pattern: str | None = None) -> TestSuite:
    """Run all tests under the given path. Returns a TestSuite."""
    files = discover_test_files(path)
    suite = TestSuite()

    t0 = time.perf_counter()
    for filepath in files:
        results = run_test_file(filepath, filter_pattern=filter_pattern)
        suite.results.extend(results)
    suite.duration = time.perf_counter() - t0

    return suite


def format_results(suite: TestSuite, verbose: bool = False) -> str:
    """Format test results for terminal output."""
    lines: list[str] = []

    if not suite.results:
        lines.append("no tests found")
        return "\n".join(lines)

    # Group by file
    by_file: dict[str, list[TestResult]] = {}
    for r in suite.results:
        by_file.setdefault(r.file, []).append(r)

    for filepath, results in by_file.items():
        rel = os.path.relpath(filepath)
        lines.append(f"  {rel}")
        for r in results:
            status = "PASS" if r.passed else "FAIL"
            duration_ms = r.duration * 1000
            line = f"    {status}  {r.name} ({duration_ms:.1f}ms)"
            lines.append(line)
            if not r.passed and r.error:
                for err_line in r.error.split("\n"):
                    lines.append(f"           {err_line}")

    lines.append("")
    lines.append(
        f"result: {suite.passed} passed, {suite.failed} failed "
        f"({suite.total} total) in {suite.duration:.2f}s"
    )

    return "\n".join(lines)


def _read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()
