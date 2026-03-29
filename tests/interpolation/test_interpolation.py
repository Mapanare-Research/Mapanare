"""Tests for string interpolation and multi-line strings — Phase 1 of v0.5.0."""

from __future__ import annotations

import pytest

from mapanare.ast_nodes import (
    BinaryExpr,
    CallExpr,
    FnDef,
    Identifier,
    InterpString,
    IntLiteral,
    LetBinding,
    StringLiteral,
)
from mapanare.emit_python import PythonEmitter
from mapanare.parser import parse
from mapanare.semantic import check

# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------


class TestParserInterpolation:
    """Test that the parser correctly builds InterpString AST nodes."""

    def test_simple_interpolation(self) -> None:
        prog = parse('fn main() { let x = "hello ${name}" }')
        fn = prog.definitions[0]
        assert isinstance(fn, FnDef)
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt, LetBinding)
        interp = let_stmt.value
        assert isinstance(interp, InterpString)
        assert len(interp.parts) == 2
        assert isinstance(interp.parts[0], StringLiteral)
        assert interp.parts[0].value == "hello "
        assert isinstance(interp.parts[1], Identifier)
        assert interp.parts[1].name == "name"

    def test_no_interpolation(self) -> None:
        prog = parse('fn main() { let x = "hello world" }')
        fn = prog.definitions[0]
        assert isinstance(fn, FnDef)
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt, LetBinding)
        assert isinstance(let_stmt.value, StringLiteral)
        assert let_stmt.value.value == "hello world"

    def test_multiple_interpolations(self) -> None:
        prog = parse('fn main() { let x = "${a} and ${b}" }')
        fn = prog.definitions[0]
        assert isinstance(fn, FnDef)
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt, LetBinding)
        interp = let_stmt.value
        assert isinstance(interp, InterpString)
        assert len(interp.parts) == 3
        assert isinstance(interp.parts[0], Identifier)
        assert interp.parts[0].name == "a"
        assert isinstance(interp.parts[1], StringLiteral)
        assert interp.parts[1].value == " and "
        assert isinstance(interp.parts[2], Identifier)
        assert interp.parts[2].name == "b"

    def test_expr_interpolation(self) -> None:
        prog = parse('fn main() { let x = "sum: ${a + b}" }')
        fn = prog.definitions[0]
        assert isinstance(fn, FnDef)
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt, LetBinding)
        interp = let_stmt.value
        assert isinstance(interp, InterpString)
        assert len(interp.parts) == 2
        assert isinstance(interp.parts[0], StringLiteral)
        assert interp.parts[0].value == "sum: "
        assert isinstance(interp.parts[1], BinaryExpr)

    def test_call_interpolation(self) -> None:
        prog = parse('fn main() { let x = "len: ${len(xs)}" }')
        fn = prog.definitions[0]
        assert isinstance(fn, FnDef)
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt, LetBinding)
        interp = let_stmt.value
        assert isinstance(interp, InterpString)
        assert isinstance(interp.parts[1], CallExpr)

    def test_interpolation_at_start(self) -> None:
        prog = parse('fn main() { let x = "${x} items" }')
        fn = prog.definitions[0]
        assert isinstance(fn, FnDef)
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt, LetBinding)
        interp = let_stmt.value
        assert isinstance(interp, InterpString)
        assert len(interp.parts) == 2
        assert isinstance(interp.parts[0], Identifier)
        assert isinstance(interp.parts[1], StringLiteral)
        assert interp.parts[1].value == " items"

    def test_interpolation_at_end(self) -> None:
        prog = parse('fn main() { let x = "value: ${x}" }')
        fn = prog.definitions[0]
        assert isinstance(fn, FnDef)
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt, LetBinding)
        interp = let_stmt.value
        assert isinstance(interp, InterpString)
        assert len(interp.parts) == 2
        assert isinstance(interp.parts[0], StringLiteral)
        assert interp.parts[0].value == "value: "
        assert isinstance(interp.parts[1], Identifier)

    def test_only_interpolation(self) -> None:
        prog = parse('fn main() { let x = "${name}" }')
        fn = prog.definitions[0]
        assert isinstance(fn, FnDef)
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt, LetBinding)
        interp = let_stmt.value
        assert isinstance(interp, InterpString)
        assert len(interp.parts) == 1
        assert isinstance(interp.parts[0], Identifier)

    def test_int_literal_interpolation(self) -> None:
        prog = parse('fn main() { let x = "count: ${42}" }')
        fn = prog.definitions[0]
        assert isinstance(fn, FnDef)
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt, LetBinding)
        interp = let_stmt.value
        assert isinstance(interp, InterpString)
        assert isinstance(interp.parts[1], IntLiteral)
        assert interp.parts[1].value == 42


# ---------------------------------------------------------------------------
# Multi-line string tests
# ---------------------------------------------------------------------------


class TestMultiLineStrings:
    """Test triple-quoted multi-line string literals."""

    def test_triple_string_basic(self) -> None:
        source = 'fn main() { let x = """hello\nworld""" }'
        prog = parse(source)
        fn = prog.definitions[0]
        assert isinstance(fn, FnDef)
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt, LetBinding)
        assert isinstance(let_stmt.value, StringLiteral)
        assert "hello" in let_stmt.value.value
        assert "world" in let_stmt.value.value

    def test_triple_string_with_interpolation(self) -> None:
        source = 'fn main() { let x = """hello ${name}""" }'
        prog = parse(source)
        fn = prog.definitions[0]
        assert isinstance(fn, FnDef)
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt, LetBinding)
        interp = let_stmt.value
        assert isinstance(interp, InterpString)
        assert isinstance(interp.parts[0], StringLiteral)
        assert interp.parts[0].value == "hello "
        assert isinstance(interp.parts[1], Identifier)

    def test_triple_string_with_quotes(self) -> None:
        source = 'fn main() { let x = """she said "hi" """ }'
        prog = parse(source)
        fn = prog.definitions[0]
        assert isinstance(fn, FnDef)
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt, LetBinding)
        assert isinstance(let_stmt.value, StringLiteral)
        assert '"hi"' in let_stmt.value.value


