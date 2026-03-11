"""Tests for C FFI (Phase 4): extern "C" declarations, semantic checking, LLVM emission."""

from mapanare.ast_nodes import ExternFnDef, NamedType
from mapanare.parser import parse
from mapanare.semantic import check

# ---------------------------------------------------------------------------
# Task 1: Grammar — parsing extern "C" fn declarations
# ---------------------------------------------------------------------------


class TestExternFnParsing:
    """Tests for extern function declaration parsing."""

    def test_extern_fn_basic(self) -> None:
        """extern "C" fn with params and return type parses correctly."""
        ast = parse('extern "C" fn puts(s: String) -> Int')
        assert len(ast.definitions) == 1
        defn = ast.definitions[0]
        assert isinstance(defn, ExternFnDef)
        assert defn.name == "puts"
        assert defn.abi == "C"
        assert len(defn.params) == 1
        assert defn.params[0].name == "s"
        assert isinstance(defn.return_type, NamedType)
        assert defn.return_type.name == "Int"

    def test_extern_fn_no_return(self) -> None:
        """extern "C" fn with no return type defaults to Void."""
        ast = parse('extern "C" fn abort()')
        defn = ast.definitions[0]
        assert isinstance(defn, ExternFnDef)
        assert defn.name == "abort"
        assert defn.return_type is None
        assert defn.params == []

    def test_extern_fn_multiple_params(self) -> None:
        """extern "C" fn with multiple parameters."""
        ast = parse('extern "C" fn write(fd: Int, buf: String, count: Int) -> Int')
        defn = ast.definitions[0]
        assert isinstance(defn, ExternFnDef)
        assert len(defn.params) == 3
        assert defn.params[0].name == "fd"
        assert defn.params[1].name == "buf"
        assert defn.params[2].name == "count"

    def test_extern_fn_with_regular_fn(self) -> None:
        """extern "C" fn can coexist with regular fn definitions."""
        src = """extern "C" fn puts(s: String) -> Int

fn main() -> Int {
    return 0
}
"""
        ast = parse(src)
        assert len(ast.definitions) == 2
        assert isinstance(ast.definitions[0], ExternFnDef)
        assert ast.definitions[0].name == "puts"
        assert ast.definitions[1].name == "main"

    def test_extern_fn_span(self) -> None:
        """extern "C" fn has source span information."""
        ast = parse('extern "C" fn puts(s: String) -> Int')
        defn = ast.definitions[0]
        assert isinstance(defn, ExternFnDef)
        assert defn.span.line >= 1


# ---------------------------------------------------------------------------
# Task 2: Semantic checker — extern fn validation
# ---------------------------------------------------------------------------


class TestExternFnSemantic:
    """Tests for semantic checking of extern function declarations."""

    def test_extern_fn_registers_in_scope(self) -> None:
        """extern fn is callable from other functions."""
        src = """extern "C" fn puts(s: String) -> Int

fn main() -> Int {
    puts("hello")
    return 0
}
"""
        errors = check(parse(src))
        assert len(errors) == 0

    def test_extern_fn_bad_abi(self) -> None:
        """Only "C" ABI is supported."""
        src = 'extern "Rust" fn foo(x: Int) -> Int'
        errors = check(parse(src))
        assert len(errors) == 1
        assert "Unsupported ABI" in errors[0].message

    def test_extern_fn_arg_count_mismatch(self) -> None:
        """Calling extern fn with wrong number of args produces error."""
        src = """extern "C" fn puts(s: String) -> Int

fn main() -> Int {
    puts("a", "b")
    return 0
}
"""
        errors = check(parse(src))
        assert len(errors) == 1
        assert "expects 1 argument" in errors[0].message

    def test_extern_fn_void_return(self) -> None:
        """extern fn with no return type is valid."""
        src = """extern "C" fn abort()

fn main() -> Int {
    abort()
    return 0
}
"""
        errors = check(parse(src))
        assert len(errors) == 0

    def test_multiple_extern_fns(self) -> None:
        """Multiple extern fns can coexist."""
        src = """extern "C" fn puts(s: String) -> Int
extern "C" fn abort()
extern "C" fn exit(code: Int)

fn main() -> Int {
    puts("hello")
    return 0
}
"""
        errors = check(parse(src))
        assert len(errors) == 0


# ---------------------------------------------------------------------------
# Task 3: LLVM emitter — extern fn declaration and call codegen
# ---------------------------------------------------------------------------


