"""Tests for MIR data structures, pretty-printer, and verifier (Phase 1 tasks 1-7)."""

from __future__ import annotations

from mapanare.mir import (
    AgentSend,
    AgentSpawn,
    AgentSync,
    BasicBlock,
    BinOp,
    BinOpKind,
    Branch,
    Call,
    Cast,
    Const,
    Copy,
    EnumInit,
    EnumPayload,
    EnumTag,
    ExternCall,
    FieldGet,
    FieldSet,
    IndexGet,
    IndexSet,
    InterpConcat,
    Jump,
    ListInit,
    MapInit,
    MIRFunction,
    MIRModule,
    MIRParam,
    MIRType,
    Phi,
    Return,
    SignalGet,
    SignalInit,
    SignalSet,
    StreamOp,
    StreamOpKind,
    StructInit,
    Switch,
    UnaryOp,
    UnaryOpKind,
    Unwrap,
    Value,
    VerifyError,
    WrapErr,
    WrapNone,
    WrapOk,
    WrapSome,
    is_terminator,
    mir_bool,
    mir_float,
    mir_int,
    mir_string,
    mir_void,
    pretty_print_function,
    pretty_print_instruction,
    pretty_print_module,
    verify,
)
from mapanare.types import TypeInfo, TypeKind

# ===================================================================
# Task 1 & 2: MIR data structures and instruction enum
# ===================================================================


class TestMIRDataStructures:
    """Test that all MIR data structures can be constructed."""

    def test_value_creation(self) -> None:
        v = Value(name="%0", ty=mir_int())
        assert v.name == "%0"
        assert v.ty.kind == TypeKind.INT

    def test_value_equality(self) -> None:
        a = Value(name="%x")
        b = Value(name="%x")
        c = Value(name="%y")
        assert a == b
        assert a != c
        assert hash(a) == hash(b)

    def test_basic_block(self) -> None:
        bb = BasicBlock(
            label="bb0",
            instructions=[
                Const(dest=Value("%0"), ty=mir_int(), value=42),
                Return(val=Value("%0")),
            ],
        )
        assert bb.label == "bb0"
        assert len(bb.instructions) == 2
        assert bb.terminator is not None
        assert isinstance(bb.terminator, Return)

    def test_basic_block_no_terminator(self) -> None:
        bb = BasicBlock(
            label="bb0",
            instructions=[Const(dest=Value("%0"), ty=mir_int(), value=42)],
        )
        assert bb.terminator is None

    def test_function(self) -> None:
        fn = MIRFunction(
            name="main",
            params=[MIRParam(name="x", ty=mir_int())],
            return_type=mir_int(),
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[Return(val=Value("%x"))],
                )
            ],
        )
        assert fn.name == "main"
        assert fn.entry_block is not None
        assert fn.entry_block.label == "entry"
        bm = fn.block_map()
        assert "entry" in bm

    def test_module(self) -> None:
        module = MIRModule(name="test")
        fn = MIRFunction(name="foo", blocks=[])
        module.functions.append(fn)
        assert module.get_function("foo") is fn
        assert module.get_function("bar") is None

    def test_module_structs(self) -> None:
        module = MIRModule(
            name="test",
            structs={"Point": [("x", mir_float()), ("y", mir_float())]},
        )
        assert "Point" in module.structs
        assert len(module.structs["Point"]) == 2

    def test_module_enums(self) -> None:
        module = MIRModule(
            name="test",
            enums={"Shape": [("Circle", [mir_float()]), ("Square", [mir_float()])]},
        )
        assert "Shape" in module.enums


