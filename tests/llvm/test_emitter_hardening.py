"""Phase 2 — Emitter Hardening tests.

Task 5: Mutable variable reassignment in loops produces correct values.
Task 6: List accumulation via reassignment in loops.
Task 7: Emitter output comparison suite (10+ programs).

All tests compile Mapanare source to LLVM IR via the MIR pipeline and
verify the IR is structurally correct.
"""

from __future__ import annotations

import textwrap

from mapanare.cli import _compile_to_llvm_ir


def _to_ir(source: str, filename: str = "test.mn") -> str:
    """Compile Mapanare source to LLVM IR string via MIR pipeline."""
    return _compile_to_llvm_ir(source, filename, use_mir=True)


# ===========================================================================
# Task 5: Mutable variable reassignment in loops
# ===========================================================================


class TestMutableVarReassignInLoop:
    """Task 5 — mutable variable reassignment in loops produces correct values."""

    def test_simple_counter_loop(self) -> None:
        """let mut x = 0; for i in 0..5 { x = x + 1 } — x should be 5."""
        source = textwrap.dedent("""\
            fn main() {
                let mut x: Int = 0
                for i in 0..5 {
                    x = x + 1
                }
                println(str(x))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        # Must have an add instruction for x + 1
        assert "add i64" in ir_text or "add nsw i64" in ir_text
        # Must store back to the alloca for x
        assert "store i64" in ir_text

    def test_compound_assign_in_loop(self) -> None:
        """let mut total = 0; for i in 0..10 { total += i } — compound assign."""
        source = textwrap.dedent("""\
            fn main() {
                let mut total: Int = 0
                for i in 0..10 {
                    total += i
                }
                println(str(total))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "add i64" in ir_text or "add nsw i64" in ir_text

    def test_reassign_string_in_loop(self) -> None:
        """let mut s = ""; for i in 0..3 { s = "hello" } — string reassignment."""
        source = textwrap.dedent("""\
            fn main() {
                let mut s: String = "start"
                for i in 0..3 {
                    s = "updated"
                }
                println(s)
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text

    def test_while_loop_counter(self) -> None:
        """let mut n = 10; while n > 0 { n = n - 1 } — while loop mutation."""
        source = textwrap.dedent("""\
            fn main() {
                let mut n: Int = 10
                while n > 0 {
                    n = n - 1
                }
                println(str(n))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "sub i64" in ir_text or "add i64" in ir_text

    def test_nested_loop_mutation(self) -> None:
        """Mutable variable updated in nested loops."""
        source = textwrap.dedent("""\
            fn main() {
                let mut count: Int = 0
                for i in 0..3 {
                    for j in 0..3 {
                        count = count + 1
                    }
                }
                println(str(count))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "add i64" in ir_text or "add nsw i64" in ir_text

    def test_reassign_after_loop(self) -> None:
        """Variable used after loop should see final value."""
        source = textwrap.dedent("""\
            fn main() {
                let mut x: Int = 0
                for i in 0..5 {
                    x = x + 1
                }
                let y: Int = x + 100
                println(str(y))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        # Should reference x's alloca after the loop
        assert "add i64" in ir_text or "add nsw i64" in ir_text


# ===========================================================================
# Task 6: List accumulation via reassignment in loops
# ===========================================================================


class TestListAccumulationReassign:
    """Task 6 — list accumulation via reassignment in loops."""

    def test_list_push_in_loop(self) -> None:
        """let mut xs = []; for i in 0..3 { xs.push(i) } — push-based."""
        source = textwrap.dedent("""\
            fn main() {
                let mut xs: List<Int> = []
                for i in 0..3 {
                    xs.push(i)
                }
                println(str(len(xs)))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "__mn_list_push" in ir_text

    def test_list_concat_reassign_in_loop(self) -> None:
        """let mut xs = []; for i in 0..3 { xs = xs + [i] } — concat reassignment."""
        source = textwrap.dedent("""\
            fn main() {
                let mut xs: List<Int> = []
                for i in 0..3 {
                    xs = xs + [i]
                }
                println(str(len(xs)))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text

    def test_list_push_preserves_elements(self) -> None:
        """Push then index access — elements should be preserved."""
        source = textwrap.dedent("""\
            fn main() {
                let mut xs: List<Int> = []
                xs.push(10)
                xs.push(20)
                xs.push(30)
                println(str(xs[0]))
                println(str(xs[1]))
                println(str(xs[2]))
            }
        """)
        ir_text = _to_ir(source)
        assert "__mn_list_push" in ir_text
        assert "__mn_list_get" in ir_text


# ===========================================================================
# Task 7: Emitter output comparison suite (10+ programs)
# ===========================================================================


class TestEmitterOutputSuite:
    """Task 7 — verify LLVM IR output for 10+ programs.

    Each test compiles a program and checks the IR contains
    the expected structural elements.
    """

    def test_hello_world(self) -> None:
        """Simple hello world program."""
        source = textwrap.dedent("""\
            fn main() {
                println("Hello, world!")
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "Hello, world!" in ir_text or "Hello" in ir_text

    def test_fibonacci(self) -> None:
        """Fibonacci function with recursion."""
        source = textwrap.dedent("""\
            fn fib(n: Int) -> Int {
                if n <= 1 {
                    return n
                }
                return fib(n - 1) + fib(n - 2)
            }

            fn main() {
                println(str(fib(10)))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "fib" in ir_text
        # Recursive call
        assert "call" in ir_text

    def test_factorial(self) -> None:
        """Factorial function."""
        source = textwrap.dedent("""\
            fn factorial(n: Int) -> Int {
                if n <= 1 {
                    return 1
                }
                return n * factorial(n - 1)
            }

            fn main() {
                println(str(factorial(5)))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "factorial" in ir_text
        assert "mul i64" in ir_text or "mul nsw i64" in ir_text

    def test_if_else(self) -> None:
        """If-else branching."""
        source = textwrap.dedent("""\
            fn classify(n: Int) -> String {
                if n > 0 {
                    return "positive"
                } else if n < 0 {
                    return "negative"
                } else {
                    return "zero"
                }
            }

            fn main() {
                println(classify(42))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "icmp" in ir_text
        assert "br" in ir_text

    def test_for_loop(self) -> None:
        """For loop with range."""
        source = textwrap.dedent("""\
            fn main() {
                for i in 0..10 {
                    println(str(i))
                }
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "__range" in ir_text or "__iter" in ir_text

    def test_match_expression(self) -> None:
        """Match expression with patterns."""
        source = textwrap.dedent("""\
            fn describe(n: Int) -> String {
                let result: String = match n {
                    0 => "zero",
                    1 => "one",
                    _ => "other"
                }
                return result
            }

            fn main() {
                println(describe(1))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "switch" in ir_text or "icmp" in ir_text

    def test_struct_creation(self) -> None:
        """Struct definition and field access."""
        source = textwrap.dedent("""\
            struct Point {
                x: Int,
                y: Int,
            }

            fn main() {
                let p: Point = Point(10, 20)
                println(str(p.x))
                println(str(p.y))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text

    def test_enum_and_match(self) -> None:
        """Enum definition with pattern matching."""
        source = textwrap.dedent("""\
            enum Color {
                Red,
                Green,
                Blue,
            }

            fn name(c: Color) -> String {
                let result: String = match c {
                    Red => "red",
                    Green => "green",
                    Blue => "blue"
                }
                return result
            }

            fn main() {
                let c: Color = Color::Red
                println(name(c))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text

    def test_list_operations(self) -> None:
        """List creation, push, and index access."""
        source = textwrap.dedent("""\
            fn main() {
                let mut xs: List<Int> = [1, 2, 3]
                xs.push(4)
                println(str(xs[0]))
                println(str(len(xs)))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "__mn_list" in ir_text

    def test_string_methods(self) -> None:
        """String method calls."""
        source = textwrap.dedent("""\
            fn main() {
                let s: String = "Hello, World!"
                println(str(len(s)))
                println(s.to_upper())
                println(s.to_lower())
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text

    def test_result_type(self) -> None:
        """Result<T, E> construction and matching."""
        source = textwrap.dedent("""\
            fn divide(a: Int, b: Int) -> Result<Int, String> {
                if b == 0 {
                    return Err("division by zero")
                }
                return Ok(a / b)
            }

            fn main() {
                let r: Result<Int, String> = divide(10, 2)
                match r {
                    Ok(v) => { println(str(v)) },
                    Err(e) => { println(e) }
                }
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text

    def test_closure(self) -> None:
        """Closure with captured variable."""
        source = textwrap.dedent("""\
            fn main() {
                let x: Int = 10
                let add_x = (n) => n + x
                println(str(add_x(5)))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text

    def test_multiple_functions(self) -> None:
        """Multiple function definitions and calls."""
        source = textwrap.dedent("""\
            fn add(a: Int, b: Int) -> Int {
                return a + b
            }

            fn mul(a: Int, b: Int) -> Int {
                return a * b
            }

            fn main() {
                let x: Int = add(3, 4)
                let y: Int = mul(x, 2)
                println(str(y))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "add" in ir_text
        assert "mul" in ir_text
