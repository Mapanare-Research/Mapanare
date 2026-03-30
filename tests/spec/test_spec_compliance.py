"""Task 24 — Spec compliance tests.

One test per major grammar rule verifying parse -> compile -> expected behavior.
Uses the parser and semantic checker (LLVM tests require llvmlite).
"""

from __future__ import annotations

import textwrap

import pytest

from mapanare.parser import parse
from mapanare.semantic import check

try:
    from mapanare.cli import _compile_to_llvm_ir

    HAS_LLVMLITE = True
except Exception:
    HAS_LLVMLITE = False


def _parse_ok(source: str) -> None:
    """Assert that source parses without error."""
    program = parse(source, filename="spec_test.mn")
    assert program is not None


def _check_ok(source: str) -> None:
    """Assert that source parses and type-checks without error."""
    program = parse(source, filename="spec_test.mn")
    errors = check(program, filename="spec_test.mn")
    assert errors == [], f"Expected no errors, got: {errors}"


def _compile_ok(source: str) -> str:
    """Assert that source compiles to LLVM IR."""
    ir_out = _compile_to_llvm_ir(source, "spec_test.mn", use_mir=True)
    assert ir_out, "Expected non-empty LLVM IR"
    return ir_out


# ── Primitive types and literals ──


class TestPrimitiveLiterals:
    def test_int_literal(self) -> None:
        _check_ok("fn main() { let x: Int = 42 }")

    def test_float_literal(self) -> None:
        _check_ok("fn main() { let x: Float = 3.14 }")

    def test_bool_literal(self) -> None:
        _check_ok("fn main() { let x: Bool = true }")

    def test_string_literal(self) -> None:
        _check_ok('fn main() { let x: String = "hello" }')

    def test_hex_int(self) -> None:
        _check_ok("fn main() { let x: Int = 0xFF }")

    def test_bin_int(self) -> None:
        _check_ok("fn main() { let x: Int = 0b1010 }")

    def test_oct_int(self) -> None:
        _check_ok("fn main() { let x: Int = 0o77 }")

    def test_float_scientific(self) -> None:
        _check_ok("fn main() { let x: Float = 1.0e10 }")

    def test_underscore_numeric(self) -> None:
        _check_ok("fn main() { let x: Int = 1_000_000 }")

    def test_none_literal(self) -> None:
        _check_ok("fn main() { let x: Option<Int> = none }")

    def test_char_literal(self) -> None:
        _parse_ok("fn main() { let c = 'a' }")

    def test_triple_string(self) -> None:
        _parse_ok('fn main() { let s = """hello\nworld""" }')


# ── String interpolation ──


class TestStringInterpolation:
    def test_basic_interpolation(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let name: String = "world"
                let msg: String = "hello ${name}"
            }
        """))

    def test_expr_interpolation(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let a: Int = 1
                let b: Int = 2
                let msg: String = "sum: ${a + b}"
            }
        """))


# ── Let bindings and mutability ──


class TestLetBindings:
    def test_immutable_binding(self) -> None:
        _check_ok("fn main() { let x = 42 }")

    def test_mutable_binding(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let mut x = 0
                x = 42
            }
        """))

    def test_type_annotation(self) -> None:
        _check_ok("fn main() { let x: Int = 42 }")

    def test_type_inference(self) -> None:
        _check_ok("fn main() { let x = 42 }")


# ── Functions ──


class TestFunctions:
    def test_simple_fn(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn add(a: Int, b: Int) -> Int {
                return a + b
            }
        """))

    def test_void_fn(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn greet() {
                print("hi")
            }
        """))

    def test_pub_fn(self) -> None:
        _parse_ok(textwrap.dedent("""\
            pub fn helper() -> Int {
                return 1
            }
        """))

    def test_generic_fn(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn identity<T>(x: T) -> T {
                return x
            }
        """))


# ── Control flow ──