class TestMIRInstructions:
    """Test all instruction dataclasses can be constructed."""

    def test_const(self) -> None:
        inst = Const(dest=Value("%0"), ty=mir_int(), value=42)
        assert inst.value == 42

    def test_copy(self) -> None:
        inst = Copy(dest=Value("%1"), src=Value("%0"))
        assert inst.src.name == "%0"

    def test_cast(self) -> None:
        inst = Cast(dest=Value("%1"), src=Value("%0"), target_type=mir_float())
        assert inst.target_type.kind == TypeKind.FLOAT

    def test_binop(self) -> None:
        inst = BinOp(dest=Value("%2"), op=BinOpKind.ADD, lhs=Value("%0"), rhs=Value("%1"))
        assert inst.op == BinOpKind.ADD

    def test_unaryop(self) -> None:
        inst = UnaryOp(dest=Value("%1"), op=UnaryOpKind.NEG, operand=Value("%0"))
        assert inst.op == UnaryOpKind.NEG

    def test_struct_init(self) -> None:
        inst = StructInit(
            dest=Value("%0"),
            struct_type=MIRType(TypeInfo(kind=TypeKind.STRUCT, name="Point")),
            fields=[("x", Value("%1")), ("y", Value("%2"))],
        )
        assert len(inst.fields) == 2

    def test_field_get_set(self) -> None:
        get = FieldGet(dest=Value("%1"), obj=Value("%0"), field_name="x")
        assert get.field_name == "x"
        st = FieldSet(obj=Value("%0"), field_name="x", val=Value("%1"))
        assert st.field_name == "x"

    def test_list_init(self) -> None:
        inst = ListInit(
            dest=Value("%0"),
            elem_type=mir_int(),
            elements=[Value("%1"), Value("%2")],
        )
        assert len(inst.elements) == 2

    def test_index_get_set(self) -> None:
        get = IndexGet(dest=Value("%2"), obj=Value("%0"), index=Value("%1"))
        assert get.obj.name == "%0"
        st = IndexSet(obj=Value("%0"), index=Value("%1"), val=Value("%2"))
        assert st.val.name == "%2"

    def test_map_init(self) -> None:
        inst = MapInit(
            dest=Value("%0"),
            key_type=mir_string(),
            val_type=mir_int(),
            pairs=[(Value("%1"), Value("%2"))],
        )
        assert len(inst.pairs) == 1

    def test_enum_init(self) -> None:
        inst = EnumInit(
            dest=Value("%0"),
            enum_type=MIRType(TypeInfo(kind=TypeKind.ENUM, name="Shape")),
            variant="Circle",
            payload=[Value("%1")],
        )
        assert inst.variant == "Circle"

    def test_enum_tag_payload(self) -> None:
        tag = EnumTag(dest=Value("%1"), enum_val=Value("%0"))
        assert tag.enum_val.name == "%0"
        payload = EnumPayload(dest=Value("%2"), enum_val=Value("%0"), variant="Circle")
        assert payload.variant == "Circle"

    def test_option_result_wrappers(self) -> None:
        some = WrapSome(dest=Value("%1"), val=Value("%0"))
        assert some.val.name == "%0"
        none = WrapNone(dest=Value("%1"), ty=mir_int())
        assert none.ty.kind == TypeKind.INT
        ok = WrapOk(dest=Value("%1"), val=Value("%0"))
        assert ok.val.name == "%0"
        err = WrapErr(dest=Value("%1"), val=Value("%0"))
        assert err.val.name == "%0"
        unwrap = Unwrap(dest=Value("%2"), val=Value("%1"))
        assert unwrap.val.name == "%1"

    def test_call(self) -> None:
        inst = Call(dest=Value("%0"), fn_name="add", args=[Value("%1"), Value("%2")])
        assert inst.fn_name == "add"

    def test_return(self) -> None:
        ret_val = Return(val=Value("%0"))
        assert ret_val.val is not None
        ret_void = Return()
        assert ret_void.val is None

    def test_extern_call(self) -> None:
        inst = ExternCall(
            dest=Value("%0"),
            abi="Python",
            module="math",
            fn_name="sqrt",
            args=[Value("%1")],
        )
        assert inst.abi == "Python"
        assert inst.module == "math"

    def test_jump(self) -> None:
        inst = Jump(target="bb1")
        assert inst.target == "bb1"

    def test_branch(self) -> None:
        inst = Branch(cond=Value("%0"), true_block="bb1", false_block="bb2")
        assert inst.true_block == "bb1"

    def test_switch(self) -> None:
        inst = Switch(
            tag=Value("%0"),
            cases=[(0, "bb1"), (1, "bb2")],
            default_block="bb3",
        )
        assert len(inst.cases) == 2

    def test_agent_instructions(self) -> None:
        spawn = AgentSpawn(
            dest=Value("%0"),
            agent_type=MIRType(TypeInfo(kind=TypeKind.AGENT, name="Worker")),
            args=[],
        )
        assert spawn.agent_type.kind == TypeKind.AGENT

        send = AgentSend(agent=Value("%0"), channel="input", val=Value("%1"))
        assert send.channel == "input"

        sync = AgentSync(dest=Value("%2"), agent=Value("%0"), channel="output")
        assert sync.channel == "output"

    def test_signal_instructions(self) -> None:
        init = SignalInit(
            dest=Value("%0"),
            signal_type=mir_int(),
            initial_val=Value("%1"),
        )
        assert init.signal_type.kind == TypeKind.INT

        get = SignalGet(dest=Value("%2"), signal=Value("%0"))
        assert get.signal.name == "%0"

        st = SignalSet(signal=Value("%0"), val=Value("%3"))
        assert st.val.name == "%3"

    def test_stream_op(self) -> None:
        inst = StreamOp(
            dest=Value("%1"),
            op_kind=StreamOpKind.MAP,
            source=Value("%0"),
            args=[Value("%fn")],
        )
        assert inst.op_kind == StreamOpKind.MAP

    def test_interp_concat(self) -> None:
        inst = InterpConcat(
            dest=Value("%0"),
            parts=[Value("%1"), Value("%2"), Value("%3")],
        )
        assert len(inst.parts) == 3

    def test_phi(self) -> None:
        inst = Phi(
            dest=Value("%0"),
            incoming=[("bb0", Value("%1")), ("bb1", Value("%2"))],
        )
        assert len(inst.incoming) == 2


