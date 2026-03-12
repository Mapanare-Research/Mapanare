"""Tests for Python interop (Phase 3): extern "Python" declarations,
semantic checking, and Python emission."""

from mapanare.ast_nodes import ExternFnDef, GenericType, NamedType
from mapanare.parser import parse
from mapanare.semantic import check

# ---------------------------------------------------------------------------
# Task 1-2: Grammar & AST — parsing extern "Python" fn declarations
# ---------------------------------------------------------------------------


class TestExternPythonParsing:
    """Tests for extern 'Python' function declaration parsing."""

    def test_extern_python_basic(self) -> None:
        """extern 'Python' fn with module::name parses correctly."""
        ast = parse('extern "Python" fn math::sqrt(x: Float) -> Float')
        assert len(ast.definitions) == 1
        defn = ast.definitions[0]
        assert isinstance(defn, ExternFnDef)
        assert defn.name == "sqrt"
        assert defn.abi == "Python"
        assert defn.module == "math"
        assert len(defn.params) == 1
        assert defn.params[0].name == "x"
        assert isinstance(defn.return_type, NamedType)
        assert defn.return_type.name == "Float"

    def test_extern_python_no_return(self) -> None:
        """extern 'Python' fn with no return type."""
        ast = parse('extern "Python" fn os::chdir(path: String)')
        defn = ast.definitions[0]
        assert isinstance(defn, ExternFnDef)
        assert defn.name == "chdir"
        assert defn.module == "os"
        assert defn.return_type is None

    def test_extern_python_multiple_params(self) -> None:
        """extern 'Python' fn with multiple parameters."""
        ast = parse('extern "Python" fn json::dumps(obj: String, indent: Int) -> String')
        defn = ast.definitions[0]
        assert isinstance(defn, ExternFnDef)
        assert defn.module == "json"
        assert defn.name == "dumps"
        assert len(defn.params) == 2

    def test_extern_python_no_params(self) -> None:
        """extern 'Python' fn with no parameters."""
        ast = parse('extern "Python" fn os::getcwd() -> String')
        defn = ast.definitions[0]
        assert isinstance(defn, ExternFnDef)
        assert defn.name == "getcwd"
        assert defn.module == "os"
        assert defn.params == []

    def test_extern_python_with_regular_fn(self) -> None:
        """extern 'Python' fn can coexist with regular fn definitions."""
        src = """extern "Python" fn math::sqrt(x: Float) -> Float

fn main() {
    let result: Float = sqrt(4.0)
    println(result)
}
"""
        ast = parse(src)
        assert len(ast.definitions) == 2
        assert isinstance(ast.definitions[0], ExternFnDef)
        assert ast.definitions[0].abi == "Python"

    def test_extern_python_with_extern_c(self) -> None:
        """extern 'Python' and extern 'C' can coexist."""
        src = """extern "C" fn puts(s: String) -> Int
extern "Python" fn math::sqrt(x: Float) -> Float
"""
        ast = parse(src)
        assert len(ast.definitions) == 2
        c_fn = ast.definitions[0]
        py_fn = ast.definitions[1]
        assert isinstance(c_fn, ExternFnDef) and c_fn.abi == "C"
        assert isinstance(py_fn, ExternFnDef) and py_fn.abi == "Python"

    def test_extern_python_result_return(self) -> None:
        """extern 'Python' fn with Result return type."""
        ast = parse('extern "Python" fn json::loads(s: String) -> Result<String, String>')
        defn = ast.definitions[0]
        assert isinstance(defn, ExternFnDef)
        assert isinstance(defn.return_type, GenericType)
        assert defn.return_type.name == "Result"

    def test_extern_python_span(self) -> None:
        """extern 'Python' fn has source span information."""
        ast = parse('extern "Python" fn math::sqrt(x: Float) -> Float')
        defn = ast.definitions[0]
        assert isinstance(defn, ExternFnDef)
        assert defn.span.line >= 1


# ---------------------------------------------------------------------------
# Task 3: Semantic checker — extern Python fn validation
# ---------------------------------------------------------------------------


