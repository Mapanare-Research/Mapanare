"""Cross-backend equivalence tests for MIR emitters (Phase 4, Task 11)."""

import os
import subprocess
import sys
import tempfile

from mapanare.cli import _compile_source

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _run_code(python_code: str, timeout: float = 10) -> str:
    """Execute Python code and return stdout."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8", dir=_PROJECT_ROOT
    ) as tmp:
        tmp.write(python_code)
        tmp_path = tmp.name
    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=_PROJECT_ROOT,
        )
        return result.stdout
    finally:
        os.unlink(tmp_path)


def _check_equiv(source: str) -> None:
    """Compile via both paths and check output matches."""
    ast_code = _compile_source(source, "<test>", use_mir=False)
    mir_code = _compile_source(source, "<test>", use_mir=True)
    ast_out = _run_code(ast_code)
    mir_out = _run_code(mir_code)
    assert ast_out == mir_out, f"AST output: {ast_out!r}\nMIR output: {mir_out!r}"


class TestEmitterEquivalence:
    """Verify MIR Python emitter produces semantically equivalent output to AST emitter."""

    def test_hello_world(self) -> None:
        _check_equiv('println("Hello, world!")')

    def test_arithmetic(self) -> None:
        _check_equiv("""\
let x: Int = 10 + 5
println(str(x))
""")

    def test_if_else(self) -> None:
        _check_equiv("""\
let x: Int = 10
if x > 5 {
    println("big")
} else {
    println("small")
}
""")

    def test_while_loop(self) -> None:
        _check_equiv("""\
let mut i: Int = 0
while i < 5 {
    println(str(i))
    i = i + 1
}
""")

    def test_for_loop_range(self) -> None:
        _check_equiv("""\
for i in 0..5 {
    println(str(i))
}
""")

    def test_function_calls(self) -> None:
        _check_equiv("""\
fn add(a: Int, b: Int) -> Int {
    return a + b
}
let result: Int = add(3, 4)
println(str(result))
""")

    def test_struct_creation_and_field_access(self) -> None:
        _check_equiv("""\
struct Point {
    x: Int,
    y: Int
}
let p: Point = Point(1, 2)
println(str(p.x))
println(str(p.y))
""")

    def test_multiple_functions(self) -> None:
        """Multiple function definitions and calls."""
        _check_equiv("""\
fn double(x: Int) -> Int {
    return x * 2
}
fn triple(x: Int) -> Int {
    return x * 3
}
println(str(double(5)))
println(str(triple(4)))
""")

    def test_string_interpolation(self) -> None:
        _check_equiv("""\
let name: String = "world"
println("Hello, {name}!")
""")

    def test_list_operations(self) -> None:
        _check_equiv("""\
let xs: List<Int> = [1, 2, 3]
println(str(len(xs)))
println(str(xs[0]))
""")

    def test_boolean_logic(self) -> None:
        _check_equiv("""\
let a: Bool = true
let b: Bool = false
if a && !b {
    println("yes")
} else {
    println("no")
}
""")

    def test_nested_if_else(self) -> None:
        _check_equiv("""\
let x: Int = 15
if x > 20 {
    println("very big")
} else {
    if x > 10 {
        println("big")
    } else {
        println("small")
    }
}
""")
