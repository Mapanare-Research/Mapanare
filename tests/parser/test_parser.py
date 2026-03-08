"""Comprehensive parser tests for the Mapanare language — Phase 2.2."""

from __future__ import annotations

import pytest

from mapa.ast_nodes import (
    AgentDef,
    AssignExpr,
    BinaryExpr,
    Block,
    BoolLiteral,
    CallExpr,
    CharLiteral,
    ConstructorPattern,
    EnumDef,
    ErrorPropExpr,
    ExportDef,
    Expr,
    ExprStmt,
    FieldAccessExpr,
    FloatLiteral,
    FnDef,
    FnType,
    ForLoop,
    GenericType,
    Identifier,
    IdentPattern,
    IfExpr,
    ImplDef,
    ImportDef,
    IndexExpr,
    IntLiteral,
    LambdaExpr,
    LetBinding,
    ListLiteral,
    LiteralPattern,
    MatchExpr,
    MethodCallExpr,
    NamedType,
    NamespaceAccessExpr,
    NoneLiteral,
    PipeDef,
    PipeExpr,
    Program,
    RangeExpr,
    ReturnStmt,
    SendExpr,
    SignalExpr,
    SpawnExpr,
    StringLiteral,
    StructDef,
    SyncExpr,
    TensorType,
    TypeAlias,
    UnaryExpr,
    WildcardPattern,
)
from mapa.parser import ParseError, parse

# ===================================================================
# Helpers
# ===================================================================


def parse_expr(src: str) -> Expr:
    """Parse a single expression wrapped in a function."""
    p = parse(f"fn _() {{ let _r = {src} }}")
    stmt = p.definitions[0].body.stmts[0]
    assert isinstance(stmt, LetBinding)
    return stmt.value


def parse_stmt(src: str) -> object:
    """Parse a single statement inside a function."""
    p = parse(f"fn _() {{ {src} }}")
    return p.definitions[0].body.stmts[0]


def parse_def(src: str) -> object:
    """Parse a single top-level definition."""
    p = parse(src)
    assert len(p.definitions) == 1
    return p.definitions[0]


# ===================================================================
# 1. AST node dataclasses — structural tests
# ===================================================================


class TestASTNodes:
    def test_program_empty(self) -> None:
        p = parse("")
        assert isinstance(p, Program)
        assert p.definitions == []

    def test_program_multiple_defs(self) -> None:
        p = parse("fn a() { }\nfn b() { }")
        assert len(p.definitions) == 2


# ===================================================================
# 2. Parse agent definitions
# ===================================================================


class TestAgentDef:
    def test_basic_agent(self) -> None:
        d = parse_def(
            "agent Greeter {\n"
            "    input name: String\n"
            "    output greeting: String\n"
            "    fn handle(name: String) -> String {\n"
            "        return 42\n"
            "    }\n"
            "}"
        )
        assert isinstance(d, AgentDef)
        assert d.name == "Greeter"
        assert len(d.inputs) == 1
        assert d.inputs[0].name == "name"
        assert isinstance(d.inputs[0].type_annotation, NamedType)
        assert d.inputs[0].type_annotation.name == "String"
        assert len(d.outputs) == 1
        assert d.outputs[0].name == "greeting"
        assert len(d.methods) == 1
        assert d.methods[0].name == "handle"

    def test_agent_with_state(self) -> None:
        d = parse_def(
            "agent Counter {\n"
            "    input increment: Int\n"
            "    output count: Int\n"
            "    let mut state: Int = 0\n"
            "    fn handle(increment: Int) -> Int {\n"
            "        return 0\n"
            "    }\n"
            "}"
        )
        assert isinstance(d, AgentDef)
        assert len(d.state) == 1
        assert d.state[0].name == "state"
        assert d.state[0].mutable is True

    def test_pub_agent(self) -> None:
        d = parse_def("pub agent MyAgent {\n    input x: Int\n}")
        assert isinstance(d, AgentDef)
        assert d.public is True


# ===================================================================
# 3. Parse pipe definitions
# ===================================================================