class TestExternPythonSemantic:
    """Tests for semantic checking of extern Python function declarations."""

    def test_extern_python_registers_in_scope(self) -> None:
        """extern 'Python' fn is callable from other functions."""
        src = """extern "Python" fn math::sqrt(x: Float) -> Float

fn main() {
    let result: Float = sqrt(4.0)
    println(result)
}
"""
        errors = check(parse(src))
        assert len(errors) == 0

    def test_extern_python_bad_abi(self) -> None:
        """Unsupported ABI produces error."""
        src = 'extern "Java" fn foo(x: Int) -> Int'
        errors = check(parse(src))
        assert len(errors) == 1
        assert "Unsupported ABI" in errors[0].message

    def test_extern_python_accepts_c_and_python(self) -> None:
        """Both C and Python ABIs are accepted."""
        src = """extern "C" fn puts(s: String) -> Int
extern "Python" fn math::sqrt(x: Float) -> Float

fn main() {
    let a: Int = puts("hello")
    let b: Float = sqrt(9.0)
}
"""
        errors = check(parse(src))
        assert len(errors) == 0

    def test_extern_python_no_module_error(self) -> None:
        """extern 'Python' without module qualifier produces error."""
        src = 'extern "Python" fn sqrt(x: Float) -> Float'
        errors = check(parse(src))
        assert len(errors) == 1
        assert "module qualifier" in errors[0].message

    def test_extern_python_arg_count_mismatch(self) -> None:
        """Calling extern Python fn with wrong arg count produces error."""
        src = """extern "Python" fn math::sqrt(x: Float) -> Float

fn main() {
    sqrt(1.0, 2.0)
}
"""
        errors = check(parse(src))
        assert len(errors) == 1
        assert "expects 1 argument" in errors[0].message

    def test_extern_python_multiple(self) -> None:
        """Multiple extern Python fns can coexist."""
        src = """extern "Python" fn math::sqrt(x: Float) -> Float
extern "Python" fn math::floor(x: Float) -> Float
extern "Python" fn os::getcwd() -> String

fn main() {
    let a: Float = sqrt(9.0)
    let b: Float = floor(3.7)
    let c: String = getcwd()
}
"""
        errors = check(parse(src))
        assert len(errors) == 0


# ---------------------------------------------------------------------------
# Task 4-5: Python emitter — import generation and type marshalling
# ---------------------------------------------------------------------------


class TestExternPythonEmit:
    """Tests for Python code emission of extern Python interop."""

    def _emit(self, src: str, python_path: list[str] | None = None) -> str:
        """Parse, check, and emit Python code."""
        from mapanare.emit_python import PythonEmitter

        ast = parse(src)
        errors = check(ast)
        assert len(errors) == 0, f"Unexpected errors: {errors}"
        emitter = PythonEmitter(python_path=python_path)
        return emitter.emit(ast)

    def test_emits_import(self) -> None:
        """extern 'Python' fn generates an import statement."""
        code = self._emit("""extern "Python" fn math::sqrt(x: Float) -> Float

fn main() {
    let r: Float = sqrt(4.0)
}
""")
        assert "import math" in code

    def test_emits_wrapper_function(self) -> None:
        """extern 'Python' fn generates a wrapper that calls module.function."""
        code = self._emit("""extern "Python" fn math::sqrt(x: Float) -> Float

fn main() {
    let r: Float = sqrt(4.0)
}
""")
        assert "def sqrt(x):" in code
        assert "math.sqrt(x)" in code

    def test_emits_result_wrapper(self) -> None:
        """extern 'Python' fn with Result return type wraps in try/except."""
        code = self._emit("""extern "Python" fn json::loads(s: String) -> Result<String, String>

fn main() {
    let r: Result<String, String> = loads("{}")
}
""")
        assert "try:" in code
        assert "Ok(json.loads(s))" in code
        assert "except Exception" in code
        assert "Err(str(" in code

    def test_emits_python_path(self) -> None:
        """--python-path generates sys.path.insert."""
        code = self._emit(
            """extern "Python" fn math::sqrt(x: Float) -> Float

fn main() {
    let r: Float = sqrt(4.0)
}
""",
            python_path=["/custom/path"],
        )
        assert "import sys" in code
        assert "sys.path.insert(0, '/custom/path')" in code

    def test_multiple_modules_import(self) -> None:
        """Multiple extern fns from different modules generate separate imports."""
        code = self._emit("""extern "Python" fn math::sqrt(x: Float) -> Float
extern "Python" fn os::getcwd() -> String

fn main() {
    let a: Float = sqrt(4.0)
    let b: String = getcwd()
}
""")
        assert "import math" in code
        assert "import os" in code

    def test_same_module_single_import(self) -> None:
        """Multiple extern fns from same module generate one import."""
        code = self._emit("""extern "Python" fn math::sqrt(x: Float) -> Float
extern "Python" fn math::floor(x: Float) -> Float

fn main() {
    let a: Float = sqrt(4.0)
    let b: Float = floor(3.7)
}
""")
        # Should only have one 'import math' line
        assert code.count("import math") == 1

    def test_void_return_wrapper(self) -> None:
        """extern 'Python' fn with no return type still generates wrapper."""
        code = self._emit("""extern "Python" fn os::chdir(path: String)

fn main() {
    chdir("/tmp")
}
""")
        assert "def chdir(path):" in code
        assert "os.chdir(path)" in code


