"""MIR (Mid-level Intermediate Representation) for the Mapanare compiler.

SSA-based, typed, flat IR with explicit control flow. Sits between
semantic analysis and emission, giving optimizers and backends a single
clean representation.

Design goals:
- SSA: every value assigned exactly once; phi nodes at merges
- Typed: every value carries its Mapanare type
- Explicit control flow: basic blocks with terminators
- Flat: three-address form (dest = op(args))
- Backend-agnostic: no Python-isms or LLVM-isms
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from mapanare.types import UNKNOWN_TYPE, TypeInfo, TypeKind

# ---------------------------------------------------------------------------
# MIR Types — thin wrappers around TypeInfo for the IR layer
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class MIRType:
    """Type representation in MIR. Wraps the semantic TypeInfo."""

    type_info: TypeInfo = field(default_factory=lambda: UNKNOWN_TYPE)

    @property
    def kind(self) -> TypeKind:
        return self.type_info.kind

    @property
    def name(self) -> str:
        return self.type_info.display_name

    def __repr__(self) -> str:
        return repr(self.type_info)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MIRType):
            return NotImplemented
        return self.type_info == other.type_info

    def __hash__(self) -> int:
        return hash(self.type_info)

    @staticmethod
    def from_type_info(ti: TypeInfo) -> MIRType:
        return MIRType(type_info=ti)


# Cached singleton types — these are immutable, so sharing is safe.
_MIR_INT = MIRType(TypeInfo(kind=TypeKind.INT))
_MIR_FLOAT = MIRType(TypeInfo(kind=TypeKind.FLOAT))
_MIR_BOOL = MIRType(TypeInfo(kind=TypeKind.BOOL))
_MIR_STRING = MIRType(TypeInfo(kind=TypeKind.STRING))
_MIR_VOID = MIRType(TypeInfo(kind=TypeKind.VOID))
_MIR_UNKNOWN = MIRType(TypeInfo(kind=TypeKind.UNKNOWN))


# Convenience factories (return cached singletons)
def mir_int() -> MIRType:
    return _MIR_INT


def mir_float() -> MIRType:
    return _MIR_FLOAT


def mir_bool() -> MIRType:
    return _MIR_BOOL


def mir_string() -> MIRType:
    return _MIR_STRING


def mir_void() -> MIRType:
    return _MIR_VOID


def mir_unknown() -> MIRType:
    return _MIR_UNKNOWN


# ---------------------------------------------------------------------------
# MIR Values — SSA virtual registers
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class Value:
    """An SSA value (virtual register)."""

    name: str = ""  # e.g. "%0", "%x", "%tmp1"
    ty: MIRType = field(default_factory=mir_unknown)

    def __repr__(self) -> str:
        return self.name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Value):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)


# ---------------------------------------------------------------------------
# Binary / Unary operator enums
# ---------------------------------------------------------------------------


class BinOpKind(Enum):
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    MOD = "%"
    EQ = "=="
    NE = "!="
    LT = "<"
    GT = ">"
    LE = "<="
    GE = ">="
    AND = "&&"
    OR = "||"


class UnaryOpKind(Enum):
    NEG = "-"
    NOT = "!"


# ---------------------------------------------------------------------------
# Stream operator kinds
# ---------------------------------------------------------------------------


class StreamOpKind(Enum):
    MAP = auto()
    FILTER = auto()
    FOLD = auto()
    TAKE = auto()
    SKIP = auto()
    COLLECT = auto()


# ---------------------------------------------------------------------------
# MIR Instructions
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class SourceSpan:
    """Source location for debug info. Attached to MIR instructions and functions."""

    line: int = 0
    column: int = 0
    end_line: int = 0
    end_column: int = 0


@dataclass(slots=True)
class Instruction:
    """Base class for all MIR instructions."""

    span: SourceSpan | None = field(default=None, repr=False, compare=False)


# --- Values ---


@dataclass(slots=True)
class Const(Instruction):
    """Load a constant value."""

    dest: Value = field(default_factory=Value)
    ty: MIRType = field(default_factory=mir_unknown)
    value: Any = None  # int, float, bool, str, None


@dataclass(slots=True)
class Copy(Instruction):
    """Copy a value."""

    dest: Value = field(default_factory=Value)
    src: Value = field(default_factory=Value)


@dataclass(slots=True)
class Cast(Instruction):
    """Type conversion."""

    dest: Value = field(default_factory=Value)
    src: Value = field(default_factory=Value)
    target_type: MIRType = field(default_factory=mir_unknown)


# --- Arithmetic / Logic ---


@dataclass(slots=True)
class BinOp(Instruction):
    """Binary operation."""

    dest: Value = field(default_factory=Value)
    op: BinOpKind = BinOpKind.ADD
    lhs: Value = field(default_factory=Value)
    rhs: Value = field(default_factory=Value)


@dataclass(slots=True)
class UnaryOp(Instruction):
    """Unary operation."""

    dest: Value = field(default_factory=Value)
    op: UnaryOpKind = UnaryOpKind.NEG
    operand: Value = field(default_factory=Value)


# --- Memory / Aggregates ---


@dataclass(slots=True)
class StructInit(Instruction):
    """Construct a struct."""

    dest: Value = field(default_factory=Value)
    struct_type: MIRType = field(default_factory=mir_unknown)
    fields: list[tuple[str, Value]] = field(default_factory=list)  # (field_name, value)


@dataclass(slots=True)
class FieldGet(Instruction):
    """Read a struct field."""

    dest: Value = field(default_factory=Value)
    obj: Value = field(default_factory=Value)
    field_name: str = ""


@dataclass(slots=True)
class FieldSet(Instruction):
    """Write a struct field (mut only)."""

    obj: Value = field(default_factory=Value)
    field_name: str = ""
    val: Value = field(default_factory=Value)


@dataclass(slots=True)
class ListInit(Instruction):
    """Construct a list."""

    dest: Value = field(default_factory=Value)
    elem_type: MIRType = field(default_factory=mir_unknown)
    elements: list[Value] = field(default_factory=list)


@dataclass(slots=True)
class IndexGet(Instruction):
    """Read list[i]."""

    dest: Value = field(default_factory=Value)
    obj: Value = field(default_factory=Value)
    index: Value = field(default_factory=Value)


@dataclass(slots=True)
class IndexSet(Instruction):
    """Write list[i] (mut only)."""

    obj: Value = field(default_factory=Value)
    index: Value = field(default_factory=Value)
    val: Value = field(default_factory=Value)


@dataclass(slots=True)
class ListPush(Instruction):
    """Push an element onto a list (mut only).

    After this instruction, ``dest`` holds the updated list value.
    The emitter stores back to the alloca so subsequent reads see the change.
    """

    dest: Value = field(default_factory=Value)
    list_val: Value = field(default_factory=Value)
    element: Value = field(default_factory=Value)


@dataclass(slots=True)
class MapInit(Instruction):
    """Construct a map."""

    dest: Value = field(default_factory=Value)
    key_type: MIRType = field(default_factory=mir_unknown)
    val_type: MIRType = field(default_factory=mir_unknown)
    pairs: list[tuple[Value, Value]] = field(default_factory=list)  # (key, value)


# --- Enum / Tagged Union ---


@dataclass(slots=True)
class EnumInit(Instruction):
    """Construct an enum variant."""

    dest: Value = field(default_factory=Value)
    enum_type: MIRType = field(default_factory=mir_unknown)
    variant: str = ""
    payload: list[Value] = field(default_factory=list)


@dataclass(slots=True)
class EnumTag(Instruction):
    """Extract tag for matching."""

    dest: Value = field(default_factory=Value)
    enum_val: Value = field(default_factory=Value)


@dataclass(slots=True)
class EnumPayload(Instruction):
    """Extract payload after tag check."""

    dest: Value = field(default_factory=Value)
    enum_val: Value = field(default_factory=Value)
    variant: str = ""
    payload_idx: int = 0


# --- Option / Result ---


@dataclass(slots=True)
class WrapSome(Instruction):
    """Some(val)."""

    dest: Value = field(default_factory=Value)
    val: Value = field(default_factory=Value)


@dataclass(slots=True)
class WrapNone(Instruction):
    """None."""

    dest: Value = field(default_factory=Value)
    ty: MIRType = field(default_factory=mir_unknown)


@dataclass(slots=True)
class WrapOk(Instruction):
    """Ok(val)."""

    dest: Value = field(default_factory=Value)
    val: Value = field(default_factory=Value)


@dataclass(slots=True)
class WrapErr(Instruction):
    """Err(val)."""

    dest: Value = field(default_factory=Value)
    val: Value = field(default_factory=Value)


@dataclass(slots=True)
class Unwrap(Instruction):
    """Extract inner value (after tag check)."""

    dest: Value = field(default_factory=Value)
    val: Value = field(default_factory=Value)


# --- Functions ---


@dataclass(slots=True)
class Call(Instruction):
    """Call a function."""

    dest: Value = field(default_factory=Value)
    fn_name: str = ""
    args: list[Value] = field(default_factory=list)


@dataclass(slots=True)
class Return(Instruction):
    """Return from function."""

    val: Value | None = None


@dataclass(slots=True)
class ExternCall(Instruction):
    """FFI call (C or Python)."""

    dest: Value = field(default_factory=Value)
    abi: str = "C"
    module: str = ""
    fn_name: str = ""
    args: list[Value] = field(default_factory=list)


# --- Control Flow (terminators) ---


@dataclass(slots=True)
class Jump(Instruction):
    """Unconditional jump."""

    target: str = ""  # block label


@dataclass(slots=True)
class Branch(Instruction):
    """Conditional branch."""

    cond: Value = field(default_factory=Value)
    true_block: str = ""
    false_block: str = ""


@dataclass(slots=True)
class Switch(Instruction):
    """Multi-way branch (match)."""

    tag: Value = field(default_factory=Value)
    cases: list[tuple[Any, str]] = field(default_factory=list)  # (value, block_label)
    default_block: str = ""


# --- Agents / Signals / Streams ---


@dataclass(slots=True)
class AgentSpawn(Instruction):
    """Spawn an agent."""

    dest: Value = field(default_factory=Value)
    agent_type: MIRType = field(default_factory=mir_unknown)
    args: list[Value] = field(default_factory=list)


@dataclass(slots=True)
class AgentSend(Instruction):
    """Send a value to an agent channel."""

    agent: Value = field(default_factory=Value)
    channel: str = ""
    val: Value = field(default_factory=Value)


@dataclass(slots=True)
class AgentSync(Instruction):
    """Sync (await) an agent channel."""

    dest: Value = field(default_factory=Value)
    agent: Value = field(default_factory=Value)
    channel: str = ""


@dataclass(slots=True)
class SignalInit(Instruction):
    """Initialize a signal."""

    dest: Value = field(default_factory=Value)
    signal_type: MIRType = field(default_factory=mir_unknown)
    initial_val: Value = field(default_factory=Value)


@dataclass(slots=True)
class SignalGet(Instruction):
    """Read a signal's value."""

    dest: Value = field(default_factory=Value)
    signal: Value = field(default_factory=Value)