class TestIsTerminator:
    """Test terminator detection."""

    def test_terminators(self) -> None:
        assert is_terminator(Jump(target="bb0"))
        assert is_terminator(Branch(cond=Value("%0"), true_block="bb1", false_block="bb2"))
        assert is_terminator(Switch(tag=Value("%0"), cases=[], default_block="bb1"))
        assert is_terminator(Return())

    def test_non_terminators(self) -> None:
        assert not is_terminator(Const(dest=Value("%0"), ty=mir_int(), value=42))
        assert not is_terminator(BinOp())
        assert not is_terminator(Call())
        assert not is_terminator(Phi())


# ===================================================================
# Task 3: MIR types
# ===================================================================


class TestMIRTypes:
    """Test MIR type wrappers."""

    def test_primitive_types(self) -> None:
        assert mir_int().kind == TypeKind.INT
        assert mir_float().kind == TypeKind.FLOAT
        assert mir_bool().kind == TypeKind.BOOL
        assert mir_string().kind == TypeKind.STRING
        assert mir_void().kind == TypeKind.VOID

    def test_type_names(self) -> None:
        assert mir_int().name == "Int"
        assert mir_float().name == "Float"
        assert mir_bool().name == "Bool"
        assert mir_string().name == "String"
        assert mir_void().name == "Void"

    def test_from_type_info(self) -> None:
        ti = TypeInfo(kind=TypeKind.LIST, args=[TypeInfo(kind=TypeKind.INT)])
        mt = MIRType.from_type_info(ti)
        assert mt.kind == TypeKind.LIST

    def test_struct_type(self) -> None:
        mt = MIRType(TypeInfo(kind=TypeKind.STRUCT, name="Point"))
        assert mt.kind == TypeKind.STRUCT
        assert mt.name == "Point"

    def test_type_equality(self) -> None:
        a = mir_int()
        b = mir_int()
        assert a == b

    def test_type_hashing(self) -> None:
        a = mir_int()
        b = mir_int()
        assert hash(a) == hash(b)
        s = {a, b}
        assert len(s) == 1


# ===================================================================
# Task 4: Pretty-printer
# ===================================================================


