"""LLVM IR emitter -- compiles AST to LLVM IR.

Phase 4.1: Type mapping from Mapanare types to LLVM IR types via llvmlite.
Phase 4.2: IR emitter — AST nodes to LLVM instructions.
Phase 5.1: Tensor operations — element-wise SIMD, matmul runtime calls.
Phase 6.1: Core runtime integration — string ops, list ops, struct/enum codegen.
"""

from __future__ import annotations

from llvmlite import ir

from mapanare.ast_nodes import (
    AgentDef,
    AssignExpr,
    BinaryExpr,
    Block,
    BoolLiteral,
    CallExpr,
    CharLiteral,
    ConstructExpr,
    DocComment,
    EnumDef,
    ExprStmt,
    ExternFnDef,
    FieldAccessExpr,
    FloatLiteral,
    FnDef,
    ForLoop,
    GenericType,
    Identifier,
    IfExpr,
    ImplDef,
    ImportDef,
    IndexExpr,
    InterpString,
    IntLiteral,
    LambdaExpr,
    LetBinding,
    ListLiteral,
    LiteralPattern,
    MapLiteral,
    MatchArm,
    MatchExpr,
    MethodCallExpr,
    NamedType,
    NoneLiteral,
    PipeExpr,
    Program,
    ReturnStmt,
    SendExpr,
    SpawnExpr,
    StringLiteral,
    StructDef,
    SyncExpr,
    TensorType,
    TraitDef,
    TypeExpr,
    UnaryExpr,
    WhileLoop,
    WildcardPattern,
)
from mapanare.types import PRIMITIVE_TYPES as _CANONICAL_PRIMITIVES

# ---------------------------------------------------------------------------
# LLVM type constants
# ---------------------------------------------------------------------------

# Primitives
LLVM_INT = ir.IntType(64)  # Int → i64
LLVM_FLOAT = ir.DoubleType()  # Float → double
LLVM_BOOL = ir.IntType(1)  # Bool → i1
LLVM_CHAR = ir.IntType(8)  # Char → i8
LLVM_VOID = ir.VoidType()  # Void
LLVM_PTR = ir.IntType(8).as_pointer()  # void* / opaque pointer
LLVM_I32 = ir.IntType(32)  # i32 for C int

# String: { i8*, i64 } — pointer to data + length (matches MnString in C runtime)
LLVM_STRING = ir.LiteralStructType([ir.IntType(8).as_pointer(), LLVM_INT])

# List: { i8*, i64, i64, i64 } — data, len, cap, elem_size (matches MnList in C runtime)
LLVM_LIST = ir.LiteralStructType([ir.IntType(8).as_pointer(), LLVM_INT, LLVM_INT, LLVM_INT])


def option_type(inner: ir.Type) -> ir.LiteralStructType:
    """Option<T> → { i1, T } — tag (1=Some, 0=None) + value."""
    return ir.LiteralStructType([LLVM_BOOL, inner])


def result_type(ok_ty: ir.Type, err_ty: ir.Type) -> ir.LiteralStructType:
    """Result<T, E> → { i1, { T, E } } — tag (1=Ok, 0=Err) + payload union.

    Since LLVM doesn't have real unions, we store both fields and the tag
    indicates which is valid. The struct size is the sum of both types.
    """
    return ir.LiteralStructType([LLVM_BOOL, ir.LiteralStructType([ok_ty, err_ty])])


def tensor_type(element_ty: ir.Type) -> ir.LiteralStructType:
    """Tensor<T>[...] → { T*, i64, i64*, i64 }

    Layout:
      - data:  pointer to contiguous heap-allocated element buffer
      - ndim:  number of dimensions (i64)
      - shape: pointer to shape array (i64* — ndim elements)
      - size:  total number of elements (i64)
    """
    return ir.LiteralStructType(
        [element_ty.as_pointer(), LLVM_INT, LLVM_INT.as_pointer(), LLVM_INT]
    )


def list_type(element_ty: ir.Type) -> ir.LiteralStructType:
    """List<T> → { i8*, i64, i64, i64 } — data, len, cap, elem_size.

    Matches the MnList layout in the C runtime. Data pointer is i8*
    (type-erased) and elem_size tracks element size for push/get.
    """
    return LLVM_LIST


def map_type(key_ty: ir.Type, val_ty: ir.Type) -> ir.LiteralStructType:
    """Map<K, V> → opaque pointer (hash map implementation detail).

    Represented as { i8*, i64 } — pointer to hash table + count.
    """
    return ir.LiteralStructType([ir.IntType(8).as_pointer(), LLVM_INT])


# ---------------------------------------------------------------------------
# Named type table — keys must match mapanare.types.PRIMITIVE_TYPES
# ---------------------------------------------------------------------------

_PRIMITIVE_MAP: dict[str, ir.Type] = {
    "Int": LLVM_INT,
    "Float": LLVM_FLOAT,
    "Bool": LLVM_BOOL,
    "Char": LLVM_CHAR,
    "String": LLVM_STRING,
    "Void": LLVM_VOID,
}

assert set(_PRIMITIVE_MAP.keys()) == _CANONICAL_PRIMITIVES, (
    f"LLVM _PRIMITIVE_MAP keys out of sync with types.py: "
    f"{set(_PRIMITIVE_MAP.keys()) ^ _CANONICAL_PRIMITIVES}"
)


# ---------------------------------------------------------------------------
# Type resolver: Mapanare TypeExpr → LLVM ir.Type
# ---------------------------------------------------------------------------


class TypeMapper:
    """Resolves Mapanare AST type expressions to llvmlite IR types."""

    def __init__(self) -> None:
        self._struct_types: dict[str, ir.Type] = {}

    def register_struct(self, name: str, llvm_ty: ir.Type) -> None:
        """Register a named struct type (for user-defined structs)."""
        self._struct_types[name] = llvm_ty

    def resolve(self, ty: TypeExpr) -> ir.Type:
        """Convert a Mapanare TypeExpr AST node to the corresponding LLVM type."""
        if isinstance(ty, NamedType):
            return self._resolve_named(ty)
        if isinstance(ty, GenericType):
            return self._resolve_generic(ty)
        if isinstance(ty, TensorType):
            return self._resolve_tensor(ty)
        raise TypeError(f"Unsupported Mapanare type expression: {type(ty).__name__}")

    # -- private helpers -----------------------------------------------------

    def _resolve_named(self, ty: NamedType) -> ir.Type:
        if ty.name in _PRIMITIVE_MAP:
            return _PRIMITIVE_MAP[ty.name]
        if ty.name in self._struct_types:
            return self._struct_types[ty.name]
        raise TypeError(f"Unknown Mapanare type: {ty.name}")

    def _resolve_generic(self, ty: GenericType) -> ir.Type:
        name = ty.name

        if name == "Option":
            if len(ty.args) != 1:
                raise TypeError("Option expects exactly 1 type argument")
            inner = self.resolve(ty.args[0])
            return option_type(inner)

        if name == "Result":
            if len(ty.args) != 2:
                raise TypeError("Result expects exactly 2 type arguments")
            ok = self.resolve(ty.args[0])
            err = self.resolve(ty.args[1])
            return result_type(ok, err)

        if name == "List":
            if len(ty.args) != 1:
                raise TypeError("List expects exactly 1 type argument")
            elem = self.resolve(ty.args[0])
            return list_type(elem)

        if name == "Map":
            if len(ty.args) != 2:
                raise TypeError("Map expects exactly 2 type arguments")
            key = self.resolve(ty.args[0])
            val = self.resolve(ty.args[1])
            return map_type(key, val)

        raise TypeError(f"Unknown generic Mapanare type: {name}")

    def _resolve_tensor(self, ty: TensorType) -> ir.Type:
        elem = self.resolve(ty.element_type)
        return tensor_type(elem)


# ---------------------------------------------------------------------------
# IR Emitter: Mapanare AST → LLVM IR module
# ---------------------------------------------------------------------------


