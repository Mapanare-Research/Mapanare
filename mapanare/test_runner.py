"""Built-in test runner for Mapanare.

Discovers and runs @test-decorated functions in .mn source files.
Uses the LLVM JIT backend to compile and execute tests natively.
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
from mapanare.diagnostics import _supports_color
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
    from mapanare.emit_llvm_text import LLVMTextEmitter
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

    emitter = LLVMTextEmitter(module_name=module_name)
    return emitter.emit(mir_module)


def _find_runtime_lib() -> str | None:
    """Locate the native runtime shared/static library for linking.

    Canonical artifacts (matched in priority order):

    * ``libmapanare_rt.a``      — built by ``make build-rt`` (8 modules + Metal
      on Darwin); the link target ``cli.py`` and every CI workflow rely on.
    * ``libmapanare_runtime.so`` — built by ``runtime/native/build_native.py``;
      shared-library variant used by the docker runtime image.

    Pre-fix the candidates included ``libmapanare_core.*`` — stale names that
    no current build target produces. The mismatch silently returned ``None``
    so ``mapanare test`` shipped clang invocations with no runtime library,
    and the linker failed on ``__mn_str_eq`` / ``__mn_str_println`` only on
    fresh-checkout CI (a stale local ``libmapanare_core.so`` masked it on
    developer machines).
    """
    this_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(this_dir, "..", "runtime", "native"),
        os.path.join(this_dir, "runtime", "native"),
    ]
    names = (
        "libmapanare_rt.a",
        "libmapanare_runtime.so",
        "libmapanare_runtime.dylib",
        "libmapanare_runtime.dll",
    )
    for d in candidates:
        for name in names:
            path = os.path.join(d, name)
            if os.path.isfile(path):
                return os.path.abspath(path)
    return None


_TEST_MAIN_TEMPLATE = """
; v5.13.1 At.1: per-test main wrapper synthesized by mapanare.test_runner.
; The lowered IR for a @test fn has no entry point; clang/ld would fail
; with "undefined reference to `main`". Each test gets its own binary
; with a main that calls exactly that test and returns 0 on normal
; completion. Assertion failures inside the test call exit(1) directly.
define i32 @main() {{
  call void @{symbol}()
  ret i32 0
}}
"""


def _emit_test_main(symbol: str) -> str:
    """Build the per-test entry-point IR fragment that calls ``symbol``."""
    return _TEST_MAIN_TEMPLATE.format(symbol=symbol)


def _build_clang_cmd(
    ir_path: str, bin_path: str, rt_lib: str | None
) -> tuple[list[str], dict[str, str] | None]:
    from mapanare.toolchain import detect_toolchain, invocation_env

    tc = detect_toolchain()
    clang_exe = tc.clang if tc else "clang"
    cmd = [clang_exe or "clang", "-O2", ir_path, "-o", bin_path]
    if rt_lib:
        cmd.append(rt_lib)
    if tc is None or tc.needs_libm_flag:
        cmd.append("-lm")
    if tc is None or tc.needs_pthread_flag:
        cmd.append("-lpthread")
    env = invocation_env(tc) if tc else None
    return cmd, env


def _extract_failure_message(stdout: str, stderr: str, returncode: int) -> str:
    """Pull the most useful failure context out of a crashed test process."""
    combined = (stdout + stderr).strip()
    for line in combined.split("\n"):
        if "assertion failed" in line.lower():
            return line.strip()
    if combined:
        return combined
    return f"process exited with code {returncode}"


def _run_one_test(base_ir: str, filepath: str, name: str, rt_lib: str | None) -> TestResult:
    """Compile + run a single @test function in its own subprocess."""
    full_ir = base_ir + _emit_test_main(name)

    ir_fd, ir_path = tempfile.mkstemp(suffix=".ll", prefix=f"mn_test_{name}_")
    exe_ext = ".exe" if sys.platform == "win32" else ""
    bin_path = ir_path.replace(".ll", exe_ext or ".out")

    try:
        with os.fdopen(ir_fd, "w", encoding="utf-8") as f:
            f.write(full_ir)

        clang_cmd, env = _build_clang_cmd(ir_path, bin_path, rt_lib)
        compile_result = subprocess.run(
            clang_cmd, capture_output=True, text=True, timeout=60, env=env
        )
        if compile_result.returncode != 0:
            return TestResult(
                name=name,
                file=filepath,
                passed=False,
                error=f"clang compile error: {compile_result.stderr.strip()}",
            )

        t0 = time.perf_counter()
        try:
            proc = subprocess.run([bin_path], capture_output=True, text=True, timeout=60)
        except subprocess.TimeoutExpired:
            return TestResult(
                name=name,
                file=filepath,
                passed=False,
                duration=time.perf_counter() - t0,
                error="timeout (60s)",
            )
        duration = time.perf_counter() - t0

        if proc.returncode == 0:
            return TestResult(name=name, file=filepath, passed=True, duration=duration)
        return TestResult(
            name=name,
            file=filepath,
            passed=False,
            duration=duration,
            error=_extract_failure_message(proc.stdout, proc.stderr, proc.returncode),
        )
    finally:
        if os.path.exists(ir_path):
            os.unlink(ir_path)
        if os.path.exists(bin_path):
            os.unlink(bin_path)


def run_test_file(filepath: str, filter_pattern: str | None = None) -> list[TestResult]:
    """Run all @test functions in a single .mn file via clang AOT compilation.

    Each test compiles to its own binary (the lowered IR has no main; we
    synthesize one per test) and runs in a subprocess so assertion exit(1)
    can't take down the runner.
    """
    source = _read_file(filepath)
    test_names = discover_tests(source, filepath)

    if filter_pattern:
        test_names = [n for n in test_names if filter_pattern in n]

    if not test_names:
        return []

    try:
        base_ir = _compile_test_to_llvm(source, filepath, test_names)
    except (ParseError, SemanticErrors, Exception) as e:
        return [
            TestResult(name=n, file=filepath, passed=False, error=f"compile error: {e}")
            for n in test_names
        ]

    rt_lib = _find_runtime_lib()
    return [_run_one_test(base_ir, filepath, name, rt_lib) for name in test_names]


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

    use_color = _supports_color()

    for filepath, results in by_file.items():
        rel = os.path.relpath(filepath)
        lines.append(f"  {rel}")
        for r in results:
            if r.passed:
                status = "\033[32mPASS\033[0m" if use_color else "PASS"
            else:
                status = "\033[31mFAIL\033[0m" if use_color else "FAIL"
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
