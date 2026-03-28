"""Built-in test runner for Mapanare.

Discovers and runs @test-decorated functions in .mn source files.
Uses the LLVM JIT backend to compile and execute tests natively.
Usage: mapanare test [path] [--filter pattern]
"""

from __future__ import annotations

import json
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


def _compile_test_to_llvm(source: str, filename: str, test_names: list[str]) -> str:
    """Compile a .mn file to LLVM IR for JIT execution.

    Test functions are marked public so the JIT engine can resolve them by name.
    """
    from mapanare.emit_llvm_mir import LLVMMIREmitter
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

    # Mark @test functions as public so they get external linkage in LLVM IR
    test_name_set = set(test_names)
    for fn in mir_module.functions:
        if fn.name in test_name_set:
            fn.is_public = True

    emitter = LLVMMIREmitter()
    llvm_module = emitter.emit(mir_module)
    return str(llvm_module)


# Subprocess harness script template.  The subprocess loads the LLVM IR from a
# temp file, JIT-compiles it, and calls the named test function.  On success it
# prints a JSON result line; on assertion failure (exit(1) from compiled code)
# the process exits with code 1 and stderr carries the assertion message.
_JIT_HARNESS = """\
import ctypes, json, sys, time
import llvmlite.binding as llvm

llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

ir_path = sys.argv[1]
fn_name = sys.argv[2]

with open(ir_path, encoding="utf-8") as f:
    llvm_ir = f.read()

target = llvm.Target.from_default_triple()
tm = target.create_target_machine(opt=2)
mod = llvm.parse_assembly(llvm_ir)
mod.triple = tm.triple
mod.data_layout = str(tm.target_data)
mod.verify()

if hasattr(llvm, "create_pass_manager_builder"):
    pmb = llvm.create_pass_manager_builder()
    pmb.opt_level = 2
    pm = llvm.create_module_pass_manager()
    pmb.populate(pm)
    pm.run(mod)
elif hasattr(llvm, "create_pass_builder"):
    pb = llvm.create_pass_builder(tm)
    pb.run(mod)

engine = llvm.create_mcjit_compiler(mod, tm)
engine.finalize_object()
engine.run_static_constructors()

t0 = time.perf_counter()
ptr = engine.get_function_address(fn_name)
if ptr == 0:
    print(json.dumps({"passed": False, "error": f"function '{fn_name}' not found"}))
    sys.exit(0)

cfunc = ctypes.CFUNCTYPE(None)(ptr)
cfunc()
dur = time.perf_counter() - t0
print(json.dumps({"passed": True, "duration": dur}))
"""


def run_test_file(filepath: str, filter_pattern: str | None = None) -> list[TestResult]:
    """Run all @test functions in a single .mn file via LLVM JIT.

    Each test function is executed in a separate subprocess so that assertion
    failures (which call exit(1) in compiled code) do not kill the runner.
    """
    source = _read_file(filepath)
    test_names = discover_tests(source, filepath)

    if filter_pattern:
        test_names = [n for n in test_names if filter_pattern in n]

    if not test_names:
        return []

    # Compile to LLVM IR (once per file)
    try:
        llvm_ir = _compile_test_to_llvm(source, filepath, test_names)
    except (ParseError, SemanticErrors, Exception) as e:
        return [
            TestResult(name=n, file=filepath, passed=False, error=f"compile error: {e}")
            for n in test_names
        ]

    # Write LLVM IR and harness script to temp files
    ir_fd, ir_path = tempfile.mkstemp(suffix=".ll", prefix="mn_test_")
    harness_fd, harness_path = tempfile.mkstemp(suffix=".py", prefix="mn_harness_")
    try:
        with os.fdopen(ir_fd, "w", encoding="utf-8") as f:
            f.write(llvm_ir)
        with os.fdopen(harness_fd, "w", encoding="utf-8") as f:
            f.write(_JIT_HARNESS)

        results: list[TestResult] = []
        for name in test_names:
            t0 = time.perf_counter()
            try:
                proc = subprocess.run(
                    [sys.executable, harness_path, ir_path, name],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                duration = time.perf_counter() - t0

                if proc.returncode == 0 and proc.stdout.strip():
                    data = json.loads(proc.stdout.strip().split("\n")[-1])
                    results.append(
                        TestResult(
                            name=name,
                            file=filepath,
                            passed=data["passed"],
                            duration=data.get("duration", duration),
                            error=data.get("error", ""),
                        )
                    )
                else:
                    # Process exited non-zero (assertion failure calls exit(1))
                    stderr = proc.stderr.strip()
                    # Extract assertion message from stderr/stdout
                    error_msg = stderr or proc.stdout.strip()
                    if not error_msg:
                        error_msg = f"process exited with code {proc.returncode}"
                    # Clean up the error: look for "assertion failed" in output
                    combined = (proc.stdout + proc.stderr).strip()
                    for line in combined.split("\n"):
                        if "assertion failed" in line.lower():
                            error_msg = line.strip()
                            break
                    results.append(
                        TestResult(
                            name=name,
                            file=filepath,
                            passed=False,
                            duration=duration,
                            error=error_msg,
                        )
                    )
            except subprocess.TimeoutExpired:
                results.append(
                    TestResult(
                        name=name,
                        file=filepath,
                        passed=False,
                        duration=time.perf_counter() - t0,
                        error="timeout (60s)",
                    )
                )
            except Exception as e:
                results.append(
                    TestResult(
                        name=name,
                        file=filepath,
                        passed=False,
                        duration=time.perf_counter() - t0,
                        error=str(e),
                    )
                )

        return results
    finally:
        os.unlink(ir_path)
        os.unlink(harness_path)


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