# ---------------------------------------------------------------------------
# Task 6: CLI — --python-path flag
# ---------------------------------------------------------------------------


class TestPythonPathCLI:
    """Tests for --python-path CLI flag."""

    def test_python_path_compile(self) -> None:
        """--python-path is accepted by the compile subcommand."""
        from mapanare.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["compile", "test.mn", "--python-path", "/custom/lib"])
        assert args.python_path == ["/custom/lib"]

    def test_python_path_run(self) -> None:
        """--python-path is accepted by the run subcommand."""
        from mapanare.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["run", "test.mn", "--python-path", "/custom/lib"])
        assert args.python_path == ["/custom/lib"]

    def test_python_path_multiple(self) -> None:
        """Multiple --python-path flags accumulate."""
        from mapanare.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["run", "test.mn", "--python-path", "/a", "--python-path", "/b"])
        assert args.python_path == ["/a", "/b"]

    def test_python_path_absent(self) -> None:
        """Without --python-path, the attribute is None."""
        from mapanare.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["run", "test.mn"])
        assert args.python_path is None


# ---------------------------------------------------------------------------
# Task 8: Test — call math.sqrt from Mapanare
# ---------------------------------------------------------------------------


class TestMathSqrt:
    """Tests for calling math.sqrt from Mapanare."""

    def test_math_sqrt_compiles(self) -> None:
        """A program calling math.sqrt compiles to valid Python."""
        src = """extern "Python" fn math::sqrt(x: Float) -> Float

fn main() {
    let result: Float = sqrt(16.0)
    println(result)
}
"""
        from mapanare.emit_python import PythonEmitter

        ast = parse(src)
        errors = check(ast)
        assert len(errors) == 0
        emitter = PythonEmitter()
        code = emitter.emit(ast)
        assert "import math" in code
        assert "math.sqrt" in code

    def test_math_sqrt_executes(self) -> None:
        """math.sqrt actually executes correctly via Python interop."""
        src = """extern "Python" fn math::sqrt(x: Float) -> Float

fn main() {
    let result: Float = sqrt(16.0)
    println(result)
}
"""
        from mapanare.emit_python import PythonEmitter

        ast = parse(src)
        errors = check(ast)
        assert len(errors) == 0
        emitter = PythonEmitter()
        code = emitter.emit(ast)

        # Execute and capture output
        import io
        import sys

        old_stdout = sys.stdout
        sys.stdout = captured = io.StringIO()
        try:
            exec(compile(code, "<test>", "exec"), {"__name__": "__main__"})
        finally:
            sys.stdout = old_stdout
        output = captured.getvalue().strip()
        assert output == "4.0"

    def test_math_floor_executes(self) -> None:
        """math.floor works via Python interop."""
        src = """extern "Python" fn math::floor(x: Float) -> Int

fn main() {
    let result: Int = floor(3.7)
    println(result)
}
"""
        from mapanare.emit_python import PythonEmitter

        ast = parse(src)
        errors = check(ast)
        assert len(errors) == 0
        emitter = PythonEmitter()
        code = emitter.emit(ast)

        import io
        import sys

        old_stdout = sys.stdout
        sys.stdout = captured = io.StringIO()
        try:
            exec(compile(code, "<test>", "exec"), {"__name__": "__main__"})
        finally:
            sys.stdout = old_stdout
        output = captured.getvalue().strip()
        assert output == "3"


# ---------------------------------------------------------------------------
# Task 9: Test — call json.loads / json.dumps from Mapanare
# ---------------------------------------------------------------------------


class TestJsonInterop:
    """Tests for calling json.loads and json.dumps from Mapanare."""

    def test_json_dumps_compiles(self) -> None:
        """json.dumps compiles correctly."""
        src = """extern "Python" fn json::dumps(obj: String) -> String

fn main() {
    let result: String = dumps("hello")
    println(result)
}
"""
        ast = parse(src)
        errors = check(ast)
        assert len(errors) == 0

    def test_json_loads_with_result(self) -> None:
        """json.loads with Result return type wraps errors."""
        src = """extern "Python" fn json::loads(s: String) -> Result<String, String>

fn main() {
    let result: Result<String, String> = loads("{}")
}
"""
        from mapanare.emit_python import PythonEmitter

        ast = parse(src)
        errors = check(ast)
        assert len(errors) == 0
        emitter = PythonEmitter()
        code = emitter.emit(ast)
        assert "try:" in code
        assert "json.loads" in code

    def test_json_loads_error_wrapped(self) -> None:
        """json.loads with invalid JSON returns Err via Result wrapper."""
        src = """extern "Python" fn json::loads(s: String) -> Result<String, String>

fn main() {
    let result: Result<String, String> = loads("not valid json")
}
"""
        from mapanare.emit_python import PythonEmitter

        ast = parse(src)
        errors = check(ast)
        assert len(errors) == 0
        emitter = PythonEmitter()
        code = emitter.emit(ast)
        # Execute — should not raise, error is captured in Err
        exec(compile(code, "<test>", "exec"), {"__name__": "__test__"})