class LLVMEmitter:
    """Compiles an Mapanare AST into an LLVM IR module using llvmlite."""

    def __init__(
        self,
        module_name: str = "mapanare_module",
        target_triple: str | None = None,
        data_layout: str | None = None,
    ) -> None:
        self.module = ir.Module(name=module_name)
        if target_triple is not None:
            self.module.triple = target_triple
        if data_layout is not None:
            self.module.data_layout = data_layout
        self.type_mapper = TypeMapper()
        self._builder: ir.IRBuilder | None = None
        # Variable name → alloca instruction (stack slot)
        self._locals: dict[str, ir.AllocaInstr] = {}
        # Function name → LLVM function
        self._functions: dict[str, ir.Function] = {}
        # Track mutable variables
        self._mutables: set[str] = set()
        # Printf support
        self._printf_fn: ir.Function | None = None
        self._fmt_strings: dict[str, ir.GlobalVariable] = {}
        # Core runtime function cache
        self._runtime_fns: dict[str, ir.Function] = {}
        # Struct type registry: struct name → (LLVM type, field names list)
        self._struct_defs: dict[str, tuple[ir.LiteralStructType, list[str]]] = {}
        # Arena support: stack of arena alloca pointers per function scope
        self._arena_ptr: ir.AllocaInstr | None = None
        # Track string temporaries for cleanup at function exit
        self._string_temps: list[ir.AllocaInstr] = []
        # Agent support: agent definitions and variable→agent-type tracking
        self._agent_defs: dict[str, AgentDef] = {}
        self._agent_types: dict[str, str] = {}  # var_name → agent_type_name

    @property
    def builder(self) -> ir.IRBuilder:
        assert self._builder is not None, "No active IRBuilder — not inside a function"
        return self._builder

    # -----------------------------------------------------------------------
    # Core runtime declarations (Phase 6.1)
    # -----------------------------------------------------------------------

    def _declare_runtime_fn(
        self, name: str, ret_ty: ir.Type, param_types: list[ir.Type]
    ) -> ir.Function:
        """Declare an external C runtime function if not already declared."""
        if name in self._runtime_fns:
            return self._runtime_fns[name]
        fn_ty = ir.FunctionType(ret_ty, param_types)
        func = ir.Function(self.module, fn_ty, name=name)
        self._runtime_fns[name] = func
        return func

    def _rt_str_concat(self) -> ir.Function:
        """Declare __mn_str_concat(MnString, MnString) -> MnString."""
        return self._declare_runtime_fn("__mn_str_concat", LLVM_STRING, [LLVM_STRING, LLVM_STRING])

    def _rt_str_eq(self) -> ir.Function:
        """Declare __mn_str_eq(MnString, MnString) -> i64."""
        return self._declare_runtime_fn("__mn_str_eq", LLVM_INT, [LLVM_STRING, LLVM_STRING])

    def _rt_str_cmp(self) -> ir.Function:
        """Declare __mn_str_cmp(MnString, MnString) -> i64."""
        return self._declare_runtime_fn("__mn_str_cmp", LLVM_INT, [LLVM_STRING, LLVM_STRING])

    def _rt_str_len(self) -> ir.Function:
        """Declare __mn_str_len(MnString) -> i64."""
        return self._declare_runtime_fn("__mn_str_len", LLVM_INT, [LLVM_STRING])

    def _rt_str_char_at(self) -> ir.Function:
        """Declare __mn_str_char_at(MnString, i64) -> MnString."""
        return self._declare_runtime_fn("__mn_str_char_at", LLVM_STRING, [LLVM_STRING, LLVM_INT])

    def _rt_str_byte_at(self) -> ir.Function:
        """Declare __mn_str_byte_at(MnString, i64) -> i64."""
        return self._declare_runtime_fn("__mn_str_byte_at", LLVM_INT, [LLVM_STRING, LLVM_INT])

    def _rt_str_substr(self) -> ir.Function:
        """Declare __mn_str_substr(MnString, i64, i64) -> MnString."""
        return self._declare_runtime_fn(
            "__mn_str_substr", LLVM_STRING, [LLVM_STRING, LLVM_INT, LLVM_INT]
        )

    def _rt_str_from_int(self) -> ir.Function:
        """Declare __mn_str_from_int(i64) -> MnString."""
        return self._declare_runtime_fn("__mn_str_from_int", LLVM_STRING, [LLVM_INT])

    def _rt_str_println(self) -> ir.Function:
        """Declare __mn_str_println(MnString) -> void."""
        return self._declare_runtime_fn("__mn_str_println", LLVM_VOID, [LLVM_STRING])

    def _rt_str_print(self) -> ir.Function:
        """Declare __mn_str_print(MnString) -> void."""
        return self._declare_runtime_fn("__mn_str_print", LLVM_VOID, [LLVM_STRING])

    def _rt_str_eprintln(self) -> ir.Function:
        """Declare __mn_str_eprintln(MnString) -> void."""
        return self._declare_runtime_fn("__mn_str_eprintln", LLVM_VOID, [LLVM_STRING])

    def _rt_str_starts_with(self) -> ir.Function:
        return self._declare_runtime_fn(
            "__mn_str_starts_with", LLVM_INT, [LLVM_STRING, LLVM_STRING]
        )

    def _rt_str_ends_with(self) -> ir.Function:
        return self._declare_runtime_fn("__mn_str_ends_with", LLVM_INT, [LLVM_STRING, LLVM_STRING])

    def _rt_str_find(self) -> ir.Function:
        return self._declare_runtime_fn("__mn_str_find", LLVM_INT, [LLVM_STRING, LLVM_STRING])

    def _rt_list_new(self) -> ir.Function:
        """Declare __mn_list_new(i64 elem_size) -> MnList."""
        return self._declare_runtime_fn("__mn_list_new", LLVM_LIST, [LLVM_INT])

    def _rt_list_push(self) -> ir.Function:
        """Declare __mn_list_push(MnList*, void*) -> void."""
        return self._declare_runtime_fn(
            "__mn_list_push", LLVM_VOID, [LLVM_LIST.as_pointer(), ir.IntType(8).as_pointer()]
        )

    def _rt_list_get(self) -> ir.Function:
        """Declare __mn_list_get(MnList*, i64) -> i8*."""
        return self._declare_runtime_fn(
            "__mn_list_get", ir.IntType(8).as_pointer(), [LLVM_LIST.as_pointer(), LLVM_INT]
        )

    def _rt_list_len(self) -> ir.Function:
        """Declare __mn_list_len(MnList*) -> i64."""
        return self._declare_runtime_fn("__mn_list_len", LLVM_INT, [LLVM_LIST.as_pointer()])

    def _rt_panic(self) -> ir.Function:
        """Declare __mn_panic(MnString) -> void."""
        return self._declare_runtime_fn("__mn_panic", LLVM_VOID, [LLVM_STRING])

    def _rt_file_read(self) -> ir.Function:
        """Declare __mn_file_read(MnString, i64*) -> MnString."""
        return self._declare_runtime_fn(
            "__mn_file_read", LLVM_STRING, [LLVM_STRING, LLVM_INT.as_pointer()]
        )

    def _rt_str_free(self) -> ir.Function:
        """Declare __mn_str_free(MnString) -> void."""
        return self._declare_runtime_fn("__mn_str_free", LLVM_VOID, [LLVM_STRING])

    def _rt_list_free(self) -> ir.Function:
        """Declare __mn_list_free(MnList*) -> void."""
        return self._declare_runtime_fn("__mn_list_free", LLVM_VOID, [LLVM_LIST.as_pointer()])

    def _rt_list_free_strings(self) -> ir.Function:
        """Declare __mn_list_free_strings(MnList*) -> void."""
        return self._declare_runtime_fn(
            "__mn_list_free_strings", LLVM_VOID, [LLVM_LIST.as_pointer()]
        )

    def _rt_arena_create(self) -> ir.Function:
        """Declare mn_arena_create(i64) -> i8*."""
        return self._declare_runtime_fn("mn_arena_create", ir.IntType(8).as_pointer(), [LLVM_INT])

    def _rt_arena_destroy(self) -> ir.Function:
        """Declare mn_arena_destroy(i8*) -> void."""
        return self._declare_runtime_fn("mn_arena_destroy", LLVM_VOID, [ir.IntType(8).as_pointer()])

    def _rt_alloc(self) -> ir.Function:
        """Declare __mn_alloc(i64) -> i8*."""
        return self._declare_runtime_fn("__mn_alloc", LLVM_PTR, [LLVM_INT])

    def _rt_free(self) -> ir.Function:
        """Declare __mn_free(i8*) -> void."""
        return self._declare_runtime_fn("__mn_free", LLVM_VOID, [LLVM_PTR])

    # -- Agent runtime declarations (Phase 2.1) --

    def _rt_agent_new(self) -> ir.Function:
        """Declare mapanare_agent_new(name, handler, data, inbox_cap, outbox_cap) -> agent*."""
        return self._declare_runtime_fn(
            "mapanare_agent_new", LLVM_PTR, [LLVM_PTR, LLVM_PTR, LLVM_PTR, LLVM_I32, LLVM_I32]
        )

    def _rt_agent_spawn(self) -> ir.Function:
        """Declare mapanare_agent_spawn(agent*) -> i32."""
        return self._declare_runtime_fn("mapanare_agent_spawn", LLVM_I32, [LLVM_PTR])

    def _rt_agent_send(self) -> ir.Function:
        """Declare mapanare_agent_send(agent*, msg*) -> i32."""
        return self._declare_runtime_fn("mapanare_agent_send", LLVM_I32, [LLVM_PTR, LLVM_PTR])

    def _rt_agent_recv_blocking(self) -> ir.Function:
        """Declare mapanare_agent_recv_blocking(agent*, out**) -> i32."""
        return self._declare_runtime_fn(
            "mapanare_agent_recv_blocking", LLVM_I32, [LLVM_PTR, LLVM_PTR.as_pointer()]
        )

    def _rt_agent_stop(self) -> ir.Function:
        """Declare mapanare_agent_stop(agent*) -> void."""
        return self._declare_runtime_fn("mapanare_agent_stop", LLVM_VOID, [LLVM_PTR])

    def _rt_agent_destroy(self) -> ir.Function:
        """Declare mapanare_agent_destroy(agent*) -> void."""
        return self._declare_runtime_fn("mapanare_agent_destroy", LLVM_VOID, [LLVM_PTR])

    def _rt_agent_set_restart_policy(self) -> ir.Function:
        """Declare mapanare_agent_set_restart_policy(agent*, policy, max_restarts) -> void."""
        return self._declare_runtime_fn(
            "mapanare_agent_set_restart_policy", LLVM_VOID, [LLVM_PTR, LLVM_I32, LLVM_I32]
        )

    # -----------------------------------------------------------------------
    # Public entry point
    # -----------------------------------------------------------------------

    def emit_program(self, program: Program, resolver: object | None = None) -> ir.Module:
        """Emit an entire Mapanare program to an LLVM module."""
        # Unwrap DocComment nodes to get at the inner definitions
        defs = [
            d.definition if isinstance(d, DocComment) and d.definition else d
            for d in program.definitions
        ]
        # Pass 0: declare imported symbols as external
        for defn in defs:
            if isinstance(defn, ImportDef):
                self._emit_import(defn, resolver)
        # Pass 0.5: declare extern "C" functions as external (skip Python interop)
        for defn in defs:
            if isinstance(defn, ExternFnDef) and defn.abi != "Python":
                self._emit_extern_fn(defn)
        # First pass: forward-declare all types (enums as tagged unions, structs as placeholders)
        for defn in defs:
            if isinstance(defn, EnumDef):
                self._register_enum(defn)
        for defn in defs:
            if isinstance(defn, StructDef):
                self._forward_declare_struct(defn)
        # Second pass: resolve struct field types now that all names are known
        for defn in defs:
            if isinstance(defn, StructDef):
                self._register_struct(defn)
        # Forward-declare all functions so calls to later-defined functions resolve
        for defn in defs:
            if isinstance(defn, FnDef):
                self._declare_fn(defn)
        # Emit agent definitions (handler methods + wrappers)
        for defn in defs:
            if isinstance(defn, AgentDef):
                self._emit_agent(defn)
        # Emit function bodies
        for defn in defs:
            if isinstance(defn, FnDef):
                self._emit_fn_body(defn)
            elif isinstance(defn, ImplDef):
                self._emit_impl_methods(defn)
            elif isinstance(defn, TraitDef):
                pass  # Traits are type-level only; no LLVM codegen needed
        return self.module

    def _emit_import(self, imp: ImportDef, resolver: object | None) -> None:
        """Declare imported symbols as external functions/globals in the LLVM module."""
        if resolver is None:
            return

        from mapanare.modules import ModuleResolver

        if not isinstance(resolver, ModuleResolver):
            return

        mod_name = imp.path[-1] if imp.path else ""
        # Try to get the resolved module from cache
        cached = None
        for _fp, mod in resolver.all_modules():
            import os

            if os.path.splitext(os.path.basename(_fp))[0] == mod_name:
                cached = mod
                break

        if cached is None:
            return

        # Determine which symbols to import
        names_to_import: list[str] = []
        if imp.items:
            names_to_import = imp.items
        else:
            names_to_import = [name for name, exp in cached.exports.items() if exp.public]

        # Declare each imported function as external
        for name in names_to_import:
            export = cached.exports.get(name)
            if export is None:
                continue
            defn = export.definition
            if isinstance(defn, FnDef):
                # Declare as external function
                param_types = [
                    self.type_mapper.resolve(p.type_annotation) if p.type_annotation else LLVM_INT
                    for p in defn.params
                ]
                ret_type = (
                    self.type_mapper.resolve(defn.return_type) if defn.return_type else LLVM_VOID
                )
                fn_ty = ir.FunctionType(ret_type, param_types)
                try:
                    self.module.get_global(name)
                except KeyError:
                    ir.Function(self.module, fn_ty, name=name)
            elif isinstance(defn, StructDef):
                self._register_struct(defn)
            elif isinstance(defn, EnumDef):
                pass  # enums are value types, no external declaration needed

    def _emit_extern_fn(self, node: ExternFnDef) -> ir.Function:
        """Declare an external C function in the LLVM module."""
        param_types: list[ir.Type] = []
        for p in node.params:
            if p.type_annotation is not None:
                resolved = self.type_mapper.resolve(p.type_annotation)
                # For FFI: map Mapanare String to i8* (C char*)
                if resolved == LLVM_STRING:
                    param_types.append(ir.IntType(8).as_pointer())
                else:
                    param_types.append(resolved)
            else:
                param_types.append(LLVM_INT)

        if node.return_type is not None:
            ret_type = self.type_mapper.resolve(node.return_type)
        else:
            ret_type = LLVM_VOID

        # Map Mapanare Int (i64) to C int (i32) for standard C functions
        fn_type = ir.FunctionType(ret_type, param_types)
        try:
            func = self.module.get_global(node.name)
        except KeyError:
            func = ir.Function(self.module, fn_type, name=node.name)
        self._functions[node.name] = func
        return func

    def _emit_impl_methods(self, impl: ImplDef) -> None:
        """Emit impl methods as standalone LLVM functions (monomorphization)."""
        for method in impl.methods:
            # Skip 'self' parameter for now — methods are emitted as free functions
            # with mangled name: TargetType_methodName
            mangled = FnDef(
                name=f"{impl.target}_{method.name}",
                public=method.public,
                type_params=method.type_params,
                params=[p for p in method.params if p.name != "self"],
                return_type=method.return_type,
                body=method.body,
                decorators=method.decorators,
            )
            self.emit_fn(mangled)

    def _register_enum(self, node: EnumDef) -> None:
        """Register an enum as a tagged union: { i32 tag, [payload_size x i8] }.

        For enums with no variant fields (simple enums), just { i32 }.
        This enables type resolution for functions that use enum types,
        even though full enum lowering is not yet implemented.
        """
        max_payload = 0
        for variant in node.variants:
            variant_size = 0
            for field_ty in variant.fields:
                try:
                    resolved = self.type_mapper.resolve(field_ty)
                    # Approximate size: 8 bytes for pointers and i64, 4 for i32, etc.
                    if resolved == LLVM_INT:
                        variant_size += 8
                    elif resolved == LLVM_FLOAT:
                        variant_size += 8
                    elif resolved == LLVM_BOOL:
                        variant_size += 1
                    elif resolved == LLVM_CHAR:
                        variant_size += 4
                    elif resolved == LLVM_STRING:
                        # MnString struct is ~24 bytes (data ptr + len + cap)
                        variant_size += 24
                    else:
                        variant_size += 8  # default: pointer-sized
                except TypeError:
                    variant_size += 8  # unresolvable type → pointer-sized placeholder
            max_payload = max(max_payload, variant_size)

        if max_payload > 0:
            llvm_ty = ir.LiteralStructType([LLVM_I32, ir.ArrayType(ir.IntType(8), max_payload)])
        else:
            llvm_ty = ir.LiteralStructType([LLVM_I32])
        self.type_mapper.register_struct(node.name, llvm_ty)

    def _forward_declare_struct(self, node: StructDef) -> None:
        """Forward-declare a struct type so other types can reference it.

        Creates a placeholder struct with pointer-sized fields. The actual
        field types are resolved in _register_struct after all types are
        forward-declared.
        """
        if node.name in self._struct_defs:
            return
        # Placeholder: each field is pointer-sized (i8*)
        placeholder_fields = [ir.IntType(8).as_pointer() for _ in node.fields]
        placeholder_ty = (
            ir.LiteralStructType(placeholder_fields)
            if placeholder_fields
            else ir.LiteralStructType([LLVM_I32])
        )
        self.type_mapper.register_struct(node.name, placeholder_ty)

    def _register_struct(self, node: StructDef) -> None:
        """Register a struct definition with resolved field types.

        Must be called after all types are forward-declared so cross-references
        between structs and enums resolve correctly.
        """
        field_types: list[ir.Type] = []
        field_names: list[str] = []
        for f in node.fields:
            try:
                field_types.append(self.type_mapper.resolve(f.type_annotation))
            except TypeError:
                # Unresolvable type (e.g., cross-module import) → pointer placeholder
                field_types.append(ir.IntType(8).as_pointer())
            field_names.append(f.name)
        llvm_ty = ir.LiteralStructType(field_types)
        self._struct_defs[node.name] = (llvm_ty, field_names)
        self.type_mapper.register_struct(node.name, llvm_ty)

    # -----------------------------------------------------------------------
    # Task 1: fn → LLVM function declarations
    # -----------------------------------------------------------------------

    def _declare_fn(self, node: FnDef) -> ir.Function:
        """Forward-declare a function (signature only, no body)."""
        if node.name in self._functions:
            return self._functions[node.name]
        param_types: list[ir.Type] = []
        for p in node.params:
            if p.type_annotation is not None:
                try:
                    param_types.append(self.type_mapper.resolve(p.type_annotation))
                except TypeError:
                    param_types.append(ir.IntType(8).as_pointer())
            else:
                param_types.append(LLVM_INT)
        if node.return_type is not None:
            try:
                ret_type = self.type_mapper.resolve(node.return_type)
            except TypeError:
                ret_type = ir.IntType(8).as_pointer()
        else:
            ret_type = LLVM_VOID
        fn_type = ir.FunctionType(ret_type, param_types)
        try:
            func = self.module.get_global(node.name)
        except KeyError:
            func = ir.Function(self.module, fn_type, name=node.name)
        for i, p in enumerate(node.params):
            if i < len(func.args):
                func.args[i].name = p.name
        self._functions[node.name] = func
        return func

    def _emit_fn_body(self, node: FnDef) -> ir.Function:
        """Emit the body of a previously declared function."""
        func = self._functions.get(node.name)
        if func is None:
            func = self._declare_fn(node)
        return self._emit_fn_impl(func, node)

    def emit_fn(self, node: FnDef) -> ir.Function:
        """Emit a function definition as an LLVM function (declare + body)."""
        func = self._declare_fn(node)
        return self._emit_fn_impl(func, node)

    def _emit_fn_impl(self, func: ir.Function, node: FnDef) -> ir.Function:
        """Internal: emit function body into an already-declared function."""
        # Resolve parameter types for body emission
        param_types: list[ir.Type] = []
        for p in node.params:
            if p.type_annotation is not None:
                try:
                    param_types.append(self.type_mapper.resolve(p.type_annotation))
                except TypeError:
                    param_types.append(ir.IntType(8).as_pointer())
            else:
                param_types.append(LLVM_INT)

        if node.return_type is not None:
            try:
                ret_type = self.type_mapper.resolve(node.return_type)
            except TypeError:
                ret_type = ir.IntType(8).as_pointer()
        else:
            ret_type = LLVM_VOID

        # Create entry block and builder
        block = func.append_basic_block(name="entry")
        old_builder = self._builder
        old_locals = self._locals.copy()
        old_mutables = self._mutables.copy()
        old_arena = self._arena_ptr
        old_temps = self._string_temps
        self._builder = ir.IRBuilder(block)
        self._locals = {}
        self._mutables = set()
        self._string_temps = []

        # Create scope arena at function entry
        arena_ptr = self.builder.call(
            self._rt_arena_create(),
            [ir.Constant(LLVM_INT, 8192)],
            name="scope_arena",
        )
        arena_alloca = self.builder.alloca(ir.IntType(8).as_pointer(), name="arena_ptr")
        self.builder.store(arena_ptr, arena_alloca)
        self._arena_ptr = arena_alloca

        # Alloca params so they can be loaded/stored like locals
        for i, p in enumerate(node.params):
            alloca = self.builder.alloca(param_types[i], name=p.name)
            self.builder.store(func.args[i], alloca)
            self._locals[p.name] = alloca

        # Emit function body
        self._emit_block(node.body)

        # Cleanup: free string temporaries and destroy arena before return
        if not self.builder.block.is_terminated:
            self._emit_scope_cleanup()
            if isinstance(ret_type, ir.VoidType):
                self.builder.ret_void()
            else:
                self.builder.ret(ir.Constant(ret_type, 0))

        # Restore state
        self._builder = old_builder
        self._locals = old_locals
        self._mutables = old_mutables
        self._arena_ptr = old_arena
        self._string_temps = old_temps

        return func

    def _emit_scope_cleanup(self) -> None:
        """Emit cleanup code: free tracked string temps and destroy the scope arena."""
        # Free tracked string temporaries
        str_free = self._rt_str_free()
        for temp_alloca in self._string_temps:
            val = self.builder.load(temp_alloca, name="tmp_str")
            self.builder.call(str_free, [val])
        # Destroy scope arena
        if self._arena_ptr is not None:
            arena = self.builder.load(self._arena_ptr, name="arena")
            self.builder.call(self._rt_arena_destroy(), [arena])

    # -----------------------------------------------------------------------
    # Block & statement emission
    # -----------------------------------------------------------------------

    def _emit_block(self, block: Block) -> ir.Value | None:
        """Emit all statements in a block, returning the last expression value."""
        result: ir.Value | None = None
        for stmt in block.stmts:
            result = self._emit_stmt(stmt)
        return result

    def _emit_stmt(self, stmt: object) -> ir.Value | None:
        """Emit a single statement."""
        if isinstance(stmt, LetBinding):
            return self._emit_let(stmt)
        if isinstance(stmt, ReturnStmt):
            return self._emit_return(stmt)
        if isinstance(stmt, ExprStmt):
            return self._emit_expr(stmt.expr)
        if isinstance(stmt, ForLoop):
            return self._emit_for(stmt)
        if isinstance(stmt, WhileLoop):
            return self._emit_while(stmt)
        return None

    # -----------------------------------------------------------------------
    # Task 7: let → stack alloca + store/load
    # -----------------------------------------------------------------------

    def _emit_let(self, node: LetBinding) -> ir.Value:
        """Emit a let binding as alloca + store."""
        val = self._emit_expr(node.value)
        alloca = self.builder.alloca(val.type, name=node.name)
        self.builder.store(val, alloca)
        self._locals[node.name] = alloca
        if node.mutable:
            self._mutables.add(node.name)
        # Track agent type for spawn expressions
        if isinstance(node.value, SpawnExpr) and isinstance(node.value.callee, Identifier):
            self._agent_types[node.name] = node.value.callee.name
        return val

    # -----------------------------------------------------------------------
    # Return statement
    # -----------------------------------------------------------------------

    def _emit_return(self, node: ReturnStmt) -> ir.Value | None:
        """Emit a return statement with scope cleanup before returning."""
        if node.value is not None:
            val = self._emit_expr(node.value)
            # If returning a string, remove it from temps (it escapes)
            self._untrack_string_temp(val)
            self._emit_scope_cleanup()
            self.builder.ret(val)
            return val
        self._emit_scope_cleanup()
        self.builder.ret_void()
        return None

    def _track_string_temp(self, val: ir.Value) -> None:
        """Track a heap-allocated string temporary for cleanup at scope exit."""
        if self._is_string_type(val):
            alloca = self.builder.alloca(LLVM_STRING, name="str_tmp")
            self.builder.store(val, alloca)
            self._string_temps.append(alloca)

    def _untrack_string_temp(self, val: ir.Value) -> None:
        """Remove a string from the temp tracker (it escapes the scope)."""
        # We can't easily match LLVM values, so we remove the last tracked
        # temp if returning a string type. This is conservative.
        if self._is_string_type(val) and self._string_temps:
            self._string_temps.pop()

    # -----------------------------------------------------------------------
    # Expression dispatch
    # -----------------------------------------------------------------------

    def _emit_expr(self, expr: object) -> ir.Value:
        """Emit an expression, returning its LLVM value."""
        if isinstance(expr, IntLiteral):
            return ir.Constant(LLVM_INT, expr.value)

        if isinstance(expr, FloatLiteral):
            return ir.Constant(LLVM_FLOAT, expr.value)

        if isinstance(expr, BoolLiteral):
            return ir.Constant(LLVM_BOOL, int(expr.value))

        if isinstance(expr, StringLiteral):
            return self._emit_string_literal(expr)

        if isinstance(expr, InterpString):
            return self._emit_interp_string(expr)

        if isinstance(expr, Identifier):
            return self._emit_identifier(expr)

        if isinstance(expr, BinaryExpr):
            return self._emit_binary(expr)

        if isinstance(expr, UnaryExpr):
            return self._emit_unary(expr)

        if isinstance(expr, CallExpr):
            return self._emit_call(expr)

        if isinstance(expr, PipeExpr):
            return self._emit_pipe(expr)

        if isinstance(expr, IfExpr):
            return self._emit_if(expr)

        if isinstance(expr, MatchExpr):
            return self._emit_match(expr)

        if isinstance(expr, AssignExpr):
            return self._emit_assign(expr)

        if isinstance(expr, CharLiteral):
            return self._emit_string_literal(StringLiteral(value=expr.value))

        if isinstance(expr, NoneLiteral):
            return ir.Constant(LLVM_INT, 0)

        if isinstance(expr, ConstructExpr):
            return self._emit_construct(expr)

        if isinstance(expr, FieldAccessExpr):
            return self._emit_field_access(expr)

        if isinstance(expr, MethodCallExpr):
            return self._emit_method_call(expr)

        if isinstance(expr, ListLiteral):
            return self._emit_list_literal(expr)

        if isinstance(expr, MapLiteral):
            raise NotImplementedError("Map literals are not yet supported in the LLVM backend")

        if isinstance(expr, IndexExpr):
            return self._emit_index(expr)

        if isinstance(expr, LambdaExpr):
            return self._emit_lambda(expr)

        if isinstance(expr, SpawnExpr):
            return self._emit_spawn(expr)

        if isinstance(expr, SendExpr):
            return self._emit_send(expr)

        if isinstance(expr, SyncExpr):
            return self._emit_sync_expr(expr)

        raise NotImplementedError(f"Cannot emit expression: {type(expr).__name__}")

    # -----------------------------------------------------------------------
    # Literals & identifiers
    # -----------------------------------------------------------------------

    def _emit_string_literal(self, node: StringLiteral) -> ir.Value:
        """Emit a string literal as a global constant."""
        encoded = node.value.encode("utf-8")
        str_const = ir.Constant(ir.ArrayType(LLVM_CHAR, len(encoded)), bytearray(encoded))
        gname = self.module.get_unique_name("str")
        global_str = ir.GlobalVariable(self.module, str_const.type, name=gname)
        global_str.global_constant = True
        global_str.initializer = str_const
        global_str.linkage = "private"

        # GEP to get i8* pointer
        zero = ir.Constant(LLVM_INT, 0)
        ptr = self.builder.gep(global_str, [zero, zero], inbounds=True, name="str_ptr")

        # Build { i8*, i64 } struct
        str_struct = ir.Constant(LLVM_STRING, ir.Undefined)
        str_struct = self.builder.insert_value(str_struct, ptr, 0, name="str_data")
        str_struct = self.builder.insert_value(
            str_struct, ir.Constant(LLVM_INT, len(encoded)), 1, name="str_len"
        )
        return str_struct

    def _rt_str_from_float(self) -> ir.Function:
        """Declare __mn_str_from_float(double) -> MnString."""
        return self._declare_runtime_fn("__mn_str_from_float", LLVM_STRING, [LLVM_FLOAT])

    def _emit_interp_string(self, node: InterpString) -> ir.Value:
        """Emit an interpolated string as a series of str conversions + concatenations."""
        result: ir.Value | None = None
        for part in node.parts:
            if isinstance(part, StringLiteral):
                val = self._emit_string_literal(part)
            else:
                raw = self._emit_expr(part)
                val = self._to_string(raw)
            if result is None:
                result = val
            else:
                concat = self.builder.call(self._rt_str_concat(), [result, val], name="interp_cat")
                self._track_string_temp(concat)
                result = concat
        if result is None:
            return self._emit_string_literal(StringLiteral(value=""))
        return result

    def _to_string(self, val: ir.Value) -> ir.Value:
        """Convert an LLVM value to MnString."""
        if self._is_string_type(val):
            return val
        if isinstance(val.type, ir.IntType):
            if val.type.width == 64:
                result = self.builder.call(self._rt_str_from_int(), [val], name="to_str")
                self._track_string_temp(result)
                return result
            if val.type.width == 1:
                # Bool → extend to i64 → str_from_int
                ext = self.builder.zext(val, LLVM_INT, name="bool_ext")
                result = self.builder.call(self._rt_str_from_int(), [ext], name="bool_to_str")
                self._track_string_temp(result)
                return result
        if isinstance(val.type, ir.DoubleType):
            result = self.builder.call(self._rt_str_from_float(), [val], name="float_to_str")
            self._track_string_temp(result)
            return result
        # Fallback: emit "<unknown>"
        return self._emit_string_literal(StringLiteral(value="<unknown>"))

    def _emit_identifier(self, node: Identifier) -> ir.Value:
        """Load a variable from its stack slot."""
        if node.name in self._locals:
            return self.builder.load(self._locals[node.name], name=node.name)
        if node.name in self._functions:
            return self._functions[node.name]
        raise NameError(f"Undefined variable: {node.name}")

    # -----------------------------------------------------------------------
    # Task 2: Arithmetic expressions → LLVM arithmetic instructions
    # -----------------------------------------------------------------------

    def _is_string_type(self, val: ir.Value) -> bool:
        """Check if an LLVM value has the MnString struct type."""
        return (
            isinstance(val.type, ir.LiteralStructType)
            and len(val.type.elements) == 2
            and isinstance(val.type.elements[0], ir.PointerType)
            and isinstance(val.type.elements[1], ir.IntType)
            and val.type.elements[1].width == 64
        )

    def _emit_binary(self, node: BinaryExpr) -> ir.Value:
        """Emit a binary expression."""
        left = self._emit_expr(node.left)
        right = self._emit_expr(node.right)

        # Determine if we're working with ints or floats
        is_float = isinstance(left.type, ir.DoubleType) or isinstance(right.type, ir.DoubleType)
        is_string = self._is_string_type(left) or self._is_string_type(right)

        # String operations via core runtime
        if is_string:
            if node.op == "+":
                result = self.builder.call(self._rt_str_concat(), [left, right], name="str_concat")
                self._track_string_temp(result)
                return result
            if node.op == "==":
                eq_i64 = self.builder.call(self._rt_str_eq(), [left, right], name="str_eq_i64")
                return self.builder.trunc(eq_i64, LLVM_BOOL, name="str_eq")
            if node.op == "!=":
                eq_i64 = self.builder.call(self._rt_str_eq(), [left, right], name="str_eq_i64")
                eq_bool = self.builder.trunc(eq_i64, LLVM_BOOL, name="str_eq")
                return self.builder.not_(eq_bool, name="str_ne")
            if node.op in ("<", "<=", ">", ">="):
                cmp_i64 = self.builder.call(self._rt_str_cmp(), [left, right], name="str_cmp")
                zero = ir.Constant(LLVM_INT, 0)
                return self.builder.icmp_signed(node.op, cmp_i64, zero, name="str_ord")
            raise NotImplementedError(f"String operator not supported: {node.op}")

        # Arithmetic
        if node.op == "+":
            if is_float:
                return self.builder.fadd(left, right, name="fadd")
            return self.builder.add(left, right, name="add")

        if node.op == "-":
            if is_float:
                return self.builder.fsub(left, right, name="fsub")
            return self.builder.sub(left, right, name="sub")

        if node.op == "*":
            if is_float:
                return self.builder.fmul(left, right, name="fmul")
            return self.builder.mul(left, right, name="mul")

        if node.op == "/":
            if is_float:
                return self.builder.fdiv(left, right, name="fdiv")
            return self.builder.sdiv(left, right, name="sdiv")

        if node.op == "%":
            if is_float:
                return self.builder.frem(left, right, name="frem")
            return self.builder.srem(left, right, name="srem")

        # Matrix multiply (@ operator) — emitted as a call to runtime matmul
        if node.op == "@":
            if "__mapanare_matmul" not in self._functions:
                # Declare the external matmul runtime function
                # Signature: mapanare_matmul(a: Tensor*, b: Tensor*) -> Tensor*
                tensor_ptr = ir.IntType(8).as_pointer()
                matmul_ty = ir.FunctionType(tensor_ptr, [tensor_ptr, tensor_ptr])
                matmul_fn = ir.Function(self.module, matmul_ty, name="__mapanare_matmul")
                self._functions["__mapanare_matmul"] = matmul_fn
            matmul_fn = self._functions["__mapanare_matmul"]
            return self.builder.call(matmul_fn, [left, right], name="matmul")

        # ---------------------------------------------------------------
        # Task 3: Boolean expressions → LLVM comparison instructions
        # ---------------------------------------------------------------

        if node.op == "==":
            if is_float:
                return self.builder.fcmp_ordered("==", left, right, name="feq")
            return self.builder.icmp_signed("==", left, right, name="eq")

        if node.op == "!=":
            if is_float:
                return self.builder.fcmp_ordered("!=", left, right, name="fne")
            return self.builder.icmp_signed("!=", left, right, name="ne")

        if node.op == "<":
            if is_float:
                return self.builder.fcmp_ordered("<", left, right, name="flt")
            return self.builder.icmp_signed("<", left, right, name="lt")

        if node.op == "<=":
            if is_float:
                return self.builder.fcmp_ordered("<=", left, right, name="fle")
            return self.builder.icmp_signed("<=", left, right, name="le")

        if node.op == ">":
            if is_float:
                return self.builder.fcmp_ordered(">", left, right, name="fgt")
            return self.builder.icmp_signed(">", left, right, name="gt")

        if node.op == ">=":
            if is_float:
                return self.builder.fcmp_ordered(">=", left, right, name="fge")
            return self.builder.icmp_signed(">=", left, right, name="ge")

        # Logical
        if node.op == "&&":
            return self.builder.and_(left, right, name="and")

        if node.op == "||":
            return self.builder.or_(left, right, name="or")

        raise NotImplementedError(f"Unknown binary operator: {node.op}")

    def _emit_unary(self, node: UnaryExpr) -> ir.Value:
        """Emit a unary expression."""
        operand = self._emit_expr(node.operand)

        if node.op == "-":
            if isinstance(operand.type, ir.DoubleType):
                return self.builder.fneg(operand, name="fneg")
            return self.builder.neg(operand, name="neg")

        if node.op == "!":
            return self.builder.not_(operand, name="not")

        raise NotImplementedError(f"Unknown unary operator: {node.op}")

    # -----------------------------------------------------------------------
    # Runtime: printf and print()
    # -----------------------------------------------------------------------

    def _ensure_printf(self) -> ir.Function:
        """Declare C printf if not already declared."""
        if self._printf_fn is not None:
            return self._printf_fn
        voidptr_ty = ir.IntType(8).as_pointer()
        printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
        self._printf_fn = ir.Function(self.module, printf_ty, name="printf")
        return self._printf_fn

    def _get_fmt_string(self, fmt: str) -> ir.Value:
        """Get or create a global format string constant, return i8* pointer."""
        if fmt in self._fmt_strings:
            gv = self._fmt_strings[fmt]
        else:
            encoded = fmt.encode("utf-8").decode("unicode_escape").encode("utf-8") + b"\x00"
            arr_ty = ir.ArrayType(LLVM_CHAR, len(encoded))
            str_const = ir.Constant(arr_ty, bytearray(encoded))
            gname = self.module.get_unique_name("fmt")
            gv = ir.GlobalVariable(self.module, arr_ty, name=gname)
            gv.global_constant = True
            gv.initializer = str_const
            gv.linkage = "private"
            self._fmt_strings[fmt] = gv
        zero = ir.Constant(LLVM_INT, 0)
        return self.builder.gep(gv, [zero, zero], inbounds=True, name="fmt_ptr")

    def _emit_print(self, args: list[object]) -> ir.Value:
        """Emit a print() call — dispatches to core runtime for strings."""
        if len(args) == 0:
            printf = self._ensure_printf()
            fmt_ptr = self._get_fmt_string("\\n")
            return self.builder.call(printf, [fmt_ptr], name="printf_call")
        val = self._emit_expr(args[0])
        # String: use __mn_str_println
        if self._is_string_type(val):
            return self.builder.call(self._rt_str_println(), [val], name="print_str")
        printf = self._ensure_printf()
        if isinstance(val.type, ir.DoubleType):
            fmt_ptr = self._get_fmt_string("%g\\n")
        elif isinstance(val.type, ir.IntType) and val.type.width == 1:
            val = self.builder.zext(val, LLVM_INT, name="bool_ext")
            fmt_ptr = self._get_fmt_string("%lld\\n")
        else:
            fmt_ptr = self._get_fmt_string("%lld\\n")
        return self.builder.call(printf, [fmt_ptr, val], name="printf_call")

    # -----------------------------------------------------------------------
    # Task 6: Function calls → LLVM call instructions
    # -----------------------------------------------------------------------

    def _emit_call(self, node: CallExpr) -> ir.Value:
        """Emit a function call instruction."""
        # Built-in: print() / println()
        if isinstance(node.callee, Identifier) and node.callee.name in ("print", "println"):
            return self._emit_print(list(node.args))

        # Built-in: len()
        if isinstance(node.callee, Identifier) and node.callee.name == "len":
            if node.args:
                val = self._emit_expr(node.args[0])
                if self._is_string_type(val):
                    return self.builder.call(self._rt_str_len(), [val], name="len")
                if val.type == LLVM_LIST:
                    list_alloca = self.builder.alloca(LLVM_LIST, name="len_tmp")
                    self.builder.store(val, list_alloca)
                    return self.builder.call(self._rt_list_len(), [list_alloca], name="len")
            return ir.Constant(LLVM_INT, 0)

        # Built-in: toString() / str()
        if isinstance(node.callee, Identifier) and node.callee.name in ("toString", "str"):
            if node.args:
                val = self._emit_expr(node.args[0])
                if isinstance(val.type, ir.IntType) and val.type.width == 64:
                    result = self.builder.call(self._rt_str_from_int(), [val], name="to_str")
                    self._track_string_temp(result)
                    return result
                if self._is_string_type(val):
                    return val
            return self._emit_string_literal(StringLiteral(value=""))

        # Built-in: int() — Float→Int truncation
        if isinstance(node.callee, Identifier) and node.callee.name == "int":
            if node.args:
                val = self._emit_expr(node.args[0])
                if isinstance(val.type, ir.DoubleType):
                    return self.builder.fptosi(val, LLVM_INT, name="to_int")
                if isinstance(val.type, ir.IntType):
                    return val
            return ir.Constant(LLVM_INT, 0)

        # Built-in: float() — Int→Float conversion
        if isinstance(node.callee, Identifier) and node.callee.name == "float":
            if node.args:
                val = self._emit_expr(node.args[0])
                if isinstance(val.type, ir.IntType) and val.type.width == 64:
                    return self.builder.sitofp(val, ir.DoubleType(), name="to_float")
                if isinstance(val.type, ir.DoubleType):
                    return val
            return ir.Constant(ir.DoubleType(), 0.0)

        # Resolve the callee
        if isinstance(node.callee, Identifier):
            if node.callee.name not in self._functions:
                raise NameError(f"Undefined function: {node.callee.name}")
            func = self._functions[node.callee.name]
        else:
            func = self._emit_expr(node.callee)

        args = [self._emit_expr(a) for a in node.args]

        # FFI coercion: adapt argument types to match function signature
        if hasattr(func, "function_type"):
            fn_ty = func.function_type
            for i, (arg, expected_ty) in enumerate(zip(args, fn_ty.args)):
                # MnString → i8*: extract the data pointer for C FFI
                if self._is_string_type(arg) and isinstance(expected_ty, ir.PointerType):
                    args[i] = self.builder.extract_value(arg, 0, name="str_to_cptr")

        return self.builder.call(func, args, name="call")

    # -----------------------------------------------------------------------
    # Task 9: |> → inlined LLVM call chain
    # -----------------------------------------------------------------------

    def _emit_pipe(self, node: PipeExpr) -> ir.Value:
        """Emit a pipe expression as an inlined call chain.

        `a |> f |> g` becomes `g(f(a))`.
        """
        left_val = self._emit_expr(node.left)

        # The right side should be a callable (Identifier or CallExpr)
        if isinstance(node.right, Identifier):
            # f(left_val)
            if node.right.name not in self._functions:
                raise NameError(f"Undefined function: {node.right.name}")
            func = self._functions[node.right.name]
            return self.builder.call(func, [left_val], name="pipe_call")

        if isinstance(node.right, CallExpr) and isinstance(node.right.callee, Identifier):
            # f(extra_args...)(left_val) → f(left_val, extra_args...)
            if node.right.callee.name not in self._functions:
                raise NameError(f"Undefined function: {node.right.callee.name}")
            func = self._functions[node.right.callee.name]
            args = [left_val] + [self._emit_expr(a) for a in node.right.args]
            return self.builder.call(func, args, name="pipe_call")

        raise NotImplementedError("Pipe RHS must be an identifier or call expression")

    # -----------------------------------------------------------------------
    # Task 4: if/else → basic blocks + branch instructions
    # -----------------------------------------------------------------------

    def _emit_if(self, node: IfExpr) -> ir.Value:
        """Emit an if/else as basic blocks with conditional branches."""
        cond = self._emit_expr(node.condition)
        func = self.builder.function

        then_bb = func.append_basic_block(name="if.then")
        else_bb = func.append_basic_block(name="if.else")
        merge_bb = func.append_basic_block(name="if.merge")

        self.builder.cbranch(cond, then_bb, else_bb)

        # Then block
        self._builder = ir.IRBuilder(then_bb)
        then_val = self._emit_block(node.then_block)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_bb)
        then_exit_bb = self.builder.block

        # Else block
        self._builder = ir.IRBuilder(else_bb)
        if node.else_block is not None:
            if isinstance(node.else_block, IfExpr):
                else_val = self._emit_if(node.else_block)
            else:
                else_val = self._emit_block(node.else_block)
        else:
            else_val = None
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_bb)
        else_exit_bb = self.builder.block

        # Merge block
        self._builder = ir.IRBuilder(merge_bb)

        # If both branches produce values of the same type, create a phi node
        if then_val is not None and else_val is not None and then_val.type == else_val.type:
            phi = self.builder.phi(then_val.type, name="if.val")
            phi.add_incoming(then_val, then_exit_bb)
            phi.add_incoming(else_val, else_exit_bb)
            return phi

        # Return a dummy zero value
        return ir.Constant(LLVM_INT, 0)

    # -----------------------------------------------------------------------
    # Task 5: for/in → LLVM loop with phi nodes
    # -----------------------------------------------------------------------

    def _emit_for(self, node: ForLoop) -> ir.Value:
        """Emit a for/in loop over a range as LLVM loop with phi node.

        Compiles `for x in start..end { body }` to:
          - preheader: compute start and end
          - header: phi node for loop variable, compare with end
          - body: emit body, increment counter
          - exit: continue after loop
        """
        from mapanare.ast_nodes import RangeExpr

        func = self.builder.function

        if not isinstance(node.iterable, RangeExpr):
            raise NotImplementedError("for/in currently only supports range iterables")

        # Evaluate range bounds in current block
        start_val = self._emit_expr(node.iterable.start)
        end_val = self._emit_expr(node.iterable.end)

        # Create blocks
        header_bb = func.append_basic_block(name="for.header")
        body_bb = func.append_basic_block(name="for.body")
        exit_bb = func.append_basic_block(name="for.exit")

        # Branch from current block to header
        preheader_bb = self.builder.block
        self.builder.branch(header_bb)

        # Header: phi node for loop variable
        self._builder = ir.IRBuilder(header_bb)
        phi = self.builder.phi(LLVM_INT, name=node.var_name)
        phi.add_incoming(start_val, preheader_bb)

        # Store loop variable so body can access it
        loop_alloca = self.builder.alloca(LLVM_INT, name=f"{node.var_name}.addr")
        self.builder.store(phi, loop_alloca)
        old_var = self._locals.get(node.var_name)
        self._locals[node.var_name] = loop_alloca

        # Condition: i < end (or i <= end for inclusive)
        if node.iterable.inclusive:
            cmp = self.builder.icmp_signed("<=", phi, end_val, name="for.cond")
        else:
            cmp = self.builder.icmp_signed("<", phi, end_val, name="for.cond")
        self.builder.cbranch(cmp, body_bb, exit_bb)

        # Body
        self._builder = ir.IRBuilder(body_bb)
        self._emit_block(node.body)

        # Increment loop variable
        next_val = self.builder.add(phi, ir.Constant(LLVM_INT, 1), name="for.next")
        if not self.builder.block.is_terminated:
            self.builder.branch(header_bb)
        body_exit_bb = self.builder.block

        # Add incoming from body back-edge
        phi.add_incoming(next_val, body_exit_bb)

        # Restore and continue at exit
        if old_var is not None:
            self._locals[node.var_name] = old_var
        else:
            del self._locals[node.var_name]
        self._builder = ir.IRBuilder(exit_bb)

        return ir.Constant(LLVM_INT, 0)

    # -----------------------------------------------------------------------
    # While loop → LLVM conditional loop
    # -----------------------------------------------------------------------

    def _emit_while(self, node: WhileLoop) -> ir.Value:
        """Emit a while loop as LLVM conditional branch loop.

        Compiles `while cond { body }` to:
          - header: evaluate condition, branch to body or exit
          - body: emit body, branch back to header
          - exit: continue after loop
        """
        func = self.builder.function

        header_bb = func.append_basic_block(name="while.header")
        body_bb = func.append_basic_block(name="while.body")
        exit_bb = func.append_basic_block(name="while.exit")

        # Branch from current block to header
        self.builder.branch(header_bb)

        # Header: evaluate condition
        self._builder = ir.IRBuilder(header_bb)
        cond_val = self._emit_expr(node.condition)
        # Ensure condition is i1 (bool)
        if cond_val.type != ir.IntType(1):
            cond_val = self.builder.icmp_signed(
                "!=", cond_val, ir.Constant(cond_val.type, 0), name="while.cond"
            )
        self.builder.cbranch(cond_val, body_bb, exit_bb)

        # Body
        self._builder = ir.IRBuilder(body_bb)
        self._emit_block(node.body)
        if not self.builder.block.is_terminated:
            self.builder.branch(header_bb)

        # Continue at exit
        self._builder = ir.IRBuilder(exit_bb)

        return ir.Constant(LLVM_INT, 0)

    # -----------------------------------------------------------------------
    # Task 8: match → LLVM switch + conditional branches
    # -----------------------------------------------------------------------

    def _emit_match(self, node: MatchExpr) -> ir.Value:
        """Emit a match expression as LLVM switch + conditional branches.

        Integer literal patterns use the LLVM switch instruction.
        Wildcard patterns become the switch default.
        """
        subject = self._emit_expr(node.subject)
        func = self.builder.function

        merge_bb = func.append_basic_block(name="match.merge")

        # Separate arms into literal arms and default (wildcard) arm
        literal_arms: list[tuple[int, MatchArm]] = []
        default_arm: MatchArm | None = None

        for arm in node.arms:
            if isinstance(arm.pattern, LiteralPattern) and isinstance(
                arm.pattern.value, IntLiteral
            ):
                literal_arms.append((arm.pattern.value.value, arm))
            elif isinstance(arm.pattern, WildcardPattern):
                default_arm = arm
            else:
                literal_arms.append((0, arm))

        # Create basic blocks for each arm
        arm_blocks: list[ir.Block] = []
        for _ in literal_arms:
            arm_blocks.append(func.append_basic_block(name="match.arm"))

        default_bb = func.append_basic_block(name="match.default")

        # Build switch instruction
        switch = self.builder.switch(subject, default_bb)
        for i, (val, _arm) in enumerate(literal_arms):
            switch.add_case(ir.Constant(LLVM_INT, val), arm_blocks[i])

        # Emit each literal arm
        arm_values: list[tuple[ir.Value, ir.Block]] = []
        for i, (_val, arm) in enumerate(literal_arms):
            self._builder = ir.IRBuilder(arm_blocks[i])
            if isinstance(arm.body, Block):
                result = self._emit_block(arm.body)
            else:
                result = self._emit_expr(arm.body)
            if not self.builder.block.is_terminated:
                self.builder.branch(merge_bb)
            if result is not None:
                arm_values.append((result, self.builder.block))

        # Emit default arm
        self._builder = ir.IRBuilder(default_bb)
        if default_arm is not None:
            if isinstance(default_arm.body, Block):
                default_result = self._emit_block(default_arm.body)
            else:
                default_result = self._emit_expr(default_arm.body)
        else:
            default_result = ir.Constant(LLVM_INT, 0)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_bb)
        if default_result is not None:
            arm_values.append((default_result, self.builder.block))

        # Merge block
        self._builder = ir.IRBuilder(merge_bb)

        # If all arms produced values of same type, phi them together
        if arm_values and all(v.type == arm_values[0][0].type for v, _bb in arm_values):
            phi = self.builder.phi(arm_values[0][0].type, name="match.val")
            for val, bb in arm_values:
                phi.add_incoming(val, bb)
            return phi

        return ir.Constant(LLVM_INT, 0)

    # -----------------------------------------------------------------------
    # Phase 2.1: Agent codegen — native agents via C runtime
    # -----------------------------------------------------------------------

    def _sizeof_type(self, ty: ir.Type) -> int:
        """Return the size in bytes of an LLVM type (for boxing/unboxing)."""
        if isinstance(ty, ir.IntType):
            return int(max(1, ty.width // 8))
        if isinstance(ty, ir.DoubleType):
            return 8
        if isinstance(ty, ir.LiteralStructType):
            return sum(self._sizeof_type(e) for e in ty.elements)
        if isinstance(ty, ir.PointerType):
            return 8
        return 8

    def _emit_agent(self, agent: AgentDef) -> None:
        """Emit agent definition: handler method as function + C-compatible wrapper."""
        self._agent_defs[agent.name] = agent

        # Emit handler methods as standalone LLVM functions
        for method in agent.methods:
            method_fn = FnDef(
                name=f"{agent.name}_{method.name}",
                params=method.params,
                return_type=method.return_type,
                body=method.body,
            )
            self.emit_fn(method_fn)

        # Emit C-compatible handler wrapper
        self._emit_agent_handler(agent)

    def _emit_agent_handler(self, agent: AgentDef) -> ir.Function:
        """Emit C-compatible handler wrapper: unbox msg, call method, box output."""
        handler_name = f"__mn_handler_{agent.name}"
        fn_ty = ir.FunctionType(LLVM_I32, [LLVM_PTR, LLVM_PTR, LLVM_PTR.as_pointer()])
        func = ir.Function(self.module, fn_ty, name=handler_name)
        func.args[0].name = "agent_data"
        func.args[1].name = "msg"
        func.args[2].name = "out_msg"

        block = func.append_basic_block("entry")
        old_builder = self._builder
        self._builder = ir.IRBuilder(block)

        # Find handler method (first method or one named "handle")
        handler_method = None
        for m in agent.methods:
            if m.name == "handle" or handler_method is None:
                handler_method = m

        has_input = len(agent.inputs) > 0
        has_output = len(agent.outputs) > 0

        if handler_method and has_input:
            # Determine input LLVM type
            input_type = self.type_mapper.resolve(agent.inputs[0].type_annotation)

            # Unbox: cast void* to typed pointer, load value
            msg_typed = self.builder.bitcast(
                func.args[1], input_type.as_pointer(), name="msg_typed"
            )
            msg_val = self.builder.load(msg_typed, name="msg_val")

            # Free the message box
            self.builder.call(self._rt_free(), [func.args[1]])

            # Call the handler method function
            method_fn = self._functions[f"{agent.name}_{handler_method.name}"]
            result = self.builder.call(method_fn, [msg_val], name="result")

            if has_output and not isinstance(result.type, ir.VoidType):
                # Box the result
                type_size = self._sizeof_type(result.type)
                out_box = self.builder.call(
                    self._rt_alloc(), [ir.Constant(LLVM_INT, type_size)], name="out_box"
                )
                out_typed = self.builder.bitcast(
                    out_box, result.type.as_pointer(), name="out_typed"
                )
                self.builder.store(result, out_typed)
                self.builder.store(out_box, func.args[2])
            else:
                self.builder.store(ir.Constant(LLVM_PTR, None), func.args[2])
        else:
            self.builder.store(ir.Constant(LLVM_PTR, None), func.args[2])

        self.builder.ret(ir.Constant(LLVM_I32, 0))

        self._builder = old_builder
        self._functions[handler_name] = func
        return func

    def _emit_spawn(self, expr: SpawnExpr) -> ir.Value:
        """Emit spawn: allocate agent, init with handler, start thread."""
        agent_name = expr.callee.name if isinstance(expr.callee, Identifier) else "Agent"

        # Get handler function pointer
        handler_name = f"__mn_handler_{agent_name}"
        handler_fn = self._functions.get(handler_name)
        if handler_fn is None:
            raise NameError(f"Unknown agent: {agent_name}")

        # Create C string for agent name
        name_bytes = agent_name.encode("utf-8") + b"\x00"
        arr_ty = ir.ArrayType(ir.IntType(8), len(name_bytes))
        name_const = ir.Constant(arr_ty, bytearray(name_bytes))
        gname = self.module.get_unique_name("agent_name")
        global_name = ir.GlobalVariable(self.module, name_const.type, name=gname)
        global_name.global_constant = True
        global_name.initializer = name_const
        global_name.linkage = "private"
        zero = ir.Constant(LLVM_INT, 0)
        name_ptr = self.builder.gep(global_name, [zero, zero], inbounds=True, name="name_ptr")

        # Bitcast handler function to void* for FFI
        handler_ptr = self.builder.bitcast(handler_fn, LLVM_PTR, name="handler")

        # Call mapanare_agent_new(name, handler, data, inbox_cap, outbox_cap)
        agent_ptr = self.builder.call(
            self._rt_agent_new(),
            [
                name_ptr,
                handler_ptr,
                ir.Constant(LLVM_PTR, None),  # agent_data (NULL for stateless)
                ir.Constant(LLVM_I32, 256),
                ir.Constant(LLVM_I32, 256),
            ],
            name="agent",
        )

        # Apply supervision policy from decorators
        agent_def = self._agent_defs.get(agent_name)
        if agent_def:
            self._apply_supervision(agent_ptr, agent_def)

        # Spawn (start thread)
        self.builder.call(self._rt_agent_spawn(), [agent_ptr])

        return agent_ptr

    def _apply_supervision(self, agent_ptr: ir.Value, agent_def: AgentDef) -> None:
        """Set supervision policy based on agent decorators."""
        restart_policy = 0  # MAPANARE_RESTART_STOP
        max_restarts = 0

        for dec in agent_def.decorators:
            if dec.name == "restart":
                restart_policy = 1  # MAPANARE_RESTART_RESTART
                if dec.args and isinstance(dec.args[0], IntLiteral):
                    max_restarts = dec.args[0].value
                else:
                    max_restarts = 3  # default

        if restart_policy != 0:
            self.builder.call(
                self._rt_agent_set_restart_policy(),
                [
                    agent_ptr,
                    ir.Constant(LLVM_I32, restart_policy),
                    ir.Constant(LLVM_I32, max_restarts),
                ],
            )

    def _emit_send(self, expr: SendExpr) -> ir.Value:
        """Emit send: box value and push to agent's inbox."""
        # Get agent pointer from target (agent.channel field access)
        if isinstance(expr.target, FieldAccessExpr):
            agent_ptr = self._emit_expr(expr.target.object)
        else:
            agent_ptr = self._emit_expr(expr.target)

        # Emit value
        value = self._emit_expr(expr.value)

        # Box the value: allocate + store
        type_size = self._sizeof_type(value.type)
        box_ptr = self.builder.call(
            self._rt_alloc(), [ir.Constant(LLVM_INT, type_size)], name="msg_box"
        )
        typed_ptr = self.builder.bitcast(box_ptr, value.type.as_pointer(), name="msg_typed")
        self.builder.store(value, typed_ptr)

        # Send to agent inbox
        result = self.builder.call(self._rt_agent_send(), [agent_ptr, box_ptr], name="send_rc")
        return result

    def _emit_sync_expr(self, expr: SyncExpr) -> ir.Value:
        """Emit sync: blocking receive from agent's outbox, unbox result."""
        inner = expr.expr

        # Get agent pointer
        if isinstance(inner, FieldAccessExpr):
            agent_ptr = self._emit_expr(inner.object)
        else:
            agent_ptr = self._emit_expr(inner)

        # Allocate space for the output pointer
        out_alloca = self.builder.alloca(LLVM_PTR, name="recv_out")

        # Call recv_blocking
        self.builder.call(self._rt_agent_recv_blocking(), [agent_ptr, out_alloca], name="recv_rc")

        # Load the output pointer
        out_ptr = self.builder.load(out_alloca, name="out_ptr")

        # Determine output type from agent definition
        output_type = LLVM_INT  # default
        if isinstance(inner, FieldAccessExpr) and isinstance(inner.object, Identifier):
            agent_type_name = self._agent_types.get(inner.object.name)
            if agent_type_name and agent_type_name in self._agent_defs:
                agent_def = self._agent_defs[agent_type_name]
                for output in agent_def.outputs:
                    if output.name == inner.field_name:
                        output_type = self.type_mapper.resolve(output.type_annotation)
                        break
                else:
                    # If field name doesn't match, use first output type
                    if agent_def.outputs:
                        output_type = self.type_mapper.resolve(agent_def.outputs[0].type_annotation)

        # Unbox: cast void* to typed pointer, load value
        typed_ptr = self.builder.bitcast(out_ptr, output_type.as_pointer(), name="out_typed")
        result = self.builder.load(typed_ptr, name="result")

        # Free the box
        self.builder.call(self._rt_free(), [out_ptr])

        return result

    # -----------------------------------------------------------------------
    # Tensor runtime helpers (Phase 5.1)
    # -----------------------------------------------------------------------

    def _declare_tensor_runtime(self, name: str) -> ir.Function:
        """Declare an external tensor runtime function if not already declared.

        All tensor runtime functions use opaque pointer (i8*) for tensor structs,
        following C FFI conventions.
        """
        if name in self._functions:
            return self._functions[name]

        tensor_ptr = ir.IntType(8).as_pointer()
        # LLVM_INT used as device kind enum (i64)
        device_kind_ty = LLVM_INT

        # Element-wise ops: (Tensor*, Tensor*) -> Tensor*
        if name in (
            "__mapanare_tensor_add",
            "__mapanare_tensor_sub",
            "__mapanare_tensor_mul",
            "__mapanare_tensor_div",
            "__mapanare_matmul",
        ):
            fn_ty = ir.FunctionType(tensor_ptr, [tensor_ptr, tensor_ptr])
        # GPU dispatch ops: (Tensor*, Tensor*, device_kind) -> Tensor*
        elif name in (
            "__mapanare_tensor_add_dispatch",
            "__mapanare_tensor_sub_dispatch",
            "__mapanare_tensor_mul_dispatch",
            "__mapanare_tensor_div_dispatch",
            "__mapanare_tensor_matmul_dispatch",
        ):
            fn_ty = ir.FunctionType(tensor_ptr, [tensor_ptr, tensor_ptr, device_kind_ty])
        # Tensor alloc: (i64 ndim, i64* shape, i64 elem_size) -> Tensor*
        elif name == "__mapanare_tensor_alloc":
            fn_ty = ir.FunctionType(tensor_ptr, [LLVM_INT, LLVM_INT.as_pointer(), LLVM_INT])
        # Tensor free: (Tensor*) -> void
        elif name == "__mapanare_tensor_free":
            fn_ty = ir.FunctionType(LLVM_VOID, [tensor_ptr])
        # Shape check: (Tensor*, Tensor*) -> i1
        elif name == "__mapanare_tensor_shape_eq":
            fn_ty = ir.FunctionType(LLVM_BOOL, [tensor_ptr, tensor_ptr])
        # GPU detection: () -> i8* (detection struct pointer)
        elif name == "__mapanare_detect_gpus":
            fn_ty = ir.FunctionType(tensor_ptr, [])
        else:
            raise ValueError(f"Unknown tensor runtime function: {name}")

        func = ir.Function(self.module, fn_ty, name=name)
        self._functions[name] = func
        return func

    def _emit_tensor_elementwise_loop(self, a_ptr: ir.Value, b_ptr: ir.Value, op: str) -> ir.Value:
        """Emit an element-wise tensor operation as a vectorizable loop.

        Generates LLVM IR with loop structure that LLVM's auto-vectorizer
        can convert to SIMD instructions (SSE/AVX/NEON) when optimizing.

        For the interpreter/Python path, we call the runtime helper instead.
        """
        # Call the appropriate runtime function
        if op == "+":
            fn = self._declare_tensor_runtime("__mapanare_tensor_add")
        elif op == "-":
            fn = self._declare_tensor_runtime("__mapanare_tensor_sub")
        elif op == "*":
            fn = self._declare_tensor_runtime("__mapanare_tensor_mul")
        elif op == "/":
            fn = self._declare_tensor_runtime("__mapanare_tensor_div")
        else:
            raise NotImplementedError(f"Unknown tensor elementwise op: {op}")

        return self.builder.call(fn, [a_ptr, b_ptr], name=f"tensor_{op}")

    # -----------------------------------------------------------------------
    # Assignment expression
    # -----------------------------------------------------------------------

    def _emit_assign(self, node: AssignExpr) -> ir.Value:
        """Emit an assignment to a mutable variable."""
        if not isinstance(node.target, Identifier):
            raise NotImplementedError("Assignment target must be an identifier")
        name = node.target.name
        if name not in self._locals:
            raise NameError(f"Undefined variable: {name}")

        val = self._emit_expr(node.value)

        if node.op == "=":
            self.builder.store(val, self._locals[name])
            return val

        # Compound assignment: +=, -=, *=, /=
        current = self.builder.load(self._locals[name], name=f"{name}.cur")
        is_float = isinstance(current.type, ir.DoubleType)
        is_string = self._is_string_type(current)
        if node.op == "+=":
            if is_string:
                result = self.builder.call(self._rt_str_concat(), [current, val], name="str_append")
                # Free the old string after concat has read it
                self.builder.call(self._rt_str_free(), [current])
            elif is_float:
                result = self.builder.fadd(current, val, name="fadd_assign")
            else:
                result = self.builder.add(current, val, name="add_assign")
        elif node.op == "-=":
            if is_float:
                result = self.builder.fsub(current, val, name="fsub_assign")
            else:
                result = self.builder.sub(current, val, name="sub_assign")
        elif node.op == "*=":
            if is_float:
                result = self.builder.fmul(current, val, name="fmul_assign")
            else:
                result = self.builder.mul(current, val, name="mul_assign")
        elif node.op == "/=":
            if is_float:
                result = self.builder.fdiv(current, val, name="fdiv_assign")
            else:
                result = self.builder.sdiv(current, val, name="div_assign")
        else:
            raise NotImplementedError(f"Unknown assignment operator: {node.op}")

        self.builder.store(result, self._locals[name])
        return result

    # -----------------------------------------------------------------------
    # Phase 6.1: Struct construction and field access
    # -----------------------------------------------------------------------

    def _emit_construct(self, node: ConstructExpr) -> ir.Value:
        """Emit struct construction: `Token { tok_type: x, value: y, ... }`."""
        if node.name not in self._struct_defs:
            raise NameError(f"Unknown struct type: {node.name}")
        llvm_ty, field_names = self._struct_defs[node.name]

        # Build field value map from the ConstructExpr
        field_vals: dict[str, ir.Value] = {}
        for fi in node.fields:
            field_vals[fi.name] = self._emit_expr(fi.value)

        # Construct the struct value using insertvalue
        struct_val = ir.Constant(llvm_ty, ir.Undefined)
        for i, fname in enumerate(field_names):
            if fname in field_vals:
                struct_val = self.builder.insert_value(
                    struct_val, field_vals[fname], i, name=f"{node.name}.{fname}"
                )
            else:
                # Default: zero-initialize missing fields
                field_ty = llvm_ty.elements[i]
                is_struct = isinstance(field_ty, ir.LiteralStructType)
                default = ir.Undefined if is_struct else 0
                struct_val = self.builder.insert_value(
                    struct_val, ir.Constant(field_ty, default), i, name=f"{node.name}.{fname}"
                )
        return struct_val

    def _emit_field_access(self, node: FieldAccessExpr) -> ir.Value:
        """Emit field access: `token.value`, `lexer.pos`."""
        # Agent field access (e.g., agent.input, agent.output) — return agent pointer
        if isinstance(node.object, Identifier) and node.object.name in self._agent_types:
            return self._emit_expr(node.object)

        obj = self._emit_expr(node.object)

        # Try to find the struct type in our registry
        for sname, (stype, field_names) in self._struct_defs.items():
            if obj.type == stype:
                if node.field_name in field_names:
                    idx = field_names.index(node.field_name)
                    return self.builder.extract_value(obj, idx, name=f"{sname}.{node.field_name}")

        # For MnString, .len is at index 1
        if self._is_string_type(obj):
            if node.field_name == "len":
                return self.builder.extract_value(obj, 1, name="str_len")

        raise NameError(f"Unknown field: {node.field_name}")

    # -----------------------------------------------------------------------
    # Phase 6.1: Method calls
    # -----------------------------------------------------------------------

    def _emit_method_call(self, node: MethodCallExpr) -> ir.Value:
        """Emit method calls, dispatching to runtime for built-in types."""
        obj = self._emit_expr(node.object)
        args = [self._emit_expr(a) for a in node.args]

        # String methods
        if self._is_string_type(obj):
            if node.method == "len":
                return self.builder.call(self._rt_str_len(), [obj], name="str_len")
            if node.method == "char_at" and len(args) == 1:
                return self.builder.call(self._rt_str_char_at(), [obj, args[0]], name="str_char_at")
            if node.method == "byte_at" and len(args) == 1:
                return self.builder.call(self._rt_str_byte_at(), [obj, args[0]], name="str_byte_at")
            if node.method == "substr" and len(args) == 2:
                return self.builder.call(
                    self._rt_str_substr(), [obj, args[0], args[1]], name="str_substr"
                )
            if node.method == "starts_with" and len(args) == 1:
                return self.builder.call(self._rt_str_starts_with(), [obj, args[0]], name="str_sw")
            if node.method == "ends_with" and len(args) == 1:
                return self.builder.call(self._rt_str_ends_with(), [obj, args[0]], name="str_ew")
            if node.method == "find" and len(args) == 1:
                return self.builder.call(self._rt_str_find(), [obj, args[0]], name="str_find")

        raise NotImplementedError(f"Method call not supported: .{node.method}()")

    # -----------------------------------------------------------------------
    # Phase 6.1: List operations
    # -----------------------------------------------------------------------

    def _emit_list_literal(self, node: ListLiteral) -> ir.Value:
        """Emit a list literal: `[a, b, c]` or `[]`."""
        if not node.elements:
            # Empty list — default to i64-sized elements
            return self.builder.call(
                self._rt_list_new(), [ir.Constant(LLVM_INT, 8)], name="empty_list"
            )

        # Evaluate all elements to determine the element type
        vals = [self._emit_expr(e) for e in node.elements]
        elem_ty = vals[0].type

        # Determine element size
        if isinstance(elem_ty, ir.IntType):
            elem_size = elem_ty.width // 8
        elif isinstance(elem_ty, ir.DoubleType):
            elem_size = 8
        elif isinstance(elem_ty, ir.LiteralStructType):
            # Approximate: sum of element sizes
            # For MnString { i8*, i64 } = 16 bytes on 64-bit
            elem_size = sum(
                8 if isinstance(e, (ir.PointerType, ir.IntType, ir.DoubleType)) else 8
                for e in elem_ty.elements
            )
        else:
            elem_size = 8

        # Create list
        list_val = self.builder.call(
            self._rt_list_new(), [ir.Constant(LLVM_INT, elem_size)], name="list"
        )

        # Alloca the list so we can pass &list to push
        list_alloca = self.builder.alloca(LLVM_LIST, name="list_alloca")
        self.builder.store(list_val, list_alloca)

        # Push each element
        for val in vals:
            # Alloca the element to get a pointer
            elem_alloca = self.builder.alloca(val.type, name="elem_tmp")
            self.builder.store(val, elem_alloca)
            elem_ptr = self.builder.bitcast(
                elem_alloca, ir.IntType(8).as_pointer(), name="elem_ptr"
            )
            self.builder.call(self._rt_list_push(), [list_alloca, elem_ptr])

        return self.builder.load(list_alloca, name="list_result")

    def _emit_index(self, node: IndexExpr) -> ir.Value:
        """Emit index expression: `list[i]` or `str[i]`."""
        obj = self._emit_expr(node.object)
        idx = self._emit_expr(node.index)

        # String indexing → char_at
        if self._is_string_type(obj):
            return self.builder.call(self._rt_str_char_at(), [obj, idx], name="str_idx")

        # List indexing — returns raw pointer, needs cast
        if obj.type == LLVM_LIST:
            list_alloca = self.builder.alloca(LLVM_LIST, name="list_tmp")
            self.builder.store(obj, list_alloca)
            raw_ptr = self.builder.call(
                self._rt_list_get(), [list_alloca, idx], name="list_elem_ptr"
            )
            # Default: load as i64
            typed_ptr = self.builder.bitcast(raw_ptr, LLVM_INT.as_pointer(), name="typed_ptr")
            return self.builder.load(typed_ptr, name="list_elem")

        raise NotImplementedError(f"Index not supported on type: {obj.type}")

    # -----------------------------------------------------------------------
    # Phase 6.1: Lambda (closure-less function pointer)
    # -----------------------------------------------------------------------

    def _emit_lambda(self, node: LambdaExpr) -> ir.Value:
        """Emit a lambda as an anonymous function. Returns function pointer."""
        # Generate unique name
        lambda_name = self.module.get_unique_name("lambda")

        # Build parameter types (default to i64 if no annotation)
        param_types: list[ir.Type] = []
        for p in node.params:
            if p.type_annotation is not None:
                param_types.append(self.type_mapper.resolve(p.type_annotation))
            else:
                param_types.append(LLVM_INT)

        # Infer return type from body — default to i64
        ret_type = LLVM_INT

        fn_type = ir.FunctionType(ret_type, param_types)
        func = ir.Function(self.module, fn_type, name=lambda_name)
        for i, p in enumerate(node.params):
            func.args[i].name = p.name
        self._functions[lambda_name] = func

        # Save state
        old_builder = self._builder
        old_locals = self._locals.copy()
        old_mutables = self._mutables.copy()

        # Build lambda body
        block = func.append_basic_block(name="entry")
        self._builder = ir.IRBuilder(block)
        self._locals = {}
        self._mutables = set()

        for i, p in enumerate(node.params):
            alloca = self.builder.alloca(param_types[i], name=p.name)
            self.builder.store(func.args[i], alloca)
            self._locals[p.name] = alloca

        if isinstance(node.body, Block):
            self._emit_block(node.body)
        else:
            val = self._emit_expr(node.body)
            self.builder.ret(val)

        if not self.builder.block.is_terminated:
            self.builder.ret(ir.Constant(ret_type, 0))

        # Restore state
        self._builder = old_builder
        self._locals = old_locals
        self._mutables = old_mutables

        return func

    # -----------------------------------------------------------------------
    # Phase 6.1: Extended print support (string-aware)
    # -----------------------------------------------------------------------