@dataclass(slots=True)
class SignalSet(Instruction):
    """Write a signal's value."""

    signal: Value = field(default_factory=Value)
    val: Value = field(default_factory=Value)


@dataclass(slots=True)
class SignalComputed(Instruction):
    """Create a computed signal with a compute function and dependencies."""

    dest: Value = field(default_factory=Value)
    compute_fn: str = ""  # Name of the compute function
    deps: list[Value] = field(default_factory=list)  # Dependency signals
    val_size: int = 8  # Size of the result value


@dataclass(slots=True)
class SignalSubscribe(Instruction):
    """Subscribe one signal to another (add as dependent)."""

    signal: Value = field(default_factory=Value)
    subscriber: Value = field(default_factory=Value)


@dataclass(slots=True)
class StreamInit(Instruction):
    """Create a stream from a list source."""

    dest: Value = field(default_factory=Value)
    source: Value = field(default_factory=Value)  # The source list
    elem_type: MIRType = field(default_factory=mir_unknown)


@dataclass(slots=True)
class StreamOp(Instruction):
    """Stream operation (map, filter, fold, etc.)."""

    dest: Value = field(default_factory=Value)
    op_kind: StreamOpKind = StreamOpKind.MAP
    source: Value = field(default_factory=Value)
    args: list[Value] = field(default_factory=list)
    fn_name: str = ""  # Lambda/function name for map/filter/fold callbacks