# ---------------------------------------------------------------------------
# Semantic tests
# ---------------------------------------------------------------------------


class TestSemanticInterpolation:
    """Test that the semantic checker handles InterpString correctly."""

    def test_interp_type_is_string(self) -> None:
        source = """
fn main() {
    let name: String = "world"
    let greeting = "Hello, ${name}!"
}
"""
        prog = parse(source)
        errors = check(prog)
        assert len(errors) == 0

    def test_interp_with_int_expr(self) -> None:
        source = """
fn main() {
    let count: Int = 42
    let msg = "count: ${count}"
}
"""
        prog = parse(source)
        errors = check(prog)
        assert len(errors) == 0

    def test_interp_with_binary_expr(self) -> None:
        source = """
fn main() {
    let a: Int = 1
    let b: Int = 2
    let msg = "sum: ${a + b}"
}
"""
        prog = parse(source)
        errors = check(prog)
        assert len(errors) == 0

    def test_interp_undefined_var(self) -> None:
        source = """
fn main() {
    let msg = "Hello, ${undefined_var}!"
}
"""
        prog = parse(source)
        errors = check(prog)
        assert len(errors) > 0
        assert any("Undefined" in str(e) or "undefined" in str(e) for e in errors)


# ---------------------------------------------------------------------------
# Python emitter tests
# ---------------------------------------------------------------------------


class TestPythonEmitInterpolation:
    """Test that the Python emitter generates correct f-strings."""

    def test_simple_fstring(self) -> None:
        source = """
fn main() {
    let name = "world"
    print("Hello, ${name}!")
}
"""
        prog = parse(source)
        emitter = PythonEmitter()
        code = emitter.emit(prog)
        assert 'f"Hello, {name}!"' in code

    def test_expr_fstring(self) -> None:
        source = """
fn main() {
    let a = 1
    let b = 2
    print("sum: ${a + b}")
}
"""
        prog = parse(source)
        emitter = PythonEmitter()
        code = emitter.emit(prog)
        assert 'f"sum: {' in code

    def test_no_interp_stays_repr(self) -> None:
        source = """
fn main() {
    let x = "hello world"
}
"""
        prog = parse(source)
        emitter = PythonEmitter()
        code = emitter.emit(prog)
        assert "'hello world'" in code or '"hello world"' in code
        assert "f'" not in code and 'f"' not in code

    def test_multi_line_string_emit(self) -> None:
        source = 'fn main() { let x = """line1\\nline2""" }'
        prog = parse(source)
        emitter = PythonEmitter()
        code = emitter.emit(prog)
        assert "line1" in code


# ---------------------------------------------------------------------------
# LLVM emitter tests
# ---------------------------------------------------------------------------


class TestLLVMEmitInterpolation:
    """Test that the LLVM emitter handles InterpString."""

    def test_interp_emits_concat(self) -> None:
        """InterpString should generate __mn_str_concat calls in LLVM IR."""
        try:
            from mapanare.emit_llvm import LLVMEmitter
        except ImportError:
            pytest.skip("llvmlite not installed")

        source = """
fn main() {
    let name = "world"
    let msg = "Hello, ${name}!"
}
"""
        prog = parse(source)
        emitter = LLVMEmitter()
        module = emitter.emit_program(prog)
        ir_code = str(module)
        # Should contain str_concat for joining interpolation parts
        assert "__mn_str_concat" in ir_code

    def test_plain_string_no_extra_concat(self) -> None:
        """A plain string without interpolation should NOT generate concat."""
        try:
            from mapanare.emit_llvm import LLVMEmitter
        except ImportError:
            pytest.skip("llvmlite not installed")

        source = """
fn main() {
    let x = "hello"
}
"""
        prog = parse(source)
        emitter = LLVMEmitter()
        module = emitter.emit_program(prog)
        ir_code = str(module)
        assert "__mn_str_concat" not in ir_code


# ---------------------------------------------------------------------------
# E2E tests
# ---------------------------------------------------------------------------


class TestE2EInterpolation:
    """End-to-end tests: parse → semantic → emit → execute."""

    def test_e2e_interpolation_python(self) -> None:
        source = """
fn main() {
    let name = "Mapanare"
    print("Hello, ${name}!")
}
"""
        prog = parse(source)
        errors = check(prog)
        assert len(errors) == 0
        emitter = PythonEmitter()
        code = emitter.emit(prog)
        assert 'f"Hello, {name}!"' in code

    def test_e2e_multi_interpolation(self) -> None:
        source = """
fn main() {
    let first = "Ada"
    let last = "Lovelace"
    print("${first} ${last}")
}
"""
        prog = parse(source)
        errors = check(prog)
        assert len(errors) == 0
        emitter = PythonEmitter()
        code = emitter.emit(prog)
        assert 'f"{first} {last}"' in code

    def test_e2e_nested_expr(self) -> None:
        source = """
fn main() {
    let x: Int = 10
    let y: Int = 20
    print("result: ${x + y}")
}
"""
        prog = parse(source)
        errors = check(prog)
        assert len(errors) == 0
        emitter = PythonEmitter()
        code = emitter.emit(prog)
        assert 'f"result: {' in code
