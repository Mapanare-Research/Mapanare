"""LLVM IR emitter that consumes MIR (not AST).

Translates MIR basic blocks, instructions, and phi nodes into LLVM IR
via llvmlite. Because LLVM IR natively uses basic blocks and SSA form,
the mapping is nearly 1:1 with MIR.

Usage:
    from mapanare.emit_llvm_mir import LLVMMIREmitter
    emitter = LLVMMIREmitter(module_name="test")
    llvm_module = emitter.emit(mir_module)
    llvm_ir_string = str(llvm_module)
"""

from __future__ import annotations

from typing import Any

try:
    from llvmlite import ir

    _HAS_LLVMLITE = True
except ImportError:
    _HAS_LLVMLITE = False
    ir = None  # type: ignore[assignment,unused-ignore]

from mapanare.mir import (
    AgentSend,
    AgentSpawn,
    AgentSync,
    Assert,
    BinOp,
    BinOpKind,
    Branch,
    Call,
    Cast,
    ClosureCall,
    ClosureCreate,
    Const,
    Copy,
    EnumInit,
    EnumPayload,
    EnumTag,
    EnvLoad,
    ExternCall,
    FieldGet,
    FieldSet,
    IndexGet,
    IndexSet,
    Instruction,
    InterpConcat,
    Jump,
    ListInit,
    ListPush,
    MapInit,
    MIRFunction,
    MIRModule,
    MIRPipeInfo,
    MIRType,
    Phi,
    Return,
    SignalComputed,
    SignalGet,
    SignalInit,
    SignalSet,
    SignalSubscribe,
    SourceSpan,
    StreamInit,
    StreamOp,
    StreamOpKind,
    StructInit,
    Switch,
    UnaryOp,
    UnaryOpKind,
    Unwrap,
    Value,
    WrapErr,
    WrapNone,
    WrapOk,
    WrapSome,
)
from mapanare.types import TypeKind


def _require_llvmlite() -> None:
    """Raise a clear error if llvmlite is not installed."""
    if not _HAS_LLVMLITE:
        raise ImportError(
            "llvmlite is required for the LLVM MIR emitter. "
            "Install it with: pip install llvmlite"
        )


# ---------------------------------------------------------------------------
# LLVM type constants (created lazily to avoid errors when llvmlite absent)
# ---------------------------------------------------------------------------

_llvm_types_initialized = False
LLVM_INT: Any = None
LLVM_FLOAT: Any = None
LLVM_BOOL: Any = None
LLVM_CHAR: Any = None
LLVM_VOID: Any = None
LLVM_PTR: Any = None
LLVM_I32: Any = None
LLVM_STRING: Any = None
LLVM_LIST: Any = None
LLVM_MAP: Any = None
LLVM_CLOSURE: Any = None  # {i8* fn_ptr, i8* env_ptr}


def _init_llvm_types() -> None:
    """Initialize LLVM type constants. Must be called after confirming llvmlite exists."""
    global _llvm_types_initialized
    global LLVM_INT, LLVM_FLOAT, LLVM_BOOL, LLVM_CHAR, LLVM_VOID
    global LLVM_PTR, LLVM_I32, LLVM_STRING, LLVM_LIST, LLVM_MAP, LLVM_CLOSURE

    if _llvm_types_initialized:
        return

    LLVM_INT = ir.IntType(64)
    LLVM_FLOAT = ir.DoubleType()
    LLVM_BOOL = ir.IntType(1)
    LLVM_CHAR = ir.IntType(8)
    LLVM_VOID = ir.VoidType()
    LLVM_PTR = ir.IntType(8).as_pointer()
    LLVM_I32 = ir.IntType(32)
    LLVM_STRING = ir.LiteralStructType([ir.IntType(8).as_pointer(), LLVM_INT])
    LLVM_LIST = ir.LiteralStructType([ir.IntType(8).as_pointer(), LLVM_INT, LLVM_INT, LLVM_INT])
    LLVM_MAP = ir.IntType(8).as_pointer()  # Opaque pointer to C MnMap struct
    LLVM_CLOSURE = ir.LiteralStructType(
        [ir.IntType(8).as_pointer(), ir.IntType(8).as_pointer()]
    )  # {fn_ptr, env_ptr}

    _llvm_types_initialized = True


def _coerce_arg(builder: Any, arg: Any, expected_ty: Any, name: str) -> Any:
    """Coerce a single LLVM arg to match expected type (cross-module fix)."""
    if arg.type == expected_ty:
        return arg
    actual = arg.type
    # Pointer → integer
    if isinstance(actual, ir.PointerType) and isinstance(expected_ty, ir.IntType):
        return builder.ptrtoint(arg, expected_ty, name=name)
    # Integer → pointer
    if isinstance(actual, ir.IntType) and isinstance(expected_ty, ir.PointerType):
        return builder.inttoptr(arg, expected_ty, name=name)
    # Pointer → pointer
    if isinstance(actual, ir.PointerType) and isinstance(expected_ty, ir.PointerType):
        return builder.bitcast(arg, expected_ty, name=name)
    # Pointer → struct: bitcast ptr to struct*, load
    if isinstance(actual, ir.PointerType) and isinstance(expected_ty, ir.LiteralStructType):
        typed_ptr = builder.bitcast(arg, expected_ty.as_pointer(), name=f"{name}.ptr")
        return builder.load(typed_ptr, name=name)
    # Array → pointer: alloca, store, GEP
    if isinstance(actual, ir.ArrayType) and isinstance(expected_ty, ir.PointerType):
        tmp = builder.alloca(actual, name=f"{name}.tmp")
        builder.store(arg, tmp)
        zero = ir.Constant(ir.IntType(64), 0)
        return builder.gep(tmp, [zero, zero], inbounds=True, name=name)
    # Struct → pointer: alloca, store, bitcast
    if isinstance(actual, ir.LiteralStructType) and isinstance(expected_ty, ir.PointerType):
        tmp = builder.alloca(actual, name=f"{name}.tmp")
        builder.store(arg, tmp)
        return builder.bitcast(tmp, expected_ty, name=name)
    # Struct → struct: reinterpret via memory
    if isinstance(actual, ir.LiteralStructType) and isinstance(expected_ty, ir.LiteralStructType):
        actual_size = _approx_type_size(actual)
        expected_size = _approx_type_size(expected_ty)
        if actual_size >= expected_size:
            # Source >= dest: safe to reinterpret directly
            tmp = builder.alloca(actual, name=f"{name}.tmp")
            builder.store(arg, tmp)
            typed_ptr = builder.bitcast(tmp, expected_ty.as_pointer(), name=f"{name}.ptr")
            return builder.load(typed_ptr, name=name)
        else:
            # Source < dest (e.g. None {i1, i8*} → Option<BigStruct>):
            # allocate the larger type, zero it, overlay the source
            tmp = builder.alloca(expected_ty, name=f"{name}.tmp")
            builder.store(ir.Constant(expected_ty, None), tmp)
            src_ptr = builder.bitcast(tmp, actual.as_pointer(), name=f"{name}.src")
            builder.store(arg, src_ptr)
            return builder.load(tmp, name=name)
    # Integer → integer (size mismatch)
    if isinstance(actual, ir.IntType) and isinstance(expected_ty, ir.IntType):
        if actual.width < expected_ty.width:
            return builder.zext(arg, expected_ty, name=name)
        else:
            return builder.trunc(arg, expected_ty, name=name)
    # Integer/scalar → struct/array: store to memory, reinterpret
    if isinstance(expected_ty, (ir.LiteralStructType, ir.ArrayType)):
        if isinstance(actual, ir.VoidType):
            return ir.Constant(expected_ty, ir.Undefined)
        tmp = builder.alloca(expected_ty, name=f"{name}.tmp")
        src_ptr_ty = (
            actual.as_pointer()
            if hasattr(actual, "as_pointer") and not isinstance(actual, ir.VoidType)
            else ir.IntType(8).as_pointer()
        )
        raw_ptr = builder.bitcast(tmp, src_ptr_ty, name=f"{name}.rptr")
        builder.store(arg, raw_ptr)
        return builder.load(tmp, name=name)
    # Struct/array → integer: store to memory, load as int
    if isinstance(actual, (ir.LiteralStructType, ir.ArrayType)) and isinstance(
        expected_ty, ir.IntType
    ):
        tmp = builder.alloca(actual, name=f"{name}.tmp")
        builder.store(arg, tmp)
        int_ptr = builder.bitcast(tmp, expected_ty.as_pointer(), name=f"{name}.iptr")
        return builder.load(int_ptr, name=name)
    # Fallback: memory reinterpretation
    try:
        return builder.bitcast(arg, expected_ty, name=name)
    except Exception:
        tmp = builder.alloca(actual, name=f"{name}.tmp")
        builder.store(arg, tmp)
        cast_ptr = builder.bitcast(tmp, expected_ty.as_pointer(), name=f"{name}.cptr")
        return builder.load(cast_ptr, name=name)


def _coerce_args(builder: Any, args: list[Any], expected_types: list[Any], name: str) -> list[Any]:
    """Coerce LLVM args to match expected types (cross-module fix)."""
    return [
        _coerce_arg(builder, arg, exp_ty, f"{name}.c{i}")
        for i, (arg, exp_ty) in enumerate(zip(args, expected_types))
    ]


def _option_llvm_type(inner: Any) -> Any:
    """Option<T> -> {i1, T}."""
    return ir.LiteralStructType([LLVM_BOOL, inner])


def _result_llvm_type(ok_ty: Any, err_ty: Any) -> Any:
    """Result<T, E> -> {i1, {T, E}}."""
    return ir.LiteralStructType([LLVM_BOOL, ir.LiteralStructType([ok_ty, err_ty])])


def _tensor_llvm_type(elem_ty: Any) -> Any:
    """Tensor<T> -> {T*, i64, i64*, i64}."""
    return ir.LiteralStructType([elem_ty.as_pointer(), LLVM_INT, LLVM_INT.as_pointer(), LLVM_INT])


# ---------------------------------------------------------------------------
# LLVMMIREmitter
# ---------------------------------------------------------------------------