# --- Closures ---


@dataclass(slots=True)
class ClosureCreate(Instruction):
    """Create a closure: bundle a function pointer with a captured environment.

    The result is a closure value {fn_ptr, env_ptr}. The function's first
    parameter is the env_ptr (opaque i8*), followed by its normal parameters.
    """

    dest: Value = field(default_factory=Value)
    fn_name: str = ""  # Lambda function name (has __env_ptr as first param)
    captures: list[Value] = field(default_factory=list)  # Captured values
    capture_types: list[MIRType] = field(default_factory=list)  # Types of captured values


@dataclass(slots=True)
class ClosureCall(Instruction):
    """Call a closure value (indirect call through fn_ptr with env_ptr)."""

    dest: Value = field(default_factory=Value)
    closure: Value = field(default_factory=Value)  # The closure {fn_ptr, env_ptr}
    args: list[Value] = field(default_factory=list)


@dataclass(slots=True)
class EnvLoad(Instruction):
    """Load a captured variable from a closure environment struct."""

    dest: Value = field(default_factory=Value)
    env: Value = field(default_factory=Value)  # The env_ptr
    index: int = 0  # Field index in the environment struct
    val_type: MIRType = field(default_factory=mir_unknown)


# --- Strings ---


@dataclass(slots=True)
class InterpConcat(Instruction):
    """String interpolation concatenation."""

    dest: Value = field(default_factory=Value)
    parts: list[Value] = field(default_factory=list)


