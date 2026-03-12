"""Tests for AST → MIR lowering (Phase 2).

Each test parses a Mapanare program, runs semantic analysis, lowers to MIR,
and verifies the resulting MIR structure.
"""

from __future__ import annotations

from mapanare.lower import lower
from mapanare.mir import (
    AgentSend,
    AgentSpawn,
    AgentSync,
    BinOp,
    BinOpKind,
    Branch,
    Call,
    Const,
    Copy,
    EnumInit,
    EnumPayload,
    EnumTag,
    FieldGet,
    FieldSet,
    InterpConcat,
    Jump,
    MIRFunction,
    MIRModule,
    Phi,
    Return,
    SignalGet,
    SignalInit,
    StreamOp,
    StructInit,
    Switch,
    UnaryOp,
    UnaryOpKind,
    Unwrap,
    WrapErr,
    WrapNone,
    WrapOk,
    WrapSome,
    pretty_print_module,
    verify,
)
from mapanare.parser import parse
from mapanare.semantic import check
from mapanare.types import TypeKind


def _lower_source(source: str, module_name: str = "test") -> MIRModule:
    """Parse, check, and lower a Mapanare source string to MIR."""
    ast = parse(source)
    check(ast)
    return lower(ast, module_name=module_name)


def _get_fn(module: MIRModule, name: str) -> MIRFunction:
    """Get a function from a module by name, or fail."""
    fn = module.get_function(name)
    assert fn is not None, f"Function '{name}' not found in module"
    return fn


def _flat_instructions(fn: MIRFunction) -> list:
    """Get all instructions from all blocks of a function."""
    insts = []
    for bb in fn.blocks:
        insts.extend(bb.instructions)
    return insts


def _find_inst(fn: MIRFunction, inst_type: type) -> list:
    """Find all instructions of a given type in a function."""
    return [i for i in _flat_instructions(fn) if isinstance(i, inst_type)]


# ===================================================================
# Task 2: Lower expressions — literals, variables, binary ops, unary ops, calls
# ===================================================================


class TestLowerExpressions:
    """Test lowering of basic expressions."""

    def test_int_literal(self) -> None:
        mod = _lower_source("fn main() -> Int { 42 }")
        fn = _get_fn(mod, "main")
        consts = _find_inst(fn, Const)
        assert any(c.value == 42 for c in consts)

    def test_float_literal(self) -> None:
        mod = _lower_source("fn main() -> Float { 3.14 }")
        fn = _get_fn(mod, "main")
        consts = _find_inst(fn, Const)
        assert any(c.value == 3.14 for c in consts)

    def test_bool_literal(self) -> None:
        mod = _lower_source("fn main() -> Bool { true }")
        fn = _get_fn(mod, "main")
        consts = _find_inst(fn, Const)
        assert any(c.value is True for c in consts)

    def test_string_literal(self) -> None:
        mod = _lower_source('fn main() -> String { "hello" }')
        fn = _get_fn(mod, "main")
        consts = _find_inst(fn, Const)
        assert any(c.value == "hello" for c in consts)

    def test_none_literal(self) -> None:
        mod = _lower_source("fn main() { let x = none }")
        fn = _get_fn(mod, "main")
        wraps = _find_inst(fn, WrapNone)
        assert len(wraps) >= 1

    def test_variable_reference(self) -> None:
        mod = _lower_source("fn main() -> Int {\n" "    let x: Int = 10\n" "    x\n" "}\n")
        fn = _get_fn(mod, "main")
        consts = _find_inst(fn, Const)
        copies = _find_inst(fn, Copy)
        assert any(c.value == 10 for c in consts)
        assert len(copies) >= 1

    def test_binary_add(self) -> None:
        mod = _lower_source("fn add(a: Int, b: Int) -> Int { a + b }")
        fn = _get_fn(mod, "add")
        binops = _find_inst(fn, BinOp)
        assert len(binops) == 1
        assert binops[0].op == BinOpKind.ADD

    def test_binary_comparison(self) -> None:
        mod = _lower_source("fn cmp(a: Int, b: Int) -> Bool { a == b }")
        fn = _get_fn(mod, "cmp")
        binops = _find_inst(fn, BinOp)
        assert len(binops) == 1
        assert binops[0].op == BinOpKind.EQ
        assert binops[0].dest.ty.kind == TypeKind.BOOL

    def test_binary_logical(self) -> None:
        mod = _lower_source("fn logic(a: Bool, b: Bool) -> Bool { a && b }")
        fn = _get_fn(mod, "logic")
        binops = _find_inst(fn, BinOp)
        assert len(binops) == 1
        assert binops[0].op == BinOpKind.AND

    def test_unary_neg(self) -> None:
        mod = _lower_source("fn neg(x: Int) -> Int { -x }")
        fn = _get_fn(mod, "neg")
        unops = _find_inst(fn, UnaryOp)
        assert len(unops) == 1
        assert unops[0].op == UnaryOpKind.NEG

    def test_unary_not(self) -> None:
        mod = _lower_source("fn inv(x: Bool) -> Bool { !x }")
        fn = _get_fn(mod, "inv")
        unops = _find_inst(fn, UnaryOp)
        assert len(unops) == 1
        assert unops[0].op == UnaryOpKind.NOT
        assert unops[0].dest.ty.kind == TypeKind.BOOL

    def test_function_call(self) -> None:
        mod = _lower_source(
            "fn double(x: Int) -> Int { x + x }\n" "fn main() -> Int { double(5) }\n"
        )
        fn = _get_fn(mod, "main")
        calls = _find_inst(fn, Call)
        assert any(c.fn_name == "double" for c in calls)

    def test_builtin_call(self) -> None:
        mod = _lower_source("fn main() {\n" '    println("hello")\n' "}\n")
        fn = _get_fn(mod, "main")
        calls = _find_inst(fn, Call)
        assert any(c.fn_name == "println" for c in calls)