class TestPipeDef:
    def test_basic_pipe(self) -> None:
        d = parse_def("pipe ClassifyText {\n    Tokenizer |> Classifier\n}")
        assert isinstance(d, PipeDef)
        assert d.name == "ClassifyText"
        assert len(d.stages) == 2
        assert d.stages[0].name == "Tokenizer"
        assert d.stages[1].name == "Classifier"

    def test_multi_stage_pipe(self) -> None:
        d = parse_def("pipe Pipeline {\n    A |> B |> C |> D\n}")
        assert isinstance(d, PipeDef)
        assert len(d.stages) == 4

    def test_pub_pipe(self) -> None:
        d = parse_def("pub pipe P {\n    A |> B\n}")
        assert isinstance(d, PipeDef)
        assert d.public is True


# ===================================================================
# 4. Parse fn definitions
# ===================================================================


class TestFnDef:
    def test_basic_fn(self) -> None:
        d = parse_def("fn main() { }")
        assert isinstance(d, FnDef)
        assert d.name == "main"
        assert d.params == []
        assert d.return_type is None

    def test_fn_with_params(self) -> None:
        d = parse_def("fn add(a: Int, b: Int) -> Int { return 0 }")
        assert isinstance(d, FnDef)
        assert d.name == "add"
        assert len(d.params) == 2
        assert d.params[0].name == "a"
        assert isinstance(d.params[0].type_annotation, NamedType)
        assert d.params[0].type_annotation.name == "Int"
        assert isinstance(d.return_type, NamedType)
        assert d.return_type.name == "Int"

    def test_pub_fn(self) -> None:
        d = parse_def("pub fn greet() { }")
        assert isinstance(d, FnDef)
        assert d.public is True

    def test_fn_generic(self) -> None:
        d = parse_def("fn identity<T>(x: T) -> T { return x }")
        assert isinstance(d, FnDef)
        assert d.type_params == ["T"]

    def test_fn_multi_generics(self) -> None:
        d = parse_def("fn pair<A, B>(a: A, b: B) -> Int { return 0 }")
        assert isinstance(d, FnDef)
        assert d.type_params == ["A", "B"]

    def test_fn_body_stmts(self) -> None:
        d = parse_def("fn f() {\n    let x = 1\n    let y = 2\n}")
        assert isinstance(d, FnDef)
        assert len(d.body.stmts) == 2


# ===================================================================
# 5. Parse let and mut bindings
# ===================================================================


class TestLetMut:
    def test_let_basic(self) -> None:
        s = parse_stmt("let x = 42")
        assert isinstance(s, LetBinding)
        assert s.name == "x"
        assert s.mutable is False
        assert isinstance(s.value, IntLiteral)
        assert s.value.value == 42

    def test_let_mut(self) -> None:
        s = parse_stmt("let mut y = 0")
        assert isinstance(s, LetBinding)
        assert s.mutable is True
        assert s.name == "y"

    def test_let_with_type(self) -> None:
        s = parse_stmt("let x: Int = 42")
        assert isinstance(s, LetBinding)
        assert isinstance(s.type_annotation, NamedType)
        assert s.type_annotation.name == "Int"

    def test_let_mut_with_type(self) -> None:
        s = parse_stmt("let mut count: Int = 0")
        assert isinstance(s, LetBinding)
        assert s.mutable is True
        assert isinstance(s.type_annotation, NamedType)

    def test_let_string(self) -> None:
        s = parse_stmt('let s = "hello"')
        assert isinstance(s, LetBinding)
        assert isinstance(s.value, StringLiteral)
        assert s.value.value == "hello"

    def test_let_bool(self) -> None:
        s = parse_stmt("let b = true")
        assert isinstance(s, LetBinding)
        assert isinstance(s.value, BoolLiteral)
        assert s.value.value is True

    def test_let_none(self) -> None:
        s = parse_stmt("let n = none")
        assert isinstance(s, LetBinding)
        assert isinstance(s.value, NoneLiteral)

    def test_let_float(self) -> None:
        s = parse_stmt("let f = 3.14")
        assert isinstance(s, LetBinding)
        assert isinstance(s.value, FloatLiteral)
        assert s.value.value == pytest.approx(3.14)

    def test_let_char(self) -> None:
        s = parse_stmt("let c = 'a'")
        assert isinstance(s, LetBinding)
        assert isinstance(s.value, CharLiteral)
        assert s.value.value == "a"