class TestControlFlow:
    def test_if_else(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let x = 5
                if x > 0 {
                    print("positive")
                } else {
                    print("non-positive")
                }
            }
        """))

    def test_if_elseif(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let x = 5
                if x > 10 {
                    print("big")
                } else if x > 0 {
                    print("small")
                } else {
                    print("non-positive")
                }
            }
        """))

    def test_for_range(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                for i in 0..10 {
                    print("hi")
                }
            }
        """))

    def test_while_loop(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let mut count = 0
                while count < 10 {
                    count += 1
                }
            }
        """))

    def test_break_statement(self) -> None:
        _parse_ok(textwrap.dedent("""\
            fn main() {
                for i in 0..100 {
                    if i > 10 {
                        break
                    }
                }
            }
        """))

    def test_return_statement(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn double(x: Int) -> Int {
                return x * 2
            }
        """))

    def test_assert_statement(self) -> None:
        _parse_ok(textwrap.dedent("""\
            fn main() {
                assert 1 + 1 == 2
            }
        """))

    def test_assert_with_message(self) -> None:
        _parse_ok(textwrap.dedent("""\
            fn main() {
                assert 1 + 1 == 2, "math is broken"
            }
        """))


# ── Match expressions ──


class TestMatchExpressions:
    def test_match_option(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let x: Option<Int> = Some(42)
                match x {
                    Some(v) => { print("got it") },
                    None => { print("nothing") }
                }
            }
        """))

    def test_match_result(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let r: Result<Int, String> = Ok(42)
                match r {
                    Ok(v) => { print("ok") },
                    Err(e) => { print("err") }
                }
            }
        """))

    def test_match_wildcard(self) -> None:
        _parse_ok(textwrap.dedent("""\
            fn main() {
                let x = 42
                match x {
                    0 => 0,
                    _ => 1
                }
            }
        """))

    def test_match_literal_patterns(self) -> None:
        _parse_ok(textwrap.dedent("""\
            fn main() {
                let x = true
                match x {
                    true => 1,
                    false => 0
                }
            }
        """))


# ── Structs ──


class TestStructs:
    def test_struct_def(self) -> None:
        _check_ok(textwrap.dedent("""\
            struct Point {
                x: Float,
                y: Float,
            }
        """))

    def test_struct_construction(self) -> None:
        _check_ok(textwrap.dedent("""\
            struct Point {
                x: Float,
                y: Float,
            }
            fn main() {
                let p = new Point { x: 1.0, y: 2.0 }
            }
        """))

    def test_struct_field_access(self) -> None:
        _check_ok(textwrap.dedent("""\
            struct Point {
                x: Float,
                y: Float,
            }
            fn main() {
                let p = new Point { x: 1.0, y: 2.0 }
                let xv = p.x
            }
        """))

    def test_struct_impl(self) -> None:
        _check_ok(textwrap.dedent("""\
            struct Counter {
                value: Int,
            }
            impl Counter {
                fn get(self) -> Int {
                    return self.value
                }
            }
        """))

    def test_generic_struct(self) -> None:
        _parse_ok(textwrap.dedent("""\
            struct Pair<A, B> {
                first: A,
                second: B,
            }
        """))

    def test_pub_struct(self) -> None:
        _parse_ok(textwrap.dedent("""\
            pub struct Config {
                name: String,
            }
        """))


# ── Enums ──


class TestEnums:
    def test_enum_def(self) -> None:
        _check_ok(textwrap.dedent("""\
            enum Color {
                Red,
                Green,
                Blue,
            }
        """))

    def test_enum_with_data(self) -> None:
        _check_ok(textwrap.dedent("""\
            enum Shape {
                Circle(Float),
                Rectangle(Float, Float),
            }
        """))

    def test_enum_match(self) -> None:
        _check_ok(textwrap.dedent("""\
            enum Shape {
                Circle(Float),
                Rect(Float, Float),
            }
            fn area(s: Shape) -> Float {
                match s {
                    Circle(r) => r * r,
                    Rect(w, h) => w * h
                }
            }
        """))

    def test_generic_enum(self) -> None:
        _parse_ok(textwrap.dedent("""\
            enum Either<A, B> {
                Left(A),
                Right(B),
            }
        """))


# ── Traits ──


class TestTraits:
    def test_trait_def(self) -> None:
        _check_ok(textwrap.dedent("""\
            trait Greetable {
                fn greet(self) -> String
            }
        """))

    def test_impl_trait(self) -> None:
        _check_ok(textwrap.dedent("""\
            struct Person {
                name: String,
            }
            trait Greetable {
                fn greet(self) -> String
            }
            impl Greetable for Person {
                fn greet(self) -> String {
                    return self.name
                }
            }
        """))


# ── Type aliases ──


class TestTypeAliases:
    def test_simple_alias(self) -> None:
        _parse_ok("type Name = String")

    def test_generic_alias(self) -> None:
        _parse_ok("type Ids = List<Int>")

    def test_fn_type_alias(self) -> None:
        _parse_ok("type Predicate = fn(Int) -> Bool")


# ── Agents ──


class TestAgents:
    def test_agent_def(self) -> None:
        _check_ok(textwrap.dedent("""\
            agent Greeter {
                input name: String
                output greeting: String

                fn handle(name: String) -> String {
                    return "Hello, " + name
                }
            }
        """))

    def test_spawn_and_send(self) -> None:
        _check_ok(textwrap.dedent("""\
            agent Echo {
                input msg: String
                output reply: String

                fn handle(msg: String) -> String {
                    return msg
                }
            }
            fn main() {
                let e = spawn Echo()
                e.msg <- "hello"
                let r = sync e.reply
            }
        """))


# ── Signals ──


class TestSignals:
    def test_signal_creation(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let mut count = signal(0)
            }
        """))

    def test_signal_computed(self) -> None:
        _parse_ok(textwrap.dedent("""\
            fn main() {
                let mut count = signal(0)
                let doubled = signal { count.value * 2 }
            }
        """))