class TestPrettyPrinter:
    """Test MIR pretty-printer output."""

    def test_const_int(self) -> None:
        inst = Const(dest=Value("%0"), ty=mir_int(), value=42)
        assert pretty_print_instruction(inst) == "%0 = const Int 42"

    def test_const_bool(self) -> None:
        inst = Const(dest=Value("%0"), ty=mir_bool(), value=True)
        assert pretty_print_instruction(inst) == "%0 = const Bool true"

    def test_const_string(self) -> None:
        inst = Const(dest=Value("%0"), ty=mir_string(), value="hello")
        assert pretty_print_instruction(inst) == '%0 = const String "hello"'

    def test_const_none(self) -> None:
        inst = Const(dest=Value("%0"), ty=mir_void(), value=None)
        assert pretty_print_instruction(inst) == "%0 = const Void none"

    def test_copy(self) -> None:
        inst = Copy(dest=Value("%1"), src=Value("%0"))
        assert pretty_print_instruction(inst) == "%1 = copy %0"

    def test_cast(self) -> None:
        inst = Cast(dest=Value("%1"), src=Value("%0"), target_type=mir_float())
        assert pretty_print_instruction(inst) == "%1 = cast %0 to Float"

    def test_binop(self) -> None:
        inst = BinOp(dest=Value("%2"), op=BinOpKind.ADD, lhs=Value("%0"), rhs=Value("%1"))
        assert pretty_print_instruction(inst) == "%2 = + %0, %1"

    def test_unaryop(self) -> None:
        inst = UnaryOp(dest=Value("%1"), op=UnaryOpKind.NOT, operand=Value("%0"))
        assert pretty_print_instruction(inst) == "%1 = ! %0"

    def test_call(self) -> None:
        inst = Call(dest=Value("%0"), fn_name="add", args=[Value("%1"), Value("%2")])
        assert pretty_print_instruction(inst) == "%0 = call add(%1, %2)"

    def test_return_value(self) -> None:
        inst = Return(val=Value("%0"))
        assert pretty_print_instruction(inst) == "ret %0"

    def test_return_void(self) -> None:
        inst = Return()
        assert pretty_print_instruction(inst) == "ret void"

    def test_jump(self) -> None:
        inst = Jump(target="bb1")
        assert pretty_print_instruction(inst) == "jump bb1"

    def test_branch(self) -> None:
        inst = Branch(cond=Value("%0"), true_block="bb1", false_block="bb2")
        assert pretty_print_instruction(inst) == "branch %0, bb1, bb2"

    def test_switch(self) -> None:
        inst = Switch(
            tag=Value("%0"),
            cases=[(0, "bb1"), (1, "bb2")],
            default_block="bb3",
        )
        assert pretty_print_instruction(inst) == "switch %0 [0 => bb1, 1 => bb2] default bb3"

    def test_struct_init(self) -> None:
        inst = StructInit(
            dest=Value("%0"),
            struct_type=MIRType(TypeInfo(kind=TypeKind.STRUCT, name="Point")),
            fields=[("x", Value("%1")), ("y", Value("%2"))],
        )
        result = pretty_print_instruction(inst)
        assert result == "%0 = struct_init Point {x: %1, y: %2}"

    def test_field_get(self) -> None:
        inst = FieldGet(dest=Value("%1"), obj=Value("%0"), field_name="x")
        assert pretty_print_instruction(inst) == "%1 = field_get %0.x"

    def test_field_set(self) -> None:
        inst = FieldSet(obj=Value("%0"), field_name="x", val=Value("%1"))
        assert pretty_print_instruction(inst) == "field_set %0.x = %1"

    def test_list_init(self) -> None:
        inst = ListInit(
            dest=Value("%0"),
            elem_type=mir_int(),
            elements=[Value("%1"), Value("%2")],
        )
        assert pretty_print_instruction(inst) == "%0 = list_init Int [%1, %2]"

    def test_index_get(self) -> None:
        inst = IndexGet(dest=Value("%2"), obj=Value("%0"), index=Value("%1"))
        assert pretty_print_instruction(inst) == "%2 = index_get %0[%1]"

    def test_index_set(self) -> None:
        inst = IndexSet(obj=Value("%0"), index=Value("%1"), val=Value("%2"))
        assert pretty_print_instruction(inst) == "index_set %0[%1] = %2"

    def test_map_init(self) -> None:
        inst = MapInit(
            dest=Value("%0"),
            key_type=mir_string(),
            val_type=mir_int(),
            pairs=[(Value("%1"), Value("%2"))],
        )
        assert pretty_print_instruction(inst) == "%0 = map_init String:Int {%1: %2}"

    def test_enum_init(self) -> None:
        inst = EnumInit(
            dest=Value("%0"),
            enum_type=MIRType(TypeInfo(kind=TypeKind.ENUM, name="Shape")),
            variant="Circle",
            payload=[Value("%1")],
        )
        assert pretty_print_instruction(inst) == "%0 = enum_init Shape::Circle(%1)"

    def test_enum_init_no_payload(self) -> None:
        inst = EnumInit(
            dest=Value("%0"),
            enum_type=MIRType(TypeInfo(kind=TypeKind.ENUM, name="Color")),
            variant="Red",
            payload=[],
        )
        assert pretty_print_instruction(inst) == "%0 = enum_init Color::Red"

    def test_enum_tag(self) -> None:
        inst = EnumTag(dest=Value("%1"), enum_val=Value("%0"))
        assert pretty_print_instruction(inst) == "%1 = enum_tag %0"

    def test_enum_payload(self) -> None:
        inst = EnumPayload(dest=Value("%2"), enum_val=Value("%0"), variant="Circle")
        assert pretty_print_instruction(inst) == "%2 = enum_payload %0::Circle"

    def test_wrap_some(self) -> None:
        inst = WrapSome(dest=Value("%1"), val=Value("%0"))
        assert pretty_print_instruction(inst) == "%1 = wrap_some %0"

    def test_wrap_none(self) -> None:
        inst = WrapNone(dest=Value("%1"), ty=mir_int())
        assert pretty_print_instruction(inst) == "%1 = wrap_none Int"

    def test_wrap_ok_err(self) -> None:
        ok = WrapOk(dest=Value("%1"), val=Value("%0"))
        assert pretty_print_instruction(ok) == "%1 = wrap_ok %0"
        err = WrapErr(dest=Value("%1"), val=Value("%0"))
        assert pretty_print_instruction(err) == "%1 = wrap_err %0"

    def test_unwrap(self) -> None:
        inst = Unwrap(dest=Value("%2"), val=Value("%1"))
        assert pretty_print_instruction(inst) == "%2 = unwrap %1"

    def test_extern_call(self) -> None:
        inst = ExternCall(
            dest=Value("%0"), abi="Python", module="math", fn_name="sqrt", args=[Value("%1")]
        )
        assert pretty_print_instruction(inst) == '%0 = extern_call "Python" math::sqrt(%1)'

    def test_agent_spawn(self) -> None:
        inst = AgentSpawn(
            dest=Value("%0"),
            agent_type=MIRType(TypeInfo(kind=TypeKind.AGENT, name="Worker")),
            args=[Value("%1")],
        )
        assert pretty_print_instruction(inst) == "%0 = agent_spawn Worker(%1)"

    def test_agent_send(self) -> None:
        inst = AgentSend(agent=Value("%0"), channel="input", val=Value("%1"))
        assert pretty_print_instruction(inst) == "agent_send %0.input <- %1"

    def test_agent_sync(self) -> None:
        inst = AgentSync(dest=Value("%2"), agent=Value("%0"), channel="output")
        assert pretty_print_instruction(inst) == "%2 = agent_sync %0.output"

    def test_signal_init(self) -> None:
        inst = SignalInit(dest=Value("%0"), signal_type=mir_int(), initial_val=Value("%1"))
        assert pretty_print_instruction(inst) == "%0 = signal_init Int %1"

    def test_signal_get(self) -> None:
        inst = SignalGet(dest=Value("%1"), signal=Value("%0"))
        assert pretty_print_instruction(inst) == "%1 = signal_get %0"

    def test_signal_set(self) -> None:
        inst = SignalSet(signal=Value("%0"), val=Value("%1"))
        assert pretty_print_instruction(inst) == "signal_set %0 = %1"

    def test_stream_op(self) -> None:
        inst = StreamOp(
            dest=Value("%1"), op_kind=StreamOpKind.FILTER, source=Value("%0"), args=[Value("%fn")]
        )
        assert pretty_print_instruction(inst) == "%1 = stream_op filter %0, %fn"

    def test_stream_op_no_args(self) -> None:
        inst = StreamOp(dest=Value("%1"), op_kind=StreamOpKind.COLLECT, source=Value("%0"), args=[])
        assert pretty_print_instruction(inst) == "%1 = stream_op collect %0"

    def test_interp_concat(self) -> None:
        inst = InterpConcat(dest=Value("%0"), parts=[Value("%1"), Value("%2")])
        assert pretty_print_instruction(inst) == "%0 = interp_concat [%1, %2]"

    def test_phi(self) -> None:
        inst = Phi(
            dest=Value("%0"),
            incoming=[("bb0", Value("%1")), ("bb1", Value("%2"))],
        )
        assert pretty_print_instruction(inst) == "%0 = phi [bb0: %1, bb1: %2]"

    def test_pretty_print_function(self) -> None:
        fn = MIRFunction(
            name="main",
            params=[],
            return_type=mir_int(),
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[
                        Const(dest=Value("%0"), ty=mir_int(), value=42),
                        Return(val=Value("%0")),
                    ],
                )
            ],
        )
        output = pretty_print_function(fn)
        assert "fn main() -> Int" in output
        assert "entry:" in output
        assert "%0 = const Int 42" in output
        assert "ret %0" in output

    def test_pretty_print_function_empty(self) -> None:
        fn = MIRFunction(name="noop", return_type=mir_void(), blocks=[])
        output = pretty_print_function(fn)
        assert output == "fn noop() -> Void {}"

    def test_pretty_print_function_with_params(self) -> None:
        fn = MIRFunction(
            name="add",
            params=[MIRParam(name="a", ty=mir_int()), MIRParam(name="b", ty=mir_int())],
            return_type=mir_int(),
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[
                        BinOp(dest=Value("%0"), op=BinOpKind.ADD, lhs=Value("%a"), rhs=Value("%b")),
                        Return(val=Value("%0")),
                    ],
                )
            ],
        )
        output = pretty_print_function(fn)
        assert "fn add(a: Int, b: Int) -> Int" in output

    def test_pretty_print_module(self) -> None:
        module = MIRModule(
            name="test",
            structs={"Point": [("x", mir_float()), ("y", mir_float())]},
            functions=[
                MIRFunction(
                    name="main",
                    return_type=mir_void(),
                    blocks=[
                        BasicBlock(label="entry", instructions=[Return()]),
                    ],
                )
            ],
        )
        output = pretty_print_module(module)
        assert "module test" in output
        assert "struct Point" in output
        assert "fn main" in output

    def test_pretty_print_module_with_enums(self) -> None:
        module = MIRModule(
            name="shapes",
            enums={
                "Shape": [
                    ("Circle", [mir_float()]),
                    ("Square", [mir_float()]),
                    ("Empty", []),
                ]
            },
            functions=[],
        )
        output = pretty_print_module(module)
        assert "enum Shape" in output
        assert "Circle(Float)" in output
        assert "Empty" in output

    def test_pretty_print_module_with_extern(self) -> None:
        module = MIRModule(
            name="ffi",
            extern_fns=[("C", "", "puts", [mir_string()], mir_void())],
            functions=[],
        )
        output = pretty_print_module(module)
        assert 'extern "C"' in output
        assert "puts" in output


