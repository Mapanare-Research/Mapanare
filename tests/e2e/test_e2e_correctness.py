"""End-to-end correctness tests — Phase 3.3.

Covers gaps in the existing e2e suite:
- Arithmetic edge cases, string operations, closures, recursion
- Struct creation/field access, enum variants with data, nested pattern matching
- While loops, break/continue semantics
"""

from __future__ import annotations

import textwrap

from tests.e2e.test_e2e import _run_mapanare

# ── Arithmetic ────────────────────────────────────────────────────────────────


class TestArithmeticCorrectness:
    """E2e: arithmetic operations produce correct output."""

    def test_integer_division(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let a: Int = 7
                let b: Int = 2
                print(a / b)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "3" in result.stdout

    def test_modulo(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                print(17 % 5)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "2" in result.stdout

    def test_negative_arithmetic(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let x: Int = -10
                let y: Int = 3
                print(x + y)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "-7" in result.stdout

    def test_float_arithmetic(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let a: Float = 1.5
                let b: Float = 2.5
                print(a + b)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "4.0" in result.stdout

    def test_mixed_comparison_operators(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                if 5 >= 5 {
                    print("ge")
                }
                if 5 <= 5 {
                    print("le")
                }
                if 5 != 4 {
                    print("ne")
                }
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "ge" in result.stdout
        assert "le" in result.stdout
        assert "ne" in result.stdout

    def test_operator_precedence(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let x: Int = 2 + 3 * 4
                print(x)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "14" in result.stdout

    def test_boolean_operators(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                if true && true {
                    print("and")
                }
                if false || true {
                    print("or")
                }
                if !false {
                    print("not")
                }
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "and" in result.stdout
        assert "or" in result.stdout
        assert "not" in result.stdout


# ── Strings ──────────────────────────────────────────────────────────────────


class TestStringCorrectness:
    """E2e: string operations produce correct output."""

    def test_string_length(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let s: String = "hello"
                print(len(s))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "5" in result.stdout

    def test_str_conversion(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let n: Int = 42
                let s: String = str(n)
                print(s)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "42" in result.stdout

    def test_string_multi_concat(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let a: String = "foo"
                let b: String = "bar"
                let c: String = "baz"
                print(a + b + c)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "foobarbaz" in result.stdout

    def test_empty_string(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let s: String = ""
                print(len(s))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "0" in result.stdout


# ── Functions ────────────────────────────────────────────────────────────────


class TestFunctionCorrectness:
    """E2e: functions and recursion produce correct output."""

    def test_recursive_factorial(self) -> None:
        source = textwrap.dedent("""\
            fn factorial(n: Int) -> Int {
                if n <= 1 {
                    return 1
                }
                return n * factorial(n - 1)
            }

            fn main() {
                print(factorial(5))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "120" in result.stdout

    def test_recursive_fibonacci(self) -> None:
        source = textwrap.dedent("""\
            fn fib(n: Int) -> Int {
                if n <= 1 {
                    return n
                }
                return fib(n - 1) + fib(n - 2)
            }

            fn main() {
                print(fib(10))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "55" in result.stdout

    def test_multiple_return_paths(self) -> None:
        source = textwrap.dedent("""\
            fn abs_val(n: Int) -> Int {
                if n < 0 {
                    return -n
                }
                return n
            }

            fn main() {
                print(abs_val(-42))
                print(abs_val(7))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "42" in lines[0]
        assert "7" in lines[1]

    def test_function_as_expression(self) -> None:
        source = textwrap.dedent("""\
            fn square(x: Int) -> Int {
                return x * x
            }

            fn main() {
                print(square(3) + square(4))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "25" in result.stdout

    def test_many_params(self) -> None:
        source = textwrap.dedent("""\
            fn sum4(a: Int, b: Int, c: Int, d: Int) -> Int {
                return a + b + c + d
            }

            fn main() {
                print(sum4(1, 2, 3, 4))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "10" in result.stdout


# ── Closures / Lambdas ───────────────────────────────────────────────────────


class TestClosureCorrectness:
    """E2e: lambda expressions produce correct output."""

    def test_lambda_in_variable(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let double = (x) => x * 2
                print(double(5))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "10" in result.stdout

    def test_lambda_in_stream_map(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let s = stream([1, 2, 3])
                let mapped = s.map((x) => x + 10)
                let result = sync mapped.collect()
                print(result)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "[11, 12, 13]" in result.stdout

    def test_lambda_in_stream_filter(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let s = stream([1, 2, 3, 4, 5, 6])
                let odds = s.filter((x) => x % 2 != 0)
                let result = sync odds.collect()
                print(result)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "[1, 3, 5]" in result.stdout


# ── Structs ──────────────────────────────────────────────────────────────────


class TestStructCorrectness:
    """E2e: struct creation and field access produce correct output."""

    def test_struct_creation_and_access(self) -> None:
        source = textwrap.dedent("""\
            struct Point {
                x: Int,
                y: Int
            }

            fn main() {
                let p = Point(10, 20)
                print(p.x)
                print(p.y)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "10" in lines[0]
        assert "20" in lines[1]

    def test_struct_in_function(self) -> None:
        source = textwrap.dedent("""\
            struct Rect {
                w: Int,
                h: Int
            }

            fn area(r: Rect) -> Int {
                return r.w * r.h
            }

            fn main() {
                let r = Rect(5, 3)
                print(area(r))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "15" in result.stdout

    def test_struct_with_string_fields(self) -> None:
        source = textwrap.dedent("""\
            struct Person {
                name: String,
                age: Int
            }

            fn greet(p: Person) -> String {
                return "Hello, " + p.name
            }

            fn main() {
                let p = Person("Alice", 30)
                print(greet(p))
                print(p.age)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "Hello, Alice" in lines[0]
        assert "30" in lines[1]

    def test_multiple_structs(self) -> None:
        source = textwrap.dedent("""\
            struct Vec2 {
                x: Float,
                y: Float
            }

            struct Color {
                r: Int,
                g: Int,
                b: Int
            }

            fn main() {
                let pos = Vec2(1.0, 2.0)
                let col = Color(255, 0, 128)
                print(pos.x)
                print(col.r)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "1.0" in lines[0]
        assert "255" in lines[1]


# ── Enums and Pattern Matching ───────────────────────────────────────────────


class TestEnumPatternMatchCorrectness:
    """E2e: enums and pattern matching produce correct output."""

    def test_enum_with_data_destructuring(self) -> None:
        source = textwrap.dedent("""\
            enum Shape {
                Circle(Float),
                Rect(Float, Float)
            }

            fn describe(s: Shape) -> String {
                match s {
                    Shape_Circle(r) => { return "circle r=" + str(r) },
                    Shape_Rect(w, h) => { return "rect " + str(w) + "x" + str(h) },
                    _ => { return "unknown" }
                }
                return "unreachable"
            }

            fn main() {
                print(describe(Shape_Circle(5.0)))
                print(describe(Shape_Rect(3.0, 4.0)))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "circle r=5.0" in lines[0]
        assert "rect 3.0x4.0" in lines[1]

    def test_simple_enum_no_data(self) -> None:
        source = textwrap.dedent("""\
            enum Direction {
                North,
                South,
                East,
                West
            }

            fn name(d: Direction) -> String {
                match d {
                    Direction_North() => { return "north" },
                    Direction_South() => { return "south" },
                    Direction_East() => { return "east" },
                    Direction_West() => { return "west" },
                    _ => { return "?" }
                }
                return "unreachable"
            }

            fn main() {
                print(name(Direction_North()))
                print(name(Direction_West()))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "north" in lines[0]
        assert "west" in lines[1]

    def test_match_wildcard_default(self) -> None:
        source = textwrap.dedent("""\
            fn classify(n: Int) -> String {
                match n {
                    0 => { return "zero" },
                    1 => { return "one" },
                    _ => { return "many" }
                }
                return "unreachable"
            }

            fn main() {
                print(classify(0))
                print(classify(1))
                print(classify(42))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "zero" in lines[0]
        assert "one" in lines[1]
        assert "many" in lines[2]

    def test_match_string_literal(self) -> None:
        source = textwrap.dedent("""\
            fn greet(lang: String) -> String {
                match lang {
                    "en" => { return "Hello" },
                    "es" => { return "Hola" },
                    _ => { return "Hi" }
                }
                return "unreachable"
            }

            fn main() {
                print(greet("en"))
                print(greet("es"))
                print(greet("fr"))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "Hello" in lines[0]
        assert "Hola" in lines[1]
        assert "Hi" in lines[2]


# ── While loops, mutability ──────────────────────────────────────────────────


class TestControlFlowCorrectness:
    """E2e: control flow constructs produce correct output."""

    def test_while_countdown(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let mut n: Int = 5
                while n > 0 {
                    print(n)
                    n -= 1
                }
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 5
        assert "5" in lines[0]
        assert "1" in lines[4]

    def test_mutable_variable(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let mut x: Int = 0
                x += 10
                x *= 2
                x -= 5
                print(x)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "15" in result.stdout

    def test_nested_if(self) -> None:
        source = textwrap.dedent("""\
            fn categorize(n: Int) -> String {
                if n > 0 {
                    if n > 100 {
                        return "big"
                    } else {
                        return "small"
                    }
                } else {
                    return "non-positive"
                }
            }

            fn main() {
                print(categorize(200))
                print(categorize(5))
                print(categorize(-1))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "big" in lines[0]
        assert "small" in lines[1]
        assert "non-positive" in lines[2]

    def test_list_operations(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let mut nums: List<Int> = []
                nums.push(1)
                nums.push(2)
                nums.push(3)
                print(len(nums))
                print(nums[0])
                print(nums[2])
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "3" in lines[0]
        assert "1" in lines[1]
        assert "3" in lines[2]