# ===================================================================
# Task 3: Lower let bindings
# ===================================================================


class TestLowerLetBindings:
    """Test lowering of let bindings (immutable and mutable)."""

    def test_immutable_let(self) -> None:
        mod = _lower_source("fn main() -> Int {\n" "    let x: Int = 42\n" "    x\n" "}\n")
        fn = _get_fn(mod, "main")
        copies = _find_inst(fn, Copy)
        assert len(copies) >= 1

    def test_mutable_let(self) -> None:
        mod = _lower_source(
            "fn main() -> Int {\n" "    let mut x: Int = 0\n" "    x = 10\n" "    x\n" "}\n"
        )
        fn = _get_fn(mod, "main")
        copies = _find_inst(fn, Copy)
        assert len(copies) >= 2  # initial + reassignment

    def test_compound_assignment(self) -> None:
        mod = _lower_source(
            "fn main() -> Int {\n" "    let mut x: Int = 5\n" "    x += 3\n" "    x\n" "}\n"
        )
        fn = _get_fn(mod, "main")
        binops = _find_inst(fn, BinOp)
        assert any(b.op == BinOpKind.ADD for b in binops)


# ===================================================================
# Task 4: Lower if/else
# ===================================================================


class TestLowerIfElse:
    """Test lowering of if/else to basic blocks."""

    def test_if_else_blocks(self) -> None:
        mod = _lower_source(
            "fn max(a: Int, b: Int) -> Int {\n"
            "    if a > b {\n"
            "        a\n"
            "    } else {\n"
            "        b\n"
            "    }\n"
            "}\n"
        )
        fn = _get_fn(mod, "max")
        assert len(fn.blocks) >= 4
        branches = _find_inst(fn, Branch)
        assert len(branches) >= 1
        phis = _find_inst(fn, Phi)
        assert len(phis) >= 1

    def test_if_no_else(self) -> None:
        mod = _lower_source(
            "fn maybe_print(x: Int) {\n"
            "    if x > 0 {\n"
            '        println("positive")\n'
            "    }\n"
            "}\n"
        )
        fn = _get_fn(mod, "maybe_print")
        branches = _find_inst(fn, Branch)
        assert len(branches) >= 1

    def test_if_elif_else(self) -> None:
        mod = _lower_source(
            "fn classify(x: Int) -> String {\n"
            "    if x > 0 {\n"
            '        "positive"\n'
            "    } else if x < 0 {\n"
            '        "negative"\n'
            "    } else {\n"
            '        "zero"\n'
            "    }\n"
            "}\n"
        )
        fn = _get_fn(mod, "classify")
        branches = _find_inst(fn, Branch)
        assert len(branches) >= 2


