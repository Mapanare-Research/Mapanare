"""E2E tests for every code sample in docs/getting-started.md.

Each test compiles an .mn source string from the tutorial, runs it, and
asserts on stdout to verify the tutorial is accurate.
"""

from __future__ import annotations

import textwrap

from tests.e2e.test_e2e import _run_mapanare

# ── Section 1: Hello, World ──────────────────────────────────────────────────


class TestTutorialHelloWorld:
    def test_hello_world(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                print("Hello, Mapanare!")
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "Hello, Mapanare!" in result.stdout


# ── Section 2: Variables and Types ───────────────────────────────────────────


class TestTutorialVariables:
    def test_variables_and_types(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let name = "World"
                let x: Int = 42
                let pi: Float = 3.14159
                let active: Bool = true

                print("Hello, " + name + "!")
                print("x = " + str(x))
                print("pi = " + str(pi))

                let mut count: Int = 0
                count += 1
                print("count = " + str(count))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "Hello, World!" in lines[0]
        assert "x = 42" in lines[1]
        assert "pi = 3.14159" in lines[2]
        assert "count = 1" in lines[3]


# ── Section 3: Functions ─────────────────────────────────────────────────────


class TestTutorialFunctions:
    def test_functions(self) -> None:
        source = textwrap.dedent("""\
            fn add(a: Int, b: Int) -> Int {
                return a + b
            }

            fn greet(name: String) -> String {
                return "Hello, " + name + "!"
            }

            fn main() {
                print(str(add(3, 4)))
                print(greet("Mapanare"))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "7" in lines[0]
        assert "Hello, Mapanare!" in lines[1]


# ── Section 4: Control Flow ─────────────────────────────────────────────────


class TestTutorialControlFlow:
    def test_if_else(self) -> None:
        source = textwrap.dedent("""\
            fn classify(n: Int) -> String {
                if n < 0 {
                    return "negative"
                } else if n == 0 {
                    return "zero"
                } else {
                    return "positive"
                }
            }

            fn main() {
                print(classify(-5))
                print(classify(0))
                print(classify(42))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "negative" in lines[0]
        assert "zero" in lines[1]
        assert "positive" in lines[2]

    def test_while_loop(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let mut i: Int = 0
                while i < 5 {
                    print(str(i))
                    i += 1
                }
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 5
        assert "0" in lines[0]
        assert "4" in lines[4]

    def test_for_loops(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                for i in 0..5 {
                    print(str(i))
                }

                let mut sum: Int = 0
                for i in 1..=5 {
                    sum += i
                }
                print("sum = " + str(sum))

                let items = [10, 20, 30]
                for item in items {
                    print(str(item))
                }
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "0" in lines[0]
        assert "4" in lines[4]
        assert "sum = 15" in lines[5]
        assert "10" in lines[6]
        assert "20" in lines[7]
        assert "30" in lines[8]


# ── Section 5: Structs ──────────────────────────────────────────────────────


class TestTutorialStructs:
    def test_struct(self) -> None:
        source = textwrap.dedent("""\
            struct Point {
                x: Float,
                y: Float
            }

            fn distance(p: Point) -> Float {
                return (p.x * p.x + p.y * p.y)
            }

            fn main() {
                let p = Point(3.0, 4.0)
                print("x = " + str(p.x))
                print("y = " + str(p.y))
                print("distance squared = " + str(distance(p)))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "x = 3.0" in lines[0]
        assert "y = 4.0" in lines[1]
        assert "distance squared = 25.0" in lines[2]


# ── Section 6: Enums and Pattern Matching ────────────────────────────────────


class TestTutorialEnums:
    def test_enum_with_data(self) -> None:
        source = textwrap.dedent("""\
            enum Shape {
                Circle(Float),
                Rect(Float, Float)
            }

            fn area(s: Shape) -> Float {
                match s {
                    Shape_Circle(r) => { return 3.14159 * r * r },
                    Shape_Rect(w, h) => { return w * h },
                    _ => { return 0.0 }
                }
                return 0.0
            }

            fn main() {
                let c = Shape_Circle(5.0)
                let r = Shape_Rect(3.0, 4.0)
                print("circle area = " + str(area(c)))
                print("rect area = " + str(area(r)))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "circle area = " in lines[0]
        assert "rect area = 12.0" in lines[1]

    def test_match_int_values(self) -> None:
        source = textwrap.dedent("""\
            fn describe(n: Int) -> String {
                match n {
                    1 => { return "one" },
                    2 => { return "two" },
                    3 => { return "three" },
                    _ => { return "other" }
                }
                return "unreachable"
            }

            fn main() {
                print(describe(1))
                print(describe(99))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "one" in lines[0]
        assert "other" in lines[1]


# ── Section 7: Lists ────────────────────────────────────────────────────────


class TestTutorialLists:
    def test_lists(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let mut items: List<Int> = []
                items.push(10)
                items.push(20)
                items.push(30)

                print("length = " + str(items.length()))
                print("first = " + str(items[0]))

                let mut total: Int = 0
                for item in items {
                    total += item
                }
                print("total = " + str(total))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "length = 3" in lines[0]
        assert "first = 10" in lines[1]
        assert "total = 60" in lines[2]


# ── Section 8: Error Handling ────────────────────────────────────────────────


class TestTutorialErrorHandling:
    def test_result_with_match(self) -> None:
        source = textwrap.dedent("""\
            fn divide(a: Int, b: Int) -> Result<Int, String> {
                if b == 0 {
                    return Err("division by zero")
                }
                return Ok(a / b)
            }

            fn main() {
                let r1 = divide(10, 2)
                match r1 {
                    Ok(v) => { print("result = " + str(v)) },
                    Err(e) => { print("error: " + e) }
                }

                let r2 = divide(10, 0)
                match r2 {
                    Ok(v) => { print("result = " + str(v)) },
                    Err(e) => { print("error: " + e) }
                }
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "result = 5" in lines[0]
        assert "error: division by zero" in lines[1]

    def test_question_mark_operator(self) -> None:
        source = textwrap.dedent("""\
            fn might_fail(ok: Bool) -> Result<Int, String> {
                if ok {
                    return Ok(42)
                }
                return Err("failed")
            }

            fn do_work() -> Result<Int, String> {
                let v = might_fail(true)?
                return Ok(v + 8)
            }

            fn main() {
                let r = do_work()
                print(str(r))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "Ok(50)" in result.stdout

    def test_option_type(self) -> None:
        source = textwrap.dedent("""\
            fn find_item(items: List<Int>, target: Int) -> Option<Int> {
                for i in 0..len(items) {
                    if items[i] == target {
                        return Some(items[i])
                    }
                }
                return none
            }

            fn main() {
                let result = find_item([10, 20, 30], 20)
                match result {
                    Some(v) => { print("found: " + str(v)) },
                    _ => { print("not found") }
                }
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "found: 20" in result.stdout


# ── Section 9: Agents ────────────────────────────────────────────────────────


class TestTutorialAgents:
    def test_agent_greeter(self) -> None:
        source = textwrap.dedent("""\
            agent Greeter {
                input name: String
                output greeting: String

                fn handle(name: String) -> String {
                    return "Hello, " + name + "!"
                }
            }

            fn main() {
                let g = spawn Greeter()
                g.name <- "World"
                let msg = sync g.greeting
                print(msg)
                sync g.stop()
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "Hello, World!" in result.stdout

    def test_agent_multiple_messages(self) -> None:
        source = textwrap.dedent("""\
            agent Doubler {
                input val: Int
                output result: Int

                fn handle(val: Int) -> Int {
                    return val * 2
                }
            }

            fn main() {
                let d = spawn Doubler()
                d.val <- 21
                print(str(sync d.result))
                d.val <- 50
                print(str(sync d.result))
                sync d.stop()
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "42" in lines[0]
        assert "100" in lines[1]


# ── Section 10: Multi-Agent Pipelines ────────────────────────────────────────


class TestTutorialPipelines:
    def test_two_agent_pipeline(self) -> None:
        source = textwrap.dedent("""\
            agent Add10 {
                input val: Int
                output result: Int

                fn handle(val: Int) -> Int {
                    return val + 10
                }
            }

            agent Double {
                input val: Int
                output result: Int

                fn handle(val: Int) -> Int {
                    return val * 2
                }
            }

            fn main() {
                let a = spawn Add10()
                let d = spawn Double()

                a.val <- 5
                let mid = sync a.result
                d.val <- mid
                let final_val = sync d.result
                print(str(final_val))

                sync a.stop()
                sync d.stop()
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "30" in result.stdout

    def test_named_pipe(self) -> None:
        source = textwrap.dedent("""\
            agent Increment {
                input n: Int
                output n: Int

                fn handle(n: Int) -> Int {
                    return n + 1
                }
            }

            agent Triple {
                input n: Int
                output n: Int

                fn handle(n: Int) -> Int {
                    return n * 3
                }
            }

            pipe Transform {
                Increment |> Triple
            }

            fn main() {
                let result = sync Transform(10)
                print(str(result))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "33" in result.stdout


# ── Section 11: Signals ──────────────────────────────────────────────────────


class TestTutorialSignals:
    def test_signals_reactive(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let count = signal(0)
                let doubled = signal { count.value * 2 }

                print("doubled = " + str(doubled.value))

                count.value = 10
                print("doubled = " + str(doubled.value))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "doubled = 0" in lines[0]
        assert "doubled = 20" in lines[1]


# ── Section 12: Streams ─────────────────────────────────────────────────────


class TestTutorialStreams:
    def test_stream_map_filter(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let s = stream([1, 2, 3, 4, 5])
                let result = s.map((x) => x * 2).filter((x) => x > 4)
                let collected = sync result.collect()
                print(str(collected))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "[6, 8, 10]" in result.stdout
