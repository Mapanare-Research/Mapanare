"""Cross-backend consistency tests — Phase 3.3, Task 8.

For each test case, compile the same .mn source to both Python (and run it)
and LLVM IR (and verify it compiles). This ensures that the same program
is accepted by both backends and produces correct output on Python.

The LLVM backend cannot be executed without linking, so we verify:
1. Python backend: correct stdout output
2. LLVM backend: compiles to valid IR without errors
"""

from __future__ import annotations

import textwrap

from mapanare.cli import _compile_to_llvm_ir
from tests.e2e.test_e2e import _run_mapanare

# Each test case: (description, source, expected_output_substring)
_CROSS_BACKEND_CASES: list[tuple[str, str, str]] = [
    (
        "integer_arithmetic",
        textwrap.dedent("""\
            fn main() {
                let x: Int = 10 + 20
                print(x)
            }
        """),
        "30",
    ),
    (
        "function_call",
        textwrap.dedent("""\
            fn double(n: Int) -> Int {
                return n * 2
            }
            fn main() {
                print(double(21))
            }
        """),
        "42",
    ),
    (
        "if_else",
        textwrap.dedent("""\
            fn main() {
                let x: Int = 5
                if x > 3 {
                    print("yes")
                } else {
                    print("no")
                }
            }
        """),
        "yes",
    ),
    (
        "while_loop",
        textwrap.dedent("""\
            fn main() {
                let mut i: Int = 0
                let mut sum: Int = 0
                while i < 5 {
                    sum += i
                    i += 1
                }
                print(sum)
            }
        """),
        "10",
    ),
    (
        "for_range",
        textwrap.dedent("""\
            fn main() {
                let mut total: Int = 0
                for i in 1..=5 {
                    total += i
                }
                print(total)
            }
        """),
        "15",
    ),
    (
        "recursion",
        textwrap.dedent("""\
            fn fac(n: Int) -> Int {
                if n <= 1 { return 1 }
                return n * fac(n - 1)
            }
            fn main() {
                print(fac(6))
            }
        """),
        "720",
    ),
    (
        "string_concat",
        textwrap.dedent("""\
            fn main() {
                let a: String = "hello"
                let b: String = " world"
                print(a + b)
            }
        """),
        "hello world",
    ),
    (
        "match_int",
        textwrap.dedent("""\
            fn tag(n: Int) -> Int {
                match n {
                    0 => { return 0 },
                    1 => { return 10 },
                    _ => { return 99 }
                }
                return -1
            }
            fn main() {
                print(tag(1))
            }
        """),
        "10",
    ),
    (
        "nested_function_calls",
        textwrap.dedent("""\
            fn add(a: Int, b: Int) -> Int {
                return a + b
            }
            fn mul(a: Int, b: Int) -> Int {
                return a * b
            }
            fn main() {
                print(mul(add(2, 3), 4))
            }
        """),
        "20",
    ),
    (
        "float_ops",
        textwrap.dedent("""\
            fn main() {
                let x: Float = 2.5
                let y: Float = 3.5
                print(x + y)
            }
        """),
        "6.0",
    ),
    (
        "boolean_logic",
        textwrap.dedent("""\
            fn main() {
                if true && !false {
                    print("ok")
                }
            }
        """),
        "ok",
    ),
    (
        "multiple_prints",
        textwrap.dedent("""\
            fn main() {
                print(1)
                print(2)
                print(3)
            }
        """),
        "1",
    ),
    (
        "while_break",
        textwrap.dedent("""\
            fn main() {
                let mut i: Int = 0
                let mut sum: Int = 0
                while i < 10 {
                    if i == 5 {
                        break
                    }
                    sum += i
                    i += 1
                }
                print(sum)
            }
        """),
        "10",
    ),
    (
        "string_interpolation",
        textwrap.dedent("""\
            fn main() {
                let x: Int = 42
                let msg: String = "val=${x}"
                print(msg)
            }
        """),
        "val=42",
    ),
    (
        "nested_match",
        textwrap.dedent("""\
            fn classify(x: Int) -> Int {
                match x {
                    0 => { return 0 },
                    1 => { return 10 },
                    _ => { return 99 }
                }
                return -1
            }
            fn main() {
                print(classify(1))
            }
        """),
        "10",
    ),
]


class TestCrossBackendConsistency:
    """Same .mn source compiles on both backends; Python output is correct."""


# Dynamically generate test methods for each case
def _make_test(name: str, source: str, expected: str):  # type: ignore[no-untyped-def]
    def test_method(self) -> None:  # type: ignore[no-untyped-def]
        # 1) Python backend: compile, run, check output
        result = _run_mapanare(source)
        assert result.returncode == 0, f"Python backend failed: {result.stderr}"
        assert (
            expected in result.stdout
        ), f"Python output mismatch: expected '{expected}' in '{result.stdout.strip()}'"

        # 2) LLVM backend: compile to IR (no execution, using legacy AST path)
        ir = _compile_to_llvm_ir(source, f"{name}.mn", use_mir=False)
        assert "define" in ir, "LLVM IR missing function definitions"
        assert len(ir) > 100, "LLVM IR suspiciously short"

    test_method.__name__ = f"test_{name}"
    test_method.__qualname__ = f"TestCrossBackendConsistency.test_{name}"
    return test_method


for _name, _source, _expected in _CROSS_BACKEND_CASES:
    setattr(
        TestCrossBackendConsistency,
        f"test_{_name}",
        _make_test(_name, _source, _expected),
    )