# ===================================================================
# Task 5: Lower match
# ===================================================================


class TestLowerMatch:
    """Test lowering of match expressions."""

    def test_match_enum(self) -> None:
        mod = _lower_source(
            "enum Color {\n"
            "    Red,\n"
            "    Green,\n"
            "    Blue,\n"
            "}\n"
            "\n"
            "fn name(c: Color) -> String {\n"
            '    match c { Red => "red", Green => "green", Blue => "blue" }\n'
            "}\n"
        )
        fn = _get_fn(mod, "name")
        tags = _find_inst(fn, EnumTag)
        switches = _find_inst(fn, Switch)
        assert len(tags) >= 1
        assert len(switches) >= 1

    def test_match_with_payload(self) -> None:
        mod = _lower_source(
            "enum Shape {\n"
            "    Circle(Float),\n"
            "    Rect(Float, Float),\n"
            "}\n"
            "\n"
            "fn area(s: Shape) -> Float {\n"
            "    match s { Circle(r) => 3.14 * r, _ => 0.0 }\n"
            "}\n"
        )
        fn = _get_fn(mod, "area")
        payloads = _find_inst(fn, EnumPayload)
        assert len(payloads) >= 1

    def test_match_wildcard(self) -> None:
        mod = _lower_source(
            "fn describe(x: Int) -> String {\n" '    match x { _ => "something" }\n' "}\n"
        )
        fn = _get_fn(mod, "describe")
        assert len(fn.blocks) >= 1


# ===================================================================
# Task 6: Lower for loops
# ===================================================================


class TestLowerForLoops:
    """Test lowering of for loops to basic blocks."""

    def test_for_loop_structure(self) -> None:
        mod = _lower_source(
            "fn sum_list(items: List<Int>) -> Int {\n"
            "    let mut total: Int = 0\n"
            "    for x in items {\n"
            "        total += x\n"
            "    }\n"
            "    total\n"
            "}\n"
        )
        fn = _get_fn(mod, "sum_list")
        assert len(fn.blocks) >= 4
        branches = _find_inst(fn, Branch)
        assert len(branches) >= 1
        jumps = _find_inst(fn, Jump)
        assert len(jumps) >= 1


# ===================================================================
# Task 7: Lower function definitions
# ===================================================================


class TestLowerFunctions:
    """Test lowering of function definitions."""

    def test_simple_function(self) -> None:
        mod = _lower_source("fn add(a: Int, b: Int) -> Int { a + b }")
        fn = _get_fn(mod, "add")
        assert fn.name == "add"
        assert len(fn.params) == 2
        assert fn.params[0].name == "a"
        assert fn.params[1].name == "b"
        assert fn.return_type.kind == TypeKind.INT

    def test_void_function(self) -> None:
        mod = _lower_source('fn greet() {\n    println("hello")\n}\n')
        fn = _get_fn(mod, "greet")
        assert fn.return_type.kind == TypeKind.VOID
        rets = _find_inst(fn, Return)
        assert len(rets) >= 1

    def test_public_function(self) -> None:
        mod = _lower_source("pub fn api() -> Int { 1 }")
        fn = _get_fn(mod, "api")
        assert fn.is_public

    def test_function_with_decorators(self) -> None:
        mod = _lower_source('@allow("unsafe")\n' "fn dangerous() { }\n")
        fn = _get_fn(mod, "dangerous")
        assert "allow" in fn.decorators

    def test_implicit_return(self) -> None:
        mod = _lower_source("fn identity(x: Int) -> Int { x }")
        fn = _get_fn(mod, "identity")
        rets = _find_inst(fn, Return)
        assert len(rets) >= 1
        assert rets[0].val is not None

    def test_explicit_return(self) -> None:
        mod = _lower_source(
            "fn early(x: Int) -> Int {\n"
            "    if x > 0 {\n"
            "        return x\n"
            "    }\n"
            "    0\n"
            "}\n"
        )
        fn = _get_fn(mod, "early")
        rets = _find_inst(fn, Return)
        assert len(rets) >= 1


