"""End-to-end tests for Mapanare → Python compilation and execution.

Each test writes an .mn source string, compiles it via the mapa pipeline,
executes the resulting Python, and asserts on stdout / exit code.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap

from mapa.cli import _compile_source

# Root of the repo so `from runtime.…` imports resolve when we execute emitted code.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _run_mapanare(source: str, *, timeout: float = 10) -> subprocess.CompletedProcess[str]:
    """Compile Mapanare source to Python, write to a temp file, and execute it.

    Returns the CompletedProcess so callers can inspect stdout/stderr/returncode.
    """
    python_code = _compile_source(source, "<e2e>")

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False,
        encoding="utf-8",
        dir=_PROJECT_ROOT,
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
        return result
    finally:
        os.unlink(tmp_path)


# ── E2E: hello world ───────────────────────────────────────────────────────


class TestHelloWorld:
    """E2E: hello world"""

    def test_hello_world_print(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                print("Hello, World!")
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0
        assert "Hello, World!" in result.stdout

    def test_hello_world_println(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                println("Hello from Mapanare!")
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0
        assert "Hello from Mapanare!" in result.stdout

    def test_arithmetic_output(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let x: Int = 10
                let y: Int = 20
                let z: Int = x + y
                print(z)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0
        assert "30" in result.stdout

    def test_string_concatenation(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let greeting: String = "Hello" + ", " + "Mapanare!"
                print(greeting)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0
        assert "Hello, Mapanare!" in result.stdout

    def test_bool_and_comparison(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let a: Int = 5
                let b: Int = 10
                if a < b {
                    print("less")
                } else {
                    print("not less")
                }
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0
        assert "less" in result.stdout


# ── E2E: basic agent definition and spawn ──────────────────────────────────


class TestAgentSpawn:
    """E2E: basic agent definition and spawn"""

    def test_agent_echo(self) -> None:
        """Agent receives a message, transforms it, sends it back."""
        source = textwrap.dedent("""\
            agent Echo {
                input msg: String
                output reply: String

                fn handle(msg: String) -> String {
                    return "Echo: " + msg
                }
            }

            fn main() {
                let e = spawn Echo()
                e.msg <- "hello"
                let r = sync e.reply
                print(r)
                sync e.stop()
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "Echo: hello" in result.stdout

    def test_agent_numeric_transform(self) -> None:
        """Agent doubles an integer value."""
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
                let r = sync d.result
                print(r)
                sync d.stop()
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "42" in result.stdout

    def test_agent_multiple_messages(self) -> None:
        """Agent processes multiple messages sequentially."""
        source = textwrap.dedent("""\
            agent Adder {
                input x: Int
                output y: Int

                fn handle(x: Int) -> Int {
                    return x + 100
                }
            }

            fn main() {
                let a = spawn Adder()
                a.x <- 1
                let r1 = sync a.y
                print(r1)
                a.x <- 2
                let r2 = sync a.y
                print(r2)
                sync a.stop()
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "101" in lines[0]
        assert "102" in lines[1]


# ── E2E: signal reactivity ────────────────────────────────────────────────


class TestSignalReactivity:
    """E2E: signal reactivity"""

    def test_signal_basic_value(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let count = signal(0)
                print(count.value)
                count.value = 10
                print(count.value)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "0" in lines[0]
        assert "10" in lines[1]

    def test_signal_computed(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let base = signal(5)
                let doubled = signal { base.value * 2 }
                print(doubled.value)
                base.value = 10
                print(doubled.value)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "10" in lines[0]
        assert "20" in lines[1]

    def test_signal_subscriber_notification(self) -> None:
        """Computed signals recompute when dependencies change."""
        source = textwrap.dedent("""\
            fn main() {
                let x = signal(3)
                let y = signal { x.value + 1 }
                print(y.value)
                x.value = 7
                print(y.value)
                x.value = 0
                print(y.value)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "4" in lines[0]
        assert "8" in lines[1]
        assert "1" in lines[2]


# ── E2E: stream with map and filter ───────────────────────────────────────


class TestStreamMapFilter:
    """E2E: stream with map and filter"""

    def test_stream_collect(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let s = stream([1, 2, 3, 4, 5])
                let result = sync s.collect()
                print(result)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "[1, 2, 3, 4, 5]" in result.stdout

    def test_stream_map(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let s = stream([1, 2, 3])
                let doubled = s.map((x) => x * 2)
                let result = sync doubled.collect()
                print(result)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "[2, 4, 6]" in result.stdout

    def test_stream_filter(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let s = stream([1, 2, 3, 4, 5, 6])
                let evens = s.filter((x) => x % 2 == 0)
                let result = sync evens.collect()
                print(result)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "[2, 4, 6]" in result.stdout

    def test_stream_map_then_filter(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let s = stream([1, 2, 3, 4, 5])
                let processed = s.map((x) => x * 3).filter((x) => x > 6)
                let result = sync processed.collect()
                print(result)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "[9, 12, 15]" in result.stdout

    def test_stream_take(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let s = stream([10, 20, 30, 40, 50])
                let first3 = s.take(3)
                let result = sync first3.collect()
                print(result)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "[10, 20, 30]" in result.stdout


# ── E2E: multi-agent pipeline ─────────────────────────────────────────────


class TestMultiAgentPipeline:
    """E2E: multi-agent pipeline"""

    def test_two_agent_chain(self) -> None:
        """First agent adds 10, second agent multiplies by 2."""
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
                print(final_val)
                sync a.stop()
                sync d.stop()
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # (5 + 10) * 2 = 30
        assert "30" in result.stdout

    def test_pipe_definition(self) -> None:
        """Pipe definition chains agents together."""
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
                print(result)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # (10 + 1) * 3 = 33
        assert "33" in result.stdout

    def test_three_agent_chain(self) -> None:
        """Three agents chained manually."""
        source = textwrap.dedent("""\
            agent A {
                input x: Int
                output y: Int

                fn handle(x: Int) -> Int {
                    return x + 1
                }
            }

            agent B {
                input x: Int
                output y: Int

                fn handle(x: Int) -> Int {
                    return x * 2
                }
            }

            agent C {
                input x: Int
                output y: Int

                fn handle(x: Int) -> Int {
                    return x - 3
                }
            }

            fn main() {
                let a = spawn A()
                let b = spawn B()
                let c = spawn C()
                a.x <- 10
                let r1 = sync a.y
                b.x <- r1
                let r2 = sync b.y
                c.x <- r2
                let r3 = sync c.y
                print(r3)
                sync a.stop()
                sync b.stop()
                sync c.stop()
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # (10 + 1) * 2 - 3 = 19
        assert "19" in result.stdout


# ── E2E: Option and Result types ──────────────────────────────────────────


class TestOptionResult:
    """E2E: Option and Result types"""

    def test_ok_result(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let r = Ok(42)
                print(r)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "Ok(42)" in result.stdout

    def test_err_result(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let r = Err("not found")
                print(r)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "Err('not found')" in result.stdout

    def test_result_match(self) -> None:
        source = textwrap.dedent("""\
            fn try_divide(a: Int, b: Int) -> Result<Int, String> {
                if b == 0 {
                    return Err("division by zero")
                }
                return Ok(a / b)
            }

            fn main() {
                let r = try_divide(10, 2)
                match r {
                    Ok(v) => { print(v) },
                    Err(e) => { print(e) }
                }
                let r2 = try_divide(10, 0)
                match r2 {
                    Ok(v) => { print(v) },
                    Err(e) => { print(e) }
                }
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "5" in lines[0]
        assert "division by zero" in lines[1]

    def test_some_and_none(self) -> None:
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
                    Some(v) => { print(v) },
                    _ => { print("not found") }
                }
                let result2 = find_item([10, 20, 30], 99)
                match result2 {
                    Some(v) => { print(v) },
                    _ => { print("not found") }
                }
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "20" in lines[0]
        assert "not found" in lines[1]

    def test_error_propagation(self) -> None:
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

            fn do_work_fail() -> Result<Int, String> {
                let v = might_fail(false)?
                return Ok(v + 8)
            }

            fn main() {
                let r1 = do_work()
                print(r1)
                let r2 = do_work_fail()
                print(r2)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "Ok(50)" in lines[0]
        assert "Err('failed')" in lines[1]


# ── E2E: for loop and match ──────────────────────────────────────────────


class TestForLoopMatch:
    """E2E: for loop and match"""

    def test_for_loop_range(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let mut sum: Int = 0
                for i in 1..=5 {
                    sum += i
                }
                print(sum)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # 1+2+3+4+5 = 15
        assert "15" in result.stdout

    def test_for_loop_list(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let items = [10, 20, 30]
                let mut total: Int = 0
                for item in items {
                    total += item
                }
                print(total)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "60" in result.stdout

    def test_match_int_literal(self) -> None:
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
                print(describe(2))
                print(describe(99))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "one" in lines[0]
        assert "two" in lines[1]
        assert "other" in lines[2]

    def test_match_with_enum(self) -> None:
        source = textwrap.dedent("""\
            enum Color {
                Red,
                Green,
                Blue
            }

            fn name_color(c: Color) -> String {
                match c {
                    Color_Red() => { return "red" },
                    Color_Green() => { return "green" },
                    Color_Blue() => { return "blue" },
                    _ => { return "unknown" }
                }
                return "unreachable"
            }

            fn main() {
                let c = Color_Red()
                print(name_color(c))
                let g = Color_Green()
                print(name_color(g))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "red" in lines[0]
        assert "green" in lines[1]

    def test_nested_for_loops(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let mut count: Int = 0
                for i in 0..3 {
                    for j in 0..3 {
                        count += 1
                    }
                }
                print(count)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "9" in result.stdout

    def test_if_else_chain(self) -> None:
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


# ── E2E: import between files ─────────────────────────────────────────────


class TestImportBetweenFiles:
    """E2E: import between files

    Tests multi-file compilation by generating two Python files —
    a library module and a main module — and running the main module.
    """

    def test_import_function(self) -> None:
        """Import a function from another Mapanare file."""
        lib_source = textwrap.dedent("""\
            export fn greet(name: String) -> String {
                return "Hello, " + name
            }

            fn main() {}
        """)

        main_source = textwrap.dedent("""\
            import mathlib {greet}

            fn main() {
                let msg = greet("Mapanare")
                print(msg)
            }
        """)

        # Compile both files
        lib_code = _compile_source(lib_source, "mathlib.mn")
        main_code = _compile_source(main_source, "main.mn")

        # Create a temp directory structure
        with tempfile.TemporaryDirectory(dir=_PROJECT_ROOT) as tmpdir:
            # Write lib module
            lib_path = os.path.join(tmpdir, "mathlib.py")
            with open(lib_path, "w", encoding="utf-8") as f:
                f.write(lib_code)

            # Write main module
            main_path = os.path.join(tmpdir, "main.py")
            with open(main_path, "w", encoding="utf-8") as f:
                f.write(main_code)

            result = subprocess.run(
                [sys.executable, main_path],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=_PROJECT_ROOT,
                env={**os.environ, "PYTHONPATH": tmpdir},
            )
            assert result.returncode == 0, f"stderr: {result.stderr}"
            assert "Hello, Mapanare" in result.stdout

    def test_import_agent(self) -> None:
        """Import an agent definition from another Mapanare file."""
        lib_source = textwrap.dedent("""\
            export agent Greeter {
                input name: String
                output greeting: String

                fn handle(name: String) -> String {
                    return "Hi, " + name + "!"
                }
            }

            fn main() {}
        """)

        main_source = textwrap.dedent("""\
            import agents {Greeter}

            fn main() {
                let g = spawn Greeter()
                g.name <- "World"
                let msg = sync g.greeting
                print(msg)
                sync g.stop()
            }
        """)

        lib_code = _compile_source(lib_source, "agents.mn")
        main_code = _compile_source(main_source, "main.mn")

        with tempfile.TemporaryDirectory(dir=_PROJECT_ROOT) as tmpdir:
            lib_path = os.path.join(tmpdir, "agents.py")
            with open(lib_path, "w", encoding="utf-8") as f:
                f.write(lib_code)

            main_path = os.path.join(tmpdir, "main.py")
            with open(main_path, "w", encoding="utf-8") as f:
                f.write(main_code)

            result = subprocess.run(
                [sys.executable, main_path],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=_PROJECT_ROOT,
                env={**os.environ, "PYTHONPATH": tmpdir},
            )
            assert result.returncode == 0, f"stderr: {result.stderr}"
            assert "Hi, World!" in result.stdout