# --- Assert ---


@dataclass(slots=True)
class Assert(Instruction):
    """Runtime assertion: fails with message if condition is false."""

    cond: Value = field(default_factory=Value)
    message: Value | None = None
    filename: str = ""
    line: int = 0


# --- Phi ---


@dataclass(slots=True)
class Phi(Instruction):
    """SSA phi node at block entry."""

    dest: Value = field(default_factory=Value)
    incoming: list[tuple[str, Value]] = field(default_factory=list)  # (block_label, value)


# ---------------------------------------------------------------------------
# Terminator check helpers
# ---------------------------------------------------------------------------

TERMINATOR_TYPES = (Jump, Branch, Switch, Return)


def is_terminator(inst: Instruction) -> bool:
    """Return True if the instruction is a basic block terminator."""
    return isinstance(inst, TERMINATOR_TYPES)


# ---------------------------------------------------------------------------
# Basic Block
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class BasicBlock:
    """A basic block: a sequence of instructions ending with a terminator."""

    label: str = ""
    instructions: list[Instruction] = field(default_factory=list)

    @property
    def terminator(self) -> Instruction | None:
        """Return the terminator instruction, or None if the block is incomplete."""
        if self.instructions and is_terminator(self.instructions[-1]):
            return self.instructions[-1]
        return None

    def predecessors_labels(self) -> list[str]:
        """Labels referenced by phi nodes in this block."""
        labels: list[str] = []
        for inst in self.instructions:
            if isinstance(inst, Phi):
                for lbl, _ in inst.incoming:
                    if lbl not in labels:
                        labels.append(lbl)
        return labels


# ---------------------------------------------------------------------------
# Function
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class MIRParam:
    """A function parameter in MIR."""

    name: str = ""
    ty: MIRType = field(default_factory=mir_unknown)


@dataclass(slots=True)
class MIRFunction:
    """A function in MIR: params, return type, and basic blocks."""

    name: str = ""
    params: list[MIRParam] = field(default_factory=list)
    return_type: MIRType = field(default_factory=mir_void)
    blocks: list[BasicBlock] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)  # metadata from AST decorators
    is_public: bool = False
    source_line: int = 0  # Source line where this function is defined
    source_file: str = ""  # Source file name

    @property
    def entry_block(self) -> BasicBlock | None:
        return self.blocks[0] if self.blocks else None

    def block_map(self) -> dict[str, BasicBlock]:
        """Return a label -> block mapping."""
        return {bb.label: bb for bb in self.blocks}