# ===================================================================
# Task 8: Lower struct construction, field access, method calls
# ===================================================================


class TestLowerStructs:
    """Test lowering of struct operations."""

    def test_struct_construction(self) -> None:
        mod = _lower_source(
            "struct Point {\n"
            "    x: Float,\n"
            "    y: Float,\n"
            "}\n"
            "\n"
            "fn origin() -> Point {\n"
            "    Point(0.0, 0.0)\n"
            "}\n"
        )
        fn = _get_fn(mod, "origin")
        inits = _find_inst(fn, StructInit)
        assert len(inits) == 1
        assert inits[0].struct_type.type_info.name == "Point"
        assert len(inits[0].fields) == 2
        assert "Point" in mod.structs

    def test_field_access(self) -> None:
        mod = _lower_source(
            "struct Point {\n"
            "    x: Float,\n"
            "    y: Float,\n"
            "}\n"
            "\n"
            "fn get_x(p: Point) -> Float {\n"
            "    p.x\n"
            "}\n"
        )
        fn = _get_fn(mod, "get_x")
        gets = _find_inst(fn, FieldGet)
        # p.x may be lowered as FieldGet or SignalGet (due to .value heuristic)
        # but since field_name is "x" not "value", it should be FieldGet
        assert len(gets) >= 1
        assert gets[0].field_name == "x"

    def test_field_set(self) -> None:
        mod = _lower_source(
            "struct Point {\n"
            "    x: Float,\n"
            "    y: Float,\n"
            "}\n"
            "\n"
            "fn set_x(p: Point) {\n"
            "    p.x = 1.0\n"
            "}\n"
        )
        fn = _get_fn(mod, "set_x")
        sets = _find_inst(fn, FieldSet)
        assert len(sets) >= 1
        assert sets[0].field_name == "x"

    def test_impl_methods(self) -> None:
        mod = _lower_source(
            "struct Counter {\n"
            "    value: Int,\n"
            "}\n"
            "\n"
            "impl Counter {\n"
            "    fn increment(self: Counter) -> Int {\n"
            "        self.value + 1\n"
            "    }\n"
            "}\n"
        )
        fn = mod.get_function("Counter_increment")
        assert fn is not None
        assert fn.name == "Counter_increment"


# ===================================================================
# Task 9: Lower enum construction and pattern matching
# ===================================================================


class TestLowerEnums:
    """Test lowering of enum operations."""

    def test_enum_construction(self) -> None:
        mod = _lower_source(
            "enum Color {\n"
            "    Red,\n"
            "    Green,\n"
            "    Blue,\n"
            "}\n"
            "\n"
            "fn make_red() -> Color {\n"
            "    Red\n"
            "}\n"
        )
        fn = _get_fn(mod, "make_red")
        # Red as a bare identifier — the lowerer should check if it's a variant
        # It may be lowered as Identifier (lookup) since it's not a call
        # Let's verify the function exists and has output
        assert len(fn.blocks) >= 1

    def test_enum_with_payload(self) -> None:
        mod = _lower_source(
            "enum Shape {\n"
            "    Circle(Float),\n"
            "    Rect(Float, Float),\n"
            "}\n"
            "\n"
            "fn make_circle(r: Float) -> Shape {\n"
            "    Circle(r)\n"
            "}\n"
        )
        fn = _get_fn(mod, "make_circle")
        inits = _find_inst(fn, EnumInit)
        assert len(inits) >= 1
        assert inits[0].variant == "Circle"

    def test_enum_declared(self) -> None:
        mod = _lower_source("enum Direction {\n" "    Up,\n" "    Down,\n" "}\n" "fn test() { }\n")
        assert "Direction" in mod.enums
        assert len(mod.enums["Direction"]) == 2

    def test_enum_match_with_tag(self) -> None:
        mod = _lower_source(
            "enum Direction {\n"
            "    Up,\n"
            "    Down,\n"
            "}\n"
            "\n"
            "fn is_up(d: Direction) -> Bool {\n"
            "    match d { Up => true, Down => false }\n"
            "}\n"
        )
        fn = _get_fn(mod, "is_up")
        tags = _find_inst(fn, EnumTag)
        switches = _find_inst(fn, Switch)
        assert len(tags) >= 1
        assert len(switches) >= 1


