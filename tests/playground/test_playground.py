"""Tests for the WASM Playground — validates compiler bundling,
example programs, and share URL encoding/decoding."""

from __future__ import annotations

import base64
import textwrap
from pathlib import Path

import pytest

from mapanare.emit_python import PythonEmitter
from mapanare.optimizer import OptLevel, optimize
from mapanare.parser import parse
from mapanare.semantic import check_or_raise

REPO_ROOT = Path(__file__).parent.parent.parent
PLAYGROUND_DIR = REPO_ROOT / "playground"
COMPILER_DIR = PLAYGROUND_DIR / "public" / "compiler"


# ---------------------------------------------------------------------------
# Helper: compile + run a Mapanare program (same pipeline as playground worker)
# ---------------------------------------------------------------------------


def compile_and_run(source: str) -> str:
    """Compile Mapanare source to Python and execute, returning stdout."""
    ast = parse(source, filename="<test>")
    check_or_raise(ast, filename="<test>")
    ast, _ = optimize(ast, OptLevel.O0)
    emitter = PythonEmitter()
    python_code = emitter.emit(ast)

    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        exec(python_code, {"__name__": "__main__"})
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Example programs — each must compile and run without error
# ---------------------------------------------------------------------------

EXAMPLE_PROGRAMS = {
    "Hello World": textwrap.dedent("""\
        fn main() {
            println("Hello, Mapanare!")
        }
    """),
    "String Interpolation": textwrap.dedent("""\
        fn greet(name: String) -> String {
            return "Hello, ${name}! Welcome to Mapanare."
        }

        fn main() {
            let name = "World"
            println(greet(name))
            println("2 + 3 = ${2 + 3}")
        }
    """),
    "Fibonacci": textwrap.dedent("""\
        fn fib(n: Int) -> Int {
            if n <= 1 {
                return n
            }
            return fib(n - 1) + fib(n - 2)
        }

        fn main() {
            let mut i = 0
            while i < 10 {
                println("fib(${i}) = ${fib(i)}")
                i = i + 1
            }
        }
    """),
    "Structs & Enums": textwrap.dedent("""\
        struct Point { x: Float, y: Float }

        enum Shape {
            Circle(Float),
            Rect(Float, Float)
        }

        fn describe(s: Shape) -> String {
            match s {
                Shape_Circle(r) => { return "Circle area: " + str(3.14159 * r * r) },
                Shape_Rect(w, h) => { return "Rect area: " + str(w * h) },
                _ => { return "unknown" }
            }
            return "unreachable"
        }

        fn main() {
            let c = Shape_Circle(5.0)
            let r = Shape_Rect(4.0, 6.0)
            println(describe(c))
            println(describe(r))
        }
    """),
    "Option & Result": textwrap.dedent("""\
        fn divide(a: Float, b: Float) -> Result<Float, String> {
            if b == 0.0 {
                return Err("division by zero")
            }
            return Ok(a / b)
        }

        fn find_first(items: List<Int>, target: Int) -> Option<Int> {
            let mut i = 0
            while i < len(items) {
                if items[i] == target {
                    return Some(i)
                }
                i = i + 1
            }
            return none
        }

        fn main() {
            let result = divide(10.0, 3.0)
            println("10 / 3 = ${result}")

            let err = divide(1.0, 0.0)
            println("1 / 0 = ${err}")

            let nums = [1, 2, 3, 4, 5]
            println("find 3: ${find_first(nums, 3)}")
            println("find 9: ${find_first(nums, 9)}")
        }
    """),
    "Higher-Order Functions": textwrap.dedent("""\
        fn apply(f: fn(Int) -> Int, x: Int) -> Int {
            return f(x)
        }

        fn main() {
            let double = (x) => x * 2
            let square = (x) => x * x

            println("double(5) = ${apply(double, 5)}")
            println("square(5) = ${apply(square, 5)}")
        }
    """),
    "Pipe Operator": textwrap.dedent("""\
        fn double(x: Int) -> Int {
            return x * 2
        }

        fn add_one(x: Int) -> Int {
            return x + 1
        }

        fn main() {
            let result = 5 |> double |> add_one
            println("5 |> double |> add_one = ${result}")
        }
    """),
}


@pytest.mark.parametrize("name", list(EXAMPLE_PROGRAMS.keys()))
def test_example_compiles_and_runs(name: str) -> None:
    """Each playground example must compile and execute without error."""
    source = EXAMPLE_PROGRAMS[name]
    output = compile_and_run(source)
    assert isinstance(output, str)
    assert len(output) > 0, f"Example '{name}' produced no output"


def test_hello_world_output() -> None:
    """Hello World example produces correct output."""
    output = compile_and_run(EXAMPLE_PROGRAMS["Hello World"])
    assert output.strip() == "Hello, Mapanare!"


def test_fibonacci_output() -> None:
    """Fibonacci example produces correct sequence."""
    output = compile_and_run(EXAMPLE_PROGRAMS["Fibonacci"])
    lines = output.strip().split("\n")
    assert len(lines) == 10
    assert "fib(0) = 0" in lines[0]
    assert "fib(1) = 1" in lines[1]
    assert "fib(9) = 34" in lines[9]


def test_interpolation_output() -> None:
    """String interpolation example works correctly."""
    output = compile_and_run(EXAMPLE_PROGRAMS["String Interpolation"])
    assert "Hello, World! Welcome to Mapanare." in output
    assert "2 + 3 = 5" in output


def test_option_result_output() -> None:
    """Option/Result example works correctly."""
    output = compile_and_run(EXAMPLE_PROGRAMS["Option & Result"])
    assert "division by zero" in output.lower() or "Err" in output