# ===================================================================
# 6. Parse signal and stream declarations
# ===================================================================


class TestSignalStream:
    def test_signal_value(self) -> None:
        e = parse_expr("signal(0)")
        assert isinstance(e, SignalExpr)
        assert e.is_computed is False
        assert isinstance(e.value, IntLiteral)

    def test_signal_computed(self) -> None:
        e = parse_expr("signal { x + 1 }")
        assert isinstance(e, SignalExpr)
        assert e.is_computed is True

    def test_signal_in_let(self) -> None:
        s = parse_stmt("let mut count = signal(0)")
        assert isinstance(s, LetBinding)
        assert isinstance(s.value, SignalExpr)

    def test_signal_computed_in_let(self) -> None:
        s = parse_stmt("let doubled = signal { count + 1 }")
        assert isinstance(s, LetBinding)
        assert isinstance(s.value, SignalExpr)
        assert s.value.is_computed is True


# ===================================================================
# 7. Parse type annotations with generics
# ===================================================================


class TestTypeAnnotations:
    def test_named_type(self) -> None:
        s = parse_stmt("let x: Int = 0")
        assert isinstance(s, LetBinding)
        assert isinstance(s.type_annotation, NamedType)
        assert s.type_annotation.name == "Int"

    def test_generic_type(self) -> None:
        d = parse_def("fn f(x: List<Int>) { }")
        assert isinstance(d, FnDef)
        t = d.params[0].type_annotation
        assert isinstance(t, GenericType)
        assert t.name == "List"
        assert len(t.args) == 1
        assert isinstance(t.args[0], NamedType)
        assert t.args[0].name == "Int"

    def test_nested_generic(self) -> None:
        d = parse_def("fn f(x: Map<String, List<Int>>) { }")
        t = d.params[0].type_annotation
        assert isinstance(t, GenericType)
        assert t.name == "Map"
        assert len(t.args) == 2
        assert isinstance(t.args[0], NamedType)
        assert isinstance(t.args[1], GenericType)
        assert t.args[1].name == "List"

    def test_option_type(self) -> None:
        d = parse_def("fn f(x: Option<Int>) { }")
        t = d.params[0].type_annotation
        assert isinstance(t, GenericType)
        assert t.name == "Option"

    def test_result_type(self) -> None:
        d = parse_def("fn f() -> Result<Int, String> { return 0 }")
        t = d.return_type
        assert isinstance(t, GenericType)
        assert t.name == "Result"
        assert len(t.args) == 2

    def test_fn_type(self) -> None:
        d = parse_def("fn f(cb: fn(Int) -> Bool) { }")
        t = d.params[0].type_annotation
        assert isinstance(t, FnType)
        assert len(t.param_types) == 1
        assert isinstance(t.return_type, NamedType)

    def test_tensor_type(self) -> None:
        d = parse_def("fn f(m: Tensor<Float>[3, 3]) { }")
        t = d.params[0].type_annotation
        assert isinstance(t, TensorType)
        assert isinstance(t.element_type, NamedType)
        assert t.element_type.name == "Float"
        assert len(t.shape) == 2

    def test_type_alias(self) -> None:
        d = parse_def("type Name = String")
        assert isinstance(d, TypeAlias)
        assert d.name == "Name"
        assert isinstance(d.type_expr, NamedType)
        assert d.type_expr.name == "String"


# ===================================================================
# 8. Parse |> pipe expressions
# ===================================================================