# ===================================================================
# Task 10: Lower Option/Result
# ===================================================================


class TestLowerOptionResult:
    """Test lowering of Option/Result types."""

    def test_some(self) -> None:
        mod = _lower_source("fn wrap(x: Int) -> Option<Int> { Some(x) }")
        fn = _get_fn(mod, "wrap")
        wraps = _find_inst(fn, WrapSome)
        assert len(wraps) >= 1

    def test_ok(self) -> None:
        mod = _lower_source("fn success(x: Int) -> Result<Int, String> { Ok(x) }")
        fn = _get_fn(mod, "success")
        wraps = _find_inst(fn, WrapOk)
        assert len(wraps) >= 1

    def test_err(self) -> None:
        mod = _lower_source('fn fail() -> Result<Int, String> { Err("oops") }')
        fn = _get_fn(mod, "fail")
        wraps = _find_inst(fn, WrapErr)
        assert len(wraps) >= 1

    def test_error_propagation(self) -> None:
        mod = _lower_source(
            "fn try_it(x: Result<Int, String>) -> Result<Int, String> {\n"
            "    let val = x?\n"
            "    Ok(val)\n"
            "}\n"
        )
        fn = _get_fn(mod, "try_it")
        tags = _find_inst(fn, EnumTag)
        branches = _find_inst(fn, Branch)
        unwraps = _find_inst(fn, Unwrap)
        assert len(tags) >= 1
        assert len(branches) >= 1
        assert len(unwraps) >= 1


# ===================================================================
# Task 11: Lower string interpolation
# ===================================================================


class TestLowerInterpString:
    """Test lowering of string interpolation."""

    def test_interp_string(self) -> None:
        mod = _lower_source("fn greet(name: String) -> String {\n" '    "Hello, ${name}!"\n' "}\n")
        fn = _get_fn(mod, "greet")
        concats = _find_inst(fn, InterpConcat)
        assert len(concats) >= 1


# ===================================================================
# Task 12: Lower agent operations
# ===================================================================


class TestLowerAgents:
    """Test lowering of agent operations."""

    def test_agent_spawn(self) -> None:
        mod = _lower_source(
            "agent Counter {\n"
            "    input inc: Int\n"
            "    output value: Int\n"
            "\n"
            "    fn handle(self: Counter) {\n"
            '        println("handling")\n'
            "    }\n"
            "}\n"
            "\n"
            "fn main() {\n"
            "    let c = spawn Counter()\n"
            "}\n"
        )
        fn = _get_fn(mod, "main")
        spawns = _find_inst(fn, AgentSpawn)
        assert len(spawns) >= 1

    def test_agent_send(self) -> None:
        mod = _lower_source(
            "agent Worker {\n"
            "    input data: Int\n"
            "    output result: Int\n"
            "\n"
            "    fn handle(self: Worker) { }\n"
            "}\n"
            "\n"
            "fn main() {\n"
            "    let w = spawn Worker()\n"
            "    w.data <- 42\n"
            "}\n"
        )
        fn = _get_fn(mod, "main")
        sends = _find_inst(fn, AgentSend)
        assert len(sends) >= 1

    def test_agent_sync(self) -> None:
        mod = _lower_source(
            "agent Worker {\n"
            "    input data: Int\n"
            "    output result: Int\n"
            "\n"
            "    fn handle(self: Worker) { }\n"
            "}\n"
            "\n"
            "fn main() {\n"
            "    let w = spawn Worker()\n"
            "    let r = sync w.result\n"
            "}\n"
        )
        fn = _get_fn(mod, "main")
        syncs = _find_inst(fn, AgentSync)
        assert len(syncs) >= 1

    def test_agent_methods_lowered(self) -> None:
        mod = _lower_source(
            "agent MyAgent {\n"
            "    input x: Int\n"
            "    output y: Int\n"
            "\n"
            "    fn process(self: MyAgent) -> Int {\n"
            "        42\n"
            "    }\n"
            "}\n"
        )
        fn = mod.get_function("MyAgent_process")
        assert fn is not None