# ===================================================================
# Task 5: MIR verifier
# ===================================================================


class TestMIRVerifier:
    """Test the MIR structural verifier."""

    def _make_valid_module(self) -> MIRModule:
        """Create a simple valid module for testing."""
        return MIRModule(
            name="test",
            functions=[
                MIRFunction(
                    name="main",
                    return_type=mir_int(),
                    blocks=[
                        BasicBlock(
                            label="entry",
                            instructions=[
                                Const(dest=Value("%0"), ty=mir_int(), value=42),
                                Return(val=Value("%0")),
                            ],
                        )
                    ],
                )
            ],
        )

    def test_valid_module(self) -> None:
        module = self._make_valid_module()
        errors = verify(module)
        assert errors == []

    def test_empty_function(self) -> None:
        module = MIRModule(
            name="test",
            functions=[MIRFunction(name="empty", blocks=[])],
        )
        errors = verify(module)
        assert len(errors) == 1
        assert "no basic blocks" in errors[0].message

    def test_block_no_terminator(self) -> None:
        module = MIRModule(
            name="test",
            functions=[
                MIRFunction(
                    name="bad",
                    blocks=[
                        BasicBlock(
                            label="entry",
                            instructions=[Const(dest=Value("%0"), ty=mir_int(), value=1)],
                        )
                    ],
                )
            ],
        )
        errors = verify(module)
        assert any("does not end with a terminator" in e.message for e in errors)

    def test_terminator_in_middle(self) -> None:
        module = MIRModule(
            name="test",
            functions=[
                MIRFunction(
                    name="bad",
                    blocks=[
                        BasicBlock(
                            label="entry",
                            instructions=[
                                Return(val=Value("%0")),
                                Const(dest=Value("%1"), ty=mir_int(), value=1),
                                Return(val=Value("%1")),
                            ],
                        )
                    ],
                )
            ],
        )
        errors = verify(module)
        assert any("not last" in e.message for e in errors)

    def test_empty_block(self) -> None:
        module = MIRModule(
            name="test",
            functions=[
                MIRFunction(
                    name="bad",
                    blocks=[BasicBlock(label="entry", instructions=[])],
                )
            ],
        )
        errors = verify(module)
        assert any("no instructions" in e.message for e in errors)

    def test_jump_to_unknown_block(self) -> None:
        module = MIRModule(
            name="test",
            functions=[
                MIRFunction(
                    name="bad",
                    blocks=[
                        BasicBlock(
                            label="entry",
                            instructions=[Jump(target="nonexistent")],
                        )
                    ],
                )
            ],
        )
        errors = verify(module)
        assert any("unknown block" in e.message for e in errors)

    def test_branch_to_unknown_blocks(self) -> None:
        module = MIRModule(
            name="test",
            functions=[
                MIRFunction(
                    name="bad",
                    blocks=[
                        BasicBlock(
                            label="entry",
                            instructions=[
                                Branch(
                                    cond=Value("%0"),
                                    true_block="bb_gone",
                                    false_block="bb_also_gone",
                                )
                            ],
                        )
                    ],
                )
            ],
        )
        errors = verify(module)
        assert len(errors) >= 2
        assert any("bb_gone" in e.message for e in errors)
        assert any("bb_also_gone" in e.message for e in errors)

    def test_switch_unknown_targets(self) -> None:
        module = MIRModule(
            name="test",
            functions=[
                MIRFunction(
                    name="bad",
                    blocks=[
                        BasicBlock(
                            label="entry",
                            instructions=[
                                Switch(
                                    tag=Value("%0"),
                                    cases=[(0, "missing")],
                                    default_block="also_missing",
                                )
                            ],
                        )
                    ],
                )
            ],
        )
        errors = verify(module)
        assert any("missing" in e.message for e in errors)
        assert any("also_missing" in e.message for e in errors)

    def test_ssa_redefinition(self) -> None:
        module = MIRModule(
            name="test",
            functions=[
                MIRFunction(
                    name="bad",
                    blocks=[
                        BasicBlock(
                            label="entry",
                            instructions=[
                                Const(dest=Value("%0"), ty=mir_int(), value=1),
                                Const(dest=Value("%0"), ty=mir_int(), value=2),
                                Return(val=Value("%0")),
                            ],
                        )
                    ],
                )
            ],
        )
        errors = verify(module)
        # Relaxed SSA: redefinitions are allowed for mutable variable support
        assert not any("redefined" in e.message for e in errors)

    def test_ssa_redefinition_across_blocks(self) -> None:
        module = MIRModule(
            name="test",
            functions=[
                MIRFunction(
                    name="bad",
                    blocks=[
                        BasicBlock(
                            label="bb0",
                            instructions=[
                                Const(dest=Value("%0"), ty=mir_int(), value=1),
                                Jump(target="bb1"),
                            ],
                        ),
                        BasicBlock(
                            label="bb1",
                            instructions=[
                                Const(dest=Value("%0"), ty=mir_int(), value=2),
                                Return(val=Value("%0")),
                            ],
                        ),
                    ],
                )
            ],
        )
        errors = verify(module)
        # Relaxed SSA: redefinitions are allowed for mutable variable support
        assert not any("redefined" in e.message for e in errors)

    def test_phi_after_non_phi(self) -> None:
        module = MIRModule(
            name="test",
            functions=[
                MIRFunction(
                    name="bad",
                    blocks=[
                        BasicBlock(
                            label="bb0",
                            instructions=[
                                Const(dest=Value("%0"), ty=mir_int(), value=1),
                                Jump(target="bb1"),
                            ],
                        ),
                        BasicBlock(
                            label="bb1",
                            instructions=[
                                Const(dest=Value("%1"), ty=mir_int(), value=2),
                                Phi(
                                    dest=Value("%2"),
                                    incoming=[("bb0", Value("%0"))],
                                ),
                                Return(val=Value("%2")),
                            ],
                        ),
                    ],
                )
            ],
        )
        errors = verify(module)
        assert any("phi node after non-phi" in e.message for e in errors)

    def test_phi_at_start_is_valid(self) -> None:
        module = MIRModule(
            name="test",
            functions=[
                MIRFunction(
                    name="ok",
                    blocks=[
                        BasicBlock(
                            label="bb0",
                            instructions=[
                                Const(dest=Value("%0"), ty=mir_int(), value=1),
                                Jump(target="bb1"),
                            ],
                        ),
                        BasicBlock(
                            label="bb1",
                            instructions=[
                                Phi(
                                    dest=Value("%1"),
                                    incoming=[("bb0", Value("%0"))],
                                ),
                                Return(val=Value("%1")),
                            ],
                        ),
                    ],
                )
            ],
        )
        errors = verify(module)
        assert errors == []

    def test_phi_unknown_incoming_block(self) -> None:
        module = MIRModule(
            name="test",
            functions=[
                MIRFunction(
                    name="bad",
                    blocks=[
                        BasicBlock(
                            label="bb0",
                            instructions=[
                                Phi(
                                    dest=Value("%0"),
                                    incoming=[("nonexistent", Value("%1"))],
                                ),
                                Return(val=Value("%0")),
                            ],
                        )
                    ],
                )
            ],
        )
        errors = verify(module)
        assert any("unknown block" in e.message for e in errors)

    def test_valid_multi_block_function(self) -> None:
        """A valid if/else diamond pattern."""
        module = MIRModule(
            name="test",
            functions=[
                MIRFunction(
                    name="abs",
                    params=[MIRParam(name="x", ty=mir_int())],
                    return_type=mir_int(),
                    blocks=[
                        BasicBlock(
                            label="entry",
                            instructions=[
                                Const(dest=Value("%zero"), ty=mir_int(), value=0),
                                BinOp(
                                    dest=Value("%cmp"),
                                    op=BinOpKind.LT,
                                    lhs=Value("%x"),
                                    rhs=Value("%zero"),
                                ),
                                Branch(
                                    cond=Value("%cmp"),
                                    true_block="then",
                                    false_block="else",
                                ),
                            ],
                        ),
                        BasicBlock(
                            label="then",
                            instructions=[
                                UnaryOp(
                                    dest=Value("%neg"),
                                    op=UnaryOpKind.NEG,
                                    operand=Value("%x"),
                                ),
                                Jump(target="merge"),
                            ],
                        ),
                        BasicBlock(
                            label="else",
                            instructions=[
                                Copy(dest=Value("%pos"), src=Value("%x")),
                                Jump(target="merge"),
                            ],
                        ),
                        BasicBlock(
                            label="merge",
                            instructions=[
                                Phi(
                                    dest=Value("%result"),
                                    incoming=[("then", Value("%neg")), ("else", Value("%pos"))],
                                ),
                                Return(val=Value("%result")),
                            ],
                        ),
                    ],
                )
            ],
        )
        errors = verify(module)
        assert errors == []

    def test_verify_error_repr(self) -> None:
        err = VerifyError(function="foo", block="bb0", message="something wrong")
        assert "foo" in repr(err)
        assert "bb0" in repr(err)
        assert "something wrong" in repr(err)

    def test_multiple_functions(self) -> None:
        module = MIRModule(
            name="test",
            functions=[
                MIRFunction(
                    name="a",
                    blocks=[BasicBlock(label="entry", instructions=[Return()])],
                ),
                MIRFunction(
                    name="b",
                    blocks=[BasicBlock(label="entry", instructions=[Return()])],
                ),
            ],
        )
        errors = verify(module)
        assert errors == []

    def test_valid_jump_between_blocks(self) -> None:
        module = MIRModule(
            name="test",
            functions=[
                MIRFunction(
                    name="chain",
                    blocks=[
                        BasicBlock(
                            label="bb0",
                            instructions=[Jump(target="bb1")],
                        ),
                        BasicBlock(
                            label="bb1",
                            instructions=[Jump(target="bb2")],
                        ),
                        BasicBlock(
                            label="bb2",
                            instructions=[Return()],
                        ),
                    ],
                )
            ],
        )
        errors = verify(module)
        assert errors == []