class TestPipeExpr:
    def test_simple_pipe(self) -> None:
        e = parse_expr("data |> process")
        assert isinstance(e, PipeExpr)
        assert isinstance(e.left, Identifier)
        assert isinstance(e.right, Identifier)

    def test_chained_pipe(self) -> None:
        e = parse_expr("data |> tokenize |> classify |> format")
        # Left-associative: ((data |> tokenize) |> classify) |> format
        assert isinstance(e, PipeExpr)
        assert isinstance(e.right, Identifier)
        assert e.right.name == "format"
        assert isinstance(e.left, PipeExpr)

    def test_pipe_with_calls(self) -> None:
        e = parse_expr("data |> process()")
        assert isinstance(e, PipeExpr)
        assert isinstance(e.right, CallExpr)


# ===================================================================
# 9. Parse arithmetic and boolean expressions
# ===================================================================


class TestArithBoolExpr:
    def test_add(self) -> None:
        e = parse_expr("1 + 2")
        assert isinstance(e, BinaryExpr)
        assert e.op == "+"

    def test_sub(self) -> None:
        e = parse_expr("5 - 3")
        assert isinstance(e, BinaryExpr)
        assert e.op == "-"

    def test_mul(self) -> None:
        e = parse_expr("2 * 3")
        assert isinstance(e, BinaryExpr)
        assert e.op == "*"

    def test_div(self) -> None:
        e = parse_expr("10 / 2")
        assert isinstance(e, BinaryExpr)
        assert e.op == "/"

    def test_mod(self) -> None:
        e = parse_expr("10 % 3")
        assert isinstance(e, BinaryExpr)
        assert e.op == "%"

    def test_matmul(self) -> None:
        e = parse_expr("a @ b")
        assert isinstance(e, BinaryExpr)
        assert e.op == "@"
        assert isinstance(e.left, Identifier) and e.left.name == "a"
        assert isinstance(e.right, Identifier) and e.right.name == "b"

    def test_matmul_precedence(self) -> None:
        """@ has same precedence as * (mul_expr level)."""
        e = parse_expr("a + b @ c")
        assert isinstance(e, BinaryExpr)
        assert e.op == "+"
        assert isinstance(e.right, BinaryExpr)
        assert e.right.op == "@"

    def test_precedence_mul_over_add(self) -> None:
        e = parse_expr("1 + 2 * 3")
        assert isinstance(e, BinaryExpr)
        assert e.op == "+"
        assert isinstance(e.right, BinaryExpr)
        assert e.right.op == "*"

    def test_precedence_parens(self) -> None:
        e = parse_expr("(1 + 2) * 3")
        assert isinstance(e, BinaryExpr)
        assert e.op == "*"
        assert isinstance(e.left, BinaryExpr)
        assert e.left.op == "+"

    def test_unary_neg(self) -> None:
        e = parse_expr("-x")
        assert isinstance(e, UnaryExpr)
        assert e.op == "-"
        assert isinstance(e.operand, Identifier)

    def test_unary_not(self) -> None:
        e = parse_expr("!flag")
        assert isinstance(e, UnaryExpr)
        assert e.op == "!"

    def test_eq(self) -> None:
        e = parse_expr("a == b")
        assert isinstance(e, BinaryExpr)
        assert e.op == "=="

    def test_ne(self) -> None:
        e = parse_expr("a != b")
        assert isinstance(e, BinaryExpr)
        assert e.op == "!="

    def test_lt(self) -> None:
        e = parse_expr("a < b")
        assert isinstance(e, BinaryExpr)
        assert e.op == "<"

    def test_gt(self) -> None:
        e = parse_expr("a > b")
        assert isinstance(e, BinaryExpr)
        assert e.op == ">"

    def test_le(self) -> None:
        e = parse_expr("a <= b")
        assert isinstance(e, BinaryExpr)
        assert e.op == "<="

    def test_ge(self) -> None:
        e = parse_expr("a >= b")
        assert isinstance(e, BinaryExpr)
        assert e.op == ">="

    def test_and(self) -> None:
        e = parse_expr("a && b")
        assert isinstance(e, BinaryExpr)
        assert e.op == "&&"

    def test_or(self) -> None:
        e = parse_expr("a || b")
        assert isinstance(e, BinaryExpr)
        assert e.op == "||"

    def test_bool_precedence_and_over_or(self) -> None:
        e = parse_expr("a || b && c")
        assert isinstance(e, BinaryExpr)
        assert e.op == "||"
        assert isinstance(e.right, BinaryExpr)
        assert e.right.op == "&&"

    def test_complex_expr(self) -> None:
        e = parse_expr("a + b * c - d / e")
        assert isinstance(e, BinaryExpr)
        assert e.op == "-"

    def test_range(self) -> None:
        e = parse_expr("0..10")
        assert isinstance(e, RangeExpr)
        assert e.inclusive is False

    def test_range_inclusive(self) -> None:
        e = parse_expr("0..=10")
        assert isinstance(e, RangeExpr)
        assert e.inclusive is True

    def test_hex_int(self) -> None:
        e = parse_expr("0xFF")
        assert isinstance(e, IntLiteral)
        assert e.value == 255

    def test_bin_int(self) -> None:
        e = parse_expr("0b1010")
        assert isinstance(e, IntLiteral)
        assert e.value == 10

    def test_oct_int(self) -> None:
        e = parse_expr("0o77")
        assert isinstance(e, IntLiteral)
        assert e.value == 63

    def test_underscore_int(self) -> None:
        e = parse_expr("1_000_000")
        assert isinstance(e, IntLiteral)
        assert e.value == 1_000_000

    def test_scientific_float(self) -> None:
        e = parse_expr("1e10")
        assert isinstance(e, FloatLiteral)
        assert e.value == pytest.approx(1e10)

    def test_list_literal(self) -> None:
        e = parse_expr("[1, 2, 3]")
        assert isinstance(e, ListLiteral)
        assert len(e.elements) == 3

    def test_empty_list(self) -> None:
        e = parse_expr("[]")
        assert isinstance(e, ListLiteral)
        assert len(e.elements) == 0