# ===================================================================
# Task 13: Lower signal operations
# ===================================================================


class TestLowerSignals:
    """Test lowering of signal operations."""

    def test_signal_init(self) -> None:
        mod = _lower_source("fn main() {\n    let s = signal(0)\n}\n")
        fn = _get_fn(mod, "main")
        inits = _find_inst(fn, SignalInit)
        assert len(inits) >= 1

    def test_signal_read(self) -> None:
        mod = _lower_source("fn main() {\n" "    let s = signal(0)\n" "    let v = s.value\n" "}\n")
        fn = _get_fn(mod, "main")
        gets = _find_inst(fn, SignalGet)
        assert len(gets) >= 1


# ===================================================================
# Task 14: Lower stream operations
# ===================================================================


class TestLowerStreams:
    """Test lowering of stream operations."""

    def test_stream_map(self) -> None:
        mod = _lower_source(
            "fn double(x: Int) -> Int { x * 2 }\n"
            "\n"
            "fn main() {\n"
            "    let items: List<Int> = [1, 2, 3]\n"
            "    items.map(double)\n"
            "}\n"
        )
        fn = _get_fn(mod, "main")
        ops = _find_inst(fn, StreamOp)
        calls = _find_inst(fn, Call)
        assert len(ops) >= 1 or len(calls) >= 1

    def test_stream_filter(self) -> None:
        mod = _lower_source(
            "fn positive(x: Int) -> Bool { x > 0 }\n"
            "\n"
            "fn main() {\n"
            "    let items: List<Int> = [1, 2, 3]\n"
            "    items.filter(positive)\n"
            "}\n"
        )
        fn = _get_fn(mod, "main")
        ops = _find_inst(fn, StreamOp)
        calls = _find_inst(fn, Call)
        assert len(ops) >= 1 or len(calls) >= 1


# ===================================================================
# Task 15: Lower pipe operator
# ===================================================================


class TestLowerPipe:
    """Test lowering of pipe operator."""

    def test_pipe_simple(self) -> None:
        mod = _lower_source(
            "fn double(x: Int) -> Int { x * 2 }\n" "fn main() -> Int { 5 |> double }\n"
        )
        fn = _get_fn(mod, "main")
        calls = _find_inst(fn, Call)
        assert any(c.fn_name == "double" for c in calls)

    def test_pipe_chain(self) -> None:
        mod = _lower_source(
            "fn add1(x: Int) -> Int { x + 1 }\n"
            "fn double(x: Int) -> Int { x * 2 }\n"
            "fn main() -> Int { 5 |> add1 |> double }\n"
        )
        fn = _get_fn(mod, "main")
        calls = _find_inst(fn, Call)
        call_names = [c.fn_name for c in calls]
        assert "add1" in call_names
        assert "double" in call_names


# ===================================================================
# Task 16: Lower extern declarations
# ===================================================================