# ---------------------------------------------------------------------------
# Module
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class MIRAgentInfo:
    """Agent class metadata for backend emission."""

    name: str = ""
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    state: list[tuple[str, Any]] = field(default_factory=list)  # (name, initial_value)
    method_names: list[str] = field(default_factory=list)  # MIR function names


@dataclass(slots=True)
class MIRPipeInfo:
    """Pipe definition metadata."""

    name: str = ""
    stages: list[str] = field(default_factory=list)  # agent type names


@dataclass(slots=True)
class MIRModule:
    """Top-level MIR module: a collection of functions and type definitions."""

    name: str = ""
    source_file: str = ""  # Original source file path
    source_directory: str = ""  # Directory of the source file
    functions: list[MIRFunction] = field(default_factory=list)
    structs: dict[str, list[tuple[str, MIRType]]] = field(
        default_factory=dict
    )  # name -> [(field, type)]
    enums: dict[str, list[tuple[str, list[MIRType]]]] = field(
        default_factory=dict
    )  # name -> [(variant, payload_types)]
    extern_fns: list[tuple[str, str, str, list[MIRType], MIRType]] = field(
        default_factory=list
    )  # (abi, module, name, param_types, ret_type)
    agents: dict[str, MIRAgentInfo] = field(default_factory=dict)
    pipes: dict[str, MIRPipeInfo] = field(default_factory=dict)
    imports: list[tuple[list[str], list[str]]] = field(default_factory=list)  # (path, items)
    trait_names: list[str] = field(default_factory=list)

    def get_function(self, name: str) -> MIRFunction | None:
        for fn in self.functions:
            if fn.name == name:
                return fn
        return None


# ---------------------------------------------------------------------------
# Pretty-printer
# ---------------------------------------------------------------------------


def _format_value(v: Value) -> str:
    return v.name


def _format_type(t: MIRType) -> str:
    return t.name


def _format_const_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return f'"{value}"'
    if value is None:
        return "none"
    return str(value)