# ===================================================================
# 10. Parse function and method calls
# ===================================================================


class TestCalls:
    def test_fn_call_no_args(self) -> None:
        e = parse_expr("foo()")
        assert isinstance(e, CallExpr)
        assert isinstance(e.callee, Identifier)
        assert e.callee.name == "foo"
        assert e.args == []

    def test_fn_call_with_args(self) -> None:
        e = parse_expr("add(1, 2)")
        assert isinstance(e, CallExpr)
        assert len(e.args) == 2

    def test_method_call(self) -> None:
        e = parse_expr("text.split(x)")
        assert isinstance(e, MethodCallExpr)
        assert e.method == "split"
        assert len(e.args) == 1

    def test_field_access(self) -> None:
        e = parse_expr("point.x")
        assert isinstance(e, FieldAccessExpr)
        assert e.field_name == "x"

    def test_chained_field_access(self) -> None:
        e = parse_expr("a.b.c")
        assert isinstance(e, FieldAccessExpr)
        assert e.field_name == "c"
        assert isinstance(e.object, FieldAccessExpr)

    def test_namespace_access(self) -> None:
        e = parse_expr("Math::sqrt")
        assert isinstance(e, NamespaceAccessExpr)
        assert e.namespace == "Math"
        assert e.member == "sqrt"

    def test_namespace_call(self) -> None:
        e = parse_expr("Math::sqrt(4)")
        assert isinstance(e, CallExpr)
        assert isinstance(e.callee, NamespaceAccessExpr)

    def test_index_expr(self) -> None:
        e = parse_expr("arr[0]")
        assert isinstance(e, IndexExpr)
        assert isinstance(e.index, IntLiteral)

    def test_chained_calls(self) -> None:
        e = parse_expr("a.b().c()")
        assert isinstance(e, MethodCallExpr)
        assert e.method == "c"

    def test_error_prop(self) -> None:
        e = parse_expr("foo()?")
        assert isinstance(e, ErrorPropExpr)
        assert isinstance(e.expr, CallExpr)


# ===================================================================
# 11. Parse if/else and match
# ===================================================================


