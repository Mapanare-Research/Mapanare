"""Tests for compile-time struct JSON intrinsics: encode_struct::<T> and decode_to::<T>."""

from __future__ import annotations

from mapanare.cli import _compile_to_llvm_ir


def _compile_mir(src: str) -> str:
    return _compile_to_llvm_ir(src, "test_struct_json.mn", use_mir=True)


# ── encode_struct tests ──────────────────────────────────────────────


class TestEncodeStruct:
    def test_basic_string_int(self) -> None:
        src = """
struct User { name: String, age: Int }
fn main() {
    let u: User = User("Alice", 30)
    let json: String = encode_struct::<User>(u)
    println(json)
}
"""
        ir = _compile_mir(src)
        assert "main" in ir
        # Should contain the field name strings
        assert "name" in ir

    def test_all_primitive_types(self) -> None:
        src = """
struct Config { label: String, count: Int, ratio: Float, enabled: Bool }
fn main() {
    let c: Config = Config("test", 42, 3.14, true)
    let json: String = encode_struct::<Config>(c)
    println(json)
}
"""
        ir = _compile_mir(src)
        assert "main" in ir

    def test_single_field(self) -> None:
        src = """
struct Tag { value: String }
fn main() {
    let t: Tag = Tag("hello")
    let json: String = encode_struct::<Tag>(t)
    println(json)
}
"""
        ir = _compile_mir(src)
        assert "main" in ir

    def test_many_fields(self) -> None:
        src = """
struct Record { a: String, b: String, c: Int, d: Int, e: Float }
fn main() {
    let r: Record = Record("x", "y", 1, 2, 3.0)
    let json: String = encode_struct::<Record>(r)
    println(json)
}
"""
        ir = _compile_mir(src)
        assert "main" in ir

    def test_unknown_struct_returns_empty(self) -> None:
        src = """
fn main() {
    let x: Int = 0
    let json: String = encode_struct::<Unknown>(x)
    println(json)
}
"""
        ir = _compile_mir(src)
        assert "main" in ir


# ── decode_to tests ──────────────────────────────────────────────────

_JSON_PRELUDE = """
struct JsonError { message: String, line: Int, col: Int }
enum JsonValue { Null, Bool(Bool), Int(Int), Float(Float), Str(String), Array(List<JsonValue>), Object(Map<String, JsonValue>) }
"""


class TestDecodeTo:
    def test_basic_struct(self) -> None:
        src = _JSON_PRELUDE + """
struct Person { name: String, age: Int }
fn main() {
    let entries: Map<String, JsonValue> = #{}
    let jv: JsonValue = Object(entries)
    let result: Result<Person, JsonError> = decode_to::<Person>(jv)
    println("ok")
}
"""
        ir = _compile_mir(src)
        assert "main" in ir

    def test_single_string_field(self) -> None:
        src = _JSON_PRELUDE + """
struct Label { text: String }
fn main() {
    let entries: Map<String, JsonValue> = #{}
    let jv: JsonValue = Object(entries)
    let result: Result<Label, JsonError> = decode_to::<Label>(jv)
    println("ok")
}
"""
        ir = _compile_mir(src)
        assert "main" in ir

    def test_int_and_float_fields(self) -> None:
        src = _JSON_PRELUDE + """
struct Metrics { count: Int, avg: Float }
fn main() {
    let entries: Map<String, JsonValue> = #{}
    let jv: JsonValue = Object(entries)
    let result: Result<Metrics, JsonError> = decode_to::<Metrics>(jv)
    println("ok")
}
"""
        ir = _compile_mir(src)
        assert "main" in ir

    def test_bool_field(self) -> None:
        src = _JSON_PRELUDE + """
struct Flag { active: Bool }
fn main() {
    let entries: Map<String, JsonValue> = #{}
    let jv: JsonValue = Object(entries)
    let result: Result<Flag, JsonError> = decode_to::<Flag>(jv)
    println("ok")
}
"""
        ir = _compile_mir(src)
        assert "main" in ir

    def test_error_on_non_object(self) -> None:
        """decode_to on a non-Object JsonValue should produce error path in IR."""
        src = _JSON_PRELUDE + """
struct Item { name: String }
fn main() {
    let jv: JsonValue = Null()
    let result: Result<Item, JsonError> = decode_to::<Item>(jv)
    println("ok")
}
"""
        ir = _compile_mir(src)
        assert "main" in ir
        # Should contain the error message string
        assert "expected JSON object" in ir


# ── Turbofish syntax tests ───────────────────────────────────────────


class TestTurbofishSyntax:
    def test_parses_simple(self) -> None:
        from mapanare.parser import parse

        ast = parse("fn main() { let x: String = encode_struct::<User>(val) }")
        fn = ast.definitions[0]
        let_stmt = fn.body.stmts[0]
        call = let_stmt.value
        assert len(call.type_args) == 1
        assert call.type_args[0].name == "User"

    def test_parses_generic_type_arg(self) -> None:
        from mapanare.parser import parse

        ast = parse("fn main() { let x = decode_to::<List<User>>(val) }")
        fn = ast.definitions[0]
        let_stmt = fn.body.stmts[0]
        call = let_stmt.value
        assert len(call.type_args) == 1
        assert call.type_args[0].name == "List"
        assert call.type_args[0].args[0].name == "User"

    def test_parses_multiple_type_args(self) -> None:
        from mapanare.parser import parse

        ast = parse("fn main() { let x = foo::<A, B>(val) }")
        fn = ast.definitions[0]
        let_stmt = fn.body.stmts[0]
        call = let_stmt.value
        assert len(call.type_args) == 2
        assert call.type_args[0].name == "A"
        assert call.type_args[1].name == "B"

    def test_no_conflict_with_namespace(self) -> None:
        """namespace_access (Foo::bar) still works alongside turbofish."""
        from mapanare.parser import parse

        ast = parse("fn main() { let x: Int = Math::abs(-1) }")
        fn = ast.definitions[0]
        let_stmt = fn.body.stmts[0]
        call = let_stmt.value
        # Should parse as a call with namespace callee, NOT a turbofish
        assert call.type_args == []