# ── Streams ──


class TestStreams:
    def test_stream_creation(self) -> None:
        _parse_ok(textwrap.dedent("""\
            fn main() {
                let s = stream([1, 2, 3])
            }
        """))


# ── Pipes ──


class TestPipes:
    def test_pipe_def(self) -> None:
        _check_ok(textwrap.dedent("""\
            agent A {
                input x: Int
                output y: Int
                fn handle(x: Int) -> Int { return x }
            }
            agent B {
                input y: Int
                output z: Int
                fn handle(y: Int) -> Int { return y }
            }
            pipe AB {
                A |> B
            }
        """))


# ── Lambdas ──


class TestLambdas:
    def test_simple_lambda(self) -> None:
        _parse_ok(textwrap.dedent("""\
            fn main() {
                let double = (x) => x * 2
            }
        """))

    def test_multi_param_lambda(self) -> None:
        _parse_ok(textwrap.dedent("""\
            fn main() {
                let add = (a, b) => a + b
            }
        """))


# ── List literals ──


class TestLists:
    def test_list_literal(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let nums: List<Int> = [1, 2, 3]
            }
        """))

    def test_empty_list(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let empty: List<Int> = []
            }
        """))

    def test_list_indexing(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let nums: List<Int> = [1, 2, 3]
                let first = nums[0]
            }
        """))


# ── Map literals ──


class TestMaps:
    def test_map_literal(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let ages = #{"Alice": 30, "Bob": 25}
            }
        """))

    def test_map_indexing(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let ages = #{"Alice": 30}
                let age = ages["Alice"]
            }
        """))


# ── Option / Result ──


class TestOptionResult:
    def test_some(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let x: Option<Int> = Some(42)
            }
        """))

    def test_none(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let x: Option<Int> = none
            }
        """))

    def test_ok(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let r: Result<Int, String> = Ok(42)
            }
        """))

    def test_err(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let r: Result<Int, String> = Err("oops")
            }
        """))

    def test_error_propagation(self) -> None:
        _parse_ok(textwrap.dedent("""\
            fn parse_int(s: String) -> Result<Int, String> {
                return Ok(42)
            }
            fn process(s: String) -> Result<Int, String> {
                let n = parse_int(s)?
                return Ok(n * 2)
            }
        """))


# ── Operators ──


class TestOperators:
    def test_arithmetic(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let a = 1 + 2
                let b = 3 - 1
                let c = 2 * 3
                let d = 10 / 2
                let e = 10 % 3
            }
        """))

    def test_comparison(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let a = 1 < 2
                let b = 1 > 2
                let c = 1 <= 2
                let d = 1 >= 2
                let e = 1 == 2
                let f = 1 != 2
            }
        """))

    def test_logical(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let a = true && false
                let b = true || false
                let c = !true
            }
        """))

    def test_compound_assignment(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let mut x = 0
                x += 1
                x -= 1
                x *= 2
                x /= 2
            }
        """))

    def test_range(self) -> None:
        _parse_ok(textwrap.dedent("""\
            fn main() {
                for i in 0..10 {
                    print("hi")
                }
            }
        """))

    def test_pipe_operator(self) -> None:
        _parse_ok(textwrap.dedent("""\
            fn double(x: Int) -> Int { return x * 2 }
            fn main() {
                let r = 5 |> double
            }
        """))

    def test_unary_negation(self) -> None:
        _check_ok(textwrap.dedent("""\
            fn main() {
                let x = -42
            }
        """))


# ── Namespace access ──


class TestNamespaceAccess:
    def test_namespace(self) -> None:
        _parse_ok(textwrap.dedent("""\
            fn main() {
                let x = Math::sqrt
            }
        """))


# ── FFI ──


class TestFFI:
    def test_extern_c(self) -> None:
        _parse_ok('extern "C" fn sqrt(x: Float) -> Float')

    def test_extern_python(self) -> None:
        _parse_ok('extern "Python" fn json::loads(s: String) -> String')


# ── Decorators ──


class TestDecorators:
    def test_test_decorator(self) -> None:
        _parse_ok(textwrap.dedent("""\
            @test
            fn test_add() {
                assert 1 + 1 == 2
            }
        """))

    def test_decorator_with_args(self) -> None:
        _parse_ok(textwrap.dedent("""\
            @restart("always", 3)
            agent Worker {
                input task: String
                output result: String
                fn handle(task: String) -> String { return task }
            }
        """))


# ── Doc comments ──


class TestDocComments:
    def test_doc_comment_on_fn(self) -> None:
        _parse_ok(textwrap.dedent("""\
            /// This is a doc comment
            fn helper() -> Int {
                return 1
            }
        """))


# ── Imports / Exports ──


class TestModules:
    def test_import(self) -> None:
        _parse_ok("import encoding::json")

    def test_import_items(self) -> None:
        _parse_ok("import net::http {get, post}")

    def test_export_names(self) -> None:
        _parse_ok("export helper, Config")

    def test_export_fn(self) -> None:
        _parse_ok(textwrap.dedent("""\
            export fn helper() -> Int {
                return 1
            }
        """))


# ── Struct construction with new keyword ──


class TestNewKeyword:
    def test_new_struct(self) -> None:
        _check_ok(textwrap.dedent("""\
            struct Config {
                name: String,
                value: Int,
            }
            fn main() {
                let c = new Config { name: "test", value: 42 }
            }
        """))


# ── Turbofish generic call ──


class TestTurbofish:
    def test_turbofish_call(self) -> None:
        _parse_ok(textwrap.dedent("""\
            fn identity<T>(x: T) -> T { return x }
            fn main() {
                let x = identity::<Int>(42)
            }
        """))


# ── LLVM compilation tests (require llvmlite) ──


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestLLVMCompilation:
    def test_hello_world_compiles(self) -> None:
        ir = _compile_ok(textwrap.dedent("""\
            fn main() {
                print("Hello, Mapanare!")
            }
        """))
        assert "main" in ir

    def test_arithmetic_compiles(self) -> None:
        ir = _compile_ok(textwrap.dedent("""\
            fn add(a: Int, b: Int) -> Int {
                return a + b
            }
            fn main() {
                let x = add(1, 2)
                print(str(x))
            }
        """))
        assert "add" in ir

    def test_struct_compiles(self) -> None:
        ir = _compile_ok(textwrap.dedent("""\
            struct Point {
                x: Float,
                y: Float,
            }
            fn main() {
                let p = new Point { x: 1.0, y: 2.0 }
                print(str(p.x))
            }
        """))
        assert "Point" in ir or "main" in ir

    def test_enum_match_compiles(self) -> None:
        ir = _compile_ok(textwrap.dedent("""\
            enum Color {
                Red,
                Green,
                Blue,
            }
            fn name(c: Color) -> String {
                match c {
                    Red => "red",
                    Green => "green",
                    Blue => "blue"
                }
            }
            fn main() {
                print("ok")
            }
        """))
        assert "main" in ir

    def test_list_compiles(self) -> None:
        ir = _compile_ok(textwrap.dedent("""\
            fn main() {
                let nums: List<Int> = [1, 2, 3]
                print(str(len(nums)))
            }
        """))
        assert "main" in ir

    def test_map_compiles(self) -> None:
        ir = _compile_ok(textwrap.dedent("""\
            fn main() {
                let m = #{"a": 1, "b": 2}
                print(str(len(m)))
            }
        """))
        assert "main" in ir

    def test_while_loop_compiles(self) -> None:
        ir = _compile_ok(textwrap.dedent("""\
            fn main() {
                let mut i = 0
                while i < 10 {
                    i += 1
                }
                print(str(i))
            }
        """))
        assert "main" in ir

    def test_for_range_compiles(self) -> None:
        ir = _compile_ok(textwrap.dedent("""\
            fn main() {
                for i in 0..5 {
                    print(str(i))
                }
            }
        """))
        assert "main" in ir

    def test_option_some_none_compiles(self) -> None:
        ir = _compile_ok(textwrap.dedent("""\
            fn main() {
                let x: Option<Int> = Some(42)
                let y: Option<Int> = none
                match x {
                    Some(v) => { print(str(v)) },
                    None => { print("none") }
                }
            }
        """))
        assert "main" in ir

    def test_result_ok_err_compiles(self) -> None:
        ir = _compile_ok(textwrap.dedent("""\
            fn main() {
                let r: Result<Int, String> = Ok(42)
                match r {
                    Ok(v) => { print(str(v)) },
                    Err(e) => { print(e) }
                }
            }
        """))
        assert "main" in ir