class TestIfMatch:
    def test_if_simple(self) -> None:
        s = parse_stmt("if x > 0 { let a = 1 }")
        assert isinstance(s, ExprStmt)
        e = s.expr
        assert isinstance(e, IfExpr)
        assert isinstance(e.condition, BinaryExpr)
        assert e.else_block is None

    def test_if_else(self) -> None:
        s = parse_stmt("if x > 0 { let a = 1 } else { let b = 2 }")
        e = s.expr
        assert isinstance(e, IfExpr)
        assert e.else_block is not None
        assert isinstance(e.else_block, Block)

    def test_if_elseif(self) -> None:
        s = parse_stmt("if x > 0 { let a = 1 } else if x < 0 { let b = 2 }")
        e = s.expr
        assert isinstance(e, IfExpr)
        assert isinstance(e.else_block, IfExpr)

    def test_match_basic(self) -> None:
        s = parse_stmt("match x { 1 => 10, 2 => 20 }")
        e = s.expr
        assert isinstance(e, MatchExpr)
        assert len(e.arms) == 2

    def test_match_wildcard(self) -> None:
        s = parse_stmt("match x { 1 => 10, _ => 0 }")
        e = s.expr
        assert isinstance(e, MatchExpr)
        assert isinstance(e.arms[1].pattern, WildcardPattern)

    def test_match_constructor(self) -> None:
        s = parse_stmt("match x { Some(v) => v, _ => 0 }")
        e = s.expr
        assert isinstance(e, MatchExpr)
        assert isinstance(e.arms[0].pattern, ConstructorPattern)
        assert e.arms[0].pattern.name == "Some"
        assert len(e.arms[0].pattern.args) == 1

    def test_match_with_block_body(self) -> None:
        s = parse_stmt("match x { 1 => { let a = 10 } }")
        e = s.expr
        assert isinstance(e, MatchExpr)
        assert isinstance(e.arms[0].body, Block)

    def test_match_ident_pattern(self) -> None:
        s = parse_stmt("match x { n => n }")
        e = s.expr
        assert isinstance(e, MatchExpr)
        assert isinstance(e.arms[0].pattern, IdentPattern)
        assert e.arms[0].pattern.name == "n"

    def test_match_literal_string(self) -> None:
        s = parse_stmt('match x { "hello" => 1 }')
        e = s.expr
        assert isinstance(e, MatchExpr)
        assert isinstance(e.arms[0].pattern, LiteralPattern)


# ===================================================================
# 12. Parse for/in loops
# ===================================================================


class TestForLoop:
    def test_basic_for(self) -> None:
        s = parse_stmt("for x in items { let a = x }")
        assert isinstance(s, ForLoop)
        assert s.var_name == "x"
        assert isinstance(s.iterable, Identifier)
        assert isinstance(s.body, Block)

    def test_for_with_range(self) -> None:
        s = parse_stmt("for i in 0..10 { let a = i }")
        assert isinstance(s, ForLoop)
        assert isinstance(s.iterable, RangeExpr)

    def test_for_with_call(self) -> None:
        s = parse_stmt("for item in get_items() { let a = item }")
        assert isinstance(s, ForLoop)
        assert isinstance(s.iterable, CallExpr)


# ===================================================================
# 13. Parse import and export
# ===================================================================


class TestImportExport:
    def test_import_simple(self) -> None:
        d = parse_def("import std::io")
        assert isinstance(d, ImportDef)
        assert d.path == ["std", "io"]

    def test_import_single(self) -> None:
        d = parse_def("import mylib")
        assert isinstance(d, ImportDef)
        assert d.path == ["mylib"]

    def test_import_with_items(self) -> None:
        d = parse_def("import std::io { read, write }")
        assert isinstance(d, ImportDef)
        assert d.path == ["std", "io"]
        assert d.items == ["read", "write"]

    def test_export_fn(self) -> None:
        d = parse_def("export fn greet() { }")
        assert isinstance(d, ExportDef)
        assert isinstance(d.definition, FnDef)
        assert d.definition.name == "greet"

    def test_export_names(self) -> None:
        d = parse_def("export foo, bar")
        assert isinstance(d, ExportDef)
        assert d.names == ["foo", "bar"]

    def test_export_agent(self) -> None:
        d = parse_def("export agent Bot {\n    input msg: String\n}")
        assert isinstance(d, ExportDef)
        assert isinstance(d.definition, AgentDef)