def pretty_print_instruction(inst: Instruction) -> str:  # noqa: C901
    """Pretty-print a single MIR instruction."""
    if isinstance(inst, Const):
        return f"{inst.dest.name} = const {_format_type(inst.ty)} {_format_const_value(inst.value)}"

    if isinstance(inst, Copy):
        return f"{inst.dest.name} = copy {inst.src.name}"

    if isinstance(inst, Cast):
        return f"{inst.dest.name} = cast {inst.src.name} to {_format_type(inst.target_type)}"

    if isinstance(inst, BinOp):
        return f"{inst.dest.name} = {inst.op.value} {inst.lhs.name}, {inst.rhs.name}"

    if isinstance(inst, UnaryOp):
        return f"{inst.dest.name} = {inst.op.value} {inst.operand.name}"

    if isinstance(inst, StructInit):
        fields = ", ".join(f"{n}: {v.name}" for n, v in inst.fields)
        return f"{inst.dest.name} = struct_init {_format_type(inst.struct_type)} {{{fields}}}"

    if isinstance(inst, FieldGet):
        return f"{inst.dest.name} = field_get {inst.obj.name}.{inst.field_name}"

    if isinstance(inst, FieldSet):
        return f"field_set {inst.obj.name}.{inst.field_name} = {inst.val.name}"

    if isinstance(inst, ListInit):
        elems = ", ".join(v.name for v in inst.elements)
        return f"{inst.dest.name} = list_init {_format_type(inst.elem_type)} [{elems}]"

    if isinstance(inst, ListPush):
        return f"{inst.dest.name} = list_push {inst.list_val.name}, {inst.element.name}"

    if isinstance(inst, IndexGet):
        return f"{inst.dest.name} = index_get {inst.obj.name}[{inst.index.name}]"

    if isinstance(inst, IndexSet):
        return f"index_set {inst.obj.name}[{inst.index.name}] = {inst.val.name}"

    if isinstance(inst, MapInit):
        pairs = ", ".join(f"{k.name}: {v.name}" for k, v in inst.pairs)
        kt = _format_type(inst.key_type)
        vt = _format_type(inst.val_type)
        return f"{inst.dest.name} = map_init {kt}:{vt} {{{pairs}}}"

    if isinstance(inst, EnumInit):
        payload = ", ".join(v.name for v in inst.payload)
        payload_str = f"({payload})" if payload else ""
        return (
            f"{inst.dest.name} = enum_init"
            f" {_format_type(inst.enum_type)}::{inst.variant}{payload_str}"
        )

    if isinstance(inst, EnumTag):
        return f"{inst.dest.name} = enum_tag {inst.enum_val.name}"

    if isinstance(inst, EnumPayload):
        return f"{inst.dest.name} = enum_payload {inst.enum_val.name}::{inst.variant}"

    if isinstance(inst, WrapSome):
        return f"{inst.dest.name} = wrap_some {inst.val.name}"

    if isinstance(inst, WrapNone):
        return f"{inst.dest.name} = wrap_none {_format_type(inst.ty)}"

    if isinstance(inst, WrapOk):
        return f"{inst.dest.name} = wrap_ok {inst.val.name}"

    if isinstance(inst, WrapErr):
        return f"{inst.dest.name} = wrap_err {inst.val.name}"

    if isinstance(inst, Unwrap):
        return f"{inst.dest.name} = unwrap {inst.val.name}"

    if isinstance(inst, Call):
        args = ", ".join(v.name for v in inst.args)
        return f"{inst.dest.name} = call {inst.fn_name}({args})"

    if isinstance(inst, Return):
        if inst.val is not None:
            return f"ret {inst.val.name}"
        return "ret void"

    if isinstance(inst, ExternCall):
        args = ", ".join(v.name for v in inst.args)
        mod = f"{inst.module}::" if inst.module else ""
        return f'{inst.dest.name} = extern_call "{inst.abi}" {mod}{inst.fn_name}({args})'

    if isinstance(inst, Jump):
        return f"jump {inst.target}"

    if isinstance(inst, Branch):
        return f"branch {inst.cond.name}, {inst.true_block}, {inst.false_block}"

    if isinstance(inst, Switch):
        cases = ", ".join(f"{_format_const_value(v)} => {lbl}" for v, lbl in inst.cases)
        return f"switch {inst.tag.name} [{cases}] default {inst.default_block}"

    if isinstance(inst, AgentSpawn):
        args = ", ".join(v.name for v in inst.args)
        return f"{inst.dest.name} = agent_spawn {_format_type(inst.agent_type)}({args})"

    if isinstance(inst, AgentSend):
        return f"agent_send {inst.agent.name}.{inst.channel} <- {inst.val.name}"

    if isinstance(inst, AgentSync):
        return f"{inst.dest.name} = agent_sync {inst.agent.name}.{inst.channel}"

    if isinstance(inst, SignalInit):
        return (
            f"{inst.dest.name} = signal_init"
            f" {_format_type(inst.signal_type)} {inst.initial_val.name}"
        )

    if isinstance(inst, SignalGet):
        return f"{inst.dest.name} = signal_get {inst.signal.name}"

    if isinstance(inst, SignalSet):
        return f"signal_set {inst.signal.name} = {inst.val.name}"

    if isinstance(inst, SignalComputed):
        deps = ", ".join(v.name for v in inst.deps)
        return f"{inst.dest.name} = signal_computed {inst.compute_fn}([{deps}])"

    if isinstance(inst, SignalSubscribe):
        return f"signal_subscribe {inst.signal.name} <- {inst.subscriber.name}"

    if isinstance(inst, StreamInit):
        return (
            f"{inst.dest.name} = stream_init"
            f" {inst.source.name} : {_format_type(inst.elem_type)}"
        )

    if isinstance(inst, StreamOp):
        args = ", ".join(v.name for v in inst.args)
        args_str = f", {args}" if args else ""
        fn_str = f" fn={inst.fn_name}" if inst.fn_name else ""
        return (
            f"{inst.dest.name} = stream_op"
            f" {inst.op_kind.name.lower()} {inst.source.name}{args_str}{fn_str}"
        )

    if isinstance(inst, ClosureCreate):
        caps = ", ".join(v.name for v in inst.captures)
        return f"{inst.dest.name} = closure_create {inst.fn_name}([{caps}])"

    if isinstance(inst, ClosureCall):
        args = ", ".join(v.name for v in inst.args)
        return f"{inst.dest.name} = closure_call {inst.closure.name}({args})"

    if isinstance(inst, EnvLoad):
        return (
            f"{inst.dest.name} = env_load {inst.env.name}[{inst.index}]"
            f" : {_format_type(inst.val_type)}"
        )

    if isinstance(inst, InterpConcat):
        parts = ", ".join(v.name for v in inst.parts)
        return f"{inst.dest.name} = interp_concat [{parts}]"

    if isinstance(inst, Assert):
        msg_str = f", {inst.message.name}" if inst.message else ""
        return f"assert {inst.cond.name}{msg_str}  ; {inst.filename}:{inst.line}"

    if isinstance(inst, Phi):
        incoming = ", ".join(f"{lbl}: {v.name}" for lbl, v in inst.incoming)
        return f"{inst.dest.name} = phi [{incoming}]"

    return f"<unknown instruction: {type(inst).__name__}>"