class TestExternFnLLVM:
    """Tests for LLVM IR generation of extern function declarations."""

    def _emit(self, src: str) -> str:
        """Parse, check, and emit LLVM IR."""
        from mapanare.emit_llvm import LLVMEmitter

        ast = parse(src)
        errors = check(ast)
        assert len(errors) == 0, f"Unexpected errors: {errors}"
        emitter = LLVMEmitter(module_name="test_ffi")
        module = emitter.emit_program(ast)
        return str(module)

    def test_extern_fn_declared(self) -> None:
        """extern fn is emitted as an LLVM 'declare' (not 'define')."""
        ir = self._emit('extern "C" fn puts(s: String) -> Int')
        assert "declare" in ir
        assert '@"puts"' in ir
        # Should NOT have a body
        lines = [line for line in ir.split("\n") if "puts" in line]
        declare_line = [line for line in lines if "declare" in line]
        assert len(declare_line) >= 1

    def test_extern_fn_string_coercion(self) -> None:
        """String args are coerced from MnString {i8*, i64} to i8* for C FFI."""
        ir = self._emit("""extern "C" fn puts(s: String) -> Int

fn main() -> Int {
    puts("hello")
    return 0
}
""")
        # puts should accept i8* (not the MnString struct)
        assert "i8*" in ir
        # The call should extract the pointer from the string struct
        assert "extractvalue" in ir

    def test_extern_fn_int_params(self) -> None:
        """extern fn with Int params maps to i64."""
        ir = self._emit('extern "C" fn exit(code: Int)')
        assert "declare" in ir
        assert "i64" in ir

    def test_extern_fn_void_return_ir(self) -> None:
        """extern fn with no return type emits void."""
        ir = self._emit('extern "C" fn abort()')
        assert "declare void" in ir

    def test_extern_fn_call_emitted(self) -> None:
        """Calling an extern fn emits a call instruction."""
        ir = self._emit("""extern "C" fn exit(code: Int)

fn main() -> Int {
    exit(0)
    return 0
}
""")
        assert "call" in ir
        assert "exit" in ir


# ---------------------------------------------------------------------------
# Task 4: CLI — --link-lib flag
# ---------------------------------------------------------------------------


class TestLinkLib:
    """Tests for --link-lib linker flag passthrough."""

    def test_link_lib_parser(self) -> None:
        """--link-lib is accepted by the build subcommand."""
        from mapanare.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["build", "test.mn", "--link-lib", "m"])
        assert args.link_lib == ["m"]

    def test_link_lib_multiple(self) -> None:
        """Multiple --link-lib flags accumulate."""
        from mapanare.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(
            ["build", "test.mn", "--link-lib", "m", "--link-lib", "c", "--link-lib", "pthread"]
        )
        assert args.link_lib == ["m", "c", "pthread"]

    def test_link_lib_absent(self) -> None:
        """Without --link-lib, the attribute is None."""
        from mapanare.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["build", "test.mn"])
        assert args.link_lib is None


# ---------------------------------------------------------------------------
# Task 5: Integration — call puts from libc via FFI
# ---------------------------------------------------------------------------


class TestFFIIntegration:
    """Integration tests for FFI end-to-end."""

    def test_puts_ffi_compiles(self) -> None:
        """A program calling puts via FFI compiles to valid LLVM IR."""
        src = """extern "C" fn puts(s: String) -> Int

fn main() -> Int {
    let result: Int = puts("Hello from Mapanare FFI!")
    return 0
}
"""
        from mapanare.emit_llvm import LLVMEmitter

        ast = parse(src)
        errors = check(ast)
        assert len(errors) == 0
        emitter = LLVMEmitter(module_name="ffi_puts")
        module = emitter.emit_program(ast)
        ir = str(module)
        # Must have the extern declaration
        assert "declare" in ir and "puts" in ir
        # Must have a call to puts
        assert "call" in ir
        # Must have the string "Hello from Mapanare FFI!"
        assert "Hello from Mapanare FFI!" in ir

    def test_multiple_extern_calls(self) -> None:
        """Multiple extern fns can be declared and called."""
        src = """extern "C" fn puts(s: String) -> Int
extern "C" fn exit(code: Int)

fn main() -> Int {
    puts("test")
    exit(0)
    return 0
}
"""
        from mapanare.emit_llvm import LLVMEmitter

        ast = parse(src)
        errors = check(ast)
        assert len(errors) == 0
        emitter = LLVMEmitter(module_name="ffi_multi")
        module = emitter.emit_program(ast)
        ir = str(module)
        assert "puts" in ir
        assert "exit" in ir