# ===================================================================
# 14. Parse spawn and sync
# ===================================================================


class TestSpawnSync:
    def test_spawn_basic(self) -> None:
        e = parse_expr("spawn Greeter()")
        assert isinstance(e, SpawnExpr)
        assert isinstance(e.callee, Identifier)
        assert e.callee.name == "Greeter"
        assert e.args == []

    def test_spawn_with_args(self) -> None:
        e = parse_expr("spawn Worker(42)")
        assert isinstance(e, SpawnExpr)
        assert len(e.args) == 1

    def test_sync_field(self) -> None:
        e = parse_expr("sync g.greeting")
        assert isinstance(e, SyncExpr)
        assert isinstance(e.expr, FieldAccessExpr)

    def test_sync_method(self) -> None:
        e = parse_expr("sync g.result()")
        assert isinstance(e, SyncExpr)
        assert isinstance(e.expr, MethodCallExpr)

    def test_send_expr(self) -> None:
        s = parse_stmt("agent.name <- value")
        assert isinstance(s, ExprStmt)
        e = s.expr
        assert isinstance(e, SendExpr)


# ===================================================================
# 15. Build AST from parse tree (Lark transformers) — integration
# ===================================================================


class TestTransformerIntegration:
    def test_full_agent_pipeline(self) -> None:
        src = (
            "agent Tokenizer {\n"
            "    input text: String\n"
            "    output tokens: List<String>\n"
            "    fn handle(text: String) -> List<String> {\n"
            "        return text\n"
            "    }\n"
            "}\n"
            "pipe ClassifyText {\n"
            "    Tokenizer |> Classifier\n"
            "}\n"
            "fn main() {\n"
            "    let p = spawn ClassifyText()\n"
            "}"
        )
        p = parse(src)
        assert len(p.definitions) == 3
        assert isinstance(p.definitions[0], AgentDef)
        assert isinstance(p.definitions[1], PipeDef)
        assert isinstance(p.definitions[2], FnDef)

    def test_struct_and_impl(self) -> None:
        src = (
            "struct Point {\n"
            "    x: Float,\n"
            "    y: Float\n"
            "}\n"
            "impl Point {\n"
            "    fn dist(self: Point) -> Float {\n"
            "        return 0\n"
            "    }\n"
            "}"
        )
        p = parse(src)
        assert len(p.definitions) == 2
        assert isinstance(p.definitions[0], StructDef)
        assert isinstance(p.definitions[1], ImplDef)
        assert p.definitions[1].target == "Point"
        assert len(p.definitions[1].methods) == 1

    def test_enum_with_match(self) -> None:
        src = (
            "enum Shape {\n"
            "    Circle(Float),\n"
            "    Rectangle(Float, Float)\n"
            "}\n"
            "fn area(s: Shape) -> Float {\n"
            "    match s {\n"
            "        Circle(r) => r * r,\n"
            "        Rectangle(w, h) => w * h\n"
            "    }\n"
            "}"
        )
        p = parse(src)
        assert isinstance(p.definitions[0], EnumDef)
        assert len(p.definitions[0].variants) == 2
        fn = p.definitions[1]
        assert isinstance(fn, FnDef)
        match_stmt = fn.body.stmts[0]
        assert isinstance(match_stmt, ExprStmt)
        assert isinstance(match_stmt.expr, MatchExpr)

    def test_generic_fn(self) -> None:
        src = "fn identity<T>(x: T) -> T { return x }"
        d = parse_def(src)
        assert isinstance(d, FnDef)
        assert d.type_params == ["T"]
        assert d.params[0].name == "x"

    def test_assignments(self) -> None:
        e = parse_expr("x = 5")
        assert isinstance(e, AssignExpr)
        assert e.op == "="

        e = parse_expr("x += 1")
        assert isinstance(e, AssignExpr)
        assert e.op == "+="

        e = parse_expr("x -= 1")
        assert isinstance(e, AssignExpr)
        assert e.op == "-="

        e = parse_expr("x *= 2")
        assert isinstance(e, AssignExpr)
        assert e.op == "*="

        e = parse_expr("x /= 2")
        assert isinstance(e, AssignExpr)
        assert e.op == "/="

    def test_lambda_single_param(self) -> None:
        e = parse_expr("x => x + 1")
        assert isinstance(e, LambdaExpr)
        assert len(e.params) == 1
        assert e.params[0].name == "x"

    def test_lambda_paren_param(self) -> None:
        e = parse_expr("(x) => x + 1")
        assert isinstance(e, LambdaExpr)
        assert len(e.params) == 1

    def test_lambda_multi_param(self) -> None:
        e = parse_expr("(x, y) => x + y")
        assert isinstance(e, LambdaExpr)
        assert len(e.params) == 2

    def test_return_stmt(self) -> None:
        s = parse_stmt("return 42")
        assert isinstance(s, ReturnStmt)
        assert isinstance(s.value, IntLiteral)

    def test_return_no_value(self) -> None:
        # return with no value in a block
        p = parse("fn f() { return }")
        fn = p.definitions[0]
        assert isinstance(fn, FnDef)
        assert isinstance(fn.body.stmts[0], ReturnStmt)
        assert fn.body.stmts[0].value is None