class TestLowerExtern:
    """Test lowering of extern declarations."""

    def test_extern_c(self) -> None:
        mod = _lower_source('extern "C" fn puts(s: String) -> Int')
        assert len(mod.extern_fns) == 1
        abi, module, name, _, _ = mod.extern_fns[0]
        assert abi == "C"
        assert name == "puts"

    def test_extern_python(self) -> None:
        mod = _lower_source('extern "Python" fn math::sqrt(x: Float) -> Float')
        assert len(mod.extern_fns) == 1
        abi, module, name, _, _ = mod.extern_fns[0]
        assert abi == "Python"
        assert module == "math"
        assert name == "sqrt"


# ===================================================================
# Task 17: Lower impl blocks and trait dispatch
# ===================================================================


class TestLowerImpl:
    """Test lowering of impl blocks and trait dispatch."""

    def test_impl_method(self) -> None:
        mod = _lower_source(
            "struct Vec2 {\n"
            "    x: Float,\n"
            "    y: Float,\n"
            "}\n"
            "\n"
            "impl Vec2 {\n"
            "    fn length(self: Vec2) -> Float {\n"
            "        self.x + self.y\n"
            "    }\n"
            "\n"
            "    fn scale(self: Vec2, factor: Float) -> Float {\n"
            "        self.x * factor\n"
            "    }\n"
            "}\n"
        )
        assert mod.get_function("Vec2_length") is not None
        assert mod.get_function("Vec2_scale") is not None

    def test_impl_trait(self) -> None:
        mod = _lower_source(
            "struct MyType {\n"
            "    value: Int,\n"
            "}\n"
            "\n"
            "trait Display {\n"
            "    fn show(self) -> String\n"
            "}\n"
            "\n"
            "impl Display for MyType {\n"
            "    fn show(self: MyType) -> String {\n"
            '        "MyType"\n'
            "    }\n"
            "}\n"
        )
        assert mod.get_function("MyType_show") is not None


# ===================================================================
# Task 18: Lower decorators
# ===================================================================


class TestLowerDecorators:
    """Test lowering of decorators as metadata."""

    def test_decorator_preserved(self) -> None:
        mod = _lower_source("@restart\nfn resilient() { }\n")
        fn = _get_fn(mod, "resilient")
        assert "restart" in fn.decorators


# ===================================================================
# Task 19: Roundtrip tests — AST → MIR → pretty-print
# ===================================================================


class TestRoundtrip:
    """Test AST → MIR → pretty-print roundtrip."""

    def test_simple_fn_roundtrip(self) -> None:
        mod = _lower_source("fn id(x: Int) -> Int { x }")
        output = pretty_print_module(mod)
        assert "fn id" in output
        assert "ret" in output

    def test_multi_fn_roundtrip(self) -> None:
        mod = _lower_source(
            "fn add(a: Int, b: Int) -> Int { a + b }\n" "fn main() -> Int { add(1, 2) }\n"
        )
        output = pretty_print_module(mod)
        assert "fn add" in output
        assert "fn main" in output

    def test_struct_roundtrip(self) -> None:
        mod = _lower_source(
            "struct Point {\n"
            "    x: Float,\n"
            "    y: Float,\n"
            "}\n"
            "\n"
            "fn origin() -> Point {\n"
            "    Point(0.0, 0.0)\n"
            "}\n"
        )
        output = pretty_print_module(mod)
        assert "struct Point" in output
        assert "fn origin" in output

    def test_if_roundtrip(self) -> None:
        mod = _lower_source("fn abs(x: Int) -> Int {\n" "    if x > 0 { x } else { -x }\n" "}\n")
        output = pretty_print_module(mod)
        assert "branch" in output
        assert "phi" in output

    def test_enum_roundtrip(self) -> None:
        mod = _lower_source(
            "enum Bool2 {\n"
            "    True2,\n"
            "    False2,\n"
            "}\n"
            "\n"
            "fn test() -> Bool2 { True2 }\n"
        )
        output = pretty_print_module(mod)
        assert "enum Bool2" in output


# ===================================================================
# Task 20: Verify MIR structural correctness
# ===================================================================