# ---------------------------------------------------------------------------
# Task 10: Test — numpy (stretch goal)
# ---------------------------------------------------------------------------


class TestNumpyInterop:
    """Tests for calling numpy from Mapanare (stretch goal)."""

    def test_numpy_compiles(self) -> None:
        """A program using numpy compiles (even if numpy is not installed)."""
        src = """extern "Python" fn numpy::array(data: List<Float>) -> String

fn main() {
    let arr: String = array([1.0, 2.0, 3.0])
}
"""
        ast = parse(src)
        errors = check(ast)
        assert len(errors) == 0

        from mapanare.emit_python import PythonEmitter

        emitter = PythonEmitter()
        code = emitter.emit(ast)
        assert "import numpy" in code
        assert "numpy.array" in code


# ---------------------------------------------------------------------------
# Task 12: E2E tests for Python interop
# ---------------------------------------------------------------------------


class TestPythonInteropE2E:
    """End-to-end tests for Python interop."""

    def test_multiple_modules_e2e(self) -> None:
        """Program using multiple Python modules compiles and runs."""
        src = """extern "Python" fn math::sqrt(x: Float) -> Float
extern "Python" fn math::pi() -> Float
extern "Python" fn os::getpid() -> Int

fn main() {
    let s: Float = sqrt(25.0)
    println(s)
}
"""
        from mapanare.emit_python import PythonEmitter

        ast = parse(src)
        errors = check(ast)
        assert len(errors) == 0
        emitter = PythonEmitter()
        code = emitter.emit(ast)
        assert "import math" in code
        assert "import os" in code

        # Execute — sqrt(25) should print 5.0
        import io
        import sys

        old_stdout = sys.stdout
        sys.stdout = captured = io.StringIO()
        try:
            exec(compile(code, "<test>", "exec"), {"__name__": "__main__"})
        finally:
            sys.stdout = old_stdout
        output = captured.getvalue().strip()
        assert output == "5.0"

    def test_extern_c_not_affected(self) -> None:
        """extern 'C' declarations still work (backward compatibility)."""
        src = 'extern "C" fn puts(s: String) -> Int'
        ast = parse(src)
        defn = ast.definitions[0]
        assert isinstance(defn, ExternFnDef)
        assert defn.abi == "C"
        assert defn.module is None
        errors = check(ast)
        assert len(errors) == 0

    def test_full_pipeline_math(self) -> None:
        """Full pipeline: parse → check → optimize → emit → execute."""
        from mapanare.emit_python import PythonEmitter
        from mapanare.optimizer import OptLevel, optimize

        src = """extern "Python" fn math::sqrt(x: Float) -> Float
extern "Python" fn math::ceil(x: Float) -> Int

fn main() {
    let a: Float = sqrt(2.0)
    let b: Int = ceil(a)
    println(b)
}
"""
        ast = parse(src)
        errors = check(ast)
        assert len(errors) == 0
        ast, _ = optimize(ast, OptLevel.O2)
        emitter = PythonEmitter()
        code = emitter.emit(ast)

        import io
        import sys

        old_stdout = sys.stdout
        sys.stdout = captured = io.StringIO()
        try:
            exec(compile(code, "<test>", "exec"), {"__name__": "__main__"})
        finally:
            sys.stdout = old_stdout
        output = captured.getvalue().strip()
        assert output == "2"

    def test_llvm_emitter_skips_python_extern(self) -> None:
        """LLVM emitter skips extern 'Python' fns without error."""
        src = """extern "Python" fn math::sqrt(x: Float) -> Float

fn main() -> Int {
    return 0
}
"""
        from mapanare.emit_llvm import LLVMEmitter

        ast = parse(src)
        errors = check(ast)
        assert len(errors) == 0
        emitter = LLVMEmitter(module_name="test_skip_python")
        module = emitter.emit_program(ast)
        ir = str(module)
        # Should NOT declare sqrt as extern (it's Python-only)
        assert "sqrt" not in ir
        # main should still exist
        assert "main" in ir

    def test_lsp_analysis_python_extern(self) -> None:
        """LSP analysis handles extern 'Python' fn declarations."""
        from mapanare.lsp.analysis import analyze_document

        src = """extern "Python" fn math::sqrt(x: Float) -> Float

fn main() {
    let r: Float = sqrt(4.0)
}
"""
        analysis, diagnostics = analyze_document("file:///test.mn", src)
        # Should not crash; symbols should include sqrt
        assert analysis is not None
        assert "sqrt" in analysis.symbols