# ===================================================================
# 16. Parser unit tests — error cases
# ===================================================================


class TestParserErrors:
    def test_invalid_syntax(self) -> None:
        with pytest.raises(ParseError):
            parse("fn {}")

    def test_unclosed_brace(self) -> None:
        with pytest.raises(ParseError):
            parse("fn main() {")

    def test_unexpected_token(self) -> None:
        with pytest.raises(ParseError):
            parse("let = 5")

    def test_empty_agent(self) -> None:
        # Should parse fine — empty body
        d = parse_def("agent Empty {\n}")
        assert isinstance(d, AgentDef)
        assert d.name == "Empty"


# ===================================================================
# Additional coverage — struct/enum details
# ===================================================================


class TestStructEnum:
    def test_struct_basic(self) -> None:
        d = parse_def("struct Point {\n    x: Float,\n    y: Float\n}")
        assert isinstance(d, StructDef)
        assert d.name == "Point"
        assert len(d.fields) == 2
        assert d.fields[0].name == "x"
        assert d.fields[1].name == "y"

    def test_struct_generic(self) -> None:
        d = parse_def("struct Pair<A, B> {\n    first: A,\n    second: B\n}")
        assert isinstance(d, StructDef)
        assert d.type_params == ["A", "B"]

    def test_struct_pub(self) -> None:
        d = parse_def("pub struct Foo {\n    x: Int\n}")
        assert isinstance(d, StructDef)
        assert d.public is True

    def test_enum_basic(self) -> None:
        d = parse_def("enum Color {\n    Red,\n    Green,\n    Blue\n}")
        assert isinstance(d, EnumDef)
        assert d.name == "Color"
        assert len(d.variants) == 3
        assert d.variants[0].name == "Red"
        assert d.variants[0].fields == []

    def test_enum_with_data(self) -> None:
        d = parse_def("enum Shape {\n    Circle(Float),\n    Rect(Float, Float)\n}")
        assert isinstance(d, EnumDef)
        assert len(d.variants[0].fields) == 1
        assert len(d.variants[1].fields) == 2

    def test_enum_generic(self) -> None:
        d = parse_def("enum Option<T> {\n    Some(T),\n    None\n}")
        assert isinstance(d, EnumDef)
        assert d.type_params == ["T"]

    def test_impl_block(self) -> None:
        d = parse_def(
            "impl Point {\n"
            "    fn x(self: Point) -> Float { return 0 }\n"
            "    fn y(self: Point) -> Float { return 0 }\n"
            "}"
        )
        assert isinstance(d, ImplDef)
        assert d.target == "Point"
        assert len(d.methods) == 2