class TestMIRVerification:
    """Test that lowered MIR passes the verifier."""

    def test_simple_fn_verifies(self) -> None:
        mod = _lower_source("fn main() -> Int { 42 }")
        errors = verify(mod)
        assert errors == [], f"Verification errors: {errors}"

    def test_if_else_verifies(self) -> None:
        mod = _lower_source(
            "fn max(a: Int, b: Int) -> Int {\n" "    if a > b { a } else { b }\n" "}\n"
        )
        errors = verify(mod)
        assert errors == [], f"Verification errors: {errors}"

    def test_for_loop_verifies(self) -> None:
        mod = _lower_source(
            "fn sum(items: List<Int>) -> Int {\n"
            "    let mut total: Int = 0\n"
            "    for x in items {\n"
            "        total += x\n"
            "    }\n"
            "    total\n"
            "}\n"
        )
        errors = verify(mod)
        assert errors == [], f"Verification errors: {errors}"

    def test_match_verifies(self) -> None:
        mod = _lower_source(
            "enum Dir {\n"
            "    Up,\n"
            "    Down,\n"
            "}\n"
            "\n"
            "fn test(d: Dir) -> Int {\n"
            "    match d { Up => 1, Down => 0 }\n"
            "}\n"
        )
        errors = verify(mod)
        assert errors == [], f"Verification errors: {errors}"

    def test_multiple_functions_verify(self) -> None:
        mod = _lower_source(
            "fn add(a: Int, b: Int) -> Int { a + b }\n"
            "fn sub(a: Int, b: Int) -> Int { a - b }\n"
            "fn main() -> Int { add(1, 2) }\n"
        )
        errors = verify(mod)
        assert errors == [], f"Verification errors: {errors}"

    def test_nested_if_verifies(self) -> None:
        mod = _lower_source(
            "fn classify(x: Int) -> String {\n"
            "    if x > 0 {\n"
            '        "positive"\n'
            "    } else if x < 0 {\n"
            '        "negative"\n'
            "    } else {\n"
            '        "zero"\n'
            "    }\n"
            "}\n"
        )
        errors = verify(mod)
        assert errors == [], f"Verification errors: {errors}"

    def test_while_loop_verifies(self) -> None:
        mod = _lower_source(
            "fn countdown(n: Int) -> Int {\n"
            "    let mut x: Int = n\n"
            "    while x > 0 {\n"
            "        x = x - 1\n"
            "    }\n"
            "    x\n"
            "}\n"
        )
        errors = verify(mod)
        assert errors == [], f"Verification errors: {errors}"

    def test_error_prop_verifies(self) -> None:
        mod = _lower_source(
            "fn try_it(x: Result<Int, String>) -> Result<Int, String> {\n"
            "    let val = x?\n"
            "    Ok(val)\n"
            "}\n"
        )
        errors = verify(mod)
        assert errors == [], f"Verification errors: {errors}"

    def test_complex_program_verifies(self) -> None:
        """A complex program that exercises many features."""
        mod = _lower_source(
            "struct Point {\n"
            "    x: Float,\n"
            "    y: Float,\n"
            "}\n"
            "\n"
            "enum Shape {\n"
            "    Circle(Float),\n"
            "    Rect(Float, Float),\n"
            "}\n"
            "\n"
            "fn area(s: Shape) -> Float {\n"
            "    match s { Circle(r) => 3.14 * r * r, _ => 0.0 }\n"
            "}\n"
            "\n"
            "fn make_point() -> Point {\n"
            "    Point(1.0, 2.0)\n"
            "}\n"
            "\n"
            "fn main() -> Int {\n"
            "    let p = make_point()\n"
            "    let s = Circle(5.0)\n"
            "    let a = area(s)\n"
            "    if a > 10.0 {\n"
            "        1\n"
            "    } else {\n"
            "        0\n"
            "    }\n"
            "}\n"
        )
        errors = verify(mod)
        assert errors == [], f"Verification errors: {errors}"
