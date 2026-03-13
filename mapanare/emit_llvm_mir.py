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
    Instruction,
    InterpConcat,
    Jump,
    ListInit,
    MapInit,
    MIRFunction,
    MIRModule,
    MIRType,
    Phi,
    Return,
    SignalGet,
    SignalInit,
    SignalSet,
    SourceSpan,
    StreamOp,
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


def _init_llvm_types() -> None:
    """Initialize LLVM type constants. Must be called after confirming llvmlite exists."""
    global _llvm_types_initialized
    global LLVM_INT, LLVM_FLOAT, LLVM_BOOL, LLVM_CHAR, LLVM_VOID
    global LLVM_PTR, LLVM_I32, LLVM_STRING, LLVM_LIST, LLVM_MAP

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
    LLVM_MAP = ir.LiteralStructType([ir.IntType(8).as_pointer(), LLVM_INT])

    _llvm_types_initialized = True


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

    # -----------------------------------------------------------------------
    # Public entry point
    # -----------------------------------------------------------------------

    def emit(self, mir_module: MIRModule) -> Any:
        """Emit LLVM IR from a MIR module. Returns the llvmlite ir.Module."""
        # 0. Initialize DWARF debug info if enabled
        if self._debug:
            self._init_debug_info(mir_module)

        # 1. Register struct types
        for name, fields in mir_module.structs.items():
            self._register_struct(name, fields)

        # 2. Register enum types (tagged unions)
        for name, variants in mir_module.enums.items():
            self._register_enum(name, variants)

        # 3. Declare extern functions
        for abi, mod, fn_name, param_types, ret_type in mir_module.extern_fns:
            self._declare_extern(abi, mod, fn_name, param_types, ret_type)

        # 4. Forward-declare all MIR functions
        for mir_fn in mir_module.functions:
            self._forward_declare_function(mir_fn)

        # 5. Emit function bodies
        for mir_fn in mir_module.functions:
            self._emit_function(mir_fn)

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
            return LLVM_PTR
        if kind == TypeKind.ENUM:
            name = mir_type.type_info.name
            if name in self._enum_types:
                return self._enum_types[name][0]
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
        return LLVM_PTR

    def _resolve_type_info_arg(self, ti: Any) -> Any:
        """Resolve a TypeInfo (from type args) to LLVM type."""
        return self._resolve_mir_type(MIRType(type_info=ti))

    # -----------------------------------------------------------------------
    # Struct / Enum registration
    # -----------------------------------------------------------------------

    def _register_struct(self, name: str, fields: list[tuple[str, MIRType]]) -> None:
        """Register a named struct type."""
        field_types = [self._resolve_mir_type(ft) for _, ft in fields]
        field_names = [fn for fn, _ in fields]
        llvm_ty = ir.LiteralStructType(field_types)
        self._struct_types[name] = llvm_ty
        self._struct_fields[name] = field_names

    def _register_enum(self, name: str, variants: list[tuple[str, list[MIRType]]]) -> None:
        """Register an enum as a tagged union.

        Layout: {i32 tag, [max_payload_bytes x i8]}
        The tag is i32; the payload is sized to the largest variant.
        """
        variant_tags: dict[str, int] = {}
        variant_payloads: dict[str, list[MIRType]] = {}

        max_payload_size = 0
        for i, (vname, payload_types) in enumerate(variants):
            variant_tags[vname] = i
            variant_payloads[vname] = payload_types
            # Estimate payload size: sum of field sizes (rough but sufficient)
            size = 0
            for pt in payload_types:
                llvm_t = self._resolve_mir_type(pt)
                size += _approx_type_size(llvm_t)
            if size > max_payload_size:
                max_payload_size = size

        # Ensure at least 8 bytes for the payload area
        if max_payload_size < 8:
            max_payload_size = 8

        payload_ty = ir.ArrayType(ir.IntType(8), max_payload_size)
        enum_ty = ir.LiteralStructType([LLVM_I32, payload_ty])
        self._enum_types[name] = (enum_ty, variant_tags, variant_payloads)

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

    def _rt_str_concat(self) -> Any:
        return self._declare_runtime_fn("__mn_str_concat", LLVM_STRING, [LLVM_STRING, LLVM_STRING])

    def _rt_str_eq(self) -> Any:
        return self._declare_runtime_fn("__mn_str_eq", LLVM_INT, [LLVM_STRING, LLVM_STRING])

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

    def _rt_panic(self) -> Any:
        return self._declare_runtime_fn("__mn_panic", LLVM_VOID, [LLVM_STRING])

    def _rt_alloc(self) -> Any:
        return self._declare_runtime_fn("__mn_alloc", LLVM_PTR, [LLVM_INT])

    def _rt_free(self) -> Any:
        return self._declare_runtime_fn("__mn_free", LLVM_VOID, [LLVM_PTR])

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
        self._fmt_strings[fmt] = gv
        return gv

    # -----------------------------------------------------------------------
    # String literal helpers
    # -----------------------------------------------------------------------

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

        # 1. Create all LLVM basic blocks upfront
        llvm_blocks: dict[str, Any] = {}
        for bb in mir_fn.blocks:
            llvm_blocks[bb.label] = func.append_basic_block(bb.label)

        # 2. Value map: MIR value name -> LLVM value
        values: dict[str, Any] = {}

        # 3. Bind function parameters
        for i, param in enumerate(mir_fn.params):
            values[f"%{param.name}"] = func.args[i]
            # Also store without % prefix for flexibility
            values[param.name] = func.args[i]

        # 4. First pass: emit phi nodes and collect deferred incoming edges
        deferred_phis: list[tuple[Any, list[tuple[str, Value]], dict[str, Any]]] = []

        for bb in mir_fn.blocks:
            builder = ir.IRBuilder(llvm_blocks[bb.label])
            for inst in bb.instructions:
                if isinstance(inst, Phi):
                    llvm_type = self._resolve_mir_type(inst.dest.ty)
                    phi = builder.phi(llvm_type, name=self._val_name(inst.dest))
                    values[inst.dest.name] = phi
                    deferred_phis.append((phi, inst.incoming, llvm_blocks))
                else:
                    break  # Phi nodes must be at block start

        # 5. Emit all non-phi instructions block by block
        for bb in mir_fn.blocks:
            builder = ir.IRBuilder(llvm_blocks[bb.label])
            # Position after any phi nodes already emitted
            if builder.block.instructions:
                builder.position_at_end(builder.block)
            for inst in bb.instructions:
                if isinstance(inst, Phi):
                    continue  # Already handled
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

        # 6. Resolve deferred phi incoming edges
        for phi, incoming, blocks in deferred_phis:
            for lbl, val in incoming:
                if lbl in blocks and val.name in values:
                    phi.add_incoming(values[val.name], blocks[lbl])

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
            self._emit_return(inst, builder, values)
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
        elif isinstance(inst, StreamOp):
            self._emit_stream_op(inst, builder, values)
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
        """Look up the LLVM value for a MIR Value."""
        if val.name in values:
            return values[val.name]
        # Try without % prefix
        stripped = val.name.lstrip("%")
        if stripped in values:
            return values[stripped]
        raise KeyError(f"MIR value '{val.name}' not found in value map")

    def _store_value(self, dest: Value, llvm_val: Any, values: dict[str, Any]) -> None:
        """Store an LLVM value in the value map under the MIR dest name."""
        values[dest.name] = llvm_val

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

        # String operations
        if lhs_kind == TypeKind.STRING:
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
            else:
                result = ir.Constant(LLVM_INT, 0)
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
            if inst.args and inst.args[0].ty.kind == TypeKind.STRING:
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
                list_ptr = builder.alloca(LLVM_LIST, name=f"{name}.tmp")
                builder.store(args[0], list_ptr)
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

        # --- User-defined function call ---
        if fn_name in self._functions:
            target_fn = self._functions[fn_name]
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
        # Declare it on the fly as i64(...) → best effort
        param_types = [a.type for a in args]
        ret_ty = self._resolve_mir_type(inst.dest.ty)
        fn_ty = ir.FunctionType(ret_ty, param_types)
        extern_fn = ir.Function(self.module, fn_ty, name=fn_name)
        self._functions[fn_name] = extern_fn
        if isinstance(ret_ty, ir.VoidType):
            builder.call(extern_fn, args)
            self._store_value(inst.dest, ir.Constant(LLVM_BOOL, 0), values)
        else:
            result = builder.call(extern_fn, args, name=name)
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
            # Auto-declare
            param_types = [a.type for a in args]
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

    def _emit_return(self, inst: Return, builder: Any, values: dict[str, Any]) -> None:
        if inst.val is not None:
            val = self._get_value(inst.val, values)
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
            cond = builder.icmp_signed("!=", cond, ir.Constant(cond.type, 0), name="br.cond")
        builder.cbranch(cond, true_block, false_block)

    # --- Switch ---

    def _emit_switch(
        self, inst: Switch, builder: Any, values: dict[str, Any], llvm_blocks: dict[str, Any]
    ) -> None:
        tag = self._get_value(inst.tag, values)
        default_block = llvm_blocks[inst.default_block]
        switch = builder.switch(tag, default_block)
        for case_val, case_lbl in inst.cases:
            case_const = ir.Constant(tag.type, int(case_val))
            switch.add_case(case_const, llvm_blocks[case_lbl])

    # --- StructInit ---

    def _emit_struct_init(self, inst: StructInit, builder: Any, values: dict[str, Any]) -> None:
        struct_name = inst.struct_type.type_info.name
        name = self._val_name(inst.dest)

        if struct_name in self._struct_types:
            llvm_ty = self._struct_types[struct_name]
            field_names = self._struct_fields.get(struct_name, [])
            result = ir.Constant(llvm_ty, ir.Undefined)
            for field_name, field_val in inst.fields:
                val = self._get_value(field_val, values)
                if field_name in field_names:
                    idx = field_names.index(field_name)
                else:
                    # Positional fallback
                    idx = inst.fields.index((field_name, field_val))
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

        if obj_type_name in self._struct_fields:
            field_names = self._struct_fields[obj_type_name]
            if inst.field_name in field_names:
                idx = field_names.index(inst.field_name)
                result = builder.extract_value(obj, idx, name=name)
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

        if obj_type_name in self._struct_fields:
            field_names = self._struct_fields[obj_type_name]
            if inst.field_name in field_names:
                idx = field_names.index(inst.field_name)
                result = builder.insert_value(obj, val, idx)
                # Update the value in the map (functional update for SSA)
                values[inst.obj.name] = result

    # --- ListInit ---

    def _emit_list_init(self, inst: ListInit, builder: Any, values: dict[str, Any]) -> None:
        name = self._val_name(inst.dest)
        elem_llvm_ty = self._resolve_mir_type(inst.elem_type)
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
                # Alloca element, store, bitcast to i8*
                elem_alloca = builder.alloca(elem_llvm_ty, name=f"{name}.e{i}")
                builder.store(elem_val, elem_alloca)
                elem_ptr = builder.bitcast(elem_alloca, ir.IntType(8).as_pointer())
                builder.call(fn_push, [list_ptr, elem_ptr])

            list_val = builder.load(list_ptr, name=name)

        self._store_value(inst.dest, list_val, values)

    # --- IndexGet ---

    def _emit_index_get(self, inst: IndexGet, builder: Any, values: dict[str, Any]) -> None:
        obj = self._get_value(inst.obj, values)
        index = self._get_value(inst.index, values)
        name = self._val_name(inst.dest)
        obj_kind = inst.obj.ty.kind

        if obj_kind == TypeKind.LIST:
            fn_get = self._rt_list_get()
            list_ptr = builder.alloca(LLVM_LIST, name=f"{name}.lptr")
            builder.store(obj, list_ptr)
            raw_ptr = builder.call(fn_get, [list_ptr, index], name=f"{name}.raw")
            # Bitcast to element type pointer and load
            elem_ty = self._resolve_mir_type(inst.dest.ty)
            typed_ptr = builder.bitcast(raw_ptr, elem_ty.as_pointer(), name=f"{name}.tptr")
            result = builder.load(typed_ptr, name=name)
        elif obj_kind == TypeKind.STRING:
            # String indexing: __mn_str_byte_at or char access
            fn = self._declare_runtime_fn("__mn_str_byte_at", LLVM_INT, [LLVM_STRING, LLVM_INT])
            result = builder.call(fn, [obj, index], name=name)
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

    # --- MapInit ---

    def _emit_map_init(self, inst: MapInit, builder: Any, values: dict[str, Any]) -> None:
        # Maps are opaque pointer-based; for now emit a zeroinitializer
        result = ir.Constant(LLVM_MAP, None)
        self._store_value(inst.dest, result, values)

    # --- EnumInit ---

    def _emit_enum_init(self, inst: EnumInit, builder: Any, values: dict[str, Any]) -> None:
        name = self._val_name(inst.dest)
        enum_name = inst.enum_type.type_info.name

        if enum_name in self._enum_types:
            enum_ty, tag_map, _ = self._enum_types[enum_name]
            tag_val = tag_map.get(inst.variant, 0)

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
        result = builder.extract_value(enum_val, 0, name=name)
        self._store_value(inst.dest, result, values)

    # --- EnumPayload ---

    def _emit_enum_payload(self, inst: EnumPayload, builder: Any, values: dict[str, Any]) -> None:
        enum_val = self._get_value(inst.enum_val, values)
        name = self._val_name(inst.dest)
        enum_name = inst.enum_val.ty.type_info.name

        if enum_name in self._enum_types:
            _, _, variant_payloads = self._enum_types[enum_name]
            payload_types = variant_payloads.get(inst.variant, [])

            # Alloca the enum, extract payload bytes, bitcast
            enum_ty = self._enum_types[enum_name][0]
            enum_ptr = builder.alloca(enum_ty, name=f"{name}.eptr")
            builder.store(enum_val, enum_ptr)
            payload_ptr = builder.gep(
                enum_ptr,
                [ir.Constant(LLVM_I32, 0), ir.Constant(LLVM_I32, 1)],
                inbounds=True,
                name=f"{name}.pptr",
            )

            if len(payload_types) == 1:
                target_ty = self._resolve_mir_type(payload_types[0])
                payload_i8 = builder.bitcast(
                    payload_ptr, target_ty.as_pointer(), name=f"{name}.tptr"
                )
                result = builder.load(payload_i8, name=name)
            elif payload_types:
                # Multi-field payload: build a struct
                field_tys = [self._resolve_mir_type(pt) for pt in payload_types]
                payload_struct_ty = ir.LiteralStructType(field_tys)
                typed_ptr = builder.bitcast(
                    payload_ptr, payload_struct_ty.as_pointer(), name=f"{name}.sptr"
                )
                result = builder.load(typed_ptr, name=name)
            else:
                result = ir.Constant(LLVM_BOOL, 0)
        else:
            # Extract payload field (index 1) as fallback
            try:
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

    # --- Signal operations (opaque pointer) ---

    def _emit_signal_init(self, inst: SignalInit, builder: Any, values: dict[str, Any]) -> None:
        name = self._val_name(inst.dest)
        initial = self._get_value(inst.initial_val, values)
        # Store as an alloca'd pointer (opaque signal representation)
        fn_alloc = self._rt_alloc()
        val_size = ir.Constant(LLVM_INT, _approx_type_size(initial.type))
        ptr = builder.call(fn_alloc, [val_size], name=f"{name}.ptr")
        typed_ptr = builder.bitcast(ptr, initial.type.as_pointer())
        builder.store(initial, typed_ptr)
        self._store_value(inst.dest, ptr, values)

    def _emit_signal_get(self, inst: SignalGet, builder: Any, values: dict[str, Any]) -> None:
        signal = self._get_value(inst.signal, values)
        name = self._val_name(inst.dest)
        target_ty = self._resolve_mir_type(inst.dest.ty)
        if isinstance(target_ty, ir.VoidType):
            result = ir.Constant(LLVM_BOOL, 0)
        else:
            typed_ptr = builder.bitcast(signal, target_ty.as_pointer(), name=f"{name}.tptr")
            result = builder.load(typed_ptr, name=name)
        self._store_value(inst.dest, result, values)

    def _emit_signal_set(self, inst: SignalSet, builder: Any, values: dict[str, Any]) -> None:
        signal = self._get_value(inst.signal, values)
        val = self._get_value(inst.val, values)
        typed_ptr = builder.bitcast(signal, val.type.as_pointer())
        builder.store(val, typed_ptr)

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

    def _emit_stream_op(self, inst: StreamOp, builder: Any, values: dict[str, Any]) -> None:
        # Stream operations are not directly supported in the LLVM backend;
        # emit as an opaque pointer pass-through for now
        source = self._get_value(inst.source, values)
        self._store_value(inst.dest, source, values)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _approx_type_size(llvm_ty: Any) -> int:
    """Approximate the size in bytes of an LLVM type (for allocation sizing)."""
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
        return sum(_approx_type_size(e) for e in llvm_ty.elements)
    if isinstance(llvm_ty, ir.ArrayType):
        return int(llvm_ty.count) * _approx_type_size(llvm_ty.element)
    return 8  # Conservative default