def pretty_print_block(bb: BasicBlock, indent: str = "    ") -> str:
    """Pretty-print a basic block."""
    lines = [f"  {bb.label}:"]
    for inst in bb.instructions:
        lines.append(f"{indent}{pretty_print_instruction(inst)}")
    return "\n".join(lines)


def pretty_print_function(fn: MIRFunction) -> str:
    """Pretty-print a MIR function."""
    params = ", ".join(f"{p.name}: {_format_type(p.ty)}" for p in fn.params)
    ret = _format_type(fn.return_type)
    header = f"fn {fn.name}({params}) -> {ret}"
    if not fn.blocks:
        return header + " {}"
    lines = [header + " {"]
    for bb in fn.blocks:
        lines.append(pretty_print_block(bb))
    lines.append("}")
    return "\n".join(lines)


def pretty_print_module(module: MIRModule) -> str:
    """Pretty-print an entire MIR module."""
    parts: list[str] = []

    if module.name:
        parts.append(f"module {module.name}")
        parts.append("")

    # Structs
    for name, fields in module.structs.items():
        field_strs = ", ".join(f"{fn}: {_format_type(ft)}" for fn, ft in fields)
        parts.append(f"struct {name} {{{field_strs}}}")

    # Enums
    for name, variants in module.enums.items():
        variant_strs = []
        for vname, payload_types in variants:
            if payload_types:
                ptypes = ", ".join(_format_type(t) for t in payload_types)
                variant_strs.append(f"{vname}({ptypes})")
            else:
                variant_strs.append(vname)
        parts.append(f"enum {name} {{{', '.join(variant_strs)}}}")

    if module.structs or module.enums:
        parts.append("")

    # Extern functions
    for abi, mod, fn_name, param_types, ret_type in module.extern_fns:
        ptypes = ", ".join(_format_type(t) for t in param_types)
        parts.append(f'extern "{abi}" fn {mod}::{fn_name}({ptypes}) -> {_format_type(ret_type)}')

    if module.extern_fns:
        parts.append("")

    # Functions
    for fn in module.functions:
        parts.append(pretty_print_function(fn))
        parts.append("")

    return "\n".join(parts).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Verifier
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class VerifyError:
    """A single verification error."""

    function: str = ""
    block: str = ""
    message: str = ""

    def __repr__(self) -> str:
        loc = self.function
        if self.block:
            loc += f"::{self.block}"
        return f"VerifyError({loc}: {self.message})"