# ---------------------------------------------------------------------------
# Share URL encoding/decoding
# ---------------------------------------------------------------------------


def _encode_share(code: str) -> str:
    """Encode source code the same way the JS playground does."""
    encoded_bytes = code.encode("utf-8")
    return base64.b64encode(encoded_bytes).decode("ascii")


def _decode_share(encoded: str) -> str:
    """Decode a share hash back to source code."""
    return base64.b64decode(encoded).decode("utf-8")


def test_share_roundtrip_simple() -> None:
    """Simple ASCII code survives share encoding roundtrip."""
    code = 'fn main() {\n    println("hello")\n}'
    encoded = _encode_share(code)
    decoded = _decode_share(encoded)
    assert decoded == code


def test_share_roundtrip_unicode() -> None:
    """Unicode characters survive share encoding roundtrip."""
    code = 'fn main() {\n    println("Hola Mundo")\n}'
    encoded = _encode_share(code)
    decoded = _decode_share(encoded)
    assert decoded == code


def test_share_roundtrip_interpolation() -> None:
    """String interpolation syntax survives share encoding."""
    code = 'fn main() {\n    let x = 42\n    println("value: ${x}")\n}'
    encoded = _encode_share(code)
    decoded = _decode_share(encoded)
    assert decoded == code


def test_share_roundtrip_large_program() -> None:
    """A larger program survives share encoding."""
    code = EXAMPLE_PROGRAMS["Fibonacci"]
    encoded = _encode_share(code)
    decoded = _decode_share(encoded)
    assert decoded == code


# ---------------------------------------------------------------------------
# Compiler bundling — required modules exist
# ---------------------------------------------------------------------------


REQUIRED_COMPILER_FILES = [
    "ast_nodes.py",
    "types.py",
    "parser.py",
    "semantic.py",
    "optimizer.py",
    "emit_python.py",
    "diagnostics.py",
    "mapanare.lark",
    "__init__.py",
]

REQUIRED_RUNTIME_FILES = [
    "__init__.py",
    "agent.py",
    "signal.py",
    "stream.py",
    "result.py",
]


@pytest.mark.parametrize("filename", REQUIRED_COMPILER_FILES)
def test_compiler_module_bundled(filename: str) -> None:
    """Each required compiler module must exist in public/compiler/."""
    path = COMPILER_DIR / filename
    assert path.exists(), f"Missing bundled compiler module: {filename}"
    assert path.stat().st_size > 0, f"Bundled module is empty: {filename}"


@pytest.mark.parametrize("filename", REQUIRED_RUNTIME_FILES)
def test_runtime_module_bundled(filename: str) -> None:
    """Each required runtime module must exist in public/compiler/runtime/."""
    path = COMPILER_DIR / "runtime" / filename
    assert path.exists(), f"Missing bundled runtime module: {filename}"
    assert path.stat().st_size > 0, f"Bundled runtime module is empty: {filename}"


# ---------------------------------------------------------------------------
# Playground project structure
# ---------------------------------------------------------------------------


def test_playground_index_html_exists() -> None:
    """index.html must exist in the playground directory."""
    assert (PLAYGROUND_DIR / "index.html").exists()


def test_playground_package_json_exists() -> None:
    """package.json must exist in the playground directory."""
    assert (PLAYGROUND_DIR / "package.json").exists()


def test_playground_main_js_exists() -> None:
    """Main JS entry point must exist."""
    assert (PLAYGROUND_DIR / "src" / "main.js").exists()


def test_playground_worker_js_exists() -> None:
    """Web worker must exist."""
    assert (PLAYGROUND_DIR / "src" / "worker.js").exists()


def test_playground_style_css_exists() -> None:
    """Stylesheet must exist."""
    assert (PLAYGROUND_DIR / "src" / "style.css").exists()


def test_playground_examples_js_exists() -> None:
    """Examples module must exist."""
    assert (PLAYGROUND_DIR / "src" / "examples.js").exists()


def test_playground_mn_lang_js_exists() -> None:
    """Syntax highlighting module must exist."""
    assert (PLAYGROUND_DIR / "src" / "mn-lang.js").exists()


def test_playground_vite_config_exists() -> None:
    """Vite config must exist."""
    assert (PLAYGROUND_DIR / "vite.config.js").exists()


def test_deploy_workflow_exists() -> None:
    """GitHub Actions deploy workflow must exist."""
    workflow = REPO_ROOT / ".github" / "workflows" / "playground.yml"
    assert workflow.exists()


def test_bundle_script_exists() -> None:
    """Bundle script must exist."""
    script = PLAYGROUND_DIR / "scripts" / "bundle-compiler.sh"
    assert script.exists()


# ---------------------------------------------------------------------------
# At least 5 examples
# ---------------------------------------------------------------------------


def test_at_least_five_examples() -> None:
    """The playground must have at least 5 pre-loaded examples."""
    assert len(EXAMPLE_PROGRAMS) >= 5


# ---------------------------------------------------------------------------
# Error display — compiler errors are caught and reported
# ---------------------------------------------------------------------------


def test_parse_error_is_caught() -> None:
    """Parse errors should be caught, not crash."""
    from mapanare.parser import ParseError

    with pytest.raises(ParseError):
        parse("fn main( { broken", filename="<test>")


def test_semantic_error_is_caught() -> None:
    """Semantic errors should be caught, not crash."""
    from mapanare.semantic import SemanticErrors

    source = textwrap.dedent("""\
        fn main() {
            let x: Int = "not an int"
        }
    """)
    ast = parse(source, filename="<test>")
    with pytest.raises(SemanticErrors):
        check_or_raise(ast, filename="<test>")