class LLVMMIREmitter:
    """Emit LLVM IR from a MIR module.

    The emitter translates MIR basic blocks, instructions, and phi nodes
    into LLVM IR. Because LLVM IR is SSA with basic blocks, the mapping
    is nearly 1:1.
    """

    def __init__(
        self,
        module_name: str = "mapanare_module",
        target_triple: str | None = None,
        data_layout: str | None = None,
        debug: bool = False,
    ) -> None:
        _require_llvmlite()
        _init_llvm_types()

        self.module = ir.Module(name=module_name)
        if target_triple is not None:
            self.module.triple = target_triple
        if data_layout is not None:
            self.module.data_layout = data_layout

        # Struct name -> LLVM named struct type
        self._struct_types: dict[str, Any] = {}
        # Struct name -> ordered field names
        self._struct_fields: dict[str, list[str]] = {}
        # Enum name -> (LLVM type, variant->tag mapping, variant->payload types)
        self._enum_types: dict[str, tuple[Any, dict[str, int], dict[str, list[MIRType]]]] = {}
        # Function name -> LLVM function
        self._functions: dict[str, Any] = {}
        # Runtime function cache
        self._runtime_fns: dict[str, Any] = {}
        # Global string counter
        self._str_counter: int = 0
        # Printf format string cache
        self._fmt_strings: dict[str, Any] = {}

        # DWARF debug info state
        self._debug = debug
        self._di_file: Any = None  # DIFile
        self._di_compile_unit: Any = None  # DICompileUnit
        self._di_subprograms: dict[str, Any] = {}  # fn name -> DISubprogram
        self._di_type_cache: dict[str, Any] = {}  # type key -> DIType

        # Per-function state for alloca-based dominance fix
        self._fn_allocas: dict[str, Any] = {}
        self._current_builder: Any = None
        self._current_block_label: str = ""
        self._value_blocks: dict[str, str] = {}  # value name -> defining block label
        # Track root list allocas for push write-back chains
        self._list_roots: dict[str, str] = {}  # value name -> root value name
        # Track auto-boxed fields in recursive enums
        # enum_name -> set of (variant_name, field_index) that are heap-allocated pointers
        self._boxed_enum_fields: dict[str, set[tuple[str, int]]] = {}
        # Track auto-boxed fields in recursive structs
        # struct_name -> set of field indices that are heap-allocated pointers
        self._boxed_struct_fields: dict[str, set[int]] = {}
        # struct_name -> {field_idx: MIRType} for boxed fields (for unbox resolution)
        self._boxed_struct_mir_fields: dict[str, dict[int, MIRType]] = {}

    # -----------------------------------------------------------------------
    # Public entry point
    # -----------------------------------------------------------------------

    def emit(self, mir_module: MIRModule) -> Any:
        """Emit LLVM IR from a MIR module. Returns the llvmlite ir.Module."""
        # 0. Initialize DWARF debug info if enabled
        if self._debug:
            self._init_debug_info(mir_module)

        # 1. Register types with iterative convergence.
        #    Structs and enums may cross-reference and even mutually recurse
        #    (e.g. Expr → ElseClause → Expr).  Direct self-recursion is handled
        #    by auto-boxing in _register_enum.  Mutual recursion is detected by
        #    iterating until sizes stabilize; any types whose sizes keep growing
        #    have their enum-typed fields auto-boxed on the next iteration.
        for _pass in range(10):
            sizes_before = {n: _approx_type_size(self._enum_types[n][0]) for n in self._enum_types}
            for name, fields in mir_module.structs.items():
                self._register_struct(name, fields)
            for name, variants in mir_module.enums.items():
                self._register_enum(name, variants)
            sizes_after = {n: _approx_type_size(self._enum_types[n][0]) for n in self._enum_types}
            if sizes_before == sizes_after:
                break
            # Skip mutual-recursion detection on the first pass (all types are
            # "new" so all sizes change — that's not mutual recursion, just
            # initial registration).  Direct self-recursion is already handled
            # by _is_self_ref_field inside _register_enum.
            if not sizes_before:
                continue
            # Types whose sizes changed between two full passes are involved
            # in mutual recursion.  Box their enum-typed fields to break the
            # infinite growth cycle.
            changed = {n for n in sizes_after if sizes_after[n] != sizes_before.get(n)}
            if changed:
                self._box_mutual_recursion(changed, mir_module.enums)

        # 3. Declare extern functions
        for abi, mod, fn_name, param_types, ret_type in mir_module.extern_fns:
            self._declare_extern(abi, mod, fn_name, param_types, ret_type)

        # 4. Forward-declare all MIR functions
        for mir_fn in mir_module.functions:
            self._forward_declare_function(mir_fn)

        # 5. Emit function bodies
        for mir_fn in mir_module.functions:
            self._emit_function(mir_fn)

        # 5b. Emit pipe definitions as pipeline functions
        for pipe_name, pipe_info in mir_module.pipes.items():
            self._emit_pipe_def(pipe_name, pipe_info)

        # 6. Finalize debug info metadata
        if self._debug:
            self._finalize_debug_info()

        return self.module

    # -----------------------------------------------------------------------
    # DWARF debug info
    # -----------------------------------------------------------------------

    def _init_debug_info(self, mir_module: MIRModule) -> None:
        """Initialize DWARF compile unit and file metadata."""
        source_file = mir_module.source_file or (mir_module.name + ".mn")
        source_dir = mir_module.source_directory or "."

        self._di_file = self.module.add_debug_info(
            "DIFile",
            {"filename": source_file, "directory": source_dir},
        )
        self._di_compile_unit = self.module.add_debug_info(
            "DICompileUnit",
            {
                "language": ir.DIToken("DW_LANG_C"),
                "file": self._di_file,
                "producer": "mapanare 0.7.0",
                "isOptimized": False,
                "runtimeVersion": 0,
                "emissionKind": ir.DIToken("FullDebug"),
            },
            is_distinct=True,
        )

    def _finalize_debug_info(self) -> None:
        """Add named metadata entries for DWARF."""
        if self._di_compile_unit is None:
            return
        self.module.add_named_metadata("llvm.dbg.cu", self._di_compile_unit)
        # Debug info version flag (required by LLVM)
        di_version_flag = self.module.add_metadata(
            [ir.IntType(32)(2), self.module.add_metadata(["Debug Info Version", ir.IntType(32)(3)])]
        )
        self.module.add_named_metadata("llvm.module.flags", di_version_flag)
        # DWARF version flag
        dwarf_version_flag = self.module.add_metadata(
            [ir.IntType(32)(2), self.module.add_metadata(["Dwarf Version", ir.IntType(32)(4)])]
        )
        self.module.add_named_metadata("llvm.module.flags", dwarf_version_flag)

    def _get_di_type(self, mir_type: MIRType) -> Any:
        """Get or create a DWARF type descriptor for a MIR type."""
        kind = mir_type.kind
        key = mir_type.name

        if key in self._di_type_cache:
            return self._di_type_cache[key]

        di_type: Any = None

        if kind == TypeKind.INT:
            di_type = self.module.add_debug_info(
                "DIBasicType",
                {"name": "Int", "size": 64, "encoding": ir.DIToken("DW_ATE_signed")},
            )
        elif kind == TypeKind.FLOAT:
            di_type = self.module.add_debug_info(
                "DIBasicType",
                {"name": "Float", "size": 64, "encoding": ir.DIToken("DW_ATE_float")},
            )
        elif kind == TypeKind.BOOL:
            di_type = self.module.add_debug_info(
                "DIBasicType",
                {"name": "Bool", "size": 1, "encoding": ir.DIToken("DW_ATE_boolean")},
            )
        elif kind == TypeKind.CHAR:
            di_type = self.module.add_debug_info(
                "DIBasicType",
                {"name": "Char", "size": 8, "encoding": ir.DIToken("DW_ATE_unsigned_char")},
            )
        elif kind == TypeKind.STRING:
            di_type = self.module.add_debug_info(
                "DICompositeType",
                {
                    "tag": ir.DIToken("DW_TAG_structure_type"),
                    "name": "String",
                    "size": 128,
                    "file": self._di_file,
                    "elements": self.module.add_metadata([]),
                },
            )
        elif kind == TypeKind.STRUCT:
            name = mir_type.type_info.name
            # Build member list from registered struct fields
            members: list[Any] = []
            if name in self._struct_fields:
                offset = 0
                for field_name in self._struct_fields[name]:
                    member = self.module.add_debug_info(
                        "DIDerivedType",
                        {
                            "tag": ir.DIToken("DW_TAG_member"),
                            "name": field_name,
                            "file": self._di_file,
                            "size": 64,
                            "offset": offset,
                        },
                    )
                    members.append(member)
                    offset += 64
            total_size = len(members) * 64 if members else 0
            di_type = self.module.add_debug_info(
                "DICompositeType",
                {
                    "tag": ir.DIToken("DW_TAG_structure_type"),
                    "name": name,
                    "file": self._di_file,
                    "size": total_size,
                    "elements": self.module.add_metadata(members),
                },
            )
        elif kind == TypeKind.VOID:
            # Void has no debug type
            self._di_type_cache[key] = None
            return None
        else:
            # Opaque pointer type for complex/unsupported types
            di_type = self.module.add_debug_info(
                "DIBasicType",
                {"name": key or "opaque", "size": 64, "encoding": ir.DIToken("DW_ATE_address")},
            )

        self._di_type_cache[key] = di_type
        return di_type

    def _get_di_subroutine_type(self, mir_fn: MIRFunction) -> Any:
        """Create a DISubroutineType for a function."""
        types: list[Any] = []
        # Return type first (DWARF convention)
        ret_di = self._get_di_type(mir_fn.return_type)
        types.append(ret_di)
        # Then parameter types
        for p in mir_fn.params:
            types.append(self._get_di_type(p.ty))
        return self.module.add_debug_info(
            "DISubroutineType",
            {"types": self.module.add_metadata(types)},
        )

    def _create_di_subprogram(self, mir_fn: MIRFunction) -> Any:
        """Create a DISubprogram for a MIR function."""
        if self._di_compile_unit is None:
            return None

        di_func_type = self._get_di_subroutine_type(mir_fn)
        line = mir_fn.source_line if mir_fn.source_line > 0 else 1

        di_sp = self.module.add_debug_info(
            "DISubprogram",
            {
                "name": mir_fn.name,
                "file": self._di_file,
                "line": line,
                "type": di_func_type,
                "isLocal": not mir_fn.is_public,
                "isDefinition": True,
                "scopeLine": line,
                "unit": self._di_compile_unit,
            },
            is_distinct=True,
        )
        self._di_subprograms[mir_fn.name] = di_sp
        return di_sp

    def _attach_debug_location(self, llvm_inst: Any, span: SourceSpan, fn_name: str) -> None:
        """Attach a !dbg location to an LLVM instruction."""
        di_sp = self._di_subprograms.get(fn_name)
        if di_sp is None:
            return
        di_loc = self.module.add_debug_info(
            "DILocation",
            {
                "line": span.line,
                "column": span.column,
                "scope": di_sp,
            },
        )
        llvm_inst.set_metadata("dbg", di_loc)

    def _emit_di_local_variable(
        self, builder: Any, var_name: str, mir_type: MIRType, line: int, fn_name: str
    ) -> None:
        """Emit debug info for a local variable."""
        di_sp = self._di_subprograms.get(fn_name)
        if di_sp is None:
            return
        di_type = self._get_di_type(mir_type)
        if di_type is None:
            return
        # Create DILocalVariable metadata (stored but not attached to alloca
        # since we use SSA values — the metadata is enough for DWARF)
        self.module.add_debug_info(
            "DILocalVariable",
            {
                "name": var_name,
                "scope": di_sp,
                "file": self._di_file,
                "line": line,
                "type": di_type,
            },
        )

    # -----------------------------------------------------------------------
    # Type resolution: MIRType -> LLVM type
    # -----------------------------------------------------------------------

    def _resolve_mir_type(self, mir_type: MIRType) -> Any:
        """Map a MIR type to an LLVM IR type."""
        kind = mir_type.kind
        if kind == TypeKind.INT:
            return LLVM_INT
        if kind == TypeKind.FLOAT:
            return LLVM_FLOAT
        if kind == TypeKind.BOOL:
            return LLVM_BOOL
        if kind == TypeKind.CHAR:
            return LLVM_CHAR
        if kind == TypeKind.STRING:
            return LLVM_STRING
        if kind == TypeKind.VOID:
            return LLVM_VOID
        if kind == TypeKind.LIST:
            return LLVM_LIST
        if kind == TypeKind.MAP:
            return LLVM_MAP
        if kind == TypeKind.STRUCT:
            name = mir_type.type_info.name
            if name in self._struct_types:
                return self._struct_types[name]
            # Cross-module: try suffix match (e.g. "Span" → "parser__Span")
            for sname, stype in self._struct_types.items():
                if sname.endswith("__" + name):
                    return stype
            # Lowerer may tag user-defined enums as STRUCT (kind_from_name
            # returns UNKNOWN for non-builtin names and _resolve_type_expr
            # defaults to STRUCT).  Fall through to enum lookup.
            if name in self._enum_types:
                return self._enum_types[name][0]
            for ename, einfo in self._enum_types.items():
                if ename.endswith("__" + name):
                    return einfo[0]
            return LLVM_PTR
        if kind == TypeKind.ENUM:
            name = mir_type.type_info.name
            if name in self._enum_types:
                return self._enum_types[name][0]
            # Cross-module: try suffix match (e.g. "TypeExpr" → "ast__TypeExpr")
            for ename, einfo in self._enum_types.items():
                if ename.endswith("__" + name):
                    return einfo[0]
            return LLVM_PTR
        if kind == TypeKind.OPTION:
            args = mir_type.type_info.args
            if args:
                inner = self._resolve_type_info_arg(args[0])
                return _option_llvm_type(inner)
            return _option_llvm_type(LLVM_PTR)
        if kind == TypeKind.RESULT:
            args = mir_type.type_info.args
            if len(args) >= 2:
                ok_ty = self._resolve_type_info_arg(args[0])
                err_ty = self._resolve_type_info_arg(args[1])
                return _result_llvm_type(ok_ty, err_ty)
            return _result_llvm_type(LLVM_PTR, LLVM_PTR)
        if kind == TypeKind.TENSOR:
            args = mir_type.type_info.args
            if args:
                elem = self._resolve_type_info_arg(args[0])
                return _tensor_llvm_type(elem)
            return _tensor_llvm_type(LLVM_FLOAT)
        if kind in (TypeKind.AGENT, TypeKind.SIGNAL, TypeKind.STREAM, TypeKind.CHANNEL):
            return LLVM_PTR
        if kind == TypeKind.FN:
            return LLVM_PTR
        # Fallback for UNKNOWN, TYPE_VAR, etc.
        # Check struct and enum registries before giving up — kind_from_name
        # returns UNKNOWN for user-defined types (e.g. TypeExpr, Pattern).
        name = mir_type.type_info.name
        if name:
            if name in self._struct_types:
                return self._struct_types[name]
            for sname, stype in self._struct_types.items():
                if sname.endswith("__" + name):
                    return stype
            if name in self._enum_types:
                return self._enum_types[name][0]
            for ename, einfo in self._enum_types.items():
                if ename.endswith("__" + name):
                    return einfo[0]
        return LLVM_PTR

    def _resolve_type_info_arg(self, ti: Any) -> Any:
        """Resolve a TypeInfo (from type args) to LLVM type."""
        return self._resolve_mir_type(MIRType(type_info=ti))

    def _llvm_type_size(self, ty: Any) -> int:
        """Approximate byte size of an LLVM type."""
        if isinstance(ty, ir.IntType):
            return int(ty.width) // 8
        if isinstance(ty, ir.DoubleType):
            return 8
        if isinstance(ty, ir.PointerType):
            return 8
        if isinstance(ty, ir.LiteralStructType):
            return sum(self._llvm_type_size(e) for e in ty.elements)
        return 8

    def _resolve_enum_variant_tag(self, variant_name: str, enum_hint: str = "") -> int:
        """Look up the integer tag for an enum variant name.

        Prefers the enum matching enum_hint (exact or suffix match).
        """
        # Option/Result use special {i1, T} layout where Some/Ok=1, None/Err=0
        if variant_name == "Some" or variant_name == "Ok":
            return 1
        if variant_name == "None" or variant_name == "Err":
            return 0
        # Try scoped lookup first
        if enum_hint:
            for ename, (_, tag_map, _) in self._enum_types.items():
                if (
                    ename == enum_hint or ename.endswith("__" + enum_hint)
                ) and variant_name in tag_map:
                    return tag_map[variant_name]
        # Fallback: global search
        for _ename, (_, tag_map, _) in self._enum_types.items():
            if variant_name in tag_map:
                return tag_map[variant_name]
        return 0

    def _resolve_enum_type_from_value(self, mir_val: Value) -> Any:
        """Resolve the LLVM struct type for an enum value from its MIR type info.

        The lowerer may tag user-defined enums as STRUCT (because
        kind_from_name returns UNKNOWN).  This helper checks both the
        ENUM and STRUCT type kinds against the registered enum types.
        """
        name = mir_val.ty.type_info.name
        if name in self._enum_types:
            return self._enum_types[name][0]
        # Suffix match for cross-module enums (e.g., "Definition" → "ast__Definition")
        if name:
            for ename, einfo in self._enum_types.items():
                if ename.endswith("__" + name):
                    return einfo[0]
        return None

    def _map_key_type_tag(self, mir_type: MIRType) -> int:
        """Return MN_MAP_KEY_* tag for a MIR key type."""
        if mir_type.kind == TypeKind.STRING:
            return 1  # MN_MAP_KEY_STR
        if mir_type.kind == TypeKind.FLOAT:
            return 2  # MN_MAP_KEY_FLOAT
        return 0  # MN_MAP_KEY_INT

    # -----------------------------------------------------------------------
    # Struct / Enum registration
    # -----------------------------------------------------------------------

    def _register_struct(self, name: str, fields: list[tuple[str, MIRType]]) -> None:
        """Register a named struct type.

        Self-referential fields (e.g. Option<TypeInfo> inside TypeInfo) are
        stored as opaque pointers (boxed) to prevent infinite type growth.
        """
        field_types: list[Any] = []
        boxed_indices: set[int] = set()
        for i, (_, ft) in enumerate(fields):
            if self._is_self_ref_field(name, ft):
                # Box self-referential field: use LLVM_PTR
                field_types.append(LLVM_PTR)
                boxed_indices.add(i)
            else:
                field_types.append(self._resolve_mir_type(ft))
        field_names = [fn for fn, _ in fields]
        llvm_ty = ir.LiteralStructType(field_types)
        self._struct_types[name] = llvm_ty
        self._struct_fields[name] = field_names
        if boxed_indices:
            self._boxed_struct_fields[name] = boxed_indices
            # Store the MIR field types so we can resolve them during unboxing
            self._boxed_struct_mir_fields[name] = {
                i: ft for i, (_, ft) in enumerate(fields) if i in boxed_indices
            }

    def _resolve_field_type_for_unbox(self, struct_name: str, field_name: str) -> Any:
        """Resolve the actual LLVM type for a boxed struct field (for unboxing)."""
        mir_fields = self._boxed_struct_mir_fields.get(struct_name, {})
        field_names = self._struct_fields.get(struct_name, [])
        if field_name in field_names:
            idx = field_names.index(field_name)
            if idx in mir_fields:
                return self._resolve_mir_type(mir_fields[idx])
        return None

    def _is_self_ref_field(self, enum_name: str, mir_type: MIRType) -> bool:
        """Check if a MIR type refers (directly or via Option/Result) to the enum being registered.

        Recursive enum fields must be heap-allocated (boxed) to avoid infinite type sizes.
        """
        base_name = enum_name.rsplit("__", 1)[-1]

        def matches(type_name: str) -> bool:
            if not type_name:
                return False
            return (
                type_name == enum_name
                or type_name == base_name
                or (len(type_name) < len(enum_name) and enum_name.endswith("__" + type_name))
            )

        ti = mir_type.type_info
        if not ti:
            return False

        # Direct: field type is the same enum
        if mir_type.kind in (TypeKind.STRUCT, TypeKind.ENUM, TypeKind.UNKNOWN):
            if matches(ti.name):
                return True

        # Option<SameEnum>
        if mir_type.kind == TypeKind.OPTION and ti.args:
            inner = ti.args[0]
            if hasattr(inner, "name") and matches(inner.name):
                return True

        # Result<SameEnum, _> or Result<_, SameEnum>
        if mir_type.kind == TypeKind.RESULT and ti.args:
            for arg in ti.args:
                if hasattr(arg, "name") and matches(arg.name):
                    return True

        return False

    def _field_refs_enum_in_set(self, mir_type: MIRType, enum_set: set[str]) -> bool:
        """Check if a MIR type references any enum in the given set (directly or via Option/Result)."""
        ti = mir_type.type_info
        if not ti:
            return False

        name = ti.name or ""

        def in_set(type_name: str) -> bool:
            for ename in enum_set:
                base = ename.rsplit("__", 1)[-1]
                if type_name == ename or type_name == base:
                    return True
            return False

        # Direct enum reference
        if mir_type.kind in (TypeKind.STRUCT, TypeKind.ENUM, TypeKind.UNKNOWN):
            if in_set(name):
                return True

        # Option<Enum>
        if mir_type.kind == TypeKind.OPTION and ti.args:
            inner_name = ti.args[0].name if hasattr(ti.args[0], "name") and ti.args[0] else ""
            if in_set(inner_name):
                return True

        # Result<Enum, _>
        if mir_type.kind == TypeKind.RESULT and ti.args:
            for arg in ti.args:
                arg_name = arg.name if hasattr(arg, "name") and arg else ""
                if in_set(arg_name):
                    return True

        return False

    def _box_mutual_recursion(
        self, changed: set[str], enums: dict[str, list[tuple[str, list[MIRType]]]]
    ) -> None:
        """Box enum-type fields in variants that reference any type in 'changed' set.

        Called when iterative type registration detects sizes that keep growing,
        indicating mutual recursion (e.g. Expr → ElseClause → Expr).
        """
        for ename, variants in enums.items():
            for vname, payload_types in variants:
                for j, pt in enumerate(payload_types):
                    if self._field_refs_enum_in_set(pt, changed):
                        self._boxed_enum_fields.setdefault(ename, set()).add((vname, j))

    def _register_enum(self, name: str, variants: list[tuple[str, list[MIRType]]]) -> None:
        """Register an enum as a tagged union.

        Layout: {i32 tag, [max_payload_bytes x i8]}
        The tag is i32; the payload is sized to the largest variant.

        Recursive enums (where a variant field references the same enum) use
        auto-boxing: self-referential fields are stored as heap-allocated
        pointers (8 bytes) instead of inline values.  This prevents infinite
        type sizes for types like ``Expr`` that contain ``Binary(Expr, String, Expr)``.
        """
        variant_tags: dict[str, int] = {}
        variant_payloads: dict[str, list[MIRType]] = {}
        boxed_fields: set[tuple[str, int]] = set()

        max_payload_size = 0
        for i, (vname, payload_types) in enumerate(variants):
            variant_tags[vname] = i
            variant_payloads[vname] = payload_types
            # Compute payload size as actual struct size (with alignment padding)
            # since variants are bitcast to/from struct types.
            if payload_types:
                llvm_fields: list[Any] = []
                pre_boxed = self._boxed_enum_fields.get(name, set())
                for j, pt in enumerate(payload_types):
                    if (vname, j) in pre_boxed or self._is_self_ref_field(name, pt):
                        # Self- or mutually-referential field: store as
                        # pointer to avoid infinite type size.
                        llvm_fields.append(LLVM_PTR)
                        boxed_fields.add((vname, j))
                    else:
                        llvm_fields.append(self._resolve_mir_type(pt))
                variant_struct = ir.LiteralStructType(llvm_fields)
                size = _approx_type_size(variant_struct)
            else:
                size = 0
            if size > max_payload_size:
                max_payload_size = size

        # Ensure at least 8 bytes for the payload area
        if max_payload_size < 8:
            max_payload_size = 8

        payload_ty = ir.ArrayType(ir.IntType(8), max_payload_size)
        enum_ty = ir.LiteralStructType([LLVM_I32, payload_ty])
        self._enum_types[name] = (enum_ty, variant_tags, variant_payloads)

        if boxed_fields:
            self._boxed_enum_fields[name] = boxed_fields

    # -----------------------------------------------------------------------
    # Extern / function declarations
    # -----------------------------------------------------------------------

    def _declare_extern(
        self,
        abi: str,
        mod: str,
        fn_name: str,
        param_types: list[MIRType],
        ret_type: MIRType,
    ) -> None:
        """Declare an external function."""
        llvm_params = [self._resolve_mir_type(p) for p in param_types]
        llvm_ret = self._resolve_mir_type(ret_type)
        fn_ty = ir.FunctionType(llvm_ret, llvm_params)
        full_name = f"{mod}__{fn_name}" if mod else fn_name
        if full_name not in self._functions:
            func = ir.Function(self.module, fn_ty, name=full_name)
            func.linkage = "external"
            self._functions[full_name] = func

    def _forward_declare_function(self, mir_fn: MIRFunction) -> None:
        """Forward-declare a MIR function so it can be referenced before emission."""
        if mir_fn.name in self._functions:
            return
        param_types = [self._resolve_mir_type(p.ty) for p in mir_fn.params]
        ret_type = self._resolve_mir_type(mir_fn.return_type)
        fn_ty = ir.FunctionType(ret_type, param_types)
        func = ir.Function(self.module, fn_ty, name=mir_fn.name)
        for i, param in enumerate(mir_fn.params):
            func.args[i].name = param.name
        # Non-public functions get internal linkage (hidden from linker)
        if not mir_fn.is_public and mir_fn.name != "main":
            func.linkage = "internal"
        self._functions[mir_fn.name] = func

    # -----------------------------------------------------------------------
    # Runtime function helpers
    # -----------------------------------------------------------------------

    def _declare_runtime_fn(self, name: str, ret_ty: Any, param_types: list[Any]) -> Any:
        """Declare an external C runtime function if not already declared."""
        if name in self._runtime_fns:
            return self._runtime_fns[name]
        fn_ty = ir.FunctionType(ret_ty, param_types)
        func = ir.Function(self.module, fn_ty, name=name)
        func.linkage = "external"
        self._runtime_fns[name] = func
        return func

    def _rt_malloc(self) -> Any:
        return self._declare_runtime_fn("malloc", LLVM_PTR, [LLVM_INT])

    def _rt_str_concat(self) -> Any:
        return self._declare_runtime_fn("__mn_str_concat", LLVM_STRING, [LLVM_STRING, LLVM_STRING])

    def _rt_str_eq(self) -> Any:
        return self._declare_runtime_fn("__mn_str_eq", LLVM_INT, [LLVM_STRING, LLVM_STRING])

    def _rt_str_cmp(self) -> Any:
        return self._declare_runtime_fn("__mn_str_cmp", LLVM_INT, [LLVM_STRING, LLVM_STRING])

    def _rt_str_len(self) -> Any:
        return self._declare_runtime_fn("__mn_str_len", LLVM_INT, [LLVM_STRING])

    def _rt_str_from_int(self) -> Any:
        return self._declare_runtime_fn("__mn_str_from_int", LLVM_STRING, [LLVM_INT])

    def _rt_str_from_float(self) -> Any:
        return self._declare_runtime_fn("__mn_str_from_float", LLVM_STRING, [LLVM_FLOAT])

    def _rt_str_from_bool(self) -> Any:
        return self._declare_runtime_fn("__mn_str_from_bool", LLVM_STRING, [LLVM_BOOL])

    def _rt_str_println(self) -> Any:
        return self._declare_runtime_fn("__mn_str_println", LLVM_VOID, [LLVM_STRING])

    def _rt_str_print(self) -> Any:
        return self._declare_runtime_fn("__mn_str_print", LLVM_VOID, [LLVM_STRING])

    def _rt_list_new(self) -> Any:
        return self._declare_runtime_fn("__mn_list_new", LLVM_LIST, [LLVM_INT])

    def _rt_list_push(self) -> Any:
        return self._declare_runtime_fn(
            "__mn_list_push", LLVM_VOID, [LLVM_LIST.as_pointer(), ir.IntType(8).as_pointer()]
        )

    def _rt_list_get(self) -> Any:
        return self._declare_runtime_fn(
            "__mn_list_get", ir.IntType(8).as_pointer(), [LLVM_LIST.as_pointer(), LLVM_INT]
        )

    def _rt_list_len(self) -> Any:
        return self._declare_runtime_fn("__mn_list_len", LLVM_INT, [LLVM_LIST.as_pointer()])

    def _rt_list_concat(self) -> Any:
        return self._declare_runtime_fn(
            "__mn_list_concat", LLVM_LIST, [LLVM_LIST.as_pointer(), LLVM_LIST.as_pointer()]
        )

    def _rt_panic(self) -> Any:
        return self._declare_runtime_fn("__mn_panic", LLVM_VOID, [LLVM_STRING])

    # -- Map runtime functions ------------------------------------------------

    def _rt_map_new(self) -> Any:
        return self._declare_runtime_fn("__mn_map_new", LLVM_PTR, [LLVM_INT, LLVM_INT, LLVM_INT])

    def _rt_map_set(self) -> Any:
        return self._declare_runtime_fn("__mn_map_set", LLVM_VOID, [LLVM_PTR, LLVM_PTR, LLVM_PTR])

    def _rt_map_get(self) -> Any:
        return self._declare_runtime_fn("__mn_map_get", LLVM_PTR, [LLVM_PTR, LLVM_PTR])

    def _rt_map_del(self) -> Any:
        return self._declare_runtime_fn("__mn_map_del", LLVM_INT, [LLVM_PTR, LLVM_PTR])

    def _rt_map_len(self) -> Any:
        return self._declare_runtime_fn("__mn_map_len", LLVM_INT, [LLVM_PTR])

    def _rt_map_contains(self) -> Any:
        return self._declare_runtime_fn("__mn_map_contains", LLVM_INT, [LLVM_PTR, LLVM_PTR])

    def _rt_map_iter_new(self) -> Any:
        return self._declare_runtime_fn("__mn_map_iter_new", LLVM_PTR, [LLVM_PTR])

    def _rt_map_iter_next(self) -> Any:
        return self._declare_runtime_fn(
            "__mn_map_iter_next",
            LLVM_INT,
            [LLVM_PTR, LLVM_PTR.as_pointer(), LLVM_PTR.as_pointer()],
        )

    def _rt_map_iter_free(self) -> Any:
        return self._declare_runtime_fn("__mn_map_iter_free", LLVM_VOID, [LLVM_PTR])

    def _rt_alloc(self) -> Any:
        return self._declare_runtime_fn("__mn_alloc", LLVM_PTR, [LLVM_INT])

    def _rt_free(self) -> Any:
        return self._declare_runtime_fn("__mn_free", LLVM_VOID, [LLVM_PTR])

    # -- Signal runtime functions -----------------------------------------------

    def _rt_signal_new(self) -> Any:
        return self._declare_runtime_fn("__mn_signal_new", LLVM_PTR, [LLVM_PTR, LLVM_INT])

    def _rt_signal_get(self) -> Any:
        return self._declare_runtime_fn("__mn_signal_get", LLVM_PTR, [LLVM_PTR])

    def _rt_signal_set(self) -> Any:
        return self._declare_runtime_fn("__mn_signal_set", LLVM_VOID, [LLVM_PTR, LLVM_PTR])

    def _rt_signal_computed(self) -> Any:
        return self._declare_runtime_fn(
            "__mn_signal_computed",
            LLVM_PTR,
            [LLVM_PTR, LLVM_PTR, LLVM_PTR, LLVM_INT, LLVM_INT],
        )

    def _rt_signal_subscribe(self) -> Any:
        return self._declare_runtime_fn("__mn_signal_subscribe", LLVM_VOID, [LLVM_PTR, LLVM_PTR])

    # -- Stream runtime functions ------------------------------------------------

    def _rt_stream_from_list(self) -> Any:
        return self._declare_runtime_fn(
            "__mn_stream_from_list", LLVM_PTR, [LLVM_LIST.as_pointer(), LLVM_INT]
        )

    def _rt_stream_map(self) -> Any:
        return self._declare_runtime_fn(
            "__mn_stream_map", LLVM_PTR, [LLVM_PTR, LLVM_PTR, LLVM_PTR, LLVM_INT]
        )

    def _rt_stream_filter(self) -> Any:
        return self._declare_runtime_fn(
            "__mn_stream_filter", LLVM_PTR, [LLVM_PTR, LLVM_PTR, LLVM_PTR]
        )

    def _rt_stream_take(self) -> Any:
        return self._declare_runtime_fn("__mn_stream_take", LLVM_PTR, [LLVM_PTR, LLVM_INT])

    def _rt_stream_skip(self) -> Any:
        return self._declare_runtime_fn("__mn_stream_skip", LLVM_PTR, [LLVM_PTR, LLVM_INT])

    def _rt_stream_collect(self) -> Any:
        return self._declare_runtime_fn("__mn_stream_collect", LLVM_LIST, [LLVM_PTR, LLVM_INT])

    def _rt_stream_fold(self) -> Any:
        return self._declare_runtime_fn(
            "__mn_stream_fold",
            LLVM_VOID,
            [LLVM_PTR, LLVM_PTR, LLVM_INT, LLVM_PTR, LLVM_PTR, LLVM_PTR],
        )

    def _rt_stream_next(self) -> Any:
        return self._declare_runtime_fn("__mn_stream_next", LLVM_INT, [LLVM_PTR, LLVM_PTR])

    def _rt_stream_bounded(self) -> Any:
        return self._declare_runtime_fn(
            "__mn_stream_bounded", LLVM_PTR, [LLVM_PTR, LLVM_INT, LLVM_INT]
        )

    def _rt_stream_free(self) -> Any:
        return self._declare_runtime_fn("__mn_stream_free", LLVM_VOID, [LLVM_PTR])

    # -- Agent runtime functions ------------------------------------------------

    def _rt_agent_new(self) -> Any:
        return self._declare_runtime_fn(
            "mapanare_agent_new", LLVM_PTR, [LLVM_PTR, LLVM_PTR, LLVM_PTR, LLVM_I32, LLVM_I32]
        )

    def _rt_agent_spawn(self) -> Any:
        return self._declare_runtime_fn("mapanare_agent_spawn", LLVM_I32, [LLVM_PTR])

    def _rt_agent_send(self) -> Any:
        return self._declare_runtime_fn("mapanare_agent_send", LLVM_I32, [LLVM_PTR, LLVM_PTR])

    def _rt_agent_recv_blocking(self) -> Any:
        return self._declare_runtime_fn(
            "mapanare_agent_recv_blocking", LLVM_I32, [LLVM_PTR, LLVM_PTR.as_pointer()]
        )

    # -----------------------------------------------------------------------
    # Printf support
    # -----------------------------------------------------------------------

    def _get_printf(self) -> Any:
        """Declare printf if not already declared."""
        if "printf" in self._runtime_fns:
            return self._runtime_fns["printf"]
        voidptr_ty = ir.IntType(8).as_pointer()
        printf_ty = ir.FunctionType(LLVM_I32, [voidptr_ty], var_arg=True)
        func = ir.Function(self.module, printf_ty, name="printf")
        self._runtime_fns["printf"] = func
        return func

    def _get_fmt_string(self, fmt: str) -> Any:
        """Get or create a global format string constant."""
        if fmt in self._fmt_strings:
            return self._fmt_strings[fmt]
        fmt_bytes = bytearray(fmt.encode("utf-8")) + bytearray(b"\x00")
        c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt_bytes)), fmt_bytes)
        gv = ir.GlobalVariable(self.module, c_fmt.type, name=f".fmt.{len(self._fmt_strings)}")
        gv.global_constant = True
        gv.linkage = "private"
        gv.initializer = c_fmt
        gv.align = 2  # Ensure even address — mn_untag() clears bit 0
        self._fmt_strings[fmt] = gv
        return gv

    # -----------------------------------------------------------------------
    # String literal helpers
    # -----------------------------------------------------------------------

    def _coerce_to_string(self, builder: Any, val: Any, name: str) -> Any:
        """Coerce a value to LLVM_STRING ({i8*, i64}). Handles i8*, [N x i8], etc."""
        if val.type == LLVM_STRING:
            return val
        if isinstance(val.type, ir.PointerType):
            s = ir.Constant(LLVM_STRING, ir.Undefined)
            s = builder.insert_value(s, val, 0, name=f"{name}.s0")
            s = builder.insert_value(s, ir.Constant(LLVM_INT, 0), 1, name=f"{name}.s1")
            return s
        if isinstance(val.type, ir.ArrayType):
            # [N x i8] → GEP to i8*, then wrap in string struct
            zero = ir.Constant(LLVM_INT, 0)
            # Need to store array in alloca for GEP
            tmp = builder.alloca(val.type, name=f"{name}.arr")
            builder.store(val, tmp)
            ptr = builder.gep(tmp, [zero, zero], inbounds=True, name=f"{name}.ptr")
            length = ir.Constant(LLVM_INT, val.type.count)
            s = ir.Constant(LLVM_STRING, ir.Undefined)
            s = builder.insert_value(s, ptr, 0, name=f"{name}.s0")
            s = builder.insert_value(s, length, 1, name=f"{name}.s1")
            return s
        # Fallback: bitcast to LLVM_STRING via memory
        return _coerce_arg(builder, val, LLVM_STRING, name)

    def _make_string_constant(self, builder: Any, text: str) -> Any:
        """Create a global string constant and return an LLVM_STRING value ({i8*, i64})."""
        raw = text.encode("utf-8")
        c_str = ir.Constant(ir.ArrayType(ir.IntType(8), len(raw)), bytearray(raw))
        name = f".str.{self._str_counter}"
        self._str_counter += 1
        gv = ir.GlobalVariable(self.module, c_str.type, name=name)
        gv.global_constant = True
        gv.linkage = "private"
        gv.initializer = c_str
        gv.align = 2  # Ensure even address — mn_untag() clears bit 0
        # GEP to get i8* to the first element
        zero = ir.Constant(LLVM_INT, 0)
        ptr = builder.gep(gv, [zero, zero], inbounds=True, name=f"{name}.ptr")
        length = ir.Constant(LLVM_INT, len(raw))
        # Build the {i8*, i64} struct
        str_val = ir.Constant(LLVM_STRING, ir.Undefined)
        str_val = builder.insert_value(str_val, ptr, 0, name=f"{name}.s0")
        str_val = builder.insert_value(str_val, length, 1, name=f"{name}.s1")
        return str_val

    # -----------------------------------------------------------------------
    # Function emission
    # -----------------------------------------------------------------------

    def _emit_function(self, mir_fn: MIRFunction) -> None:
        """Emit the body of a single MIR function."""
        func = self._functions[mir_fn.name]

        if not mir_fn.blocks:
            # Function with no body — just a declaration
            return

        # Attach DISubprogram if debug info is enabled
        if self._debug:
            di_sp = self._create_di_subprogram(mir_fn)
            if di_sp is not None:
                func.set_metadata("dbg", di_sp)

        # 1. Create all LLVM basic blocks upfront.
        #    A "pre_entry" block is prepended for lazy allocas — it becomes
        #    the actual function entry point and jumps to the MIR entry block.
        #    This avoids builder position interference when inserting allocas.
        pre_entry = func.append_basic_block("pre_entry")
        llvm_blocks: dict[str, Any] = {}
        for bb in mir_fn.blocks:
            llvm_blocks[bb.label] = func.append_basic_block(bb.label)

        # 2. Value map: MIR value name -> LLVM value
        values: dict[str, Any] = {}

        # 3. Bind function parameters — also store to allocas so they're
        #    accessible from any basic block (fixes cross-block dominance
        #    when field_set/assignment modifies a param in one branch only).
        for i, param in enumerate(mir_fn.params):
            values[f"%{param.name}"] = func.args[i]
            # Also store without % prefix for flexibility
            values[param.name] = func.args[i]

        # 4. Replace MIR phi nodes with alloca/store/load patterns.
        #    This avoids LLVM phi predecessor mismatches and SSA dominance
        #    violations.  LLVM's mem2reg pass (part of -O1+) will convert
        #    these back into proper phi nodes automatically.
        self._fn_allocas = {}
        self._list_roots = {}
        self._alloca_block = pre_entry

        deferred_phi_stores: list[tuple[Any, list[tuple[str, Value]], dict[str, Any]]] = []

        ab = ir.IRBuilder(pre_entry)

        # Pre-create allocas for all function parameters and store their
        # initial values.  This ensures that if a parameter is modified
        # (field_set, assignment) in one branch, the alloca has a valid
        # initial value readable from any other branch.
        entry_builder = ir.IRBuilder(llvm_blocks[mir_fn.blocks[0].label]) if mir_fn.blocks else None
        for i, param in enumerate(mir_fn.params):
            arg_val = func.args[i]
            val_ty = arg_val.type
            if isinstance(val_ty, ir.VoidType):
                continue
            ab.position_at_end(pre_entry)
            vname = param.name.lstrip("%")
            alloca = ab.alloca(val_ty, name=f"a.{vname}")
            self._fn_allocas[f"%{param.name}"] = alloca
            self._fn_allocas[param.name] = alloca
            self._value_blocks[f"%{param.name}"] = "entry"
            self._value_blocks[param.name] = "entry"
            # Store initial value in the entry block (not pre_entry, since
            # function args aren't available until the function body starts)
            if entry_builder is not None:
                try:
                    entry_builder.store(arg_val, alloca)
                except Exception:
                    pass

        for bb in mir_fn.blocks:
            builder = ir.IRBuilder(llvm_blocks[bb.label])
            for inst in bb.instructions:
                if isinstance(inst, Phi):
                    llvm_type = self._resolve_mir_type(inst.dest.ty)
                    if isinstance(llvm_type, ir.VoidType):
                        llvm_type = LLVM_PTR
                    # Create alloca in pre_entry for the phi dest
                    ab.position_at_end(pre_entry)
                    alloca = ab.alloca(llvm_type, name=f"phi.a.{self._val_name(inst.dest)}")
                    self._fn_allocas[inst.dest.name] = alloca
                    # Load at phi position — this is the "result" of the phi
                    loaded = builder.load(alloca, name=self._val_name(inst.dest))
                    values[inst.dest.name] = loaded
                    # Defer stores until after all blocks are emitted
                    deferred_phi_stores.append((alloca, inst.incoming, llvm_blocks))
                else:
                    break  # Phi nodes must be at block start

        # 5. Emit all non-phi instructions block by block
        for bb in mir_fn.blocks:
            builder = ir.IRBuilder(llvm_blocks[bb.label])
            self._current_builder = builder
            self._current_block_label = bb.label
            # Position after any phi-replacement loads already emitted
            if builder.block.instructions:
                builder.position_at_end(builder.block)
            for inst in bb.instructions:
                if isinstance(inst, Phi):
                    continue  # Handled above via alloca
                # Track instruction count before emission for debug location
                n_before = len(builder.block.instructions) if self._debug else 0
                self._emit_instruction(inst, builder, values, llvm_blocks, func)
                # Attach debug location to newly emitted LLVM instructions
                if self._debug and inst.span is not None:
                    for llvm_inst in builder.block.instructions[n_before:]:
                        if not hasattr(llvm_inst, "metadata") or "dbg" in getattr(
                            llvm_inst, "metadata", {}
                        ):
                            continue
                        self._attach_debug_location(llvm_inst, inst.span, mir_fn.name)
                # Emit variable debug info for named copies (let bindings)
                if self._debug and isinstance(inst, Copy) and inst.span is not None:
                    dest_name = inst.dest.name
                    if dest_name.startswith("%") and not dest_name[1:].startswith("t"):
                        self._emit_di_local_variable(
                            builder,
                            dest_name[1:],
                            inst.dest.ty,
                            inst.span.line,
                            mir_fn.name,
                        )

        # 6. Resolve deferred phi stores — store incoming values to allocas
        #    in predecessor blocks (before terminators).
        for alloca, incoming, blocks in deferred_phi_stores:
            pointee = alloca.type.pointee
            for lbl, val in incoming:
                if lbl not in blocks:
                    continue
                pred_block = blocks[lbl]
                inc_builder = ir.IRBuilder(pred_block)
                term = pred_block.terminator
                if term:
                    inc_builder.position_before(term)
                # Get incoming value — prefer alloca load for cross-block safety
                def_block = self._value_blocks.get(val.name, "")
                if def_block and def_block != lbl and val.name in self._fn_allocas:
                    try:
                        inc_val = inc_builder.load(
                            self._fn_allocas[val.name],
                            name=f"phi.l.{val.name.lstrip('%')}",
                        )
                    except Exception:
                        inc_val = values.get(val.name)
                else:
                    inc_val = values.get(val.name)
                if inc_val is None:
                    if isinstance(pointee, ir.PointerType):
                        inc_val = ir.Constant(pointee, None)
                    elif isinstance(pointee, ir.LiteralStructType):
                        inc_val = ir.Constant(pointee, ir.Undefined)
                    else:
                        inc_val = ir.Constant(pointee, 0)
                # Coerce to match alloca type
                if inc_val.type != pointee:
                    inc_val = _coerce_arg(inc_builder, inc_val, pointee, "phi.s")
                inc_builder.store(inc_val, alloca)

        # 7. Ensure all blocks are properly terminated
        for bb in mir_fn.blocks:
            block = llvm_blocks[bb.label]
            if not block.is_terminated:
                builder = ir.IRBuilder(block)
                ret_ty = self._resolve_mir_type(mir_fn.return_type)
                if isinstance(ret_ty, ir.VoidType):
                    builder.ret_void()
                else:
                    builder.unreachable()

        # 8. Finalize pre_entry: jump to the real entry block
        real_entry = llvm_blocks[mir_fn.blocks[0].label]
        if not pre_entry.is_terminated:
            ab = ir.IRBuilder(pre_entry)
            ab.position_at_end(pre_entry)
            ab.branch(real_entry)

        # 9. Cleanup per-function state
        self._fn_allocas = {}
        self._current_builder = None
        self._current_block_label = ""
        self._value_blocks = {}
        self._alloca_block = None

    # -----------------------------------------------------------------------
    # Value name helper
    # -----------------------------------------------------------------------

    @staticmethod
    def _val_name(v: Value) -> str:
        """Strip the leading % from a value name for LLVM naming."""
        name = v.name
        if name.startswith("%"):
            return name[1:]
        return name

    # -----------------------------------------------------------------------
    # Instruction dispatch
    # -----------------------------------------------------------------------

    def _emit_instruction(  # noqa: C901
        self,
        inst: Instruction,
        builder: Any,
        values: dict[str, Any],
        llvm_blocks: dict[str, Any],
        func: Any,
    ) -> None:
        """Emit a single MIR instruction as LLVM IR."""
        if isinstance(inst, Const):
            self._emit_const(inst, builder, values)
        elif isinstance(inst, Copy):
            self._emit_copy(inst, values)
        elif isinstance(inst, Cast):
            self._emit_cast(inst, builder, values)
        elif isinstance(inst, BinOp):
            self._emit_binop(inst, builder, values)
        elif isinstance(inst, UnaryOp):
            self._emit_unaryop(inst, builder, values)
        elif isinstance(inst, Call):
            self._emit_call(inst, builder, values, func)
        elif isinstance(inst, ExternCall):
            self._emit_extern_call(inst, builder, values)
        elif isinstance(inst, Return):
            self._emit_return(inst, builder, values, func)
        elif isinstance(inst, Jump):
            self._emit_jump(inst, builder, llvm_blocks)
        elif isinstance(inst, Branch):
            self._emit_branch(inst, builder, values, llvm_blocks)
        elif isinstance(inst, Switch):
            self._emit_switch(inst, builder, values, llvm_blocks)
        elif isinstance(inst, StructInit):
            self._emit_struct_init(inst, builder, values)
        elif isinstance(inst, FieldGet):
            self._emit_field_get(inst, builder, values)
        elif isinstance(inst, FieldSet):
            self._emit_field_set(inst, builder, values)
        elif isinstance(inst, ListInit):
            self._emit_list_init(inst, builder, values)
        elif isinstance(inst, ListPush):
            self._emit_list_push(inst, builder, values)
        elif isinstance(inst, IndexGet):
            self._emit_index_get(inst, builder, values)
        elif isinstance(inst, IndexSet):
            self._emit_index_set(inst, builder, values)
        elif isinstance(inst, MapInit):
            self._emit_map_init(inst, builder, values)
        elif isinstance(inst, EnumInit):
            self._emit_enum_init(inst, builder, values)
        elif isinstance(inst, EnumTag):
            self._emit_enum_tag(inst, builder, values)
        elif isinstance(inst, EnumPayload):
            self._emit_enum_payload(inst, builder, values)
        elif isinstance(inst, WrapSome):
            self._emit_wrap_some(inst, builder, values)
        elif isinstance(inst, WrapNone):
            self._emit_wrap_none(inst, builder, values)
        elif isinstance(inst, WrapOk):
            self._emit_wrap_ok(inst, builder, values)
        elif isinstance(inst, WrapErr):
            self._emit_wrap_err(inst, builder, values)
        elif isinstance(inst, Unwrap):
            self._emit_unwrap(inst, builder, values)
        elif isinstance(inst, InterpConcat):
            self._emit_interp_concat(inst, builder, values)
        elif isinstance(inst, AgentSpawn):
            self._emit_agent_spawn(inst, builder, values)
        elif isinstance(inst, AgentSend):
            self._emit_agent_send(inst, builder, values)
        elif isinstance(inst, AgentSync):
            self._emit_agent_sync(inst, builder, values, func)
        elif isinstance(inst, SignalInit):
            self._emit_signal_init(inst, builder, values)
        elif isinstance(inst, SignalGet):
            self._emit_signal_get(inst, builder, values)
        elif isinstance(inst, SignalSet):
            self._emit_signal_set(inst, builder, values)
        elif isinstance(inst, SignalComputed):
            self._emit_signal_computed(inst, builder, values)
        elif isinstance(inst, SignalSubscribe):
            self._emit_signal_subscribe(inst, builder, values)
        elif isinstance(inst, StreamInit):
            self._emit_stream_init(inst, builder, values)
        elif isinstance(inst, StreamOp):
            self._emit_stream_op(inst, builder, values)
        elif isinstance(inst, ClosureCreate):
            self._emit_closure_create(inst, builder, values)
        elif isinstance(inst, ClosureCall):
            self._emit_closure_call(inst, builder, values)
        elif isinstance(inst, EnvLoad):
            self._emit_env_load(inst, builder, values)
        elif isinstance(inst, Assert):
            self._emit_assert(inst, builder, values, func)
        elif isinstance(inst, Phi):
            pass  # Handled in the first pass
        else:
            # Unknown instruction — emit as unreachable for safety
            pass

    # -----------------------------------------------------------------------
    # Instruction emitters
    # -----------------------------------------------------------------------

    def _get_value(self, val: Value, values: dict[str, Any]) -> Any:
        """Look up the LLVM value for a MIR Value.

        For same-block values, returns the SSA value directly (preserves types).
        For cross-block values, loads from the entry-block alloca (always
        dominates, fixes SSA dominance violations in nested control flow).
        """
        # Check if the value was defined in a different block — needs alloca load
        def_block = self._value_blocks.get(val.name, "")
        builder = self._current_builder
        if (
            def_block
            and def_block != self._current_block_label
            and val.name in self._fn_allocas
            and builder is not None
        ):
            try:
                return builder.load(
                    self._fn_allocas[val.name],
                    name=f"l.{val.name.lstrip('%')}",
                )
            except Exception:
                pass  # fall through to dict lookup
        if val.name in values:
            return values[val.name]
        # Try without % prefix
        stripped = val.name.lstrip("%")
        if stripped in values:
            return values[stripped]
        # Fallback: return a zero constant of the appropriate type.
        # This can happen when cross-module MIR merge creates references
        # to values defined in unreachable branches.
        fallback_ty = self._resolve_mir_type(val.ty) if val.ty else LLVM_INT
        if isinstance(fallback_ty, ir.VoidType):
            fallback_ty = LLVM_INT
        if isinstance(fallback_ty, ir.PointerType):
            return ir.Constant(fallback_ty, None)
        if isinstance(fallback_ty, ir.LiteralStructType):
            return ir.Constant(fallback_ty, ir.Undefined)
        return ir.Constant(fallback_ty, 0)

    def _store_value(self, dest: Value, llvm_val: Any, values: dict[str, Any]) -> None:
        """Store an LLVM value in the value map under the MIR dest name."""
        values[dest.name] = llvm_val
        # Track which block this value was defined in
        self._value_blocks[dest.name] = self._current_block_label
        # Also persist to an entry-block alloca so the value is accessible
        # from any basic block (fixes SSA dominance for cross-block refs).
        builder = self._current_builder
        if builder is None:
            return
        try:
            # Lazy alloca creation — use actual LLVM type to avoid mismatch.
            # Allocas go in the dedicated pre_entry block (separate from
            # instruction emission), so position interference is impossible.
            if dest.name not in self._fn_allocas:
                val_ty = llvm_val.type
                if isinstance(val_ty, ir.VoidType):
                    return
                ab = ir.IRBuilder(self._alloca_block)
                ab.position_at_end(self._alloca_block)
                vname = dest.name.lstrip("%")
                self._fn_allocas[dest.name] = ab.alloca(val_ty, name=f"a.{vname}")
            else:
                # If the new value is larger than the existing alloca (e.g.
                # a None init created a {i1, i8*} alloca but the real value
                # is {i1, {i32, [48 x i8]}}), recreate with the larger type
                # to avoid stack buffer overflow from coerced stores.
                existing = self._fn_allocas[dest.name]
                existing_size = _approx_type_size(existing.type.pointee)
                new_size = _approx_type_size(llvm_val.type)
                if new_size > existing_size:
                    ab = ir.IRBuilder(self._alloca_block)
                    ab.position_at_end(self._alloca_block)
                    vname = dest.name.lstrip("%")
                    self._fn_allocas[dest.name] = ab.alloca(llvm_val.type, name=f"a.{vname}")
            alloca = self._fn_allocas[dest.name]
            pointee = alloca.type.pointee
            val = llvm_val
            if val.type != pointee:
                val = _coerce_arg(builder, val, pointee, "sv")
            builder.store(val, alloca)
        except Exception:
            pass  # fallback: dict-only (value stays in SSA form)

    # --- Const ---

    def _emit_const(self, inst: Const, builder: Any, values: dict[str, Any]) -> None:
        kind = inst.ty.kind
        val = inst.value

        if kind == TypeKind.INT:
            result = ir.Constant(LLVM_INT, int(val) if val is not None else 0)
        elif kind == TypeKind.FLOAT:
            result = ir.Constant(LLVM_FLOAT, float(val) if val is not None else 0.0)
        elif kind == TypeKind.BOOL:
            result = ir.Constant(LLVM_BOOL, 1 if val else 0)
        elif kind == TypeKind.CHAR:
            c = ord(val) if isinstance(val, str) and val else 0
            result = ir.Constant(LLVM_CHAR, c)
        elif kind == TypeKind.STRING:
            text = str(val) if val is not None else ""
            result = self._make_string_constant(builder, text)
        elif kind == TypeKind.FN and isinstance(val, str):
            # Function reference — resolve to function pointer (i8*)
            fn = self._functions.get(val)
            if fn is not None:
                result = builder.bitcast(fn, LLVM_PTR)
            else:
                result = ir.Constant(LLVM_PTR, None)
        elif kind == TypeKind.VOID:
            # Void constants are not really values; store a dummy
            result = ir.Constant(LLVM_BOOL, 0)
        elif val is None:
            # None literal — produce a zeroinitializer for the target type
            llvm_ty = self._resolve_mir_type(inst.ty)
            result = ir.Constant(llvm_ty, None)
        else:
            # Fallback: try int
            llvm_ty = self._resolve_mir_type(inst.ty)
            try:
                result = ir.Constant(llvm_ty, val)
            except Exception:
                result = ir.Constant(llvm_ty, None)

        self._store_value(inst.dest, result, values)

    # --- Copy ---

    def _emit_copy(self, inst: Copy, values: dict[str, Any]) -> None:
        """Copy is a no-op in SSA — just alias the value."""
        src = self._get_value(inst.src, values)
        self._store_value(inst.dest, src, values)

    # --- Cast ---

    def _emit_cast(self, inst: Cast, builder: Any, values: dict[str, Any]) -> None:
        src = self._get_value(inst.src, values)
        src_kind = inst.src.ty.kind
        tgt_kind = inst.target_type.kind
        name = self._val_name(inst.dest)

        if src_kind == TypeKind.INT and tgt_kind == TypeKind.FLOAT:
            result = builder.sitofp(src, LLVM_FLOAT, name=name)
        elif src_kind == TypeKind.FLOAT and tgt_kind == TypeKind.INT:
            result = builder.fptosi(src, LLVM_INT, name=name)
        elif src_kind == TypeKind.INT and tgt_kind == TypeKind.BOOL:
            result = builder.icmp_signed("!=", src, ir.Constant(LLVM_INT, 0), name=name)
        elif src_kind == TypeKind.BOOL and tgt_kind == TypeKind.INT:
            result = builder.zext(src, LLVM_INT, name=name)
        elif src_kind == TypeKind.INT and tgt_kind == TypeKind.STRING:
            fn = self._rt_str_from_int()
            result = builder.call(fn, [src], name=name)
        elif src_kind == TypeKind.FLOAT and tgt_kind == TypeKind.STRING:
            fn = self._rt_str_from_float()
            result = builder.call(fn, [src], name=name)
        elif src_kind == TypeKind.BOOL and tgt_kind == TypeKind.STRING:
            fn = self._rt_str_from_bool()
            result = builder.call(fn, [src], name=name)
        elif src_kind == TypeKind.INT and tgt_kind == TypeKind.CHAR:
            result = builder.trunc(src, LLVM_CHAR, name=name)
        elif src_kind == TypeKind.CHAR and tgt_kind == TypeKind.INT:
            result = builder.zext(src, LLVM_INT, name=name)
        else:
            # Generic bitcast / no-op for compatible types
            tgt_ty = self._resolve_mir_type(inst.target_type)
            src_ty = src.type
            if src_ty == tgt_ty:
                result = src
            else:
                result = builder.bitcast(src, tgt_ty, name=name)

        self._store_value(inst.dest, result, values)

    # --- BinOp ---

    def _emit_binop(self, inst: BinOp, builder: Any, values: dict[str, Any]) -> None:  # noqa: C901
        lhs = self._get_value(inst.lhs, values)
        rhs = self._get_value(inst.rhs, values)
        op = inst.op
        name = self._val_name(inst.dest)
        lhs_kind = inst.lhs.ty.kind

        # Detect string type from LLVM value when MIR type is UNKNOWN
        if lhs_kind == TypeKind.UNKNOWN and lhs.type == LLVM_STRING:
            lhs_kind = TypeKind.STRING
        if lhs_kind == TypeKind.UNKNOWN and rhs.type == LLVM_STRING:
            lhs_kind = TypeKind.STRING
        # Detect list type from LLVM value when MIR type is UNKNOWN
        if lhs_kind == TypeKind.UNKNOWN and lhs.type == LLVM_LIST:
            lhs_kind = TypeKind.LIST
        if lhs_kind == TypeKind.UNKNOWN and rhs.type == LLVM_LIST:
            lhs_kind = TypeKind.LIST

        # Cross-module type coercion: if MIR says INT but LLVM value is i8*
        if lhs_kind == TypeKind.INT:
            if isinstance(lhs.type, ir.PointerType):
                lhs = builder.ptrtoint(lhs, LLVM_INT, name=f"{name}.lc")
            if isinstance(rhs.type, ir.PointerType):
                rhs = builder.ptrtoint(rhs, LLVM_INT, name=f"{name}.rc")

        # String operations
        if lhs_kind == TypeKind.STRING:
            # Ensure both operands are LLVM_STRING type
            lhs = self._coerce_to_string(builder, lhs, f"{name}.ls")
            rhs = self._coerce_to_string(builder, rhs, f"{name}.rs")
            if op == BinOpKind.ADD:
                fn = self._rt_str_concat()
                result = builder.call(fn, [lhs, rhs], name=name)
            elif op in (BinOpKind.EQ, BinOpKind.NE):
                fn = self._rt_str_eq()
                cmp_val = builder.call(fn, [lhs, rhs], name=f"{name}.cmp")
                if op == BinOpKind.EQ:
                    result = builder.icmp_signed("!=", cmp_val, ir.Constant(LLVM_INT, 0), name=name)
                else:
                    result = builder.icmp_signed("==", cmp_val, ir.Constant(LLVM_INT, 0), name=name)
            elif op in (BinOpKind.LT, BinOpKind.GT, BinOpKind.LE, BinOpKind.GE):
                fn = self._rt_str_cmp()
                cmp_val = builder.call(fn, [lhs, rhs], name=f"{name}.cmp")
                cmp_ops = {
                    BinOpKind.LT: "<",
                    BinOpKind.GT: ">",
                    BinOpKind.LE: "<=",
                    BinOpKind.GE: ">=",
                }
                result = builder.icmp_signed(
                    cmp_ops[op], cmp_val, ir.Constant(LLVM_INT, 0), name=name
                )
            else:
                result = ir.Constant(LLVM_INT, 0)
            self._store_value(inst.dest, result, values)
            return

        # List concatenation
        if lhs_kind == TypeKind.LIST and op == BinOpKind.ADD:
            fn_concat = self._rt_list_concat()
            # Both operands must be LLVM_LIST; coerce if needed
            if lhs.type != LLVM_LIST:
                lhs = _coerce_arg(builder, lhs, LLVM_LIST, f"{name}.lc")
            if rhs.type != LLVM_LIST:
                rhs = _coerce_arg(builder, rhs, LLVM_LIST, f"{name}.rc")
            # Pass both lists by pointer
            lhs_ptr = builder.alloca(LLVM_LIST, name=f"{name}.lptr")
            builder.store(lhs, lhs_ptr)
            rhs_ptr = builder.alloca(LLVM_LIST, name=f"{name}.rptr")
            builder.store(rhs, rhs_ptr)
            result = builder.call(fn_concat, [lhs_ptr, rhs_ptr], name=name)
            self._store_value(inst.dest, result, values)
            return

        # Float operations
        if lhs_kind == TypeKind.FLOAT:
            if op == BinOpKind.ADD:
                result = builder.fadd(lhs, rhs, name=name)
            elif op == BinOpKind.SUB:
                result = builder.fsub(lhs, rhs, name=name)
            elif op == BinOpKind.MUL:
                result = builder.fmul(lhs, rhs, name=name)
            elif op == BinOpKind.DIV:
                result = builder.fdiv(lhs, rhs, name=name)
            elif op == BinOpKind.MOD:
                result = builder.frem(lhs, rhs, name=name)
            elif op == BinOpKind.EQ:
                result = builder.fcmp_ordered("==", lhs, rhs, name=name)
            elif op == BinOpKind.NE:
                result = builder.fcmp_ordered("!=", lhs, rhs, name=name)
            elif op == BinOpKind.LT:
                result = builder.fcmp_ordered("<", lhs, rhs, name=name)
            elif op == BinOpKind.GT:
                result = builder.fcmp_ordered(">", lhs, rhs, name=name)
            elif op == BinOpKind.LE:
                result = builder.fcmp_ordered("<=", lhs, rhs, name=name)
            elif op == BinOpKind.GE:
                result = builder.fcmp_ordered(">=", lhs, rhs, name=name)
            else:
                result = ir.Constant(LLVM_FLOAT, 0.0)
            self._store_value(inst.dest, result, values)
            return

        # Bool logical operators
        if lhs_kind == TypeKind.BOOL and op in (BinOpKind.AND, BinOpKind.OR):
            if op == BinOpKind.AND:
                result = builder.and_(lhs, rhs, name=name)
            else:
                result = builder.or_(lhs, rhs, name=name)
            self._store_value(inst.dest, result, values)
            return

        # Integer operations (default)
        # Cross-module coercion: normalize both operands to i64 for integer ops
        for tag, operand_ref in [("lc", "lhs"), ("rc", "rhs")]:
            operand = lhs if tag == "lc" else rhs
            if isinstance(operand.type, ir.PointerType):
                operand = builder.ptrtoint(operand, LLVM_INT, name=f"{name}.{tag}")
            elif isinstance(operand.type, ir.LiteralStructType):
                # Struct → i64 via memory reinterpretation
                tmp = builder.alloca(operand.type, name=f"{name}.{tag}.tmp")
                builder.store(operand, tmp)
                int_ptr = builder.bitcast(tmp, LLVM_INT.as_pointer(), name=f"{name}.{tag}.ptr")
                operand = builder.load(int_ptr, name=f"{name}.{tag}")
            elif isinstance(operand.type, ir.ArrayType):
                tmp = builder.alloca(operand.type, name=f"{name}.{tag}.tmp")
                builder.store(operand, tmp)
                int_ptr = builder.bitcast(tmp, LLVM_INT.as_pointer(), name=f"{name}.{tag}.ptr")
                operand = builder.load(int_ptr, name=f"{name}.{tag}")
            elif isinstance(operand.type, ir.IntType) and operand.type.width != 64:
                if operand.type.width < 64:
                    operand = builder.zext(operand, LLVM_INT, name=f"{name}.{tag}")
                else:
                    operand = builder.trunc(operand, LLVM_INT, name=f"{name}.{tag}")
            if tag == "lc":
                lhs = operand
            else:
                rhs = operand
        if op == BinOpKind.ADD:
            result = builder.add(lhs, rhs, name=name)
        elif op == BinOpKind.SUB:
            result = builder.sub(lhs, rhs, name=name)
        elif op == BinOpKind.MUL:
            result = builder.mul(lhs, rhs, name=name)
        elif op == BinOpKind.DIV:
            result = builder.sdiv(lhs, rhs, name=name)
        elif op == BinOpKind.MOD:
            result = builder.srem(lhs, rhs, name=name)
        elif op == BinOpKind.EQ:
            result = builder.icmp_signed("==", lhs, rhs, name=name)
        elif op == BinOpKind.NE:
            result = builder.icmp_signed("!=", lhs, rhs, name=name)
        elif op == BinOpKind.LT:
            result = builder.icmp_signed("<", lhs, rhs, name=name)
        elif op == BinOpKind.GT:
            result = builder.icmp_signed(">", lhs, rhs, name=name)
        elif op == BinOpKind.LE:
            result = builder.icmp_signed("<=", lhs, rhs, name=name)
        elif op == BinOpKind.GE:
            result = builder.icmp_signed(">=", lhs, rhs, name=name)
        elif op == BinOpKind.AND:
            result = builder.and_(lhs, rhs, name=name)
        elif op == BinOpKind.OR:
            result = builder.or_(lhs, rhs, name=name)
        else:
            result = ir.Constant(LLVM_INT, 0)

        self._store_value(inst.dest, result, values)

    # --- UnaryOp ---

    def _emit_unaryop(self, inst: UnaryOp, builder: Any, values: dict[str, Any]) -> None:
        operand = self._get_value(inst.operand, values)
        name = self._val_name(inst.dest)
        kind = inst.operand.ty.kind

        if inst.op == UnaryOpKind.NEG:
            if kind == TypeKind.FLOAT:
                result = builder.fsub(ir.Constant(LLVM_FLOAT, 0.0), operand, name=name)
            else:
                result = builder.sub(ir.Constant(LLVM_INT, 0), operand, name=name)
        elif inst.op == UnaryOpKind.NOT:
            if kind == TypeKind.BOOL:
                result = builder.xor(operand, ir.Constant(LLVM_BOOL, 1), name=name)
            else:
                result = builder.icmp_signed("==", operand, ir.Constant(LLVM_INT, 0), name=name)
        else:
            result = operand

        self._store_value(inst.dest, result, values)

    # --- Call ---

    def _emit_call(  # noqa: C901
        self,
        inst: Call,
        builder: Any,
        values: dict[str, Any],
        func: Any,
    ) -> None:
        fn_name = inst.fn_name
        args = [self._get_value(a, values) for a in inst.args]
        name = self._val_name(inst.dest)

        # --- Builtin dispatch ---

        # print/println
        if fn_name in ("println", "print"):
            if (
                inst.args
                and inst.args[0].ty.kind == TypeKind.STRING
                and args[0].type == LLVM_STRING
            ):
                rt_fn = self._rt_str_println() if fn_name == "println" else self._rt_str_print()
                builder.call(rt_fn, [args[0]])
            elif inst.args and inst.args[0].ty.kind == TypeKind.INT:
                fmt = "%lld\n" if fn_name == "println" else "%lld"
                self._emit_printf(builder, fmt, [args[0]])
            elif inst.args and inst.args[0].ty.kind == TypeKind.FLOAT:
                fmt = "%f\n" if fn_name == "println" else "%f"
                self._emit_printf(builder, fmt, [args[0]])
            elif inst.args and inst.args[0].ty.kind == TypeKind.BOOL:
                # Convert bool to string then print
                str_fn = self._rt_str_from_bool()
                str_val = builder.call(str_fn, [args[0]], name=f"{name}.bstr")
                rt_fn = self._rt_str_println() if fn_name == "println" else self._rt_str_print()
                builder.call(rt_fn, [str_val])
            else:
                # Fallback: try printf with i64
                if inst.args:
                    fmt = "%lld\n" if fn_name == "println" else "%lld"
                    self._emit_printf(builder, fmt, [args[0]])
            # print/println returns void — store a dummy value
            self._store_value(inst.dest, ir.Constant(LLVM_BOOL, 0), values)
            return

        # len
        if fn_name == "len":
            if inst.args and inst.args[0].ty.kind == TypeKind.STRING:
                fn = self._rt_str_len()
                result = builder.call(fn, [args[0]], name=name)
            elif inst.args and inst.args[0].ty.kind == TypeKind.LIST:
                # Need a pointer for list_len — alloca + store + call
                fn = self._rt_list_len()
                list_val = args[0]
                # Coerce i8* → LLVM_LIST if needed (cross-module type resolution)
                if list_val.type != LLVM_LIST:
                    list_val = _coerce_arg(builder, list_val, LLVM_LIST, f"{name}.lc")
                list_ptr = builder.alloca(LLVM_LIST, name=f"{name}.tmp")
                builder.store(list_val, list_ptr)
                result = builder.call(fn, [list_ptr], name=name)
            elif inst.args and inst.args[0].ty.kind == TypeKind.MAP:
                fn = self._rt_map_len()
                result = builder.call(fn, [args[0]], name=name)
            elif inst.args and hasattr(args[0], "type") and args[0].type == LLVM_LIST:
                # Fallback: LLVM value type is list even though MIR type was lost
                # (common in cross-module calls where return type info is UNKNOWN)
                fn = self._rt_list_len()
                list_val = args[0]
                list_ptr = builder.alloca(LLVM_LIST, name=f"{name}.tmp")
                builder.store(list_val, list_ptr)
                result = builder.call(fn, [list_ptr], name=name)
            else:
                result = ir.Constant(LLVM_INT, 0)
            self._store_value(inst.dest, result, values)
            return

        # str / toString
        if fn_name in ("str", "toString"):
            if inst.args and inst.args[0].ty.kind == TypeKind.INT:
                fn = self._rt_str_from_int()
                result = builder.call(fn, [args[0]], name=name)
            elif inst.args and inst.args[0].ty.kind == TypeKind.FLOAT:
                fn = self._rt_str_from_float()
                result = builder.call(fn, [args[0]], name=name)
            elif inst.args and inst.args[0].ty.kind == TypeKind.BOOL:
                fn = self._rt_str_from_bool()
                result = builder.call(fn, [args[0]], name=name)
            elif inst.args and inst.args[0].ty.kind == TypeKind.STRING:
                result = args[0]  # Already a string
            else:
                result = self._make_string_constant(builder, "<?>")
            self._store_value(inst.dest, result, values)
            return

        # int() conversion
        if fn_name == "int":
            if inst.args and inst.args[0].ty.kind == TypeKind.FLOAT:
                result = builder.fptosi(args[0], LLVM_INT, name=name)
            elif inst.args and inst.args[0].ty.kind == TypeKind.BOOL:
                result = builder.zext(args[0], LLVM_INT, name=name)
            elif inst.args and inst.args[0].ty.kind == TypeKind.INT:
                result = args[0]
            else:
                result = ir.Constant(LLVM_INT, 0)
            self._store_value(inst.dest, result, values)
            return

        # float() conversion
        if fn_name == "float":
            if inst.args and inst.args[0].ty.kind == TypeKind.INT:
                result = builder.sitofp(args[0], LLVM_FLOAT, name=name)
            elif inst.args and inst.args[0].ty.kind == TypeKind.FLOAT:
                result = args[0]
            else:
                result = ir.Constant(LLVM_FLOAT, 0.0)
            self._store_value(inst.dest, result, values)
            return

        # --- String methods (lowered as Call with obj as first arg) ---
        # Canonical LLVM type signatures for string methods.
        # MIR types are unreliable in cross-module compilation, so we
        # hardcode the expected types and coerce args to match.
        ST = LLVM_STRING  # {i8*, i64}
        IT = LLVM_INT  # i64
        BT = LLVM_BOOL  # i1
        LT = LLVM_LIST  # {i8*, i64, i64, i64}
        _str_method_sig: dict[str, tuple[str, list[Any], Any]] = {
            # method: (runtime_name, [param_types], return_type)
            "char_at": ("__mn_str_char_at", [ST, IT], ST),
            "byte_at": ("__mn_str_byte_at", [ST, IT], IT),
            "substr": ("__mn_str_substr", [ST, IT, IT], ST),
            "starts_with": ("__mn_str_starts_with", [ST, ST], BT),
            "ends_with": ("__mn_str_ends_with", [ST, ST], BT),
            "find": ("__mn_str_find", [ST, ST], IT),
            "contains": ("__mn_str_contains", [ST, ST], BT),
            "trim": ("__mn_str_trim", [ST], ST),
            "trim_start": ("__mn_str_trim_start", [ST], ST),
            "trim_end": ("__mn_str_trim_end", [ST], ST),
            "to_upper": ("__mn_str_to_upper", [ST], ST),
            "to_lower": ("__mn_str_to_lower", [ST], ST),
            "split": ("__mn_str_split", [ST, ST], LT),
            "replace": ("__mn_str_replace", [ST, ST, ST], ST),
        }
        if (
            fn_name in _str_method_sig
            and fn_name not in self._functions
            and inst.args
            and inst.args[0].ty.kind == TypeKind.STRING
        ):
            rt_name, param_types, ret_type = _str_method_sig[fn_name]
            if len(args) == len(param_types):
                rt_fn = self._declare_runtime_fn(rt_name, ret_type, param_types)
                # Coerce args to match the canonical signature
                coerced = _coerce_args(builder, args, param_types, name)
                result = builder.call(rt_fn, coerced, name=name)
                self._store_value(inst.dest, result, values)
                return

        # Some / Ok / Err
        if fn_name == "Some" and args:
            inner_ty = args[0].type
            opt_ty = _option_llvm_type(inner_ty)
            result = ir.Constant(opt_ty, ir.Undefined)
            result = builder.insert_value(result, ir.Constant(LLVM_BOOL, 1), 0, name=f"{name}.tag")
            result = builder.insert_value(result, args[0], 1, name=name)
            self._store_value(inst.dest, result, values)
            return

        if fn_name == "Ok" and args:
            # For Ok, we need a Result type. Use {i1, {T, i8*}} as default
            ok_ty = args[0].type
            res_ty = _result_llvm_type(ok_ty, LLVM_PTR)
            result = ir.Constant(res_ty, ir.Undefined)
            result = builder.insert_value(result, ir.Constant(LLVM_BOOL, 1), 0, name=f"{name}.tag")
            result = builder.insert_value(result, args[0], [1, 0], name=name)
            self._store_value(inst.dest, result, values)
            return

        if fn_name == "Err" and args:
            err_ty = args[0].type
            res_ty = _result_llvm_type(LLVM_PTR, err_ty)
            result = ir.Constant(res_ty, ir.Undefined)
            result = builder.insert_value(result, ir.Constant(LLVM_BOOL, 0), 0, name=f"{name}.tag")
            result = builder.insert_value(result, args[0], [1, 1], name=name)
            self._store_value(inst.dest, result, values)
            return

        # --- Map iteration via __iter_has_next / __iter_next ---
        if fn_name == "__iter_has_next" and inst.args and inst.args[0].ty.kind == TypeKind.MAP:
            # For maps: create an iterator if not already created, then check
            # We store map iterators in a dict keyed by the map SSA value name
            map_val = args[0]
            iter_name = f"_map_iter_{inst.args[0].name}"
            if iter_name not in values:
                # Create iterator
                map_iter = builder.call(self._rt_map_iter_new(), [map_val], name=iter_name)
                values[iter_name] = map_iter
                # Allocate key/val output pointers
                key_out = builder.alloca(LLVM_PTR, name=f"{iter_name}.kout")
                val_out = builder.alloca(LLVM_PTR, name=f"{iter_name}.vout")
                values[f"{iter_name}.kout"] = key_out
                values[f"{iter_name}.vout"] = val_out
            map_iter = values[iter_name]
            key_out = values[f"{iter_name}.kout"]
            val_out = values[f"{iter_name}.vout"]
            result_i64 = builder.call(
                self._rt_map_iter_next(), [map_iter, key_out, val_out], name=f"{name}.i64"
            )
            result = builder.trunc(result_i64, LLVM_BOOL, name=name)
            self._store_value(inst.dest, result, values)
            return

        if fn_name == "__iter_next" and inst.args and inst.args[0].ty.kind == TypeKind.MAP:
            # Return the key from the last __iter_has_next call
            iter_name = f"_map_iter_{inst.args[0].name}"
            key_out = values.get(f"{iter_name}.kout")
            if key_out:
                key_ptr = builder.load(key_out, name=f"{name}.kptr")
                # Default: load as the dest type
                elem_ty = self._resolve_mir_type(inst.dest.ty)
                typed = builder.bitcast(key_ptr, elem_ty.as_pointer(), name=f"{name}.typed")
                result = builder.load(typed, name=name)
            else:
                result = ir.Constant(LLVM_INT, 0)
            self._store_value(inst.dest, result, values)
            return

        # --- Stream iteration via __iter_has_next / __iter_next ---
        if fn_name == "__iter_has_next" and inst.args and inst.args[0].ty.kind == TypeKind.STREAM:
            stream_val = args[0]
            iter_name = f"_stream_iter_{inst.args[0].name}"
            if f"{iter_name}.out" not in values:
                # Allocate output buffer for stream_next
                out_alloca = builder.alloca(LLVM_INT, name=f"{iter_name}.out")
                values[f"{iter_name}.out"] = out_alloca
            out_alloca = values[f"{iter_name}.out"]
            out_ptr = builder.bitcast(out_alloca, LLVM_PTR)
            result_i64 = builder.call(
                self._rt_stream_next(), [stream_val, out_ptr], name=f"{name}.i64"
            )
            result = builder.trunc(result_i64, LLVM_BOOL, name=name)
            self._store_value(inst.dest, result, values)
            return

        if fn_name == "__iter_next" and inst.args and inst.args[0].ty.kind == TypeKind.STREAM:
            iter_name = f"_stream_iter_{inst.args[0].name}"
            out_alloca = values.get(f"{iter_name}.out")
            if out_alloca:
                elem_ty = self._resolve_mir_type(inst.dest.ty)
                if isinstance(elem_ty, ir.VoidType):
                    result = ir.Constant(LLVM_INT, 0)
                else:
                    typed_ptr = builder.bitcast(
                        out_alloca, elem_ty.as_pointer(), name=f"{name}.tptr"
                    )
                    result = builder.load(typed_ptr, name=name)
            else:
                result = ir.Constant(LLVM_INT, 0)
            self._store_value(inst.dest, result, values)
            return

        # --- User-defined function call ---
        if fn_name in self._functions:
            target_fn = self._functions[fn_name]
            # Coerce argument types to match function signature
            expected_types = list(target_fn.function_type.args)
            args = _coerce_args(builder, args[: len(expected_types)], expected_types, name)
            # Check if return type is void
            if isinstance(target_fn.function_type.return_type, ir.VoidType):
                builder.call(target_fn, args)
                self._store_value(inst.dest, ir.Constant(LLVM_BOOL, 0), values)
            else:
                result = builder.call(target_fn, args, name=name)
                self._store_value(inst.dest, result, values)
            return

        # --- Runtime function lookup ---
        if fn_name in self._runtime_fns:
            target_fn = self._runtime_fns[fn_name]
            if isinstance(target_fn.function_type.return_type, ir.VoidType):
                builder.call(target_fn, args)
                self._store_value(inst.dest, ir.Constant(LLVM_BOOL, 0), values)
            else:
                result = builder.call(target_fn, args, name=name)
                self._store_value(inst.dest, result, values)
            return

        # Unknown function — emit a call to an extern with matching name
        # Use MIR semantic types for parameter declaration (not LLVM value types,
        # which may lose info after field extraction etc.)
        param_types = []
        for i, a in enumerate(inst.args):
            mir_ty = self._resolve_mir_type(a.ty)
            if mir_ty == LLVM_PTR and i < len(args) and args[i].type != LLVM_PTR:
                # MIR type was UNKNOWN (resolved to i8*) but we have a concrete LLVM value;
                # use the actual LLVM type as fallback.
                param_types.append(args[i].type)
            else:
                param_types.append(mir_ty)
        ret_ty = self._resolve_mir_type(inst.dest.ty)
        fn_ty = ir.FunctionType(ret_ty, param_types)
        extern_fn = ir.Function(self.module, fn_ty, name=fn_name)
        self._functions[fn_name] = extern_fn
        coerced = _coerce_args(builder, args, param_types, name)
        if isinstance(ret_ty, ir.VoidType):
            builder.call(extern_fn, coerced)
            self._store_value(inst.dest, ir.Constant(LLVM_BOOL, 0), values)
        else:
            result = builder.call(extern_fn, coerced, name=name)
            self._store_value(inst.dest, result, values)

    def _emit_printf(self, builder: Any, fmt: str, args: list[Any]) -> None:
        """Emit a printf call with the given format string and arguments."""
        printf_fn = self._get_printf()
        fmt_gv = self._get_fmt_string(fmt)
        zero = ir.Constant(LLVM_INT, 0)
        fmt_ptr = builder.gep(fmt_gv, [zero, zero], inbounds=True)
        builder.call(printf_fn, [fmt_ptr] + args)

    # --- ExternCall ---

    def _emit_extern_call(self, inst: ExternCall, builder: Any, values: dict[str, Any]) -> None:
        args = [self._get_value(a, values) for a in inst.args]
        name = self._val_name(inst.dest)
        full_name = f"{inst.module}__{inst.fn_name}" if inst.module else inst.fn_name

        if full_name in self._functions:
            target_fn = self._functions[full_name]
        elif full_name in self._runtime_fns:
            target_fn = self._runtime_fns[full_name]
        else:
            # Auto-declare — prefer MIR semantic types over LLVM value types
            param_types = []
            for i, a in enumerate(inst.args):
                mir_ty = self._resolve_mir_type(a.ty)
                if mir_ty == LLVM_PTR and i < len(args) and args[i].type != LLVM_PTR:
                    param_types.append(args[i].type)
                else:
                    param_types.append(mir_ty)
            ret_ty = self._resolve_mir_type(inst.dest.ty)
            fn_ty = ir.FunctionType(ret_ty, param_types)
            target_fn = ir.Function(self.module, fn_ty, name=full_name)
            target_fn.linkage = "external"
            self._functions[full_name] = target_fn

        if isinstance(target_fn.function_type.return_type, ir.VoidType):
            builder.call(target_fn, args)
            self._store_value(inst.dest, ir.Constant(LLVM_BOOL, 0), values)
        else:
            result = builder.call(target_fn, args, name=name)
            self._store_value(inst.dest, result, values)

    # --- Return ---

    def _emit_return(self, inst: Return, builder: Any, values: dict[str, Any], func: Any) -> None:
        if inst.val is not None:
            val = self._get_value(inst.val, values)
            # Coerce return value to match function return type
            expected_ret = func.function_type.return_type
            if val.type != expected_ret and not isinstance(expected_ret, ir.VoidType):
                val = _coerce_arg(builder, val, expected_ret, "ret.c")
            builder.ret(val)
        else:
            builder.ret_void()

    # --- Jump ---

    def _emit_jump(self, inst: Jump, builder: Any, llvm_blocks: dict[str, Any]) -> None:
        target = llvm_blocks[inst.target]
        builder.branch(target)

    # --- Branch ---

    def _emit_branch(
        self, inst: Branch, builder: Any, values: dict[str, Any], llvm_blocks: dict[str, Any]
    ) -> None:
        cond = self._get_value(inst.cond, values)
        true_block = llvm_blocks[inst.true_block]
        false_block = llvm_blocks[inst.false_block]
        # Ensure the condition is i1
        if hasattr(cond, "type") and cond.type != LLVM_BOOL:
            if isinstance(cond.type, (ir.LiteralStructType, ir.ArrayType)):
                # Struct/array → i64 via memory, then compare != 0
                tmp = builder.alloca(cond.type, name="br.cond.tmp")
                builder.store(cond, tmp)
                int_ptr = builder.bitcast(tmp, LLVM_INT.as_pointer(), name="br.cond.iptr")
                cond = builder.load(int_ptr, name="br.cond.ival")
                cond = builder.icmp_signed("!=", cond, ir.Constant(LLVM_INT, 0), name="br.cond")
            elif isinstance(cond.type, ir.PointerType):
                cond = builder.ptrtoint(cond, LLVM_INT, name="br.cond.i")
                cond = builder.icmp_signed("!=", cond, ir.Constant(LLVM_INT, 0), name="br.cond")
            else:
                cond = builder.icmp_signed("!=", cond, ir.Constant(cond.type, 0), name="br.cond")
        builder.cbranch(cond, true_block, false_block)

    # --- Switch ---

    def _emit_switch(
        self, inst: Switch, builder: Any, values: dict[str, Any], llvm_blocks: dict[str, Any]
    ) -> None:
        tag = self._get_value(inst.tag, values)
        default_block = llvm_blocks[inst.default_block]
        switch = builder.switch(tag, default_block)
        # Determine which enum this switch is on (from the tag value's MIR type)
        enum_name = inst.tag.ty.type_info.name if inst.tag.ty else ""
        seen_tags: set[int] = set()
        for case_val, case_lbl in inst.cases:
            if isinstance(case_val, str) and not case_val.lstrip("-").isdigit():
                tag_int = self._resolve_enum_variant_tag(case_val, enum_name)
                case_const = ir.Constant(tag.type, tag_int)
            else:
                case_const = ir.Constant(tag.type, int(case_val))
            # Skip duplicate case values (LLVM doesn't allow them)
            tag_val = case_const.constant
            if tag_val in seen_tags:
                continue
            seen_tags.add(tag_val)
            switch.add_case(case_const, llvm_blocks[case_lbl])

    # --- StructInit ---

    def _emit_struct_init(self, inst: StructInit, builder: Any, values: dict[str, Any]) -> None:
        struct_name = inst.struct_type.type_info.name
        name = self._val_name(inst.dest)

        if struct_name in self._struct_types:
            llvm_ty = self._struct_types[struct_name]
            field_names = self._struct_fields.get(struct_name, [])
            boxed = self._boxed_struct_fields.get(struct_name, set())
            result = ir.Constant(llvm_ty, ir.Undefined)
            for field_name, field_val in inst.fields:
                val = self._get_value(field_val, values)
                if field_name in field_names:
                    idx = field_names.index(field_name)
                else:
                    # Positional fallback
                    idx = inst.fields.index((field_name, field_val))
                if idx in boxed:
                    # Auto-boxed recursive field: heap-allocate and store pointer
                    malloc_fn = self._rt_malloc()
                    alloc_size = ir.Constant(LLVM_INT, _approx_type_size(val.type))
                    raw_ptr = builder.call(malloc_fn, [alloc_size], name=f"{name}.box.{idx}")
                    typed_box = builder.bitcast(
                        raw_ptr, val.type.as_pointer(), name=f"{name}.box.{idx}.t"
                    )
                    builder.store(val, typed_box)
                    val = raw_ptr  # Store the i8* pointer in the struct field
                else:
                    # Coerce value type to match struct field type
                    expected_ty = llvm_ty.elements[idx]
                    if val.type != expected_ty:
                        val = _coerce_arg(builder, val, expected_ty, f"{name}.c{idx}")
                result = builder.insert_value(result, val, idx, name=f"{name}.f{idx}")
        else:
            # Unknown struct — build a literal struct from fields
            field_vals = [self._get_value(fv, values) for _, fv in inst.fields]
            if field_vals:
                field_types = [v.type for v in field_vals]
                llvm_ty = ir.LiteralStructType(field_types)
                result = ir.Constant(llvm_ty, ir.Undefined)
                for i, fv in enumerate(field_vals):
                    result = builder.insert_value(result, fv, i, name=f"{name}.f{i}")
            else:
                result = ir.Constant(LLVM_PTR, None)

        self._store_value(inst.dest, result, values)

    # --- FieldGet ---

    def _emit_field_get(self, inst: FieldGet, builder: Any, values: dict[str, Any]) -> None:
        obj = self._get_value(inst.obj, values)
        name = self._val_name(inst.dest)
        obj_type_name = inst.obj.ty.type_info.name

        # Cross-module coercion: if obj is a pointer but should be a struct,
        # bitcast to struct pointer and load
        if isinstance(obj.type, ir.PointerType) and not isinstance(obj.type, ir.LiteralStructType):
            struct_ty = self._struct_types.get(obj_type_name)
            # Try suffix match for finding the struct type
            if struct_ty is None:
                for sname, stype in self._struct_types.items():
                    if sname.endswith("__" + obj_type_name):
                        struct_ty = stype
                        obj_type_name = sname
                        break
            if struct_ty is not None:
                typed_ptr = builder.bitcast(obj, struct_ty.as_pointer(), name=f"{name}.sptr")
                obj = builder.load(typed_ptr, name=f"{name}.sval")

        # Fallback 1: try suffix match for cross-module structs (e.g. "Token" → "lexer__Token")
        if obj_type_name not in self._struct_fields:
            for sname in self._struct_fields:
                if sname.endswith("__" + obj_type_name) or sname == obj_type_name:
                    obj_type_name = sname
                    break

        # Fallback 2: reverse-lookup struct by LLVM type identity
        if obj_type_name not in self._struct_fields:
            for sname, stype in self._struct_types.items():
                if stype == obj.type and sname in self._struct_fields:
                    obj_type_name = sname
                    break

        if obj_type_name in self._struct_fields:
            field_names = self._struct_fields[obj_type_name]
            if inst.field_name in field_names:
                idx = field_names.index(inst.field_name)
                result = builder.extract_value(obj, idx, name=name)
                # If this field is auto-boxed, dereference the pointer
                boxed = self._boxed_struct_fields.get(obj_type_name, set())
                if idx in boxed:
                    # Resolve the actual type for the field from MIR type info
                    actual_type = self._resolve_field_type_for_unbox(obj_type_name, inst.field_name)
                    if actual_type is not None and actual_type != LLVM_PTR:
                        typed_ptr = builder.bitcast(
                            result, actual_type.as_pointer(), name=f"{name}.unbox"
                        )
                        result = builder.load(typed_ptr, name=f"{name}.val")
            else:
                result = ir.Constant(LLVM_PTR, None)
        else:
            # Try index 0 as fallback
            try:
                result = builder.extract_value(obj, 0, name=name)
            except Exception:
                result = ir.Constant(LLVM_PTR, None)

        self._store_value(inst.dest, result, values)

    # --- FieldSet ---

    def _emit_field_set(self, inst: FieldSet, builder: Any, values: dict[str, Any]) -> None:
        obj = self._get_value(inst.obj, values)
        val = self._get_value(inst.val, values)
        obj_type_name = inst.obj.ty.type_info.name

        # Suffix match for cross-module structs
        if obj_type_name not in self._struct_fields:
            for sname in self._struct_fields:
                if sname.endswith("__" + obj_type_name) or sname == obj_type_name:
                    obj_type_name = sname
                    break

        if obj_type_name in self._struct_fields:
            field_names = self._struct_fields[obj_type_name]
            if inst.field_name in field_names:
                idx = field_names.index(inst.field_name)
                boxed = self._boxed_struct_fields.get(obj_type_name, set())
                if idx in boxed:
                    # Auto-boxed recursive field: heap-allocate and store pointer
                    name = f"{obj_type_name}.{inst.field_name}"
                    malloc_fn = self._rt_malloc()
                    alloc_size = ir.Constant(LLVM_INT, _approx_type_size(val.type))
                    raw_ptr = builder.call(malloc_fn, [alloc_size], name=f"{name}.box")
                    typed_box = builder.bitcast(
                        raw_ptr, val.type.as_pointer(), name=f"{name}.box.t"
                    )
                    builder.store(val, typed_box)
                    val = raw_ptr  # Store the i8* pointer in the struct field
                else:
                    # Coerce value type to match the struct field type
                    if isinstance(obj.type, ir.LiteralStructType) and idx < len(obj.type.elements):
                        field_ty = obj.type.elements[idx]
                        if val.type != field_ty:
                            val = _coerce_arg(
                                builder,
                                val,
                                field_ty,
                                f"{inst.obj.ty.type_info.name}.{inst.field_name}.c",
                            )
                result = builder.insert_value(obj, val, idx)
                # Update the value in the map (functional update for SSA)
                # Also persist to the alloca for cross-block dominance
                self._store_value(inst.obj, result, values)

    # --- ListInit ---

    def _emit_list_init(self, inst: ListInit, builder: Any, values: dict[str, Any]) -> None:
        name = self._val_name(inst.dest)
        elem_llvm_ty = self._resolve_mir_type(inst.elem_type)

        # If MIR elem_type resolved to generic i8* but we have actual elements,
        # use the concrete LLVM type of the first element instead.
        if inst.elements and elem_llvm_ty == LLVM_PTR:
            first_val = self._get_value(inst.elements[0], values)
            if first_val.type != LLVM_PTR:
                elem_llvm_ty = first_val.type

        # If still generic i8*, try inferring from the dest type's type args
        # (e.g. List<String> has args=[TypeInfo(kind=STRING)] → elem is {i8*, i64})
        if elem_llvm_ty == LLVM_PTR and inst.dest.ty.type_info.args:
            inferred = self._resolve_mir_type(MIRType(inst.dest.ty.type_info.args[0]))
            if inferred != LLVM_PTR:
                elem_llvm_ty = inferred

        elem_size = _approx_type_size(elem_llvm_ty)

        # Call __mn_list_new(elem_size)
        fn_new = self._rt_list_new()
        list_val = builder.call(fn_new, [ir.Constant(LLVM_INT, elem_size)], name=f"{name}.new")

        if inst.elements:
            fn_push = self._rt_list_push()
            # Alloca for the list struct (push needs a pointer)
            list_ptr = builder.alloca(LLVM_LIST, name=f"{name}.ptr")
            builder.store(list_val, list_ptr)

            for i, elem in enumerate(inst.elements):
                elem_val = self._get_value(elem, values)
                # Use the actual LLVM type of the element value for the alloca
                actual_elem_ty = elem_val.type if elem_val.type != LLVM_PTR else elem_llvm_ty
                elem_alloca = builder.alloca(actual_elem_ty, name=f"{name}.e{i}")
                builder.store(elem_val, elem_alloca)
                elem_ptr = builder.bitcast(elem_alloca, ir.IntType(8).as_pointer())
                builder.call(fn_push, [list_ptr, elem_ptr])

            list_val = builder.load(list_ptr, name=name)

        self._store_value(inst.dest, list_val, values)

    # --- ListPush ---

    def _emit_list_push(self, inst: ListPush, builder: Any, values: dict[str, Any]) -> None:
        """Emit list.push(element) — stores list to alloca, pushes, loads back."""
        elem_val = self._get_value(inst.element, values)
        name = self._val_name(inst.dest)

        # Read list from the ROOT alloca when available.  In if/else chains the
        # MIR lowerer creates a push chain (t0→t95→t103→…) where each push's
        # input is the previous push's output.  But only one branch executes per
        # iteration, so intermediate allocas (a.t95, a.t103, …) may be stale or
        # uninitialized.  The root alloca (a.t0) is always up-to-date because
        # every push writes back to it.
        src_name = inst.list_val.name
        root_name = self._list_roots.get(src_name, src_name)
        if root_name in self._fn_allocas:
            list_val = builder.load(self._fn_allocas[root_name], name=f"{name}.rl")
        else:
            list_val = self._get_value(inst.list_val, values)

        fn_push = self._rt_list_push()

        # Cross-module coercion: list value might be wrong type
        if list_val.type != LLVM_LIST:
            list_val = _coerce_arg(builder, list_val, LLVM_LIST, f"{name}.lc")

        # Store list to alloca so push can mutate it
        list_ptr = builder.alloca(LLVM_LIST, name=f"{name}.lptr")
        builder.store(list_val, list_ptr)

        # Store element to alloca, bitcast to i8*
        elem_alloca = builder.alloca(elem_val.type, name=f"{name}.eptr")
        builder.store(elem_val, elem_alloca)
        elem_ptr = builder.bitcast(elem_alloca, ir.IntType(8).as_pointer())

        builder.call(fn_push, [list_ptr, elem_ptr])

        # Load updated list
        updated = builder.load(list_ptr, name=name)
        self._store_value(inst.dest, updated, values)

        # Write-back: store updated list to the ROOT list alloca so that
        # loop back-edges and cross-branch reads see the mutation.
        # The lowerer chains pushes (t0→t75→t83→...) via _update_var,
        # so we track each push dest back to the original list variable.
        src_name = inst.list_val.name
        root_name = self._list_roots.get(src_name, src_name)
        self._list_roots[inst.dest.name] = root_name
        # Write back to root alloca and immediate source alloca
        for target_name in {root_name, src_name}:
            if target_name in self._fn_allocas:
                target_alloca = self._fn_allocas[target_name]
                try:
                    val = updated
                    if val.type != target_alloca.type.pointee:
                        val = _coerce_arg(builder, val, target_alloca.type.pointee, f"{name}.wb")
                    builder.store(val, target_alloca)
                except Exception:
                    pass

    # --- IndexGet ---

    def _emit_index_get(self, inst: IndexGet, builder: Any, values: dict[str, Any]) -> None:
        obj = self._get_value(inst.obj, values)
        index = self._get_value(inst.index, values)
        name = self._val_name(inst.dest)
        obj_kind = inst.obj.ty.kind

        # If the MIR type is UNKNOWN but the LLVM value is a list struct,
        # treat it as a list access (cross-module FieldGet loses type info).
        if obj_kind == TypeKind.UNKNOWN and hasattr(obj, "type") and obj.type == LLVM_LIST:
            obj_kind = TypeKind.LIST

        if obj_kind == TypeKind.LIST:
            fn_get = self._rt_list_get()
            list_val = obj
            # Coerce i8* → LLVM_LIST if needed (cross-module type resolution)
            if list_val.type != LLVM_LIST:
                list_val = _coerce_arg(builder, list_val, LLVM_LIST, f"{name}.lc")
            list_ptr = builder.alloca(LLVM_LIST, name=f"{name}.lptr")
            builder.store(list_val, list_ptr)
            # Ensure index is i64 (cross-module lowering may resolve as i8*)
            if index.type != LLVM_INT:
                index = builder.ptrtoint(index, LLVM_INT, name=f"{name}.idx")
            raw_ptr = builder.call(fn_get, [list_ptr, index], name=f"{name}.raw")
            # Bitcast to element type pointer and load
            elem_ty = self._resolve_mir_type(inst.dest.ty)
            if elem_ty == LLVM_PTR and inst.dest.ty.kind == TypeKind.UNKNOWN:
                # Unknown element type — return raw pointer for downstream coercion
                result = raw_ptr
            else:
                typed_ptr = builder.bitcast(raw_ptr, elem_ty.as_pointer(), name=f"{name}.tptr")
                result = builder.load(typed_ptr, name=name)
        elif obj_kind == TypeKind.STRING:
            # String indexing: __mn_str_byte_at or char access
            fn = self._declare_runtime_fn("__mn_str_byte_at", LLVM_INT, [LLVM_STRING, LLVM_INT])
            result = builder.call(fn, [obj, index], name=name)
        elif obj_kind == TypeKind.MAP:
            # Map indexing: __mn_map_get(map, &key) -> val_ptr
            key_alloca = builder.alloca(index.type, name=f"{name}.key")
            builder.store(index, key_alloca)
            key_ptr = builder.bitcast(key_alloca, LLVM_PTR)
            raw_ptr = builder.call(self._rt_map_get(), [obj, key_ptr], name=f"{name}.raw")
            elem_ty = self._resolve_mir_type(inst.dest.ty)
            typed_ptr = builder.bitcast(raw_ptr, elem_ty.as_pointer(), name=f"{name}.tptr")
            result = builder.load(typed_ptr, name=name)
        else:
            result = ir.Constant(LLVM_PTR, None)

        self._store_value(inst.dest, result, values)

    # --- IndexSet ---

    def _emit_index_set(self, inst: IndexSet, builder: Any, values: dict[str, Any]) -> None:
        obj = self._get_value(inst.obj, values)
        index = self._get_value(inst.index, values)
        val = self._get_value(inst.val, values)

        if inst.obj.ty.kind == TypeKind.LIST:
            fn_get = self._rt_list_get()
            list_ptr = builder.alloca(LLVM_LIST, name="idxset.lptr")
            builder.store(obj, list_ptr)
            raw_ptr = builder.call(fn_get, [list_ptr, index], name="idxset.raw")
            elem_ty = val.type
            typed_ptr = builder.bitcast(raw_ptr, elem_ty.as_pointer(), name="idxset.tptr")
            builder.store(val, typed_ptr)
        elif inst.obj.ty.kind == TypeKind.MAP:
            # Map assignment: __mn_map_set(map, &key, &val)
            key_alloca = builder.alloca(index.type, name="idxset.key")
            builder.store(index, key_alloca)
            key_ptr = builder.bitcast(key_alloca, LLVM_PTR)
            val_alloca = builder.alloca(val.type, name="idxset.val")
            builder.store(val, val_alloca)
            val_ptr = builder.bitcast(val_alloca, LLVM_PTR)
            builder.call(self._rt_map_set(), [obj, key_ptr, val_ptr])

    # --- MapInit ---

    def _emit_map_init(self, inst: MapInit, builder: Any, values: dict[str, Any]) -> None:
        name = self._val_name(inst.dest)

        # Determine key/val sizes and key type tag
        if inst.pairs:
            first_key = self._get_value(inst.pairs[0][0], values)
            first_val = self._get_value(inst.pairs[0][1], values)
            key_size = self._llvm_type_size(first_key.type)
            val_size = self._llvm_type_size(first_val.type)
            key_type_tag = self._map_key_type_tag(inst.key_type)
        else:
            key_size, val_size, key_type_tag = 8, 8, 0

        # Create map
        map_ptr = builder.call(
            self._rt_map_new(),
            [
                ir.Constant(LLVM_INT, key_size),
                ir.Constant(LLVM_INT, val_size),
                ir.Constant(LLVM_INT, key_type_tag),
            ],
            name=name,
        )

        # Insert each pair
        for k_val, v_val in inst.pairs:
            k = self._get_value(k_val, values)
            v = self._get_value(v_val, values)
            k_alloca = builder.alloca(k.type, name=f"{name}.k")
            builder.store(k, k_alloca)
            k_ptr = builder.bitcast(k_alloca, LLVM_PTR)
            v_alloca = builder.alloca(v.type, name=f"{name}.v")
            builder.store(v, v_alloca)
            v_ptr = builder.bitcast(v_alloca, LLVM_PTR)
            builder.call(self._rt_map_set(), [map_ptr, k_ptr, v_ptr])

        self._store_value(inst.dest, map_ptr, values)

    # --- EnumInit ---

    def _resolve_enum_name(self, raw_name: str) -> str:
        """Resolve an enum name to its canonical key in _enum_types, handling cross-module prefixes."""
        if raw_name in self._enum_types:
            return raw_name
        for ename in self._enum_types:
            if ename.endswith("__" + raw_name):
                return ename
        return raw_name

    def _emit_enum_init(self, inst: EnumInit, builder: Any, values: dict[str, Any]) -> None:
        name = self._val_name(inst.dest)
        enum_name = self._resolve_enum_name(inst.enum_type.type_info.name)

        if enum_name in self._enum_types:
            enum_ty, tag_map, _ = self._enum_types[enum_name]
            tag_val = tag_map.get(inst.variant, 0)
            boxed = self._boxed_enum_fields.get(enum_name, set())

            # Alloca the enum, store tag
            enum_ptr = builder.alloca(enum_ty, name=f"{name}.ptr")
            tag_ptr = builder.gep(
                enum_ptr,
                [ir.Constant(LLVM_I32, 0), ir.Constant(LLVM_I32, 0)],
                inbounds=True,
                name=f"{name}.tag.ptr",
            )
            builder.store(ir.Constant(LLVM_I32, tag_val), tag_ptr)

            # Store payload fields
            if inst.payload:
                payload_ptr = builder.gep(
                    enum_ptr,
                    [ir.Constant(LLVM_I32, 0), ir.Constant(LLVM_I32, 1)],
                    inbounds=True,
                    name=f"{name}.pay.ptr",
                )
                payload_i8_ptr = builder.bitcast(
                    payload_ptr, ir.IntType(8).as_pointer(), name=f"{name}.pay.i8"
                )
                offset = 0
                for i, pval in enumerate(inst.payload):
                    val = self._get_value(pval, values)

                    if (inst.variant, i) in boxed:
                        # Auto-boxed recursive field: heap-allocate and store pointer
                        field_align = 8  # pointer alignment
                        rem = offset % field_align
                        if rem != 0:
                            offset += field_align - rem
                        malloc_fn = self._rt_malloc()
                        alloc_size = ir.Constant(LLVM_INT, _approx_type_size(val.type))
                        raw_ptr = builder.call(malloc_fn, [alloc_size], name=f"{name}.box.{i}")
                        typed_box = builder.bitcast(
                            raw_ptr, val.type.as_pointer(), name=f"{name}.box.{i}.t"
                        )
                        builder.store(val, typed_box)
                        dest_ptr = builder.gep(
                            payload_i8_ptr,
                            [ir.Constant(LLVM_INT, offset)],
                            name=f"{name}.pay.{i}",
                        )
                        ptr_dest = builder.bitcast(dest_ptr, LLVM_PTR.as_pointer())
                        builder.store(raw_ptr, ptr_dest)
                        offset += 8  # pointer size
                    else:
                        # Normal inline store
                        field_align = _type_alignment(val.type)
                        rem = offset % field_align
                        if rem != 0:
                            offset += field_align - rem
                        dest_ptr = builder.gep(
                            payload_i8_ptr,
                            [ir.Constant(LLVM_INT, offset)],
                            name=f"{name}.pay.{i}",
                        )
                        typed_ptr = builder.bitcast(dest_ptr, val.type.as_pointer())
                        builder.store(val, typed_ptr)
                        offset += _approx_type_size(val.type)

            result = builder.load(enum_ptr, name=name)
        else:
            # Fallback: tag-only i32
            result = ir.Constant(LLVM_I32, 0)

        self._store_value(inst.dest, result, values)

    # --- EnumTag ---

    def _emit_enum_tag(self, inst: EnumTag, builder: Any, values: dict[str, Any]) -> None:
        enum_val = self._get_value(inst.enum_val, values)
        name = self._val_name(inst.dest)
        # For non-struct types (e.g., Int in match expressions), use the value directly
        if isinstance(enum_val.type, ir.IntType) and not isinstance(
            enum_val.type, ir.LiteralStructType
        ):
            result = enum_val
            # Truncate to i32 if needed (tags are i32)
            if enum_val.type.width != 32:
                result = (
                    builder.trunc(enum_val, LLVM_I32, name=name)
                    if enum_val.type.width > 32
                    else builder.zext(enum_val, LLVM_I32, name=name)
                )
        elif isinstance(enum_val.type, ir.LiteralStructType):
            result = builder.extract_value(enum_val, 0, name=name)
        elif isinstance(enum_val.type, ir.PointerType):
            # Value is a pointer (i8*) — resolve the actual enum struct type
            # from the MIR type info, bitcast, load, then extract tag.
            enum_struct_ty = self._resolve_enum_type_from_value(inst.enum_val)
            if enum_struct_ty is not None:
                typed_ptr = builder.bitcast(
                    enum_val, enum_struct_ty.as_pointer(), name=f"{name}.eptr"
                )
                loaded = builder.load(typed_ptr, name=f"{name}.loaded")
                result = builder.extract_value(loaded, 0, name=name)
            else:
                # Last resort: treat pointer as opaque tag
                result = builder.ptrtoint(enum_val, LLVM_I32, name=name)
        else:
            result = builder.extract_value(enum_val, 0, name=name)
        self._store_value(inst.dest, result, values)

    # --- EnumPayload ---

    def _emit_enum_payload(self, inst: EnumPayload, builder: Any, values: dict[str, Any]) -> None:
        enum_val = self._get_value(inst.enum_val, values)
        name = self._val_name(inst.dest)
        enum_name = inst.enum_val.ty.type_info.name

        # Look up enum type with suffix matching for cross-module enums
        resolved_enum_name = self._resolve_enum_name(enum_name)

        if resolved_enum_name in self._enum_types:
            _, _, variant_payloads = self._enum_types[resolved_enum_name]
            payload_types = variant_payloads.get(inst.variant, [])
            boxed = self._boxed_enum_fields.get(resolved_enum_name, set())

            # Alloca the enum, extract payload bytes, bitcast
            enum_ty = self._enum_types[resolved_enum_name][0]

            # If enum_val is a pointer (i8*), load the actual struct first
            if isinstance(enum_val.type, ir.PointerType):
                typed_ptr = builder.bitcast(enum_val, enum_ty.as_pointer(), name=f"{name}.cast")
                enum_val = builder.load(typed_ptr, name=f"{name}.loaded")

            # Use the value's actual LLVM type for the alloca (may differ from
            # the registered enum type when the value came from a function
            # parameter or cross-module boundary with a different type resolution).
            actual_ty = (
                enum_val.type if isinstance(enum_val.type, ir.LiteralStructType) else enum_ty
            )
            enum_ptr = builder.alloca(actual_ty, name=f"{name}.eptr")
            builder.store(enum_val, enum_ptr)
            payload_ptr = builder.gep(
                enum_ptr,
                [ir.Constant(LLVM_I32, 0), ir.Constant(LLVM_I32, 1)],
                inbounds=True,
                name=f"{name}.pptr",
            )

            if len(payload_types) == 1:
                is_boxed = (inst.variant, 0) in boxed
                if is_boxed:
                    # Boxed single field: load the pointer, then dereference
                    payload_i8 = builder.bitcast(
                        payload_ptr, LLVM_PTR.as_pointer(), name=f"{name}.bptr"
                    )
                    raw_ptr = builder.load(payload_i8, name=f"{name}.boxptr")
                    actual_type = self._resolve_mir_type(payload_types[0])
                    typed_unbox = builder.bitcast(
                        raw_ptr, actual_type.as_pointer(), name=f"{name}.unbox"
                    )
                    result = builder.load(typed_unbox, name=name)
                else:
                    target_ty = self._resolve_mir_type(payload_types[0])
                    payload_i8 = builder.bitcast(
                        payload_ptr, target_ty.as_pointer(), name=f"{name}.tptr"
                    )
                    result = builder.load(payload_i8, name=name)
            elif payload_types:
                # Multi-field payload: build a struct using LLVM_PTR for boxed fields
                field_tys: list[Any] = []
                for j, pt in enumerate(payload_types):
                    if (inst.variant, j) in boxed:
                        field_tys.append(LLVM_PTR)
                    else:
                        field_tys.append(self._resolve_mir_type(pt))
                payload_struct_ty = ir.LiteralStructType(field_tys)
                typed_ptr = builder.bitcast(
                    payload_ptr, payload_struct_ty.as_pointer(), name=f"{name}.sptr"
                )
                full_payload = builder.load(typed_ptr, name=f"{name}.full")
                idx = inst.payload_idx
                if idx < len(field_tys):
                    result = builder.extract_value(full_payload, idx, name=name)
                    # If this field is boxed, dereference the pointer
                    if (inst.variant, idx) in boxed:
                        actual_type = self._resolve_mir_type(payload_types[idx])
                        typed_unbox = builder.bitcast(
                            result, actual_type.as_pointer(), name=f"{name}.unbox"
                        )
                        result = builder.load(typed_unbox, name=f"{name}.val")
                else:
                    result = full_payload
            else:
                result = ir.Constant(LLVM_BOOL, 0)
        else:
            # Result/Option or unknown enum — extract payload by variant
            try:
                variant = inst.variant
                if variant == "Ok":
                    # Result<T, E>: {i1, {T, E}} → extract [1, 0]
                    result = builder.extract_value(enum_val, [1, 0], name=name)
                elif variant == "Err":
                    # Result<T, E>: {i1, {T, E}} → extract [1, 1]
                    result = builder.extract_value(enum_val, [1, 1], name=name)
                elif variant == "Some":
                    # Option<T>: {i1, T} → extract 1
                    result = builder.extract_value(enum_val, 1, name=name)
                else:
                    result = builder.extract_value(enum_val, 1, name=name)
            except Exception:
                result = ir.Constant(LLVM_PTR, None)

        self._store_value(inst.dest, result, values)

    # --- Option/Result wrappers ---

    def _emit_wrap_some(self, inst: WrapSome, builder: Any, values: dict[str, Any]) -> None:
        val = self._get_value(inst.val, values)
        name = self._val_name(inst.dest)
        opt_ty = _option_llvm_type(val.type)
        result = ir.Constant(opt_ty, ir.Undefined)
        result = builder.insert_value(result, ir.Constant(LLVM_BOOL, 1), 0, name=f"{name}.tag")
        result = builder.insert_value(result, val, 1, name=name)
        self._store_value(inst.dest, result, values)

    def _emit_wrap_none(self, inst: WrapNone, builder: Any, values: dict[str, Any]) -> None:
        opt_ty = self._resolve_mir_type(inst.ty)
        result = ir.Constant(opt_ty, None)
        self._store_value(inst.dest, result, values)

    def _emit_wrap_ok(self, inst: WrapOk, builder: Any, values: dict[str, Any]) -> None:
        val = self._get_value(inst.val, values)
        name = self._val_name(inst.dest)
        res_ty = _result_llvm_type(val.type, LLVM_PTR)
        result = ir.Constant(res_ty, ir.Undefined)
        result = builder.insert_value(result, ir.Constant(LLVM_BOOL, 1), 0, name=f"{name}.tag")
        result = builder.insert_value(result, val, [1, 0], name=name)
        self._store_value(inst.dest, result, values)

    def _emit_wrap_err(self, inst: WrapErr, builder: Any, values: dict[str, Any]) -> None:
        val = self._get_value(inst.val, values)
        name = self._val_name(inst.dest)
        res_ty = _result_llvm_type(LLVM_PTR, val.type)
        result = ir.Constant(res_ty, ir.Undefined)
        result = builder.insert_value(result, ir.Constant(LLVM_BOOL, 0), 0, name=f"{name}.tag")
        result = builder.insert_value(result, val, [1, 1], name=name)
        self._store_value(inst.dest, result, values)

    def _emit_unwrap(self, inst: Unwrap, builder: Any, values: dict[str, Any]) -> None:
        val = self._get_value(inst.val, values)
        name = self._val_name(inst.dest)
        result = builder.extract_value(val, 1, name=name)
        self._store_value(inst.dest, result, values)

    # --- InterpConcat ---

    def _emit_interp_concat(self, inst: InterpConcat, builder: Any, values: dict[str, Any]) -> None:
        name = self._val_name(inst.dest)

        if not inst.parts:
            result = self._make_string_constant(builder, "")
            self._store_value(inst.dest, result, values)
            return

        # Convert each part to string if needed, then chain-concat
        str_parts: list[Any] = []
        for part_val in inst.parts:
            val = self._get_value(part_val, values)
            part_kind = part_val.ty.kind
            if part_kind == TypeKind.STRING:
                str_parts.append(val)
            elif part_kind == TypeKind.INT:
                fn = self._rt_str_from_int()
                s = builder.call(fn, [val], name=f"{name}.i2s")
                str_parts.append(s)
            elif part_kind == TypeKind.FLOAT:
                fn = self._rt_str_from_float()
                s = builder.call(fn, [val], name=f"{name}.f2s")
                str_parts.append(s)
            elif part_kind == TypeKind.BOOL:
                fn = self._rt_str_from_bool()
                s = builder.call(fn, [val], name=f"{name}.b2s")
                str_parts.append(s)
            else:
                # Fallback: treat as int
                fn = self._rt_str_from_int()
                s = builder.call(fn, [val], name=f"{name}.x2s")
                str_parts.append(s)

        # Chain concatenation
        result = str_parts[0]
        concat_fn = self._rt_str_concat()
        for i, part in enumerate(str_parts[1:], 1):
            result = builder.call(concat_fn, [result, part], name=f"{name}.c{i}")

        self._store_value(inst.dest, result, values)

    # --- Agent operations ---

    def _emit_agent_spawn(self, inst: AgentSpawn, builder: Any, values: dict[str, Any]) -> None:
        name = self._val_name(inst.dest)
        # Create agent: mapanare_agent_new(name, handler, data, inbox_cap, outbox_cap)
        agent_name_str = self._make_string_constant(
            builder, inst.agent_type.type_info.name or "agent"
        )
        agent_name_ptr = builder.extract_value(agent_name_str, 0)
        null_ptr = ir.Constant(LLVM_PTR, None)
        cap = ir.Constant(LLVM_I32, 256)
        fn_new = self._rt_agent_new()
        agent_ptr = builder.call(
            fn_new, [agent_name_ptr, null_ptr, null_ptr, cap, cap], name=f"{name}.new"
        )
        # Spawn
        fn_spawn = self._rt_agent_spawn()
        builder.call(fn_spawn, [agent_ptr])
        self._store_value(inst.dest, agent_ptr, values)

    def _emit_agent_send(self, inst: AgentSend, builder: Any, values: dict[str, Any]) -> None:
        agent = self._get_value(inst.agent, values)
        val = self._get_value(inst.val, values)
        # Box the value: alloca, store, bitcast to i8*
        val_alloca = builder.alloca(val.type, name="send.box")
        builder.store(val, val_alloca)
        val_ptr = builder.bitcast(val_alloca, LLVM_PTR)
        fn_send = self._rt_agent_send()
        builder.call(fn_send, [agent, val_ptr])

    def _emit_agent_sync(
        self, inst: AgentSync, builder: Any, values: dict[str, Any], func: Any
    ) -> None:
        agent = self._get_value(inst.agent, values)
        name = self._val_name(inst.dest)
        # Alloca a pointer for the result
        out_ptr = builder.alloca(LLVM_PTR, name=f"{name}.out")
        fn_recv = self._rt_agent_recv_blocking()
        builder.call(fn_recv, [agent, out_ptr])
        raw_ptr = builder.load(out_ptr, name=f"{name}.raw")
        # Unbox: bitcast to target type pointer and load
        target_ty = self._resolve_mir_type(inst.dest.ty)
        if isinstance(target_ty, ir.VoidType):
            result = ir.Constant(LLVM_BOOL, 0)
        else:
            typed_ptr = builder.bitcast(raw_ptr, target_ty.as_pointer(), name=f"{name}.tptr")
            result = builder.load(typed_ptr, name=name)
        self._store_value(inst.dest, result, values)

    # --- Signal operations (C runtime) ---

    def _emit_signal_init(self, inst: SignalInit, builder: Any, values: dict[str, Any]) -> None:
        name = self._val_name(inst.dest)
        initial = self._get_value(inst.initial_val, values)
        val_size = _approx_type_size(initial.type)

        # Alloca the initial value so we can pass a pointer to __mn_signal_new
        val_alloca = builder.alloca(initial.type, name=f"{name}.init")
        builder.store(initial, val_alloca)
        val_ptr = builder.bitcast(val_alloca, LLVM_PTR)

        fn_new = self._rt_signal_new()
        sig_ptr = builder.call(
            fn_new,
            [val_ptr, ir.Constant(LLVM_INT, val_size)],
            name=f"{name}.sig",
        )
        self._store_value(inst.dest, sig_ptr, values)

    def _emit_signal_get(self, inst: SignalGet, builder: Any, values: dict[str, Any]) -> None:
        signal = self._get_value(inst.signal, values)
        name = self._val_name(inst.dest)
        target_ty = self._resolve_mir_type(inst.dest.ty)

        fn_get = self._rt_signal_get()
        raw_ptr = builder.call(fn_get, [signal], name=f"{name}.raw")

        if isinstance(target_ty, ir.VoidType):
            result = ir.Constant(LLVM_BOOL, 0)
        else:
            typed_ptr = builder.bitcast(raw_ptr, target_ty.as_pointer(), name=f"{name}.tptr")
            result = builder.load(typed_ptr, name=name)
        self._store_value(inst.dest, result, values)

    def _emit_signal_set(self, inst: SignalSet, builder: Any, values: dict[str, Any]) -> None:
        signal = self._get_value(inst.signal, values)
        val = self._get_value(inst.val, values)

        # Alloca value and pass pointer to __mn_signal_set
        val_alloca = builder.alloca(val.type, name="sig.set.val")
        builder.store(val, val_alloca)
        val_ptr = builder.bitcast(val_alloca, LLVM_PTR)

        fn_set = self._rt_signal_set()
        builder.call(fn_set, [signal, val_ptr])

    def _emit_signal_computed(
        self, inst: SignalComputed, builder: Any, values: dict[str, Any]
    ) -> None:
        name = self._val_name(inst.dest)

        # Get the compute function pointer
        compute_fn = self._functions.get(inst.compute_fn)
        if compute_fn is None:
            # Try to find it in the module
            for fn in self.module.functions:
                if fn.name == inst.compute_fn:
                    compute_fn = fn
                    break
        if compute_fn is not None:
            fn_ptr = builder.bitcast(compute_fn, LLVM_PTR)
        else:
            fn_ptr = ir.Constant(LLVM_PTR, None)

        # Build deps array
        n_deps = len(inst.deps)
        if n_deps > 0:
            deps_array_ty = ir.ArrayType(LLVM_PTR, n_deps)
            deps_alloca = builder.alloca(deps_array_ty, name=f"{name}.deps")
            for i, dep_val in enumerate(inst.deps):
                dep = self._get_value(dep_val, values)
                gep = builder.gep(
                    deps_alloca,
                    [ir.Constant(LLVM_INT, 0), ir.Constant(LLVM_INT, i)],
                    name=f"{name}.dep.{i}",
                )
                builder.store(dep, builder.bitcast(gep, LLVM_PTR.as_pointer()))
            deps_ptr = builder.bitcast(deps_alloca, LLVM_PTR)
        else:
            deps_ptr = ir.Constant(LLVM_PTR, None)

        fn_computed = self._rt_signal_computed()
        sig_ptr = builder.call(
            fn_computed,
            [
                fn_ptr,
                ir.Constant(LLVM_PTR, None),  # user_data
                deps_ptr,
                ir.Constant(LLVM_INT, n_deps),
                ir.Constant(LLVM_INT, inst.val_size),
            ],
            name=f"{name}.computed",
        )
        self._store_value(inst.dest, sig_ptr, values)

    def _emit_signal_subscribe(
        self, inst: SignalSubscribe, builder: Any, values: dict[str, Any]
    ) -> None:
        signal = self._get_value(inst.signal, values)
        subscriber = self._get_value(inst.subscriber, values)
        fn_sub = self._rt_signal_subscribe()
        builder.call(fn_sub, [signal, subscriber])

    # --- Closure operations ---

    def _emit_closure_create(
        self, inst: ClosureCreate, builder: Any, values: dict[str, Any]
    ) -> None:
        """Emit a closure: allocate env struct, store captures, build {fn_ptr, env_ptr}."""
        name = self._val_name(inst.dest)

        # Build the environment struct type from capture types
        cap_llvm_types = [self._resolve_mir_type(ct) for ct in inst.capture_types]

        if not cap_llvm_types:
            # No captures (shouldn't happen but handle gracefully)
            fn = self._functions.get(inst.fn_name)
            if fn is None:
                fn = ir.Constant(LLVM_PTR, None)
            fn_ptr = builder.bitcast(fn, LLVM_PTR, name=f"{name}.fnptr")
            env_ptr = ir.Constant(LLVM_PTR, None)
            closure = ir.Constant(LLVM_CLOSURE, ir.Undefined)
            closure = builder.insert_value(closure, fn_ptr, 0, name=f"{name}.c0")
            closure = builder.insert_value(closure, env_ptr, 1, name=name)
            self._store_value(inst.dest, closure, values)
            return

        env_struct_ty = ir.LiteralStructType(cap_llvm_types)

        # Allocate environment via __mn_alloc
        env_size = sum(self._llvm_type_size(t) for t in cap_llvm_types)
        # Ensure at least 8 bytes and round up to struct size
        env_size = max(env_size, 8)
        alloc_fn = self._declare_runtime_fn("__mn_alloc", LLVM_PTR, [LLVM_INT])
        env_raw = builder.call(alloc_fn, [ir.Constant(LLVM_INT, env_size)], name=f"{name}.env")
        env_typed = builder.bitcast(env_raw, env_struct_ty.as_pointer(), name=f"{name}.envp")

        # Store each captured value into the environment struct
        for i, cap_val in enumerate(inst.captures):
            llvm_val = self._get_value(cap_val, values)
            # Handle type mismatches (e.g., i64 into ptr-sized slot)
            expected_ty = cap_llvm_types[i]
            if llvm_val.type != expected_ty:
                if isinstance(expected_ty, ir.PointerType):
                    llvm_val = builder.inttoptr(llvm_val, expected_ty)
                elif isinstance(llvm_val.type, ir.PointerType):
                    llvm_val = builder.ptrtoint(llvm_val, expected_ty)
                else:
                    llvm_val = builder.bitcast(llvm_val, expected_ty)
            field_ptr = builder.gep(
                env_typed,
                [ir.Constant(LLVM_I32, 0), ir.Constant(LLVM_I32, i)],
                name=f"{name}.f{i}",
            )
            builder.store(llvm_val, field_ptr)

        # Build the closure struct {fn_ptr, env_ptr}
        fn = self._functions.get(inst.fn_name)
        if fn is not None:
            fn_ptr = builder.bitcast(fn, LLVM_PTR, name=f"{name}.fnptr")
        else:
            fn_ptr = ir.Constant(LLVM_PTR, None)

        closure = ir.Constant(LLVM_CLOSURE, ir.Undefined)
        closure = builder.insert_value(closure, fn_ptr, 0, name=f"{name}.c0")
        closure = builder.insert_value(closure, env_raw, 1, name=name)
        self._store_value(inst.dest, closure, values)

    def _emit_closure_call(self, inst: ClosureCall, builder: Any, values: dict[str, Any]) -> None:
        """Emit an indirect call through a closure {fn_ptr, env_ptr}."""
        name = self._val_name(inst.dest)
        closure = self._get_value(inst.closure, values)
        args = [self._get_value(a, values) for a in inst.args]

        # Extract fn_ptr and env_ptr from closure struct
        fn_raw = builder.extract_value(closure, 0, name=f"{name}.fn")
        env_ptr = builder.extract_value(closure, 1, name=f"{name}.env")

        # Build function type: ret_type(i8*, arg_types...)
        arg_types = [a.type for a in args]
        ret_type = self._resolve_mir_type(inst.dest.ty)
        if isinstance(ret_type, ir.VoidType):
            ret_type = LLVM_INT  # closures return at least i64

        fn_ty = ir.FunctionType(ret_type, [LLVM_PTR] + arg_types)
        fn_ptr = builder.bitcast(fn_raw, fn_ty.as_pointer(), name=f"{name}.fptr")

        # Call with env_ptr as first arg
        result = builder.call(fn_ptr, [env_ptr] + args, name=name)
        self._store_value(inst.dest, result, values)

    def _emit_env_load(self, inst: EnvLoad, builder: Any, values: dict[str, Any]) -> None:
        """Load a captured variable from a closure environment struct.

        The env is an i8*. We bitcast it to a struct pointer with the right
        field type at the right index and load.
        """
        name = self._val_name(inst.dest)
        env_raw = self._get_value(inst.env, values)
        field_ty = self._resolve_mir_type(inst.val_type)

        # Build a struct type with fields up to and including the target index.
        # We use a placeholder approach: put field_ty at the target offset.
        # For simplicity, build a struct of N+1 fields all sized i64 (8 bytes),
        # with the target field being the actual type.
        # This works because our captures are all 8-byte-aligned scalars or pointers.
        placeholder_fields: list[Any] = []
        for i in range(inst.index + 1):
            if i == inst.index:
                placeholder_fields.append(field_ty)
            else:
                # Use i64 as 8-byte placeholder (matches alignment)
                placeholder_fields.append(LLVM_INT)
        env_struct_ty = ir.LiteralStructType(placeholder_fields)

        env_typed = builder.bitcast(env_raw, env_struct_ty.as_pointer(), name=f"{name}.envp")
        field_ptr = builder.gep(
            env_typed,
            [ir.Constant(LLVM_I32, 0), ir.Constant(LLVM_I32, inst.index)],
            name=f"{name}.ptr",
        )
        result = builder.load(field_ptr, name=name)
        self._store_value(inst.dest, result, values)

    # --- Stream operations (runtime calls) ---

    def _emit_assert(self, inst: Assert, builder: Any, values: dict[str, Any], func: Any) -> None:
        """Emit an assert: branch on condition, print error and exit if false."""
        cond = self._get_value(inst.cond, values)
        # Ensure we have an i1
        if hasattr(cond.type, "width") and cond.type.width != 1:
            cond = builder.trunc(cond, ir.IntType(1))

        pass_bb = builder.append_basic_block(name="assert.pass")
        fail_bb = builder.append_basic_block(name="assert.fail")
        builder.cbranch(cond, pass_bb, fail_bb)

        # Fail block: print message and exit
        builder.position_at_end(fail_bb)
        msg = f"assertion failed at {inst.filename}:{inst.line}\\n"
        self._emit_printf(builder, msg, [])
        # Call exit(1)
        exit_fn = self._functions.get("exit")
        if exit_fn is None:
            exit_ty = ir.FunctionType(ir.VoidType(), [LLVM_INT])
            exit_fn = ir.Function(self.module, exit_ty, name="exit")
            exit_fn.linkage = "external"
            self._functions["exit"] = exit_fn
        builder.call(exit_fn, [ir.Constant(LLVM_INT, 1)])
        builder.unreachable()

        # Continue in pass block
        builder.position_at_end(pass_bb)

    def _emit_stream_init(self, inst: StreamInit, builder: Any, values: dict[str, Any]) -> None:
        """Emit stream creation from a list source."""
        name = self._val_name(inst.dest)
        source = self._get_value(inst.source, values)

        # Determine element size from the list's elem_size field
        elem_size = 8  # default to i64 (8 bytes)
        if inst.elem_type.kind == TypeKind.LIST:
            # Extract elem_size from the list type info
            inner = inst.elem_type.type_info
            if inner and inner.args:
                inner_ty = self._resolve_mir_type(MIRType(inner.args[0]))
                elem_size = _approx_type_size(inner_ty)

        # Store list in alloca so we can pass a pointer
        list_alloca = builder.alloca(LLVM_LIST, name=f"{name}.lptr")
        builder.store(source, list_alloca)

        fn = self._rt_stream_from_list()
        stream_ptr = builder.call(fn, [list_alloca, ir.Constant(LLVM_INT, elem_size)], name=name)
        self._store_value(inst.dest, stream_ptr, values)

    def _emit_stream_op(self, inst: StreamOp, builder: Any, values: dict[str, Any]) -> None:
        """Emit stream operations as calls to C runtime."""
        name = self._val_name(inst.dest)
        source = self._get_value(inst.source, values)
        null_ptr = ir.Constant(LLVM_PTR, None)

        if inst.op_kind == StreamOpKind.MAP:
            # Get function pointer for the map callback
            fn_ptr = self._get_stream_fn_ptr(inst, builder, values)
            result = builder.call(
                self._rt_stream_map(),
                [source, fn_ptr, null_ptr, ir.Constant(LLVM_INT, 8)],
                name=name,
            )
            self._store_value(inst.dest, result, values)

        elif inst.op_kind == StreamOpKind.FILTER:
            fn_ptr = self._get_stream_fn_ptr(inst, builder, values)
            result = builder.call(
                self._rt_stream_filter(),
                [source, fn_ptr, null_ptr],
                name=name,
            )
            self._store_value(inst.dest, result, values)

        elif inst.op_kind == StreamOpKind.TAKE:
            n = self._get_value(inst.args[0], values) if inst.args else ir.Constant(LLVM_INT, 0)
            result = builder.call(self._rt_stream_take(), [source, n], name=name)
            self._store_value(inst.dest, result, values)

        elif inst.op_kind == StreamOpKind.SKIP:
            n = self._get_value(inst.args[0], values) if inst.args else ir.Constant(LLVM_INT, 0)
            result = builder.call(self._rt_stream_skip(), [source, n], name=name)
            self._store_value(inst.dest, result, values)

        elif inst.op_kind == StreamOpKind.COLLECT:
            result = builder.call(
                self._rt_stream_collect(),
                [source, ir.Constant(LLVM_INT, 8)],
                name=name,
            )
            self._store_value(inst.dest, result, values)

        elif inst.op_kind == StreamOpKind.FOLD:
            # fold(init, fn) → __mn_stream_fold(stream, &init, size, fn, user_data, &out)
            if len(inst.args) >= 2:
                init_val = self._get_value(inst.args[0], values)
                fn_ptr = self._get_stream_fn_ptr(inst, builder, values, fn_arg_idx=1)
                init_alloca = builder.alloca(init_val.type, name=f"{name}.init")
                builder.store(init_val, init_alloca)
                init_ptr = builder.bitcast(init_alloca, LLVM_PTR)
                out_alloca = builder.alloca(init_val.type, name=f"{name}.out")
                out_ptr = builder.bitcast(out_alloca, LLVM_PTR)
                acc_size = _approx_type_size(init_val.type)
                builder.call(
                    self._rt_stream_fold(),
                    [source, init_ptr, ir.Constant(LLVM_INT, acc_size), fn_ptr, null_ptr, out_ptr],
                )
                result = builder.load(out_alloca, name=name)
            else:
                result = ir.Constant(LLVM_INT, 0)
            self._store_value(inst.dest, result, values)

        else:
            # Fallback: pass through
            self._store_value(inst.dest, source, values)

    def _get_stream_fn_ptr(
        self, inst: StreamOp, builder: Any, values: dict[str, Any], fn_arg_idx: int = 0
    ) -> Any:
        """Get a function pointer (bitcast to i8*) for stream map/filter/fold callbacks."""
        # Try to resolve from the fn_name field
        if inst.fn_name:
            fn = self._functions.get(inst.fn_name)
            if fn is None:
                for f in self.module.functions:
                    if f.name == inst.fn_name:
                        fn = f
                        break
            if fn is not None:
                return builder.bitcast(fn, LLVM_PTR)

        # Try to resolve from args (function pointer value)
        if inst.args and fn_arg_idx < len(inst.args):
            val = self._get_value(inst.args[fn_arg_idx], values)
            if hasattr(val.type, "pointee"):
                return builder.bitcast(val, LLVM_PTR)
            # It might be a function reference by name
            fn_name = inst.args[fn_arg_idx].name.lstrip("%")
            fn = self._functions.get(fn_name)
            if fn is not None:
                return builder.bitcast(fn, LLVM_PTR)

        return ir.Constant(LLVM_PTR, None)

    # --- Pipe definitions ---

    def _emit_pipe_def(self, pipe_name: str, pipe_info: MIRPipeInfo) -> None:
        """Emit a pipe definition as a function that chains agent spawn/send/recv.

        `pipe Transform { A |> B |> C }` becomes a function
        `Transform(input: i8*) -> i8*` that spawns each stage agent,
        sends data through, and returns the final result.
        """
        if not _HAS_LLVMLITE:
            return

        fn_ty = ir.FunctionType(LLVM_PTR, [LLVM_PTR])
        fn = ir.Function(self.module, fn_ty, name=pipe_name)
        fn.linkage = "internal"
        self._functions[pipe_name] = fn

        entry = fn.append_basic_block(name="entry")
        builder = ir.IRBuilder(entry)

        if not pipe_info.stages:
            builder.ret(fn.args[0])
            return

        current_val = fn.args[0]
        null_ptr = ir.Constant(LLVM_PTR, None)
        cap = ir.Constant(LLVM_I32, 256)
        fn_new = self._rt_agent_new()
        fn_spawn = self._rt_agent_spawn()
        fn_send = self._rt_agent_send()
        fn_recv = self._rt_agent_recv_blocking()
        fn_stop = self._declare_runtime_fn("mapanare_agent_stop", LLVM_VOID, [LLVM_PTR])

        for i, stage in enumerate(pipe_info.stages):
            stage_name = self._make_string_constant(builder, stage)
            name_ptr = builder.extract_value(stage_name, 0)
            agent = builder.call(fn_new, [name_ptr, null_ptr, null_ptr, cap, cap], name=f"stage{i}")
            builder.call(fn_spawn, [agent])
            builder.call(fn_send, [agent, current_val])
            out_ptr = builder.alloca(LLVM_PTR, name=f"stage{i}.out")
            builder.call(fn_recv, [agent, out_ptr])
            current_val = builder.load(out_ptr, name=f"stage{i}.result")
            builder.call(fn_stop, [agent])

        builder.ret(current_val)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _type_alignment(llvm_ty: Any) -> int:
    """Return the natural alignment in bytes of an LLVM type."""
    if not _HAS_LLVMLITE:
        return 8
    if isinstance(llvm_ty, ir.IntType):
        w = llvm_ty.width
        if w <= 8:
            return 1
        if w <= 16:
            return 2
        if w <= 32:
            return 4
        return 8
    if isinstance(llvm_ty, ir.DoubleType):
        return 8
    if isinstance(llvm_ty, ir.FloatType):
        return 4
    if isinstance(llvm_ty, ir.PointerType):
        return 8
    if isinstance(llvm_ty, ir.VoidType):
        return 1
    if isinstance(llvm_ty, ir.LiteralStructType):
        if not llvm_ty.elements:
            return 1
        return max(_type_alignment(e) for e in llvm_ty.elements)
    if isinstance(llvm_ty, ir.ArrayType):
        return _type_alignment(llvm_ty.element)
    return 8


def _approx_type_size(llvm_ty: Any) -> int:
    """Compute the ABI size in bytes of an LLVM type, including alignment padding."""
    if not _HAS_LLVMLITE:
        return 8
    if isinstance(llvm_ty, ir.IntType):
        return int(max(llvm_ty.width // 8, 1))
    if isinstance(llvm_ty, ir.DoubleType):
        return 8
    if isinstance(llvm_ty, ir.FloatType):
        return 4
    if isinstance(llvm_ty, ir.PointerType):
        return 8
    if isinstance(llvm_ty, ir.VoidType):
        return 0
    if isinstance(llvm_ty, ir.LiteralStructType):
        offset = 0
        max_align = 1
        for elem in llvm_ty.elements:
            elem_align = _type_alignment(elem)
            if elem_align > max_align:
                max_align = elem_align
            # Pad to element alignment
            rem = offset % elem_align
            if rem != 0:
                offset += elem_align - rem
            offset += _approx_type_size(elem)
        # Pad struct to its alignment
        rem = offset % max_align
        if rem != 0:
            offset += max_align - rem
        return offset
    if isinstance(llvm_ty, ir.ArrayType):
        return int(llvm_ty.count) * _approx_type_size(llvm_ty.element)
    return 8  # Conservative default