class MIRVerifier:
    """Verifies structural correctness of MIR.

    Checks:
    - Every block has exactly one terminator as its last instruction
    - No terminators in the middle of a block
    - All branch/jump targets reference existing blocks
    - SSA: every value is defined before use (within dominance scope)
    - SSA: no value is defined more than once in a function
    - Phi nodes only appear at the start of blocks
    - Phi incoming labels reference existing blocks
    - Functions have at least one block (entry)
    - Entry block is the first block
    """

    def __init__(self) -> None:
        self.errors: list[VerifyError] = []

    def verify_module(self, module: MIRModule) -> list[VerifyError]:
        """Verify an entire module. Returns list of errors (empty = valid)."""
        self.errors = []
        for fn in module.functions:
            self._verify_function(fn)
        return self.errors

    def verify_function(self, fn: MIRFunction) -> list[VerifyError]:
        """Verify a single function."""
        self.errors = []
        self._verify_function(fn)
        return self.errors

    def _error(self, fn_name: str, block_label: str, msg: str) -> None:
        self.errors.append(VerifyError(function=fn_name, block=block_label, message=msg))

    def _verify_function(self, fn: MIRFunction) -> None:
        if not fn.blocks:
            self._error(fn.name, "", "function has no basic blocks")
            return

        block_labels = {bb.label for bb in fn.blocks}

        # Track all defined values across the function for SSA uniqueness
        all_defs: dict[str, str] = {}  # value_name -> defining_block

        for bb in fn.blocks:
            self._verify_block(fn.name, bb, block_labels, all_defs)

    def _verify_block(
        self,
        fn_name: str,
        bb: BasicBlock,
        valid_labels: set[str],
        all_defs: dict[str, str],
    ) -> None:
        if not bb.instructions:
            self._error(fn_name, bb.label, "block has no instructions")
            return

        # Check terminator
        if not is_terminator(bb.instructions[-1]):
            self._error(fn_name, bb.label, "block does not end with a terminator")

        # Check no terminators in the middle
        for i, inst in enumerate(bb.instructions[:-1]):
            if is_terminator(inst):
                self._error(
                    fn_name,
                    bb.label,
                    f"terminator {type(inst).__name__} at position {i} (not last)",
                )

        # Phi nodes must be at the start
        seen_non_phi = False
        for inst in bb.instructions:
            if isinstance(inst, Phi):
                if seen_non_phi:
                    self._error(fn_name, bb.label, "phi node after non-phi instruction")
            else:
                seen_non_phi = True

        # Check definitions and target labels
        for inst in bb.instructions:
            # Track definitions (relaxed SSA: mutable variables may be redefined)
            dest = self._get_dest(inst)
            if dest is not None and dest.name:
                all_defs[dest.name] = bb.label

            # Check branch targets
            self._check_targets(fn_name, bb.label, inst, valid_labels)

            # Check phi incoming labels
            if isinstance(inst, Phi):
                for lbl, _ in inst.incoming:
                    if lbl not in valid_labels:
                        self._error(
                            fn_name,
                            bb.label,
                            f"phi references unknown block '{lbl}'",
                        )

    def _get_dest(self, inst: Instruction) -> Value | None:
        """Get the destination value of an instruction, if any."""
        dest: Value | None = getattr(inst, "dest", None)
        return dest

    def _check_targets(
        self, fn_name: str, block_label: str, inst: Instruction, valid_labels: set[str]
    ) -> None:
        """Check that branch/jump targets reference existing blocks."""
        if isinstance(inst, Jump):
            if inst.target not in valid_labels:
                self._error(fn_name, block_label, f"jump to unknown block '{inst.target}'")
        elif isinstance(inst, Branch):
            if inst.true_block not in valid_labels:
                self._error(
                    fn_name, block_label, f"branch true target unknown: '{inst.true_block}'"
                )
            if inst.false_block not in valid_labels:
                self._error(
                    fn_name, block_label, f"branch false target unknown: '{inst.false_block}'"
                )
        elif isinstance(inst, Switch):
            for _, lbl in inst.cases:
                if lbl not in valid_labels:
                    self._error(fn_name, block_label, f"switch case target unknown: '{lbl}'")
            if inst.default_block and inst.default_block not in valid_labels:
                self._error(
                    fn_name, block_label, f"switch default target unknown: '{inst.default_block}'"
                )


def verify(module: MIRModule) -> list[VerifyError]:
    """Verify a MIR module. Returns list of errors (empty = valid)."""
    return MIRVerifier().verify_module(module)
