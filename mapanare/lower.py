"""AST → MIR lowering pass.

Walks the typed AST (after semantic analysis) and produces MIR functions
with basic blocks. Nested expressions become flat three-address code and
control flow becomes explicit jumps/branches.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from typing import Any

from mapanare.ast_nodes import (
    AgentDef,
    AssertStmt,
    AssignExpr,
    ASTNode,
    AsyncFnDef,
    AwaitExpr,
    BinaryExpr,
    Block,
    BoolLiteral,
    BreakStmt,
    CallExpr,
    ChainedCompare,
    CharLiteral,
    CompClause,
    Comprehension,
    ConstDef,
    ConstructExpr,
    ConstructorPattern,
    ContinueStmt,
    Definition,
    DocComment,
    EnumDef,
    ErrExpr,
    ErrorPropExpr,
    ExportDef,
    Expr,
    ExprStmt,
    ExternFnDef,
    FieldAccessExpr,
    FieldInit,
    FloatLiteral,
    FnDef,
    FnType,
    ForAwaitLoop,
    ForLoop,
    GenericType,
    Identifier,
    IdentPattern,
    IfExpr,
    IfLetExpr,
    ImplDef,
    ImportDef,
    IndexExpr,
    InterpString,
    IntLiteral,
    LambdaExpr,
    LetBinding,
    LetDestructure,
    LetElseStmt,
    ListLiteral,
    MapLiteral,
    MatchArm,
    MatchExpr,
    MethodCallExpr,
    ModuleLetDef,
    NamedType,
    NamespaceAccessExpr,
    NoneLiteral,
    OkExpr,
    PassStmt,
    PipeDef,
    PipeExpr,
    PrintStmt,
    Program,
    RangeExpr,
    ReturnStmt,
    SendExpr,
    SignalDecl,
    SignalExpr,
    SomeExpr,
    Span,
    SpawnExpr,
    Stmt,
    StreamDecl,
    StringLiteral,
    StructDef,
    StructPattern,
    StructUpdate,
    SyncExpr,
    TensorLiteral,
    TraitDef,
    TypeExpr,
    UnaryExpr,
    WhileLetStmt,
    WhileLoop,
    WildcardPattern,
)
from mapanare.mir import (
    AgentSend,
    AgentSpawn,
    AgentSync,
    Assert,
    BasicBlock,
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
    MIRAgentInfo,
    MIRFunction,
    MIRModule,
    MIRParam,
    MIRPipeInfo,
    MIRType,
    Move,
    Phi,
    Return,
    SignalGet,
    SignalInit,
    SignalSet,
    SourceSpan,
    StreamInit,
    StreamOp,
    StreamOpKind,
    StructInit,
    Switch,
    TensorInit,
    UnaryOp,
    UnaryOpKind,
    Unwrap,
    Value,
    WrapErr,
    WrapNone,
    WrapOk,
    WrapSome,
    mir_any,
    mir_bool,
    mir_float,
    mir_int,
    mir_string,
    mir_unknown,
    mir_void,
)
from mapanare.types import TypeInfo, TypeKind, kind_from_name

# ---------------------------------------------------------------------------
# Operator mapping from AST strings to MIR enums
# ---------------------------------------------------------------------------

_BINOP_MAP: dict[str, BinOpKind] = {
    "+": BinOpKind.ADD,
    "-": BinOpKind.SUB,
    "*": BinOpKind.MUL,
    "/": BinOpKind.DIV,
    "%": BinOpKind.MOD,
    "==": BinOpKind.EQ,
    "!=": BinOpKind.NE,
    "<": BinOpKind.LT,
    ">": BinOpKind.GT,
    "<=": BinOpKind.LE,
    ">=": BinOpKind.GE,
    "&&": BinOpKind.AND,
    "||": BinOpKind.OR,
}

_UNARYOP_MAP: dict[str, UnaryOpKind] = {
    "-": UnaryOpKind.NEG,
    "!": UnaryOpKind.NOT,
}

_STREAM_OP_MAP: dict[str, StreamOpKind] = {
    "map": StreamOpKind.MAP,
    "filter": StreamOpKind.FILTER,
    "fold": StreamOpKind.FOLD,
    "take": StreamOpKind.TAKE,
    "skip": StreamOpKind.SKIP,
    "collect": StreamOpKind.COLLECT,
}

_ARITH_TRAIT_MAP: dict[str, str] = {"+": "add", "-": "sub", "*": "mul", "/": "div"}


def _ast_span_to_mir(node: ASTNode | None) -> SourceSpan | None:
    """Convert an AST node's span to a MIR SourceSpan, or None if unavailable."""
    if node is None or not hasattr(node, "span") or node.span is None:
        return None
    s = node.span
    return SourceSpan(line=s.line, column=s.column, end_line=s.end_line, end_column=s.end_column)


def _stmt_diverges(stmt: object) -> bool:
    """v5.20.0 Te.5.E: does this statement guarantee non-fall-through?

    Used to enforce the let-else divergence requirement (D5/D6).
    The accepted divergent shapes are: ReturnStmt, BreakStmt,
    ContinueStmt, calls to `panic`/`abort`, and nested control-flow
    where every leaf branch diverges.
    """
    from mapanare.ast_nodes import (
        BreakStmt,
        CallExpr,
        ContinueStmt,
        ExprStmt,
        Identifier,
        IfExpr,
        MatchExpr,
        ReturnStmt,
    )

    if isinstance(stmt, (ReturnStmt, BreakStmt, ContinueStmt)):
        return True
    if isinstance(stmt, ExprStmt):
        e = stmt.expr
        if isinstance(e, CallExpr) and isinstance(e.callee, Identifier):
            if e.callee.name in ("panic", "abort", "exit"):
                return True
        if isinstance(e, MatchExpr):
            return bool(e.arms) and all(_expr_or_block_diverges(arm.body) for arm in e.arms)
        if isinstance(e, IfExpr):
            then_div = _block_diverges(e.then_block)
            if e.else_block is None:
                return False
            if isinstance(e.else_block, IfExpr):
                # Recurse via wrapping — treat as ExprStmt for divergence.
                return then_div and _stmt_diverges(ExprStmt(expr=e.else_block))
            return then_div and _block_diverges(e.else_block)
    return False


def _expr_or_block_diverges(node: object) -> bool:
    """Helper for match-arm divergence — body may be Block or Expr."""
    from mapanare.ast_nodes import Block, Expr, ExprStmt

    if isinstance(node, Block):
        return _block_diverges(node)
    if isinstance(node, Expr):
        return _stmt_diverges(ExprStmt(expr=node))
    return False


def _block_diverges(block: object) -> bool:
    """v5.20.0 Te.5.E: does this Block guarantee non-fall-through?"""
    from mapanare.ast_nodes import Block

    if not isinstance(block, Block) or not block.stmts:
        return False
    return _stmt_diverges(block.stmts[-1])


# ---------------------------------------------------------------------------
# Type resolution helpers
# ---------------------------------------------------------------------------


def _resolve_type_expr(te: TypeExpr | None) -> MIRType:
    """Convert an AST TypeExpr to a MIRType."""
    if te is None:
        return mir_unknown()
    if isinstance(te, NamedType):
        k = kind_from_name(te.name)
        if k == TypeKind.UNKNOWN and te.name:
            return MIRType(TypeInfo(kind=TypeKind.STRUCT, name=te.name))
        return MIRType(TypeInfo(kind=k))
    if isinstance(te, GenericType):
        args = [_resolve_type_expr(a).type_info for a in te.args]
        k = kind_from_name(te.name)
        if k != TypeKind.UNKNOWN:
            return MIRType(TypeInfo(kind=k, args=args))
        return MIRType(TypeInfo(kind=TypeKind.STRUCT, name=te.name, args=args))
    if isinstance(te, FnType):
        # v4.103.0: closure type annotations (docket #5). Previously
        # FnType was handled by the `return mir_unknown()` fallback,
        # which left parameters declared with `fn(T) -> T` with a
        # UNKNOWN MIRType. The lowerer then could not tell that
        # `f(x)` inside `fn apply(f: fn(Int)->Int, x: Int)` should
        # be an indirect call through the value; it lowered to a
        # direct `@f(x)` call and linking failed. Resolve FnType to
        # a MIRType with kind=FN so the call-lowering path sees a
        # callable variable and emits a ClosureCall.
        params = [_resolve_type_expr(p).type_info for p in te.param_types]
        ret = _resolve_type_expr(te.return_type).type_info
        return MIRType(TypeInfo(kind=TypeKind.FN, args=params + [ret]))
    return mir_unknown()


def _type_for_literal(expr: Expr) -> MIRType:
    """Return the MIR type for a literal expression."""
    if isinstance(expr, IntLiteral):
        return mir_int()
    if isinstance(expr, FloatLiteral):
        return mir_float()
    if isinstance(expr, BoolLiteral):
        return mir_bool()
    if isinstance(expr, (StringLiteral, InterpString, CharLiteral)):
        return mir_string()
    if isinstance(expr, NoneLiteral):
        return MIRType(TypeInfo(kind=TypeKind.OPTION))
    return mir_unknown()


# ---------------------------------------------------------------------------
# Lowerer
# ---------------------------------------------------------------------------


@dataclass
class _VarInfo:
    """Tracks the current SSA value for a variable."""

    current: Value
    mutable: bool = False


class MIRLowerer:
    """Lowers a typed AST into MIR."""

    def __init__(
        self,
        imported_return_types: dict[str, "MIRType"] | None = None,
        imported_struct_defs: dict[str, list[tuple[str, "MIRType"]]] | None = None,
        imported_enum_defs: dict[str, list[tuple[str, list["MIRType"]]]] | None = None,
    ) -> None:
        self._module = MIRModule()
        self._fn: MIRFunction | None = None
        self._block: BasicBlock | None = None
        self._tmp_counter = 0
        self._block_counter = 0
        # v5.20.0 Te.5.C: separate counter for synthesized struct-update
        # base tmps so they don't perturb the global %tN sequence.
        self._struct_update_counter = 0
        # v5.21.0 Te.6: separate counter for synthesized chained-compare
        # tmps (see _lower_chained_compare).
        self._chain_compare_counter = 0
        # Variable name → current SSA value
        self._vars: dict[str, _VarInfo] = {}
        # Scope stack for nested scopes
        self._scope_stack: list[dict[str, _VarInfo]] = []
        # Impl methods: (type_name, method_name) → MIR function name
        self._impl_methods: dict[tuple[str, str], str] = {}
        # Struct info: name -> list of field names
        self._struct_fields: dict[str, list[str]] = {}
        # Lambda variable mappings: variable name -> lambda function name
        self._lambda_vars: dict[str, str] = {}
        # Closure variable names: variables bound to closures (lambdas with captures)
        self._closure_vars: set[str] = set()
        # Active closure captures: set during lambda lowering so _lower_fn can inject env loads
        self._pending_captures: list[tuple[str, MIRType]] | None = None
        # Enum info: name → list of variant names
        self._enum_variants: dict[str, list[str]] = {}
        # Decorator metadata for functions
        self._fn_decorators: dict[str, list[str]] = {}
        # Function parameter types: fn_name → [MIRType] for patching empty list args
        self._fn_param_types: dict[str, list[MIRType]] = {}
        # Current source span — set by _lower_expr/_lower_stmt for debug info
        self._current_span: SourceSpan | None = None
        # Module-level constants: name → (MIRType, literal value)
        self._module_consts: dict[str, tuple[MIRType, Any]] = {}
        # Loop exit label stack for break statements
        self._loop_exit_stack: list[str] = []
        self._loop_header_stack: list[str] = []
        # Function return types: fn_name → MIRType (populated in first pass).
        # Pre-seed with imported function return types so cross-module calls
        # get correct dest types during lowering.
        self._fn_return_types: dict[str, MIRType] = dict(imported_return_types or {})
        # Imported struct definitions: struct_name → [(field_name, MIRType)]
        self._imported_struct_defs: dict[str, list[tuple[str, MIRType]]] = dict(
            imported_struct_defs or {}
        )
        # Imported enum definitions: enum_name → [(variant_name, [MIRType])]
        self._imported_enum_defs: dict[str, list[tuple[str, list[MIRType]]]] = dict(
            imported_enum_defs or {}
        )
        # Generics monomorphization state
        self._generic_fn_defs: dict[str, FnDef | AsyncFnDef] = {}  # name → AST of generic fn
        self._specialized_fns: set[str] = set()  # mangled names already lowered
        self._generic_struct_defs: dict[str, StructDef] = {}  # name → AST of generic struct
        self._generic_impl_defs: dict[str, ImplDef] = {}  # target → AST of generic impl
        # Cycle guard for recursive types in _match_type_context
        self._match_ctx_stack: set[str] = set()

    # -- Name generation ---------------------------------------------------

    def _fresh_tmp(self, prefix: str = "t") -> str:
        n = self._tmp_counter
        self._tmp_counter += 1
        return f"%{prefix}{n}"

    def _fresh_block(self, prefix: str = "bb") -> str:
        n = self._block_counter
        self._block_counter += 1
        return f"{prefix}{n}"

    def _make_value(self, ty: MIRType = mir_unknown(), prefix: str = "t") -> Value:
        return Value(name=self._fresh_tmp(prefix), ty=ty)

    # -- Generics monomorphization -----------------------------------------

    @staticmethod
    def _type_params_used_in_signature(fn_def: FnDef | AsyncFnDef) -> bool:
        """Return True if any of ``fn_def.type_params`` is referenced in the
        param annotations or return type.

        v4.121.0: a function declared as ``fn max<T: Ord>(a: Int, b: Int) -> Int``
        has ``type_params=['T']`` even though ``T`` does not appear in the
        signature. Without this check the function is unconditionally deferred
        to on-demand monomorphization, but no caller ever supplies type
        arguments (``T`` cannot be inferred from arg types — it isn't there)
        so the function is silently dropped from MIR. Detecting the
        unused-type-param case lets the lowerer emit a single canonical
        instance rather than nothing at all.
        """
        if not fn_def.type_params:
            return False
        tp_set = set(fn_def.type_params)

        def uses(te: TypeExpr | None) -> bool:
            if te is None:
                return False
            if isinstance(te, NamedType):
                return te.name in tp_set
            if isinstance(te, GenericType):
                return any(uses(a) for a in te.args)
            if isinstance(te, FnType):
                return uses(te.return_type) or any(uses(p) for p in te.param_types)
            return False

        if uses(fn_def.return_type):
            return True
        return any(uses(p.type_annotation) for p in fn_def.params)

    def _mangle_generic(self, name: str, type_args: list[MIRType]) -> str:
        """Produce a mangled name: identity + [Int] → identity__Int."""
        parts = []
        for ta in type_args:
            ti = ta.type_info if hasattr(ta, "type_info") else ta
            if hasattr(ti, "name") and ti.name:
                parts.append(ti.name)
            elif hasattr(ti, "kind"):
                parts.append(str(ti.kind).split(".")[-1].capitalize())
            else:
                parts.append("Unknown")
        return f"{name}__{'_'.join(parts)}"

    def _infer_type_args(
        self, fn_def: FnDef | AsyncFnDef, arg_types: list[MIRType]
    ) -> dict[str, MIRType] | None:
        """Infer type parameter → concrete type mapping from call-site arguments."""
        subst: dict[str, MIRType] = {}
        tp_set = set(fn_def.type_params)
        for param, arg_ty in zip(fn_def.params, arg_types):
            if param.type_annotation is None:
                continue
            ann = param.type_annotation
            if isinstance(ann, NamedType) and ann.name in tp_set:
                subst[ann.name] = arg_ty
        return subst if len(subst) == len(tp_set) else None

    def _substitute_type_expr(
        self, te: "TypeExpr | None", subst: dict[str, MIRType]
    ) -> "TypeExpr | None":
        """Replace type parameter names with concrete NamedType nodes."""
        if te is None:
            return None
        if isinstance(te, NamedType) and te.name in subst:
            concrete = subst[te.name]
            ti = concrete.type_info if hasattr(concrete, "type_info") else concrete
            kind = ti.kind if hasattr(ti, "kind") else None
            name = ti.name if hasattr(ti, "name") and ti.name else ""
            if not name and kind is not None:
                _kind_names = {
                    TypeKind.INT: "Int",
                    TypeKind.FLOAT: "Float",
                    TypeKind.BOOL: "Bool",
                    TypeKind.STRING: "String",
                    TypeKind.CHAR: "Char",
                    TypeKind.VOID: "Void",
                    TypeKind.LIST: "List",
                    TypeKind.MAP: "Map",
                }
                name = _kind_names.get(kind, "Int")
            return NamedType(name=name, span=te.span)
        if isinstance(te, GenericType):
            new_args = [self._substitute_type_expr(a, subst) or a for a in te.args]
            return GenericType(name=te.name, args=new_args, span=te.span)
        return te

    def _specialize_fn(
        self, fn_def: FnDef | AsyncFnDef, subst: dict[str, MIRType]
    ) -> FnDef | AsyncFnDef:
        """Create a specialized copy of a generic function with concrete types.

        Uses dataclasses.replace() for a shallow copy, only deep-copying the
        body and params (where type substitution mutates nodes).  This avoids
        the overhead of copy.deepcopy() on the entire FnDef tree.
        """
        specialized = replace(
            fn_def,
            type_params=[],
            trait_bounds={},
            params=[replace(p) for p in fn_def.params],
            body=deepcopy(fn_def.body),
        )

        # Substitute parameter types
        for p in specialized.params:
            p.type_annotation = self._substitute_type_expr(p.type_annotation, subst)

        # Substitute return type
        specialized.return_type = self._substitute_type_expr(specialized.return_type, subst)

        return specialized

    def _monomorphize_call(
        self, fn_name: str, arg_types: list[MIRType], type_args: list[MIRType] | None
    ) -> str | None:
        """If fn_name is generic, specialize it and return the mangled name."""
        fn_def = self._generic_fn_defs.get(fn_name)
        if fn_def is None:
            return None

        # Determine type arguments: explicit (turbofish) or inferred
        if type_args and len(type_args) == len(fn_def.type_params):
            concrete_types = type_args
        else:
            subst = self._infer_type_args(fn_def, arg_types)
            if subst is None:
                return None
            concrete_types = [subst[tp] for tp in fn_def.type_params]

        mangled = self._mangle_generic(fn_name, concrete_types)

        # Specialize and lower if not already done
        if mangled not in self._specialized_fns:
            self._specialized_fns.add(mangled)
            subst_map = dict(zip(fn_def.type_params, concrete_types))
            specialized = self._specialize_fn(fn_def, subst_map)
            specialized.name = mangled
            # Register return type before lowering (for recursive calls)
            if specialized.return_type:
                self._fn_return_types[mangled] = _resolve_type_expr(specialized.return_type)
            self._lower_fn(specialized)

        return mangled

    def _monomorphize_struct(self, struct_name: str, field_values: list[Value]) -> str | None:
        """If struct_name is generic, specialize it and return the mangled name."""
        struct_def = self._generic_struct_defs.get(struct_name)
        if struct_def is None:
            return None

        # Infer type arguments from field value types
        tp_set = set(struct_def.type_params)
        subst: dict[str, MIRType] = {}
        for sf, fv in zip(struct_def.fields, field_values):
            if sf.type_annotation and isinstance(sf.type_annotation, NamedType):
                if sf.type_annotation.name in tp_set:
                    subst[sf.type_annotation.name] = fv.ty

        if len(subst) != len(struct_def.type_params):
            return None

        concrete_types = [subst[tp] for tp in struct_def.type_params]
        mangled = self._mangle_generic(struct_name, concrete_types)

        # Register the specialized struct if not already done
        if mangled not in self._module.structs:
            specialized_fields: list[tuple[str, MIRType]] = []
            for sf in struct_def.fields:
                if (
                    sf.type_annotation
                    and isinstance(sf.type_annotation, NamedType)
                    and sf.type_annotation.name in subst
                ):
                    specialized_fields.append((sf.name, subst[sf.type_annotation.name]))
                else:
                    specialized_fields.append((sf.name, _resolve_type_expr(sf.type_annotation)))
            self._module.structs[mangled] = specialized_fields
            self._struct_fields[mangled] = [sf.name for sf in struct_def.fields]
            self._fn_param_types[mangled] = [ft for _, ft in specialized_fields]

            # Monomorphize generic impl methods for this struct instantiation
            self._monomorphize_impl(struct_name, mangled, subst)

        return mangled

    def _monomorphize_impl(
        self, base_name: str, mangled_name: str, subst: dict[str, MIRType]
    ) -> None:
        """Specialize generic impl methods for a monomorphized struct."""
        impl_def = self._generic_impl_defs.get(base_name)
        if impl_def is None:
            return
        struct_ty = NamedType(name=mangled_name)
        for method in impl_def.methods:
            specialized = self._specialize_fn(method, subst)
            # Inject struct type for bare `self` parameter
            for p in specialized.params:
                if p.name == "self" and p.type_annotation is None:
                    p.type_annotation = struct_ty
            mir_name = f"{mangled_name}_{method.name}"
            # Register the impl method for dispatch
            self._impl_methods[(mangled_name, method.name)] = mir_name
            # Register return/param types
            if specialized.return_type is not None:
                self._fn_return_types[mir_name] = _resolve_type_expr(specialized.return_type)
            if specialized.params:
                self._fn_param_types[mir_name] = [
                    _resolve_type_expr(p.type_annotation) if p.type_annotation else mir_unknown()
                    for p in specialized.params
                ]
            # Lower the specialized method
            if mir_name not in self._specialized_fns:
                self._specialized_fns.add(mir_name)
                self._lower_fn(specialized, name_prefix=f"{mangled_name}_")

    # -- Block management --------------------------------------------------

    def _new_block(self, label: str | None = None) -> BasicBlock:
        if label is None:
            label = self._fresh_block()
        bb = BasicBlock(label=label)
        if self._fn is not None:
            self._fn.blocks.append(bb)
        return bb

    def _set_block(self, bb: BasicBlock) -> None:
        self._block = bb

    def _emit(self, inst: Instruction) -> None:
        assert self._block is not None, "No current basic block"
        if inst.span is None and self._current_span is not None:
            inst.span = self._current_span
        self._block.instructions.append(inst)

    def _block_terminated(self) -> bool:
        if self._block is None:
            return True
        if not self._block.instructions:
            return False
        from mapanare.mir import is_terminator

        return is_terminator(self._block.instructions[-1])

    # -- Scope management --------------------------------------------------

    def _push_scope(self) -> None:
        self._scope_stack.append(dict(self._vars))

    def _pop_scope(self) -> None:
        if self._scope_stack:
            self._vars = self._scope_stack.pop()

    def _define_var(self, name: str, val: Value, mutable: bool = False) -> None:
        self._vars[name] = _VarInfo(current=val, mutable=mutable)

    def _lookup_var(self, name: str) -> Value | None:
        info = self._vars.get(name)
        return info.current if info else None

    def _update_var(self, name: str, val: Value) -> None:
        info = self._vars.get(name)
        if info is not None:
            info.current = val

    # -- Free variable analysis --------------------------------------------

    def _analyze_free_vars(
        self,
        body: Expr | Block,
        param_names: set[str],
    ) -> list[str]:
        """Collect identifiers in a lambda body that reference enclosing scope variables.

        Returns a deduplicated list of variable names that are free in the body
        (i.e., not lambda parameters, not builtins, not struct/enum names, and
        defined in the current scope).
        """
        from mapanare.types import BUILTIN_FUNCTIONS

        builtin_names = set(BUILTIN_FUNCTIONS.keys()) | {
            "println",
            "print",
            "len",
            "str",
            "int",
            "float",
            "Some",
            "Ok",
            "Err",
            "signal",
            "stream",
            "computed",
            "block_on",
        }
        struct_names = set(self._struct_fields.keys())
        enum_names = set(self._enum_variants.keys())
        # All enum variant names as well
        variant_names: set[str] = set()
        for variants in self._enum_variants.values():
            variant_names.update(variants)

        refs: list[str] = []
        seen: set[str] = set()

        def _collect(node: Any) -> None:
            if node is None:
                return
            if isinstance(node, Identifier):
                name = node.name
                if (
                    name not in param_names
                    and name not in builtin_names
                    and name not in struct_names
                    and name not in enum_names
                    and name not in variant_names
                    and name not in seen
                    and self._lookup_var(name) is not None
                ):
                    seen.add(name)
                    refs.append(name)
                return
            if isinstance(node, LambdaExpr):
                # Nested lambda: its params shadow outer vars
                inner_params = param_names | {p.name for p in node.params}
                inner_refs: list[str] = []
                inner_seen: set[str] = set()

                def _collect_inner(n: Any) -> None:
                    if n is None:
                        return
                    if isinstance(n, Identifier):
                        nm = n.name
                        if (
                            nm not in inner_params
                            and nm not in builtin_names
                            and nm not in struct_names
                            and nm not in enum_names
                            and nm not in variant_names
                            and nm not in inner_seen
                            and self._lookup_var(nm) is not None
                        ):
                            inner_seen.add(nm)
                            inner_refs.append(nm)
                        return
                    if isinstance(n, LambdaExpr):
                        return  # Don't recurse into doubly-nested lambdas
                    for attr_val in (vars(n).values() if hasattr(n, "__dict__") else []):
                        if isinstance(attr_val, list):
                            for item in attr_val:
                                if isinstance(item, ASTNode):
                                    _collect_inner(item)
                        elif isinstance(attr_val, ASTNode):
                            _collect_inner(attr_val)

                _collect_inner(node.body)
                # Add inner refs to our refs (they're also free in the outer lambda)
                for r in inner_refs:
                    if r not in seen:
                        seen.add(r)
                        refs.append(r)
                return

            # Generic AST walk
            for attr_val in vars(node).values() if hasattr(node, "__dict__") else []:
                if isinstance(attr_val, list):
                    for item in attr_val:
                        if isinstance(item, ASTNode):
                            _collect(item)
                elif isinstance(attr_val, ASTNode):
                    _collect(attr_val)

        _collect(body)
        return refs

    # -- Top-level lowering ------------------------------------------------

    def lower(
        self,
        program: Program,
        module_name: str = "",
        source_file: str = "",
        source_directory: str = "",
    ) -> MIRModule:
        """Lower an entire program to MIR."""
        self._module = MIRModule(
            name=module_name,
            source_file=source_file,
            source_directory=source_directory,
        )

        # First pass: register struct/enum/extern/impl declarations
        self._register_declarations(program)

        # Second pass: lower function bodies
        for defn in program.definitions:
            self._lower_definition(defn)

        return self._module

    def _register_declarations(self, program: Program) -> None:
        """Pre-register type declarations and impl methods."""
        for defn in program.definitions:
            actual = defn
            if isinstance(actual, DocComment) and actual.definition is not None:
                actual = actual.definition

            if isinstance(actual, StructDef):
                if actual.type_params:
                    self._generic_struct_defs[actual.name] = actual
                else:
                    fields = [
                        (f.name, _resolve_type_expr(f.type_annotation)) for f in actual.fields
                    ]
                    self._module.structs[actual.name] = fields
                    self._struct_fields[actual.name] = [f.name for f in actual.fields]
                    # Register struct constructor param types for arg patching
                    self._fn_param_types[actual.name] = [ft for _, ft in fields]

            elif isinstance(actual, EnumDef):
                variants = []
                variant_names = []
                for v in actual.variants:
                    payload_types = [_resolve_type_expr(f) for f in v.fields]
                    variants.append((v.name, payload_types))
                    variant_names.append(v.name)
                self._module.enums[actual.name] = variants
                self._enum_variants[actual.name] = variant_names

            elif isinstance(actual, ExternFnDef):
                param_types = [_resolve_type_expr(p.type_annotation) for p in actual.params]
                ret_type = (
                    _resolve_type_expr(actual.return_type) if actual.return_type else mir_void()
                )
                self._module.extern_fns.append(
                    (actual.abi, actual.module or "", actual.name, param_types, ret_type)
                )
                # Register extern return types for call-site type propagation
                if actual.return_type is not None:
                    self._fn_return_types[actual.name] = ret_type

            elif isinstance(actual, ImplDef):
                if actual.type_params:
                    # Store generic impl for on-demand monomorphization
                    self._generic_impl_defs[actual.target] = actual
                else:
                    for method in actual.methods:
                        mir_name = f"{actual.target}_{method.name}"
                        self._impl_methods[(actual.target, method.name)] = mir_name

            elif isinstance(actual, ImportDef):
                self._module.imports.append((actual.path, actual.items))

            elif isinstance(actual, (ModuleLetDef, ConstDef)):
                val: int | float | str | None = None
                ty = mir_int()
                type_name = ""
                if isinstance(actual, ConstDef):
                    type_name = getattr(actual.type_expr, "name", "") if actual.type_expr else ""
                else:
                    type_name = actual.type_name
                if actual.value is not None:
                    if isinstance(actual.value, IntLiteral):
                        val = actual.value.value
                        ty = mir_int()
                    elif isinstance(actual.value, StringLiteral):
                        val = actual.value.value
                        ty = mir_string()
                    elif isinstance(actual.value, BoolLiteral):
                        val = 1 if actual.value.value else 0
                        ty = mir_bool()
                    elif isinstance(actual.value, FloatLiteral):
                        val = actual.value.value
                        ty = mir_float()
                    elif isinstance(actual, ConstDef):
                        # v4.55.0: const folding — evaluate constant expressions
                        from mapanare.semantic import SemanticChecker

                        folder = SemanticChecker.__new__(SemanticChecker)
                        folder._const_table = {}
                        for n, (t, v) in self._module_consts.items():
                            if v is not None:
                                folder._const_table[n] = v
                        folded = folder._fold_constant(actual.value)
                        if folded is not None:
                            if isinstance(folded, int):
                                val = folded
                                ty = mir_int()
                            elif isinstance(folded, float):
                                val = folded
                                ty = mir_float()
                            elif isinstance(folded, str):
                                val = folded
                                ty = mir_string()
                            elif isinstance(folded, bool):
                                val = 1 if folded else 0
                                ty = mir_bool()
                self._module_consts[actual.name] = (ty, val)
                self._module.consts.append((actual.name, type_name, val))

            elif isinstance(actual, TraitDef):
                self._module.trait_names.append(actual.name)

            elif isinstance(actual, PipeDef):
                stages = []
                for s in actual.stages:
                    if isinstance(s, Identifier):
                        stages.append(s.name)
                self._module.pipes[actual.name] = MIRPipeInfo(name=actual.name, stages=stages)

            # Store generic function AST definitions for monomorphization.
            # v4.121.0: only register when at least one type parameter is
            # actually used in the signature; otherwise the function is
            # effectively monomorphic (degenerate case like
            # ``fn max<T: Ord>(a: Int, b: Int) -> Int``) and is lowered
            # directly by ``_lower_definition``.
            if (
                isinstance(actual, (FnDef, AsyncFnDef))
                and actual.type_params
                and self._type_params_used_in_signature(actual)
            ):
                self._generic_fn_defs[actual.name] = actual

            # Collect function return/param types for call-site type propagation
            if isinstance(actual, (FnDef, AsyncFnDef)):
                if actual.return_type is not None:
                    self._fn_return_types[actual.name] = _resolve_type_expr(actual.return_type)
                if actual.params:
                    self._fn_param_types[actual.name] = [
                        (
                            _resolve_type_expr(p.type_annotation)
                            if p.type_annotation
                            else mir_unknown()
                        )
                        for p in actual.params
                    ]
            elif isinstance(actual, ImplDef) and not actual.type_params:
                for method in actual.methods:
                    mir_name = f"{actual.target}_{method.name}"
                    if method.return_type is not None:
                        self._fn_return_types[mir_name] = _resolve_type_expr(method.return_type)
                    if method.params:
                        self._fn_param_types[mir_name] = [
                            (
                                _resolve_type_expr(p.type_annotation)
                                if p.type_annotation
                                else mir_unknown()
                            )
                            for p in method.params
                        ]

    def _lower_definition(self, defn: Definition) -> None:
        """Lower a single top-level definition."""
        actual: Definition = defn
        if isinstance(actual, DocComment):
            if actual.definition is not None:
                actual = actual.definition
            else:
                return

        if isinstance(actual, FnDef):
            if actual.type_params and self._type_params_used_in_signature(actual):
                return  # Generic functions lowered on demand via monomorphization
            self._lower_fn(actual)
        elif isinstance(actual, AsyncFnDef):
            # v4.70.0: lower async fn — same as regular fn but marks MIRFunction
            # as is_async=True. The LLVM emitter wraps the body in the coroutine
            # prelude/epilogue (coro.id, coro.begin, coro.end, cleanup).
            if actual.type_params and self._type_params_used_in_signature(actual):
                return  # Generic async functions lowered on demand
            mir_fn = self._lower_fn(actual)
            mir_fn.is_async = True
        elif isinstance(actual, AgentDef):
            self._lower_agent(actual)
        elif isinstance(actual, ImplDef):
            if actual.type_params:
                return  # Generic impls lowered on demand via monomorphization
            self._lower_impl(actual)
        elif isinstance(actual, ExportDef):
            if actual.definition is not None:
                self._lower_definition(actual.definition)
                # Mark the lowered function as public
                if isinstance(actual.definition, FnDef):
                    fn = self._module.get_function(actual.definition.name)
                    if fn is not None:
                        fn.is_public = True
        # StructDef, EnumDef, ExternFnDef, TraitDef, TypeAlias, PipeDef, ImportDef
        # are handled in _register_declarations or need no MIR lowering

    # -- Function lowering -------------------------------------------------

    def _lower_fn(self, fn_def: FnDef | AsyncFnDef, name_prefix: str = "") -> MIRFunction:
        """Lower a function definition to MIR."""
        fn_name = f"{name_prefix}{fn_def.name}" if name_prefix else fn_def.name

        params = [
            MIRParam(
                name=p.name,
                ty=_resolve_type_expr(p.type_annotation) if p.type_annotation else mir_unknown(),
            )
            for p in fn_def.params
        ]
        # Fix enum parameter types: _resolve_type_expr defaults unknown names
        # to STRUCT, but if the name matches a registered enum, correct the kind.
        for param in params:
            if param.ty.kind == TypeKind.STRUCT and param.ty.type_info.name in self._enum_variants:
                param.ty = MIRType(TypeInfo(kind=TypeKind.ENUM, name=param.ty.type_info.name))
        ret_type = _resolve_type_expr(fn_def.return_type) if fn_def.return_type else mir_void()
        # Fix enum return type too
        if ret_type.kind == TypeKind.STRUCT and ret_type.type_info.name in self._enum_variants:
            ret_type = MIRType(TypeInfo(kind=TypeKind.ENUM, name=ret_type.type_info.name))
        decorators = [d.name for d in fn_def.decorators]

        source_line = fn_def.span.line if fn_def.span else 0
        source_file = self._module.source_file if self._module else ""

        mir_fn = MIRFunction(
            name=fn_name,
            params=params,
            return_type=ret_type,
            blocks=[],
            decorators=decorators,
            is_public=fn_def.public,
            source_line=source_line,
            source_file=source_file,
        )

        # Save/restore lowerer state for nested functions
        prev_fn = self._fn
        prev_block = self._block
        prev_tmp = self._tmp_counter
        prev_blk_cnt = self._block_counter
        prev_vars = dict(self._vars)

        self._fn = mir_fn
        self._tmp_counter = 0
        self._block_counter = 0
        self._vars = {}

        # Create entry block
        entry = self._new_block("entry")
        self._set_block(entry)

        # Bind params as variables
        for p in fn_def.params:
            param_val = Value(
                name=f"%{p.name}",
                ty=_resolve_type_expr(p.type_annotation) if p.type_annotation else mir_unknown(),
            )
            self._define_var(p.name, param_val)

        # If this is a closure lambda, inject env loads for captured variables
        if self._pending_captures is not None:
            env_val = Value(name="%__env_ptr", ty=MIRType(TypeInfo(kind=TypeKind.UNKNOWN)))
            for idx, (cap_name, cap_type) in enumerate(self._pending_captures):
                dest = Value(name=f"%{cap_name}", ty=cap_type)
                self._emit(EnvLoad(dest=dest, env=env_val, index=idx, val_type=cap_type))
                self._define_var(cap_name, dest)
            self._pending_captures = None  # consumed

        # Lower body
        last_val = self._lower_block(fn_def.body)

        # Add implicit return if block isn't terminated.
        # For functions with a return type, the last expression becomes
        # the return value (implicit return). For void functions, emit bare return.
        is_lambda = fn_name.startswith("%lambda") or fn_name.startswith("lambda")
        if not self._block_terminated():
            if is_lambda and last_val is not None and ret_type.kind == TypeKind.VOID:
                # Infer return type from last expression for lambdas
                if last_val.ty.kind != TypeKind.VOID and last_val.ty.kind != TypeKind.UNKNOWN:
                    mir_fn.return_type = last_val.ty
                self._emit(Return(val=last_val))
            elif ret_type.kind != TypeKind.VOID and last_val is not None:
                # Implicit return: last expression in a typed function
                self._emit(Return(val=last_val))
            elif ret_type.kind == TypeKind.VOID:
                self._emit(Return())
            else:
                self._emit(Return())

        # Infer unknown param types for lambdas only.
        # Lambda params lack type annotations; infer from BinOp partners,
        # then propagate to BinOp results and Return values.
        unknown_params: set[str] = set()
        if is_lambda:
            unknown_params = {
                p.name
                for p in mir_fn.params
                if p.ty.kind == TypeKind.UNKNOWN and p.name != "__env_ptr"
            }
        if unknown_params:
            from mapanare.mir import BinOp as MIRBinOp

            # Pass 1: infer param types from BinOp partners
            for bb in mir_fn.blocks:
                for inst in bb.instructions:
                    if isinstance(inst, MIRBinOp):
                        if (
                            inst.lhs.name.lstrip("%") in unknown_params
                            and inst.rhs.ty.kind != TypeKind.UNKNOWN
                        ):
                            for mp in mir_fn.params:
                                if mp.name == inst.lhs.name.lstrip("%"):
                                    mp.ty = inst.rhs.ty
                                    inst.lhs.ty = inst.rhs.ty
                                    unknown_params.discard(mp.name)
                        if (
                            inst.rhs.name.lstrip("%") in unknown_params
                            and inst.lhs.ty.kind != TypeKind.UNKNOWN
                        ):
                            for mp in mir_fn.params:
                                if mp.name == inst.rhs.name.lstrip("%"):
                                    mp.ty = inst.lhs.ty
                                    inst.rhs.ty = inst.lhs.ty
                                    unknown_params.discard(mp.name)

            # Pass 2: propagate to BinOp dest types and Return values
            for bb in mir_fn.blocks:
                for inst in bb.instructions:
                    if isinstance(inst, MIRBinOp) and inst.dest.ty.kind == TypeKind.UNKNOWN:
                        if inst.lhs.ty.kind != TypeKind.UNKNOWN:
                            inst.dest.ty = inst.lhs.ty
                        elif inst.rhs.ty.kind != TypeKind.UNKNOWN:
                            inst.dest.ty = inst.rhs.ty
            # Pass 3: update return type from return value
            from mapanare.mir import Return as MIRReturn

            for bb in mir_fn.blocks:
                for inst in bb.instructions:
                    if (
                        isinstance(inst, MIRReturn)
                        and inst.val is not None
                        and inst.val.ty.kind != TypeKind.UNKNOWN
                        and mir_fn.return_type.kind == TypeKind.VOID
                    ):
                        mir_fn.return_type = inst.val.ty

        self._module.functions.append(mir_fn)

        # v4.27.0 Path B recovery: ``@cuda``/``@vulkan``/``@gpu`` decorators
        # used to raise ``NotImplementedError`` here, which crashed the
        # compiler on any decorated function. They were only ever cosmetic
        # — GPU compute in Mapanare has always gone through the
        # ``gpu_tensor_*`` runtime builtins (see ``runtime/native/mapanare_gpu*``),
        # not a source-level decorator. The decorators are now rejected at
        # parse-time via the ``decorated_def`` rule, so this loop is removed.

        # Restore state
        self._fn = prev_fn
        self._block = prev_block
        self._tmp_counter = prev_tmp
        self._block_counter = prev_blk_cnt
        self._vars = prev_vars

        return mir_fn

    def _lower_agent(self, agent_def: AgentDef) -> None:
        """Lower an agent definition — each method becomes a standalone function."""
        method_names = []
        for method in agent_def.methods:
            fn = self._lower_fn(method, name_prefix=f"{agent_def.name}_")
            method_names.append(fn.name)

        # Store agent metadata for emitters
        state_info: list[tuple[str, Any]] = []
        for s in agent_def.state:
            val: Any = None
            if isinstance(s.value, IntLiteral):
                val = s.value.value
            elif isinstance(s.value, FloatLiteral):
                val = s.value.value
            elif isinstance(s.value, StringLiteral):
                val = s.value.value
            elif isinstance(s.value, BoolLiteral):
                val = s.value.value
            state_info.append((s.name, val))

        self._module.agents[agent_def.name] = MIRAgentInfo(
            name=agent_def.name,
            inputs=[inp.name for inp in agent_def.inputs],
            outputs=[out.name for out in agent_def.outputs],
            state=state_info,
            method_names=method_names,
        )

    def _lower_impl(self, impl_def: ImplDef) -> None:
        """Lower an impl block — each method becomes a standalone function."""
        for method in impl_def.methods:
            self._lower_fn(method, name_prefix=f"{impl_def.target}_")

    # -- Block / statement lowering ----------------------------------------

    def _lower_block(self, block: Block) -> Value | None:
        """Lower a block of statements. Returns the value of the last expression, if any."""
        last_val: Value | None = None
        self._push_scope()
        for stmt in block.stmts:
            if self._block_terminated():
                break
            val = self._lower_stmt(stmt)
            if val is not None:
                last_val = val
        self._pop_scope()
        return last_val

    def _lower_stmt(self, stmt: Stmt) -> Value | None:
        """Lower a single statement. Returns a value for expression-statements."""
        # Track source span for debug info
        span = _ast_span_to_mir(stmt)
        if span is not None:
            self._current_span = span

        if isinstance(stmt, LetBinding):
            self._lower_let(stmt)
            return None
        if isinstance(stmt, LetDestructure):
            self._lower_let_destructure(stmt)
            return None
        if isinstance(stmt, LetElseStmt):
            self._lower_let_else(stmt)
            return None
        if isinstance(stmt, WhileLetStmt):
            self._lower_while_let(stmt)
            return None
        if isinstance(stmt, ExprStmt):
            return self._lower_expr(stmt.expr)
        if isinstance(stmt, ReturnStmt):
            self._lower_return(stmt)
            return None
        if isinstance(stmt, ForLoop):
            self._lower_for(stmt)
            return None
        if isinstance(stmt, ForAwaitLoop):
            self._lower_for_await(stmt)
            return None
        if isinstance(stmt, WhileLoop):
            self._lower_while(stmt)
            return None
        if isinstance(stmt, SignalDecl):
            self._lower_signal_decl(stmt)
            return None
        if isinstance(stmt, BreakStmt):
            if self._loop_exit_stack:
                self._emit(Jump(target=self._loop_exit_stack[-1]))
            return None
        if isinstance(stmt, ContinueStmt):
            if self._loop_header_stack:
                self._emit(Jump(target=self._loop_header_stack[-1]))
            return None
        if isinstance(stmt, PassStmt):
            return None  # v5.14.0 Te.1: explicit no-op, emits no MIR
        if isinstance(stmt, AssertStmt):
            self._lower_assert(stmt)
            return None
        if isinstance(stmt, PrintStmt):
            val = self._lower_expr(stmt.expr)
            dest = self._make_value(ty=mir_void())
            self._emit(Call(dest=dest, fn_name="print", args=[val]))
            return None
        if isinstance(stmt, StreamDecl):
            self._lower_stream_decl(stmt)
            return None
        return None

    # ── any-type box/unbox helpers ────────────────────────────────────
    _ANY_BOX_FN: dict[TypeKind, str] = {
        TypeKind.INT: "__mn_any_box_int",
        TypeKind.FLOAT: "__mn_any_box_float",
        TypeKind.BOOL: "__mn_any_box_bool",
        TypeKind.STRING: "__mn_any_box_str",
    }

    def _box_for_any(self, val: Value) -> Value:
        """Box a concrete-typed value into an MnValue (any).

        Returns the original value unchanged if no boxing is needed.
        """
        box_fn = self._ANY_BOX_FN.get(val.ty.kind)
        if box_fn is None:
            # Non-boxable types: just reinterpret as any
            return Value(name=val.name, ty=mir_any())
        dest = self._make_value(ty=mir_any())
        self._emit(Call(dest=dest, fn_name=box_fn, args=[val]))
        return dest

    def _unbox_from_any(self, val: Value, target_kind: TypeKind) -> Value:
        """Unbox an MnValue (any) to a concrete type."""
        _UNBOX_FN: dict[TypeKind, tuple[str, MIRType]] = {
            TypeKind.INT: ("__mn_any_unbox_int", mir_int()),
            TypeKind.FLOAT: ("__mn_any_unbox_float", MIRType(TypeInfo(kind=TypeKind.FLOAT))),
            TypeKind.BOOL: ("__mn_any_unbox_bool", MIRType(TypeInfo(kind=TypeKind.BOOL))),
            TypeKind.STRING: ("__mn_any_unbox_str", mir_string()),
        }
        info = _UNBOX_FN.get(target_kind)
        if info is None:
            return val
        fn_name, result_ty = info
        dest = self._make_value(ty=result_ty)
        self._emit(Call(dest=dest, fn_name=fn_name, args=[val]))
        return dest

    def _lower_let(self, let: LetBinding) -> None:
        """Lower a let binding."""
        # v5.15.0 Te.2: when the RHS is a comprehension and the user has
        # annotated the binding with `List<T>` / `Map<K, V>`, hand that
        # element-type information to `_lower_comprehension` so the
        # internal accumulator list's elem_type is patched correctly.
        # Without this hint, indexing the comprehension's result would
        # see UNKNOWN element type and the LLVM emitter would fall back
        # to raw-pointer reads (printing `<?>`).
        if isinstance(let.value, Comprehension) and let.type_annotation is not None:
            self._comp_type_hint: TypeExpr | None = let.type_annotation
        else:
            self._comp_type_hint = None

        # Track lambda bindings so calls can resolve the function name
        if isinstance(let.value, LambdaExpr):
            val = self._lower_expr(let.value)
            named = Value(name=f"%{let.name}", ty=val.ty)
            self._emit(Copy(dest=named, src=val))
            self._define_var(let.name, named, mutable=let.mutable)
            # Check if this was a closure (ClosureCreate) or plain lambda (Const)
            for bb in (self._fn.blocks if self._fn else []):
                for inst in bb.instructions:
                    if isinstance(inst, ClosureCreate) and inst.dest == val:
                        self._lambda_vars[let.name] = inst.fn_name
                        self._closure_vars.add(let.name)
                        return
                    if isinstance(inst, Const) and inst.dest == val:
                        if isinstance(inst.value, str):
                            self._lambda_vars[let.name] = inst.value
            return
        val = self._lower_expr(let.value)
        # For empty lists/maps, propagate element type from the type annotation
        # so the LLVM emitter uses the correct elem_size.
        if let.type_annotation and isinstance(let.value, ListLiteral) and not let.value.elements:
            declared = _resolve_type_expr(let.type_annotation)
            if declared.type_info.args:
                # Patch the ListInit instruction's elem_type
                for bb in (self._fn.blocks if self._fn else []):
                    for inst in bb.instructions:
                        if isinstance(inst, ListInit) and inst.dest == val:
                            inst.elem_type = MIRType(declared.type_info.args[0])
                            break
                # v4.122.0 (Qs.1): also lift the Value's type so downstream
                # IndexGet / ListPush / len lowering sees the element type.
                # Without this, `let arr: List<Int> = []; print(str(arr[0]))`
                # reaches the LLVM emitter with `%arr.ty.args == [<unknown>]`
                # and IndexGet emits a raw-pointer read instead of `load i64`.
                val = Value(name=val.name, ty=declared)
        # v5.15.0 Te.2.C: same for empty MapLiteral with `Map<K, V>` annotation.
        if let.type_annotation and isinstance(let.value, MapLiteral) and not let.value.entries:
            declared = _resolve_type_expr(let.type_annotation)
            if len(declared.type_info.args) >= 2:
                k_ty = MIRType(declared.type_info.args[0])
                v_ty = MIRType(declared.type_info.args[1])
                for bb in (self._fn.blocks if self._fn else []):
                    for inst in bb.instructions:
                        if isinstance(inst, MapInit) and inst.dest == val:
                            inst.key_type = k_ty
                            inst.val_type = v_ty
                            break
                val = Value(name=val.name, ty=declared)
        # When the expression type is unknown or lacks inner type args but a type
        # annotation is provided, use the annotation to preserve full type info.
        if let.type_annotation:
            declared = _resolve_type_expr(let.type_annotation)
            if declared.kind == TypeKind.ANY and val.ty.kind != TypeKind.ANY:
                # Box concrete value into MnValue for `let x: any = 42`
                val = self._box_for_any(val)
            elif val.ty.kind == TypeKind.UNKNOWN and declared.kind != TypeKind.UNKNOWN:
                val = Value(name=val.name, ty=declared)
            elif val.ty.kind in (TypeKind.OPTION, TypeKind.RESULT) and not val.ty.type_info.args:
                if declared.kind == val.ty.kind and declared.type_info.args:
                    val = Value(name=val.name, ty=declared)
                    # Also patch the WrapNone/WrapSome instruction
                    self._patch_wrap_inst(val, declared)
        # Create a named copy for readability
        named = Value(name=f"%{let.name}", ty=val.ty)
        self._emit(Copy(dest=named, src=val))
        self._define_var(let.name, named, mutable=let.mutable)

    def _lower_let_destructure(self, dest: LetDestructure) -> None:
        """Lower `let Point { x, y } = expr`. v5.20.0 Te.5.D.

        Strategy: when the RHS is a bare Identifier, run field accesses
        directly on the source name so IR matches `let x = p.x; let y =
        p.y` byte-identically. Otherwise lower the RHS once into a tmp.
        """
        # Short-circuit when the RHS is already a bare ident — avoids
        # an extra Copy/alloca and matches the manual long-form IR.
        if isinstance(dest.value, Identifier):
            base_name = dest.value.name
            base_already_bound = self._lookup_var(base_name) is not None
            if base_already_bound:
                self._emit_destructure_pattern(
                    pattern=dest.pattern,
                    base_name=base_name,
                    outer_mut=dest.mutable,
                )
                return

        # General case: lower the RHS into a synthesized tmp, register
        # under a fresh name, then run field accesses through it.
        tmp_idx = self._struct_update_counter
        self._struct_update_counter += 1
        base_name = f"__mn_dst_{tmp_idx}"
        # Reuse _lower_let for the RHS so all type-annotation patching
        # (empty list/map element-type) works identically.
        synthetic_let = LetBinding(
            name=base_name,
            mutable=False,
            type_annotation=dest.type_annotation,
            value=dest.value,
        )
        self._lower_let(synthetic_let)
        self._emit_destructure_pattern(
            pattern=dest.pattern,
            base_name=base_name,
            outer_mut=dest.mutable,
        )

    def _emit_destructure_pattern(
        self,
        pattern: StructPattern,
        base_name: str,
        outer_mut: bool,
    ) -> None:
        """Emit per-field `let` bindings for a StructPattern over a
        named base. Recurses for nested struct sub-patterns. v5.20.0.
        """
        # Validate fields against the struct definition where possible.
        struct_name = pattern.name
        known_fields: list[str] | None = self._struct_fields.get(struct_name)
        if known_fields is None and self._imported_struct_defs:
            imported = self._imported_struct_defs.get(struct_name)
            if imported is not None:
                known_fields = [f for f, _ in imported]

        for fp in pattern.fields:
            if known_fields is not None and fp.name not in known_fields:
                raise RuntimeError(f"let destructure: '{struct_name}' has no field '{fp.name}'")
            field_access = FieldAccessExpr(
                object=Identifier(name=base_name),
                field_name=fp.name,
            )
            if fp.sub_pattern is None:
                # Leaf binding — emit `let [mut] <name> = base.<field>`.
                synthetic = LetBinding(
                    name=fp.name,
                    mutable=outer_mut or fp.mutable,
                    type_annotation=None,
                    value=field_access,
                )
                self._lower_let(synthetic)
            else:
                # Nested struct pattern — bind the field into a fresh
                # tmp, then recurse with that tmp as the new base.
                assert isinstance(fp.sub_pattern, StructPattern)
                tmp_idx = self._struct_update_counter
                self._struct_update_counter += 1
                sub_base_name = f"__mn_dst_{tmp_idx}"
                synthetic_let = LetBinding(
                    name=sub_base_name,
                    mutable=False,
                    type_annotation=None,
                    value=field_access,
                )
                self._lower_let(synthetic_let)
                self._emit_destructure_pattern(
                    pattern=fp.sub_pattern,
                    base_name=sub_base_name,
                    outer_mut=outer_mut,
                )

    # ------------------------------------------------------------------
    # v5.20.0 Te.5.E — if-let / while-let / let-else
    # ------------------------------------------------------------------

    def _lower_if_let(self, expr: IfLetExpr) -> Value:
        """Lower `if let <pat> = <scrutinee> { ... } [else { ... }]`.

        Desugars to a 2-arm match: success arm = then_block, wildcard
        arm = else_block (or empty block when omitted). Reuses
        `_lower_match` so all decision-tree compilation, exhaustiveness,
        and arm-binding scoping are inherited.
        """
        success_arm = MatchArm(pattern=expr.pattern, body=expr.then_block)
        if expr.else_block is None:
            else_body: Block | Expr = Block(stmts=[])
        elif isinstance(expr.else_block, Block):
            else_body = expr.else_block
        else:
            # IfExpr or IfLetExpr — wrap in a Block as ExprStmt.
            else_body = Block(stmts=[ExprStmt(expr=expr.else_block)])
        wildcard_arm = MatchArm(pattern=WildcardPattern(), body=else_body)
        synthetic = MatchExpr(subject=expr.scrutinee, arms=[success_arm, wildcard_arm])
        return self._lower_match(synthetic)

    def _lower_while_let(self, stmt: WhileLetStmt) -> None:
        """Lower `while let <pat> = <scrutinee> { body }` per D8.

        Desugars to:
            while true {
                match <scrutinee> {
                    <pat> => <body>,
                    _ => break,
                }
            }

        Scrutinee is re-evaluated each iteration (matches Rust).
        """
        success_arm = MatchArm(pattern=stmt.pattern, body=stmt.body)
        break_arm = MatchArm(
            pattern=WildcardPattern(),
            body=Block(stmts=[BreakStmt()]),
        )
        match_expr = MatchExpr(
            subject=stmt.scrutinee,
            arms=[success_arm, break_arm],
        )
        while_body = Block(stmts=[ExprStmt(expr=match_expr)])
        synthetic = WhileLoop(
            condition=BoolLiteral(value=True),
            body=while_body,
        )
        self._lower_while(synthetic)

    def _lower_let_else(self, stmt: LetElseStmt) -> None:
        """Lower `let <pattern> = <scrutinee> else { ... }` per D5.

        Strategy 2 (synthesized return): transform to
            let <bound> = match <scrutinee> {
                <pattern> => <bound>,
                _ => { else_block },          # diverging
            }

        For 0-arg ConstructorPattern (None) and Wildcard variants, no
        outer binding is needed — emit as a plain match-statement.

        Pattern shapes supported in v5.20.0:
            - WildcardPattern
            - ConstructorPattern with 0 args (e.g. None)
            - ConstructorPattern with 1 IdentPattern arg (Some(x), Ok(v), Err(e))
            - ConstructorPattern with 1 WildcardPattern arg (Some(_))
        Multi-binding patterns deferred to v5.21.0+.
        """
        pattern = stmt.pattern

        # Divergence check (D5/D6). The else block must end in a
        # divergent statement; the surrounding fn's implicit return
        # does NOT satisfy the requirement.
        if not _block_diverges(stmt.else_block):
            raise RuntimeError(
                "let-else: the else block must diverge "
                "(end with `return`, `break`, `continue`, or `panic(...)`). "
                "An implicit return at the function tail does NOT satisfy "
                "this requirement."
            )

        if isinstance(pattern, WildcardPattern):
            # `let _ = expr else { ... }` — wildcard always matches;
            # else is dead. Emit the match for the side effect of
            # evaluating expr.
            synthetic = MatchExpr(
                subject=stmt.scrutinee,
                arms=[MatchArm(pattern=WildcardPattern(), body=Block(stmts=[]))],
            )
            self._lower_match(synthetic)
            return

        if isinstance(pattern, ConstructorPattern):
            n_args = len(pattern.args)
            single_ident = n_args == 1 and isinstance(pattern.args[0], IdentPattern)
            single_wild = n_args == 1 and isinstance(pattern.args[0], WildcardPattern)

            if n_args == 0 or single_wild:
                # No outer binding to leak — emit as match-statement.
                synthetic = MatchExpr(
                    subject=stmt.scrutinee,
                    arms=[
                        MatchArm(pattern=pattern, body=Block(stmts=[])),
                        MatchArm(pattern=WildcardPattern(), body=stmt.else_block),
                    ],
                )
                self._lower_match(synthetic)
                return

            if single_ident:
                # `let Some(x) = opt else { ... }` — the canonical case.
                # Build: let x = match opt { Some(x) => x, _ => else_block }
                bound_name = pattern.args[0].name  # type: ignore[attr-defined]
                success_arm = MatchArm(
                    pattern=pattern,
                    body=Identifier(name=bound_name),
                )
                wildcard_arm = MatchArm(
                    pattern=WildcardPattern(),
                    body=stmt.else_block,
                )
                synthetic = MatchExpr(
                    subject=stmt.scrutinee,
                    arms=[success_arm, wildcard_arm],
                )
                synthetic_let = LetBinding(
                    name=bound_name,
                    mutable=False,
                    type_annotation=None,
                    value=synthetic,
                )
                self._lower_let(synthetic_let)
                return

        raise RuntimeError(
            f"let-else: unsupported pattern shape "
            f"{type(pattern).__name__}; v5.20.0 supports wildcard and "
            "constructor patterns with 0 or 1 args (single identifier "
            "or wildcard). Multi-binding patterns are deferred."
        )

    def _lower_return(self, ret: ReturnStmt) -> None:
        """Lower a return statement."""
        if ret.value is not None:
            val = self._lower_expr(ret.value)
            self._emit(Return(val=val))
        else:
            self._emit(Return())

    def _lower_assert(self, stmt: AssertStmt) -> None:
        """Lower an assert statement to an Assert MIR instruction."""
        cond = self._lower_expr(stmt.condition)
        msg_val = self._lower_expr(stmt.message) if stmt.message is not None else None
        line = stmt.span.line if stmt.span else 0
        filename = self._module.name if self._module else ""
        self._emit(Assert(cond=cond, message=msg_val, filename=filename, line=line))

    def _lower_for(self, loop: ForLoop) -> None:
        """Lower a for loop to basic blocks.

        Structure:
            current_block → jump header
            header: %iter_val = phi [...]; branch has_next, body, exit
            body: ... ; jump header
            exit: continue
        """
        # Lower the iterable
        iterable = self._lower_expr(loop.iterable)

        # Create blocks
        header = self._new_block(self._fresh_block("for_header"))
        body = self._new_block(self._fresh_block("for_body"))
        exit_bb = self._new_block(self._fresh_block("for_exit"))

        # Jump from current block to header
        if not self._block_terminated():
            self._emit(Jump(target=header.label))

        # Infer loop variable type from iterable
        elem_ty = self._infer_iterable_elem_type(iterable.ty)

        # Header: we model the loop variable as receiving values
        self._set_block(header)
        iter_val = self._make_value(ty=elem_ty, prefix="iter")
        self._define_var(loop.var_name, iter_val)
        # For simplicity, we use a Call to a runtime iterator function
        has_next = self._make_value(ty=mir_bool(), prefix="has_next")
        self._emit(Call(dest=has_next, fn_name="__iter_has_next", args=[iterable]))
        self._emit(Branch(cond=has_next, true_block=body.label, false_block=exit_bb.label))

        # Body
        self._set_block(body)
        next_val = self._make_value(ty=elem_ty, prefix="next")
        self._emit(Call(dest=next_val, fn_name="__iter_next", args=[iterable]))
        self._define_var(loop.var_name, next_val)
        self._push_scope()
        self._loop_exit_stack.append(exit_bb.label)
        self._loop_header_stack.append(header.label)
        # Track which variables were updated via ListPush during this loop
        _list_push_vars: set[str] = set()
        _orig_update = self._update_var

        def _tracking_update(name: str, val: Value) -> None:
            _list_push_vars.add(name)
            _orig_update(name, val)

        self._update_var = _tracking_update  # type: ignore[method-assign]
        self._lower_block(loop.body)
        self._update_var = _orig_update  # type: ignore[method-assign]
        self._loop_header_stack.pop()
        self._loop_exit_stack.pop()
        # Capture list-pushed variable values BEFORE pop
        _pushed_vals = {vn: self._vars[vn].current for vn in _list_push_vars if vn in self._vars}
        self._pop_scope()
        # Propagate ONLY variables that were updated via push
        for vn, val in _pushed_vals.items():
            if vn != loop.var_name:
                self._update_var(vn, val)
        if not self._block_terminated():
            self._emit(Jump(target=header.label))

        # Exit — free range iterator if the iterable was a range
        self._set_block(exit_bb)
        if iterable.ty.kind == TypeKind.RANGE:
            free_dest = self._make_value(ty=mir_bool(), prefix="range_free")
            self._emit(Call(dest=free_dest, fn_name="__mn_range_free", args=[iterable]))

    def _lower_for_await(self, loop: ForAwaitLoop) -> None:
        """Lower a for-await loop: `for await x in stream { body }`.

        Desugars to:
            loop {
                let next_future = __stream_next_async(stream)
                let next_opt = await next_future
                match next_opt { Some(x) => body, None => break }
            }

        For v4.74.0 simplicity, this lowers as a regular for loop over
        the stream — the iteration protocol is the same, but each item
        is conceptually awaited. The AwaitSuspend MIR instruction handles
        the inline-resume of any async producer.
        """

        iterable = self._lower_expr(loop.iterable)
        elem_ty = self._infer_iterable_elem_type(iterable.ty)

        header = self._new_block(self._fresh_block("for_await_hdr"))
        body = self._new_block(self._fresh_block("for_await_body"))
        exit_bb = self._new_block(self._fresh_block("for_await_exit"))

        if not self._block_terminated():
            self._emit(Jump(target=header.label))

        # Header: check if stream has next item
        self._set_block(header)
        has_next = self._make_value(ty=mir_bool(), prefix="aw_has")
        self._emit(Call(dest=has_next, fn_name="__iter_has_next", args=[iterable]))
        self._emit(Branch(cond=has_next, true_block=body.label, false_block=exit_bb.label))

        # Body: get next item (conceptually awaited)
        self._set_block(body)
        next_val = self._make_value(ty=elem_ty, prefix="aw_next")
        self._emit(Call(dest=next_val, fn_name="__iter_next", args=[iterable]))
        self._define_var(loop.var_name, next_val)
        self._push_scope()
        self._loop_exit_stack.append(exit_bb.label)
        self._loop_header_stack.append(header.label)
        self._lower_block(loop.body)
        self._loop_header_stack.pop()
        self._loop_exit_stack.pop()
        self._pop_scope()
        if not self._block_terminated():
            self._emit(Jump(target=header.label))

        self._set_block(exit_bb)

    def _lower_while(self, loop: WhileLoop) -> None:
        """Lower a while loop to basic blocks.

        Structure:
            current_block → jump header
            header: %cond = ...; branch %cond, body, exit
            body: ...; jump header
            exit: continue
        """
        header = self._new_block(self._fresh_block("while_header"))
        body = self._new_block(self._fresh_block("while_body"))
        exit_bb = self._new_block(self._fresh_block("while_exit"))

        if not self._block_terminated():
            self._emit(Jump(target=header.label))

        # Header
        self._set_block(header)
        cond = self._lower_expr(loop.condition)
        self._emit(Branch(cond=cond, true_block=body.label, false_block=exit_bb.label))

        # Body
        self._set_block(body)
        self._loop_exit_stack.append(exit_bb.label)
        self._loop_header_stack.append(header.label)
        self._lower_block(loop.body)
        self._loop_header_stack.pop()
        self._loop_exit_stack.pop()
        if not self._block_terminated():
            self._emit(Jump(target=header.label))

        # Exit
        self._set_block(exit_bb)

    def _lower_signal_decl(self, decl: SignalDecl) -> None:
        """Lower a signal declaration."""
        init_val = self._lower_expr(decl.value)
        sig_type = _resolve_type_expr(decl.type_annotation)
        dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.SIGNAL)), prefix="sig")
        self._emit(SignalInit(dest=dest, signal_type=sig_type, initial_val=init_val))
        self._define_var(decl.name, dest, mutable=decl.mutable)

    def _lower_stream_decl(self, decl: StreamDecl) -> None:
        """Lower a stream declaration."""
        val = self._lower_expr(decl.value)
        self._define_var(decl.name, val)

    # -- Expression lowering -----------------------------------------------

    def _lower_expr(self, expr: Expr) -> Value:  # noqa: C901
        """Lower an expression to MIR, returning the SSA value holding the result."""
        # Track source span for debug info
        span = _ast_span_to_mir(expr)
        if span is not None:
            self._current_span = span

        if isinstance(expr, IntLiteral):
            dest = self._make_value(ty=mir_int())
            self._emit(Const(dest=dest, ty=mir_int(), value=expr.value))
            return dest

        if isinstance(expr, FloatLiteral):
            dest = self._make_value(ty=mir_float())
            self._emit(Const(dest=dest, ty=mir_float(), value=expr.value))
            return dest

        if isinstance(expr, BoolLiteral):
            dest = self._make_value(ty=mir_bool())
            self._emit(Const(dest=dest, ty=mir_bool(), value=expr.value))
            return dest

        if isinstance(expr, StringLiteral):
            dest = self._make_value(ty=mir_string())
            self._emit(Const(dest=dest, ty=mir_string(), value=expr.value))
            return dest

        if isinstance(expr, CharLiteral):
            dest = self._make_value(ty=mir_string())
            self._emit(Const(dest=dest, ty=mir_string(), value=expr.value))
            return dest

        if isinstance(expr, NoneLiteral):
            ty = MIRType(TypeInfo(kind=TypeKind.OPTION))
            dest = self._make_value(ty=ty)
            self._emit(WrapNone(dest=dest, ty=ty))
            return dest

        if isinstance(expr, Identifier):
            return self._lower_identifier(expr)

        if isinstance(expr, BinaryExpr):
            return self._lower_binary(expr)

        if isinstance(expr, ChainedCompare):
            return self._lower_chained_compare(expr)

        if isinstance(expr, UnaryExpr):
            return self._lower_unary(expr)

        if isinstance(expr, CallExpr):
            return self._lower_call(expr)

        if isinstance(expr, MethodCallExpr):
            return self._lower_method_call(expr)

        if isinstance(expr, FieldAccessExpr):
            return self._lower_field_access(expr)

        if isinstance(expr, NamespaceAccessExpr):
            return self._lower_namespace_access(expr)

        if isinstance(expr, IndexExpr):
            return self._lower_index(expr)

        if isinstance(expr, PipeExpr):
            return self._lower_pipe(expr)

        if isinstance(expr, RangeExpr):
            return self._lower_range(expr)

        if isinstance(expr, LambdaExpr):
            return self._lower_lambda(expr)

        if isinstance(expr, Comprehension):
            return self._lower_comprehension(expr)

        if isinstance(expr, SpawnExpr):
            return self._lower_spawn(expr)

        if isinstance(expr, SyncExpr):
            return self._lower_sync(expr)

        if isinstance(expr, AwaitExpr):
            # v4.72.0: real await lowering. Evaluates the inner expression
            # (which returns a Future<T> ptr), then emits AwaitSuspend which
            # the LLVM emitter translates to save/suspend/switch + extraction.
            from mapanare.mir import AwaitSuspend

            future_val = self._lower_expr(expr.expr)
            dest = self._make_value(prefix="await")
            self._emit(AwaitSuspend(dest=dest, future=future_val))
            return dest

        if isinstance(expr, SendExpr):
            return self._lower_send(expr)

        if isinstance(expr, ErrorPropExpr):
            return self._lower_error_prop(expr)

        if isinstance(expr, ListLiteral):
            return self._lower_list(expr)

        if isinstance(expr, TensorLiteral):
            return self._lower_tensor_literal(expr)

        if isinstance(expr, MapLiteral):
            return self._lower_map(expr)

        if isinstance(expr, ConstructExpr):
            return self._lower_construct(expr)

        if isinstance(expr, StructUpdate):
            return self._lower_struct_update(expr)

        if isinstance(expr, SomeExpr):
            val = self._lower_expr(expr.value)
            inner_ti = (
                val.ty.type_info
                if val.ty.type_info.kind != TypeKind.UNKNOWN
                else TypeInfo(kind=TypeKind.INT)
            )
            opt_ty = MIRType(TypeInfo(kind=TypeKind.OPTION, args=[inner_ti]))
            dest = self._make_value(ty=opt_ty)
            self._emit(WrapSome(dest=dest, val=val))
            self._emit(Move(value=val))
            return dest

        if isinstance(expr, OkExpr):
            val = self._lower_expr(expr.value)
            ok_ti = (
                val.ty.type_info
                if val.ty.type_info.kind != TypeKind.UNKNOWN
                else TypeInfo(kind=TypeKind.INT)
            )
            res_ty = MIRType(
                TypeInfo(kind=TypeKind.RESULT, args=[ok_ti, TypeInfo(kind=TypeKind.STRING)])
            )
            dest = self._make_value(ty=res_ty)
            self._emit(WrapOk(dest=dest, val=val))
            self._emit(Move(value=val))
            return dest

        if isinstance(expr, ErrExpr):
            val = self._lower_expr(expr.value)
            err_ti = (
                val.ty.type_info
                if val.ty.type_info.kind != TypeKind.UNKNOWN
                else TypeInfo(kind=TypeKind.STRING)
            )
            res_ty = MIRType(
                TypeInfo(kind=TypeKind.RESULT, args=[TypeInfo(kind=TypeKind.INT), err_ti])
            )
            dest = self._make_value(ty=res_ty)
            self._emit(WrapErr(dest=dest, val=val))
            self._emit(Move(value=val))
            return dest

        if isinstance(expr, SignalExpr):
            return self._lower_signal_expr(expr)

        if isinstance(expr, AssignExpr):
            return self._lower_assign(expr)

        if isinstance(expr, IfExpr):
            return self._lower_if(expr)

        if isinstance(expr, IfLetExpr):
            return self._lower_if_let(expr)

        if isinstance(expr, MatchExpr):
            return self._lower_match(expr)

        if isinstance(expr, InterpString):
            return self._lower_interp_string(expr)

        # Fallback: unknown expression type
        dest = self._make_value()
        self._emit(Const(dest=dest, ty=mir_unknown(), value=None))
        return dest

    # -- Expression lowering helpers ---------------------------------------

    def _lower_identifier(self, expr: Identifier) -> Value:
        """Lower an identifier reference."""
        # v5.7.0: bare `None` identifier — KW_NONE only matches
        # lowercase `none`/`nada`. Mirror self-hosted lower.mn:1438
        # (v4.134.0 Sh.12) so capital `None` produces a NoneLit IR.
        if expr.name == "None":
            ty = MIRType(TypeInfo(kind=TypeKind.OPTION))
            dest = self._make_value(ty=ty)
            self._emit(WrapNone(dest=dest, ty=ty))
            return dest
        val = self._lookup_var(expr.name)
        if val is not None:
            return val
        # Check if it's a module-level constant
        if expr.name in self._module_consts:
            ty, cval = self._module_consts[expr.name]
            dest = self._make_value(ty=ty, prefix=expr.name)
            self._emit(Const(dest=dest, ty=ty, value=cval))
            return dest
        # Check if it's a bare enum variant (no payload)
        for enum_name, variant_names in self._enum_variants.items():
            if expr.name in variant_names:
                enum_ty = MIRType(TypeInfo(kind=TypeKind.ENUM, name=enum_name))
                dest = self._make_value(ty=enum_ty)
                self._emit(EnumInit(dest=dest, enum_type=enum_ty, variant=expr.name, payload=[]))
                return dest
        # Unknown variable — emit a placeholder
        dest = self._make_value(prefix=expr.name)
        self._emit(Const(dest=dest, ty=mir_unknown(), value=None))
        return dest

    def _lower_binary(self, expr: BinaryExpr) -> Value:
        """Lower a binary expression."""
        # Handle pipe operator specially
        if expr.op == "|>":
            return self._lower_pipe_binary(expr)

        lhs = self._lower_expr(expr.left)
        rhs = self._lower_expr(expr.right)

        # Trait dispatch: if the semantic checker annotated this expression with
        # a trait method, emit a method call instead of a primitive BinOp.
        trait = expr.trait_dispatch
        if trait == "eq":
            dest = self._make_value(ty=mir_bool())
            self._emit(Call(dest=dest, fn_name="eq", args=[lhs, rhs]))
            if expr.op == "!=":
                # Negate the eq result for !=
                neg = self._make_value(ty=mir_bool())
                self._emit(UnaryOp(dest=neg, op=UnaryOpKind.NOT, operand=dest))
                return neg
            return dest
        if trait == "cmp":
            cmp_val = self._make_value(ty=mir_int())
            self._emit(Call(dest=cmp_val, fn_name="cmp", args=[lhs, rhs]))
            dest = self._make_value(ty=mir_bool())
            zero = self._make_value(ty=mir_int())
            self._emit(Const(dest=zero, value=0, ty=mir_int()))
            cmp_op = {"<": BinOpKind.LT, ">": BinOpKind.GT, "<=": BinOpKind.LE, ">=": BinOpKind.GE}
            self._emit(BinOp(dest=dest, op=cmp_op[expr.op], lhs=cmp_val, rhs=zero))
            return dest
        # Arithmetic trait dispatch: add/sub/mul/div impl methods
        if trait in ("add", "sub", "mul", "div"):
            method = _ARITH_TRAIT_MAP.get(expr.op, trait)
            dest = self._make_value(ty=lhs.ty)
            self._emit(Call(dest=dest, fn_name=method, args=[lhs, rhs]))
            return dest

        # Tensor broadcast dispatch (v4.44.0)
        if lhs.ty.kind == TypeKind.TENSOR or rhs.ty.kind == TypeKind.TENSOR:
            return self._lower_tensor_binop(expr.op, lhs, rhs)

        op = _BINOP_MAP.get(expr.op)
        if op is None:
            # Unknown operator — emit as call
            dest = self._make_value()
            self._emit(Call(dest=dest, fn_name=f"__op_{expr.op}", args=[lhs, rhs]))
            return dest

        # Determine result type
        if op in (
            BinOpKind.EQ,
            BinOpKind.NE,
            BinOpKind.LT,
            BinOpKind.GT,
            BinOpKind.LE,
            BinOpKind.GE,
            BinOpKind.AND,
            BinOpKind.OR,
        ):
            result_ty = mir_bool()
        else:
            result_ty = lhs.ty  # inherit from left operand

        dest = self._make_value(ty=result_ty)
        self._emit(BinOp(dest=dest, op=op, lhs=lhs, rhs=rhs))
        return dest

    @staticmethod
    def _is_trivial_chain_operand(e: Expr) -> bool:
        """v5.21.0 Te.6 — D4 triviality predicate.

        Trivial = side-effect-free, single-evaluation read. Trivial
        operands skip the temp binding to keep IR clean. Anything not
        listed gets a temp; conservative by design.
        """
        return isinstance(
            e,
            (
                Identifier,
                IntLiteral,
                FloatLiteral,
                BoolLiteral,
                StringLiteral,
                CharLiteral,
                NoneLiteral,
            ),
        )

    def _lower_chained_compare(self, expr: ChainedCompare) -> Value:
        """v5.21.0 Te.6 — desugar a 3+ element comparison chain.

        `a op1 b op2 c op3 d` lowers to `(a op1 b) && (b op2 c) && (c op3 d)`.
        Interior non-trivial operands are bound to a synthesized
        `__mn_chain_N` local before the chain so each operand evaluates
        exactly once (D3). Trivial operands (Identifier / literals) skip
        the temp.
        """
        # Replace non-trivial interior operands with bound temps.
        operands_for_chain: list[Expr] = list(expr.operands)
        for i in range(1, len(operands_for_chain) - 1):
            sub = operands_for_chain[i]
            if not self._is_trivial_chain_operand(sub):
                tmp_name = f"__mn_chain_{self._chain_compare_counter}"
                self._chain_compare_counter += 1
                synthetic_let = LetBinding(
                    name=tmp_name,
                    mutable=False,
                    type_annotation=None,
                    value=sub,
                    span=expr.span,
                )
                self._lower_let(synthetic_let)
                operands_for_chain[i] = Identifier(name=tmp_name, span=sub.span)
        # Build pairwise BinaryExprs joined by `&&`. Recurse through
        # _lower_expr so trait dispatch (Eq / Ord) and tensor broadcast
        # paths work. Trait dispatch was annotated by the semantic
        # checker per pair; copy it onto each synthesized BinaryExpr.
        pairs: list[BinaryExpr] = []
        for i, op_str in enumerate(expr.ops):
            pair_node = BinaryExpr(
                left=operands_for_chain[i],
                op=op_str,
                right=operands_for_chain[i + 1],
                span=expr.span,
            )
            if i < len(expr.pair_trait_dispatches):
                pair_node.trait_dispatch = expr.pair_trait_dispatches[i]
            pairs.append(pair_node)
        result: Expr = pairs[0]
        for next_pair in pairs[1:]:
            result = BinaryExpr(left=result, op="&&", right=next_pair, span=expr.span)
        return self._lower_expr(result)

    def _lower_pipe_binary(self, expr: BinaryExpr) -> Value:
        """Lower `a |> f` to `Call(f, [a])`, with special handling for stream ops."""
        arg = self._lower_expr(expr.left)

        # Check for stream operations via pipe: `x |> stream()`, `x |> filter(fn)`, etc.
        if isinstance(expr.right, CallExpr) and isinstance(expr.right.callee, Identifier):
            fn_name = expr.right.callee.name

            # `list |> stream()` → StreamInit
            if fn_name == "stream" and not expr.right.args:
                dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.STREAM)))
                elem_type = arg.ty
                self._emit(
                    StreamInit(dest=dest, source=arg, elem_type=MIRType(elem_type.type_info))
                )
                return dest

            # Stream operator via pipe: `stream |> filter(fn)`, `stream |> map(fn)`, etc.
            stream_op = _STREAM_OP_MAP.get(fn_name)
            if stream_op is not None:
                extra_args = [self._lower_expr(a) for a in expr.right.args]
                dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.STREAM)))
                if stream_op == StreamOpKind.COLLECT:
                    dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.LIST)))
                # Resolve lambda function name
                fn_arg_name = ""
                if expr.right.args and isinstance(expr.right.args[0], LambdaExpr):
                    fn_arg_name = extra_args[0].name if extra_args else ""
                    for var_name, lambda_fn in self._lambda_vars.items():
                        if var_name == fn_arg_name.lstrip("%"):
                            fn_arg_name = lambda_fn
                            break
                self._emit(
                    StreamOp(
                        dest=dest,
                        op_kind=stream_op,
                        source=arg,
                        args=extra_args,
                        fn_name=fn_arg_name,
                    )
                )
                return dest

            # Regular pipe: `a |> f(b)` → `f(a, b)`
            extra_args = [self._lower_expr(a) for a in expr.right.args]
            dest = self._make_value()
            self._emit(Call(dest=dest, fn_name=fn_name, args=[arg] + extra_args))
            return dest

        # The right side should be a callable
        if isinstance(expr.right, Identifier):
            # Check for bare stream op names: `x |> collect`
            stream_op = _STREAM_OP_MAP.get(expr.right.name)
            if stream_op is not None:
                dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.STREAM)))
                if stream_op == StreamOpKind.COLLECT:
                    dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.LIST)))
                self._emit(StreamOp(dest=dest, op_kind=stream_op, source=arg, args=[]))
                return dest
            dest = self._make_value()
            self._emit(Call(dest=dest, fn_name=expr.right.name, args=[arg]))
            return dest

        # General case
        fn_val = self._lower_expr(expr.right)
        dest = self._make_value()
        self._emit(Call(dest=dest, fn_name=fn_val.name, args=[arg]))
        return dest

    def _lower_unary(self, expr: UnaryExpr) -> Value:
        """Lower a unary expression."""
        operand = self._lower_expr(expr.operand)
        op = _UNARYOP_MAP.get(expr.op)
        if op is None:
            dest = self._make_value()
            self._emit(Call(dest=dest, fn_name=f"__unary_{expr.op}", args=[operand]))
            return dest

        if op == UnaryOpKind.NOT:
            result_ty = mir_bool()
        else:
            result_ty = operand.ty

        dest = self._make_value(ty=result_ty)
        self._emit(UnaryOp(dest=dest, op=op, operand=operand))
        return dest

    def _lower_call(self, expr: CallExpr) -> Value:
        """Lower a function call."""
        args = [self._lower_expr(a) for a in expr.args]

        # Handle generic call intrinsics (turbofish syntax)
        if isinstance(expr.callee, Identifier) and expr.type_args:
            fn_name = expr.callee.name
            if fn_name == "encode_struct" and len(args) == 1:
                return self._lower_encode_struct(expr, args[0])
            if fn_name == "to_json" and len(args) == 1:
                # v5.36.0 Js.4 (Shape B): alias of encode_struct
                return self._lower_encode_struct(expr, args[0])
            if fn_name == "decode_to" and len(args) == 1:
                return self._lower_decode_to(expr, args[0])
            if fn_name == "from_json" and len(args) == 1:
                # v5.36.0 Js.4 (Shape B): parse + decode_to chain
                return self._lower_from_json(expr, args[0])
            if fn_name == "__struct_meta" and len(args) == 0:
                return self._lower_struct_meta(expr)

        # v4.73.0: block_on(future) — drive a future to completion
        if isinstance(expr.callee, Identifier) and expr.callee.name == "block_on":
            from mapanare.mir import BlockOn

            if len(args) != 1:
                dest = self._make_value()
                return dest
            dest = self._make_value(prefix="block_on")
            self._emit(BlockOn(dest=dest, future=args[0]))
            return dest

        # v4.93.0: spawn(async_call()) — enqueue for multi-threaded execution
        if isinstance(expr.callee, Identifier) and expr.callee.name == "spawn":
            if len(args) != 1:
                dest = self._make_value()
                return dest
            # spawn returns the Future handle (same as the async call result)
            # The emitter will emit __mn_coro_spawn(handle) to register it.
            dest = self._make_value(prefix="spawn")
            self._emit(Call(dest=dest, fn_name="__mn_coro_spawn", args=[args[0]]))
            return args[0]  # return the future, not the spawn result

        # v4.95.0: StringBuilder builtins.
        # v4.108.0: retargeted to the pointer-based runtime API
        # (__mn_sb_new / __mn_sb_finish). The v4.95.0 lowering emitted
        # __mn_sb_create which returns a 24-byte struct by value with
        # sret ABI — the emitter's auto-declare path treated it as a
        # plain ptr, producing calls that would fault or return garbage
        # at runtime. stdlib/ai/llm.mn and embedding.mn were effectively
        # broken since v4.95.0 because of this. The new pointer-based
        # wrappers preserve the user-facing API while fixing the ABI.
        if isinstance(expr.callee, Identifier) and expr.callee.name == "sb_create":
            # Optional initial capacity; default 64 bytes.
            dest = self._make_value(prefix="sb")
            cap_args: list[Value] = args[:1] if args else []
            if not cap_args:
                cap_val = self._make_value(prefix="sb_cap", ty=mir_int())
                self._emit(Const(dest=cap_val, ty=mir_int(), value=64))
                cap_args = [cap_val]
            self._emit(Call(dest=dest, fn_name="__mn_sb_new", args=cap_args))
            return dest
        if isinstance(expr.callee, Identifier) and expr.callee.name == "sb_append":
            if len(args) >= 2:
                dest = self._make_value(prefix="sb_app")
                self._emit(Call(dest=dest, fn_name="__mn_sb_append", args=args[:2]))
            return self._make_value()
        if isinstance(expr.callee, Identifier) and expr.callee.name == "sb_to_string":
            if len(args) >= 1:
                dest = self._make_value(prefix="sb_str", ty=mir_string())
                self._emit(Call(dest=dest, fn_name="__mn_sb_finish", args=args[:1]))
                return dest
            return self._make_value()

        # Monomorphize generic function calls
        if isinstance(expr.callee, Identifier):
            fn_name = expr.callee.name
            type_args_mir = (
                [_resolve_type_expr(ta) for ta in expr.type_args] if expr.type_args else None
            )
            mangled = self._monomorphize_call(fn_name, [a.ty for a in args], type_args_mir)
            if mangled is not None:
                ret_ty = self._fn_return_types.get(mangled, mir_unknown())
                dest = self._make_value(ty=ret_ty)
                self._emit(Call(dest=dest, fn_name=mangled, args=args))
                return dest

        # Infer return type from function declaration or builtins
        _BUILTIN_RET: dict[str, MIRType] = {
            "str": mir_string(),
            "toString": mir_string(),
            "int": mir_int(),
            "float": MIRType(TypeInfo(kind=TypeKind.FLOAT)),
            "len": mir_int(),
            "print": mir_void(),
            "println": mir_void(),
            # C runtime functions used by self-hosted compiler driver
            "__mn_argc": mir_int(),
            "__mn_argv": mir_string(),
            "__mn_file_read_or_empty": mir_string(),
            "__mn_exit": mir_void(),
            "__mn_str_eprint": mir_void(),
            "__mn_str_eprintln": mir_void(),
            # v5.8.4 Wb.2: host-detect for self-hosted ABI classifier.
            "__mn_host_is_win64": mir_int(),
            # v5.8.6 We.1: refined (is_windows, arch_bits) pair.
            "__mn_host_is_windows": mir_int(),
            "__mn_host_arch_bits": mir_int(),
            # v5.14.1 B.5/B.6: colon-block preprocessor (in C runtime).
            "__mn_indent_to_braces": mir_string(),
        }
        _call_ret_ty = mir_unknown()
        if isinstance(expr.callee, Identifier):
            _call_ret_ty = self._fn_return_types.get(
                expr.callee.name,
                _BUILTIN_RET.get(expr.callee.name, mir_unknown()),
            )
        elif isinstance(expr.callee, NamespaceAccessExpr):
            _ns = expr.callee.namespace
            _mem = expr.callee.member
            _call_ret_ty = self._fn_return_types.get(
                f"{_ns}_{_mem}",
                self._fn_return_types.get(_mem, mir_unknown()),
            )
        elif isinstance(expr.callee, FieldAccessExpr):
            _method = expr.callee.field_name
            _call_ret_ty = self._fn_return_types.get(_method, mir_unknown())
        dest = self._make_value(ty=_call_ret_ty)

        if isinstance(expr.callee, Identifier):
            fn_name = expr.callee.name

            # Handle Option/Result builtins
            if fn_name == "Some" and len(args) == 1:
                inner_ti = (
                    args[0].ty.type_info
                    if args[0].ty.type_info.kind != TypeKind.UNKNOWN
                    else TypeInfo(kind=TypeKind.INT)
                )
                opt_ty = MIRType(TypeInfo(kind=TypeKind.OPTION, args=[inner_ti]))
                dest = self._make_value(ty=opt_ty)
                self._emit(WrapSome(dest=dest, val=args[0]))
                self._emit(Move(value=args[0]))
                return dest
            if fn_name == "Ok" and len(args) == 1:
                ok_ti = (
                    args[0].ty.type_info
                    if args[0].ty.type_info.kind != TypeKind.UNKNOWN
                    else TypeInfo(kind=TypeKind.INT)
                )
                res_ty = MIRType(
                    TypeInfo(kind=TypeKind.RESULT, args=[ok_ti, TypeInfo(kind=TypeKind.STRING)])
                )
                dest = self._make_value(ty=res_ty)
                self._emit(WrapOk(dest=dest, val=args[0]))
                self._emit(Move(value=args[0]))
                return dest
            if fn_name == "Err" and len(args) == 1:
                err_ti = (
                    args[0].ty.type_info
                    if args[0].ty.type_info.kind != TypeKind.UNKNOWN
                    else TypeInfo(kind=TypeKind.STRING)
                )
                res_ty = MIRType(
                    TypeInfo(kind=TypeKind.RESULT, args=[TypeInfo(kind=TypeKind.INT), err_ti])
                )
                dest = self._make_value(ty=res_ty)
                self._emit(WrapErr(dest=dest, val=args[0]))
                self._emit(Move(value=args[0]))
                return dest

            # Handle stream() builtin: create stream from list
            if fn_name == "stream" and len(args) == 1:
                dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.STREAM)))
                elem_type = args[0].ty  # inherit element type info from source
                self._emit(
                    StreamInit(dest=dest, source=args[0], elem_type=MIRType(elem_type.type_info))
                )
                return dest

            # Handle typeof() builtin: compile-time type name for concrete types,
            # runtime __mn_any_tag for dynamic `any` values
            if fn_name == "typeof" and len(args) == 1:
                arg_kind = args[0].ty.type_info.kind
                _KIND_TO_TYPENAME: dict[TypeKind, str] = {
                    TypeKind.INT: "Int",
                    TypeKind.FLOAT: "Float",
                    TypeKind.BOOL: "Bool",
                    TypeKind.STRING: "String",
                    TypeKind.CHAR: "Char",
                    TypeKind.LIST: "List",
                    TypeKind.MAP: "Map",
                    TypeKind.OPTION: "Option",
                    TypeKind.RESULT: "Result",
                    TypeKind.SIGNAL: "Signal",
                    TypeKind.STREAM: "Stream",
                    TypeKind.AGENT: "Agent",
                    TypeKind.ENUM: "Enum",
                    TypeKind.STRUCT: "Struct",
                    TypeKind.FN: "Fn",
                    TypeKind.VOID: "Void",
                    TypeKind.RANGE: "Range",
                    TypeKind.ANY: "any",
                }
                # For concrete types, produce a compile-time string constant
                if arg_kind != TypeKind.ANY and arg_kind != TypeKind.UNKNOWN:
                    type_name = _KIND_TO_TYPENAME.get(arg_kind, "Unknown")
                    # Use user-defined name for struct/enum types
                    if arg_kind in (TypeKind.STRUCT, TypeKind.ENUM, TypeKind.AGENT):
                        uname = args[0].ty.type_info.name
                        if uname:
                            type_name = uname
                    dest = self._make_value(ty=mir_string())
                    self._emit(Const(dest=dest, ty=mir_string(), value=type_name))
                    return dest
                # For `any`/unknown, emit runtime call to __mn_any_typename
                dest = self._make_value(ty=mir_string())
                self._emit(Call(dest=dest, fn_name="__mn_any_typename", args=args))
                return dest

            # Check if this is an enum variant constructor
            # Check local enums — match by variant name AND field count
            for enum_name, variant_names in self._enum_variants.items():
                if fn_name in variant_names:
                    # Verify field count matches to avoid ambiguity when
                    # multiple enums have variants with the same name (e.g. Call)
                    enum_variants = self._module.enums.get(enum_name, [])
                    if not enum_variants:
                        # Try imported enums
                        enum_variants = self._imported_enum_defs.get(enum_name, [])
                    variant_fields = next(
                        (vtypes for vn, vtypes in enum_variants if vn == fn_name), None
                    )
                    if variant_fields is not None and len(variant_fields) != len(args):
                        continue  # field count mismatch, try next enum
                    enum_ty = MIRType(TypeInfo(kind=TypeKind.ENUM, name=enum_name))
                    dest = self._make_value(ty=enum_ty)
                    self._emit(
                        EnumInit(dest=dest, enum_type=enum_ty, variant=fn_name, payload=args)
                    )
                    for _a in args:
                        self._emit(Move(value=_a))
                    return dest
            # Check imported enums
            for enum_name, variants in self._imported_enum_defs.items():
                for vname, _ in variants:
                    if vname == fn_name:
                        enum_ty = MIRType(TypeInfo(kind=TypeKind.ENUM, name=enum_name))
                        dest = self._make_value(ty=enum_ty)
                        self._emit(
                            EnumInit(dest=dest, enum_type=enum_ty, variant=fn_name, payload=args)
                        )
                        for _a in args:
                            self._emit(Move(value=_a))
                        self._patch_list_elem_types_for_enum(enum_name, fn_name, args)
                        return dest

            # Check if this is a struct constructor (Name(args) for a known struct)
            if fn_name in self._struct_fields:
                struct_ty = MIRType(TypeInfo(kind=TypeKind.STRUCT, name=fn_name))
                field_names = self._struct_fields[fn_name]
                fields = list(zip(field_names, args))
                dest = self._make_value(ty=struct_ty)
                self._emit(StructInit(dest=dest, struct_type=struct_ty, fields=fields))
                for _a in args:
                    self._emit(Move(value=_a))
                self._patch_list_elem_types_for_struct(fn_name, field_names, args)
                self._patch_arg_types_from_params(fn_name, args)
                return dest

            # Check if this is a closure call (lambda with captures)
            if fn_name in self._closure_vars:
                closure_val = self._lookup_var(fn_name)
                if closure_val is not None:
                    self._emit(ClosureCall(dest=dest, closure=closure_val, args=args))
                    return dest

            # v4.103.0: check if the name resolves to a variable whose
            # type is a closure/function type. Parameters declared with
            # `fn(T) -> T` annotations need indirect calls through the
            # value, not direct calls by name — the v4.99.0 panel's
            # docket #5 blocker. Without this, `return f(x)` inside
            # `fn apply(f: fn(Int)->Int, x: Int) -> Int` was lowered
            # to `call @f(x)` and linking failed with an undefined
            # reference to `f`.
            var_val = self._lookup_var(fn_name)
            if var_val is not None and var_val.ty.kind == TypeKind.FN:
                self._emit(ClosureCall(dest=dest, closure=var_val, args=args))
                return dest

            # Resolve lambda variable names to actual function names
            resolved_name = self._lambda_vars.get(fn_name, fn_name)
            self._emit(Call(dest=dest, fn_name=resolved_name, args=args))
            self._patch_list_elem_types_for_fn_call(fn_name, args)
            self._patch_arg_types_from_params(fn_name, args)
        elif isinstance(expr.callee, FieldAccessExpr):
            # obj.method(args) that parsed as CallExpr(FieldAccessExpr, args)
            obj = self._lower_expr(expr.callee.object)
            method = expr.callee.field_name
            self._emit(Call(dest=dest, fn_name=method, args=[obj] + args))
        elif isinstance(expr.callee, NamespaceAccessExpr):
            ns = expr.callee.namespace
            member = expr.callee.member
            fn_name = f"{ns}_{member}"
            # Check if this is a namespace-qualified enum constructor
            if ns in self._enum_variants and member in self._enum_variants[ns]:
                enum_ty = MIRType(TypeInfo(kind=TypeKind.ENUM, name=ns))
                dest = self._make_value(ty=enum_ty)
                self._emit(EnumInit(dest=dest, enum_type=enum_ty, variant=member, payload=args))
                for _a in args:
                    self._emit(Move(value=_a))
                return dest
            # Look up return type: try NS_Member first, then bare Member
            ns_ret = self._fn_return_types.get(
                fn_name, self._fn_return_types.get(member, mir_unknown())
            )
            if ns_ret.kind != TypeKind.UNKNOWN:
                dest = self._make_value(ty=ns_ret)
            self._emit(Call(dest=dest, fn_name=fn_name, args=args))
        else:
            callee_val = self._lower_expr(expr.callee)
            self._emit(Call(dest=dest, fn_name=callee_val.name, args=args))

        return dest

    # ------------------------------------------------------------------
    # Compile-time struct intrinsics (turbofish generic calls)
    # ------------------------------------------------------------------

    def _lower_encode_struct(self, expr: CallExpr, struct_val: Value) -> Value:
        """Lower encode_struct::<T>(value) — serialize struct to JSON string."""
        type_arg = expr.type_args[0]
        struct_name = type_arg.name if hasattr(type_arg, "name") else ""
        return self._emit_struct_json_body(struct_val, struct_name)

    def _emit_struct_json_body(self, struct_val: Value, struct_name: str) -> Value:
        """Emit MIR producing a JSON `{...}` string for struct_val.

        Shared between top-level encode_struct::<T> / to_json::<T>
        (via _lower_encode_struct) and struct-typed-field recursion
        (via _encode_field_to_json's STRUCT branch). v5.39.3 Js.4.C —
        closes the `<?>` placeholder for nested struct fields.
        """
        fields = self._module.structs.get(struct_name, [])
        if not fields:
            dest = self._make_value(ty=mir_string())
            self._emit(Const(dest=dest, ty=mir_string(), value="{}"))
            return dest

        # Build JSON string: {"field1": val1, "field2": val2, ...}
        result = self._make_value(ty=mir_string())
        self._emit(Const(dest=result, ty=mir_string(), value="{"))

        for i, (fname, ftype) in enumerate(fields):
            # Add comma separator after first field
            if i > 0:
                comma = self._make_value(ty=mir_string())
                self._emit(Const(dest=comma, ty=mir_string(), value=", "))
                new_result = self._make_value(ty=mir_string())
                self._emit(BinOp(dest=new_result, op=BinOpKind.ADD, lhs=result, rhs=comma))
                result = new_result

            # Add "\"fieldname\": "
            key_str = self._make_value(ty=mir_string())
            self._emit(Const(dest=key_str, ty=mir_string(), value=f'"{fname}": '))
            new_result = self._make_value(ty=mir_string())
            self._emit(BinOp(dest=new_result, op=BinOpKind.ADD, lhs=result, rhs=key_str))
            result = new_result

            # Get field value
            field_val = self._make_value(ty=ftype)
            self._emit(FieldGet(dest=field_val, obj=struct_val, field_name=fname))

            # Convert value to JSON string based on type
            val_str = self._encode_field_to_json(field_val, ftype)
            new_result = self._make_value(ty=mir_string())
            self._emit(BinOp(dest=new_result, op=BinOpKind.ADD, lhs=result, rhs=val_str))
            result = new_result

        # Close with "}"
        close = self._make_value(ty=mir_string())
        self._emit(Const(dest=close, ty=mir_string(), value="}"))
        final = self._make_value(ty=mir_string())
        self._emit(BinOp(dest=final, op=BinOpKind.ADD, lhs=result, rhs=close))
        return final

    def _lower_struct_meta(self, expr: CallExpr) -> Value:
        """Lower __struct_meta::<T>() — returns JSON schema string for struct T (v4.48.0)."""
        type_arg = expr.type_args[0]
        struct_name = type_arg.name if hasattr(type_arg, "name") else ""
        fields = self._module.structs.get(struct_name, [])

        # Map Mapanare types to JSON schema types
        def _json_type(ftype: MIRType) -> str:
            kind = ftype.type_info.kind
            if kind == TypeKind.STRING:
                return "string"
            if kind == TypeKind.INT:
                return "integer"
            if kind == TypeKind.FLOAT:
                return "number"
            if kind == TypeKind.BOOL:
                return "boolean"
            if kind == TypeKind.LIST:
                return "array"
            if kind == TypeKind.OPTION:
                # Optional fields: use the inner type
                if ftype.type_info.args:
                    return _json_type(MIRType(ftype.type_info.args[0]))
                return "string"
            return "string"

        # Build JSON schema at compile time as a constant string
        props: list[str] = []
        required: list[str] = []
        for fname, ftype in fields:
            jtype = _json_type(ftype)
            props.append(f'"{fname}": {{"type": "{jtype}"}}')
            if ftype.type_info.kind != TypeKind.OPTION:
                required.append(f'"{fname}"')

        props_str = ", ".join(props)
        req_str = ", ".join(required)
        schema = f'{{"type": "object", "properties": {{{props_str}}}, ' f'"required": [{req_str}]}}'

        dest = self._make_value(ty=mir_string())
        self._emit(Const(dest=dest, ty=mir_string(), value=schema))
        return dest

    def _encode_field_to_json(self, field_val: Value, ftype: MIRType) -> Value:
        """Generate MIR to convert a field value to its JSON string representation."""
        kind = ftype.type_info.kind

        if kind == TypeKind.STRING:
            # Wrap in quotes: "\"" + value + "\""
            q1 = self._make_value(ty=mir_string())
            self._emit(Const(dest=q1, ty=mir_string(), value='"'))
            q2 = self._make_value(ty=mir_string())
            self._emit(Const(dest=q2, ty=mir_string(), value='"'))
            t1 = self._make_value(ty=mir_string())
            self._emit(BinOp(dest=t1, op=BinOpKind.ADD, lhs=q1, rhs=field_val))
            t2 = self._make_value(ty=mir_string())
            self._emit(BinOp(dest=t2, op=BinOpKind.ADD, lhs=t1, rhs=q2))
            return t2

        if kind in (TypeKind.INT, TypeKind.FLOAT):
            # str(value)
            dest = self._make_value(ty=mir_string())
            self._emit(Call(dest=dest, fn_name="str", args=[field_val]))
            return dest

        if kind == TypeKind.BOOL:
            # if value then "true" else "false"
            true_bb = self._new_block("encode_true")
            false_bb = self._new_block("encode_false")
            merge_bb = self._new_block("encode_merge")
            self._emit(Branch(cond=field_val, true_block=true_bb.label, false_block=false_bb.label))

            self._set_block(true_bb)
            true_str = self._make_value(ty=mir_string())
            self._emit(Const(dest=true_str, ty=mir_string(), value="true"))
            self._emit(Jump(target=merge_bb.label))
            assert self._block is not None
            true_exit = self._block.label

            self._set_block(false_bb)
            false_str = self._make_value(ty=mir_string())
            self._emit(Const(dest=false_str, ty=mir_string(), value="false"))
            self._emit(Jump(target=merge_bb.label))
            assert self._block is not None
            false_exit = self._block.label

            self._set_block(merge_bb)
            result = self._make_value(ty=mir_string())
            self._emit(Phi(dest=result, incoming=[(true_exit, true_str), (false_exit, false_str)]))
            return result

        if kind == TypeKind.OPTION:
            # Option: if Some, encode inner; if None, "null"
            tag = self._make_value(ty=mir_int())
            self._emit(EnumTag(dest=tag, enum_val=field_val))
            some_bb = self._new_block("encode_some")
            none_bb = self._new_block("encode_none")
            merge_bb = self._new_block("encode_opt_merge")
            self._emit(
                Switch(tag=tag, cases=[("Some", some_bb.label)], default_block=none_bb.label)
            )

            self._set_block(some_bb)
            inner = self._make_value(ty=mir_unknown())
            self._emit(EnumPayload(dest=inner, enum_val=field_val, variant="Some", payload_idx=0))
            # Determine inner type from Option type args
            inner_type = MIRType(ftype.type_info.args[0]) if ftype.type_info.args else mir_unknown()
            inner_str = self._encode_field_to_json(inner, inner_type)
            self._emit(Jump(target=merge_bb.label))
            assert self._block is not None
            some_exit = self._block.label

            self._set_block(none_bb)
            null_str = self._make_value(ty=mir_string())
            self._emit(Const(dest=null_str, ty=mir_string(), value="null"))
            self._emit(Jump(target=merge_bb.label))
            assert self._block is not None
            none_exit = self._block.label

            self._set_block(merge_bb)
            result = self._make_value(ty=mir_string())
            self._emit(Phi(dest=result, incoming=[(some_exit, inner_str), (none_exit, null_str)]))
            return result

        if kind == TypeKind.STRUCT:
            # v5.39.3 Js.4.C — recurse into nested struct field via shared helper.
            # Pre-fix this fell into the str() fallback below, producing the
            # `<?>` placeholder. The struct must be registered in
            # self._module.structs (any reachable struct definition is).
            struct_name = ftype.type_info.name if ftype.type_info else ""
            if struct_name and struct_name in self._module.structs:
                return self._emit_struct_json_body(field_val, struct_name)

        if kind == TypeKind.LIST:
            # v5.39.4 Js.4.D.1 — encode each element through _encode_field_to_json.
            # Pre-fix this fell into the str() fallback, producing the `<?>`
            # placeholder for any List-typed struct field.
            inner_type = (
                MIRType(ftype.type_info.args[0])
                if ftype.type_info and ftype.type_info.args
                else mir_unknown()
            )
            return self._emit_list_json_body(field_val, inner_type)

        if kind == TypeKind.MAP:
            # v5.39.6 Js.4.E.1 — encode each entry as "key": value, recursing
            # through _encode_field_to_json on the value type. Pre-fix this
            # fell into the str() fallback, producing the `<?>` placeholder
            # for any Map-typed struct field. JSON object keys must be
            # strings (RFC 8259 §4); non-String K is rejected at compile
            # time per the v5.39.6 PLAN invariant decision.
            args = ftype.type_info.args if ftype.type_info else []
            key_kind = args[0].kind if args else TypeKind.UNKNOWN
            if key_kind != TypeKind.STRING:
                raise RuntimeError(f"to_json: Map<K, V> requires K = String (got {key_kind.name})")
            val_type = MIRType(args[1]) if len(args) > 1 else mir_unknown()
            return self._emit_map_json_body(field_val, val_type)

        # Fallback: convert to string with str()
        dest = self._make_value(ty=mir_string())
        self._emit(Call(dest=dest, fn_name="str", args=[field_val]))
        return dest

    def _emit_list_json_body(self, list_val: Value, inner_type: MIRType) -> Value:
        """Emit MIR producing a JSON `[...]` string for list_val.

        Loops element-by-element and recurses through _encode_field_to_json
        on the element type, so nested List<List<T>> / List<Struct> fall
        through the existing STRUCT / LIST / primitive branches uniformly.
        v5.39.4 Js.4.D.1 — sibling to v5.39.3's STRUCT branch.

        Loop shape (mutable-Phi pattern; same as a hand-written while):
            entry: zero=0; len_v=len(list); init="["; jump header
            header: counter=phi(zero, new_counter)
                    result =phi(init, new_result)
                    cmp = counter < len_v
                    branch cmp -> body, exit
            body:   elem = list[counter]
                    elem_str = _encode_field_to_json(elem, inner_type)
                    if counter == 0: result_after = result + elem_str
                    else:            result_after = result + ", " + elem_str
                    new_counter = counter + 1
                    new_result  = result_after
                    jump header
            exit:   final = result + "]"; return final
        """
        assert self._block is not None
        entry_label = self._block.label

        zero = self._make_value(ty=mir_int())
        self._emit(Const(dest=zero, ty=mir_int(), value=0))

        len_val = self._make_value(ty=mir_int())
        self._emit(Call(dest=len_val, fn_name="len", args=[list_val]))

        init_str = self._make_value(ty=mir_string())
        self._emit(Const(dest=init_str, ty=mir_string(), value="["))

        header_bb = self._new_block(self._fresh_block("list_enc_header"))
        body_bb = self._new_block(self._fresh_block("list_enc_body"))
        exit_bb = self._new_block(self._fresh_block("list_enc_exit"))

        self._emit(Jump(target=header_bb.label))

        # Header: phi nodes for counter + accumulator (incoming filled later)
        self._set_block(header_bb)
        counter_phi_dest = self._make_value(ty=mir_int())
        counter_phi = Phi(dest=counter_phi_dest, incoming=[])
        self._emit(counter_phi)
        result_phi_dest = self._make_value(ty=mir_string())
        result_phi = Phi(dest=result_phi_dest, incoming=[])
        self._emit(result_phi)

        cmp = self._make_value(ty=mir_bool())
        self._emit(BinOp(dest=cmp, op=BinOpKind.LT, lhs=counter_phi_dest, rhs=len_val))
        self._emit(Branch(cond=cmp, true_block=body_bb.label, false_block=exit_bb.label))

        # Body: extract element, encode, append (with separator if not first)
        self._set_block(body_bb)
        elem = self._make_value(ty=inner_type)
        self._emit(IndexGet(dest=elem, obj=list_val, index=counter_phi_dest))
        elem_str = self._encode_field_to_json(elem, inner_type)

        is_first = self._make_value(ty=mir_bool())
        self._emit(BinOp(dest=is_first, op=BinOpKind.EQ, lhs=counter_phi_dest, rhs=zero))

        first_bb = self._new_block(self._fresh_block("list_enc_first"))
        rest_bb = self._new_block(self._fresh_block("list_enc_rest"))
        sep_merge_bb = self._new_block(self._fresh_block("list_enc_sep_merge"))
        self._emit(Branch(cond=is_first, true_block=first_bb.label, false_block=rest_bb.label))

        # First-element path: result + elem_str
        self._set_block(first_bb)
        first_added = self._make_value(ty=mir_string())
        self._emit(BinOp(dest=first_added, op=BinOpKind.ADD, lhs=result_phi_dest, rhs=elem_str))
        self._emit(Jump(target=sep_merge_bb.label))
        assert self._block is not None
        first_exit = self._block.label

        # Rest path: result + ", " + elem_str
        self._set_block(rest_bb)
        comma = self._make_value(ty=mir_string())
        self._emit(Const(dest=comma, ty=mir_string(), value=", "))
        with_comma = self._make_value(ty=mir_string())
        self._emit(BinOp(dest=with_comma, op=BinOpKind.ADD, lhs=result_phi_dest, rhs=comma))
        rest_added = self._make_value(ty=mir_string())
        self._emit(BinOp(dest=rest_added, op=BinOpKind.ADD, lhs=with_comma, rhs=elem_str))
        self._emit(Jump(target=sep_merge_bb.label))
        assert self._block is not None
        rest_exit = self._block.label

        # Merge separator branches
        self._set_block(sep_merge_bb)
        new_result = self._make_value(ty=mir_string())
        self._emit(
            Phi(dest=new_result, incoming=[(first_exit, first_added), (rest_exit, rest_added)])
        )

        # counter++
        one = self._make_value(ty=mir_int())
        self._emit(Const(dest=one, ty=mir_int(), value=1))
        new_counter = self._make_value(ty=mir_int())
        self._emit(BinOp(dest=new_counter, op=BinOpKind.ADD, lhs=counter_phi_dest, rhs=one))

        assert self._block is not None
        body_exit_label = self._block.label
        self._emit(Jump(target=header_bb.label))

        # Patch the header phis now that body's exit label is known
        counter_phi.incoming = [(entry_label, zero), (body_exit_label, new_counter)]
        result_phi.incoming = [(entry_label, init_str), (body_exit_label, new_result)]

        # Exit: append "]"
        self._set_block(exit_bb)
        close = self._make_value(ty=mir_string())
        self._emit(Const(dest=close, ty=mir_string(), value="]"))
        final = self._make_value(ty=mir_string())
        self._emit(BinOp(dest=final, op=BinOpKind.ADD, lhs=result_phi_dest, rhs=close))
        return final

    def _emit_map_json_body(self, map_val: Value, val_type: MIRType) -> Value:
        """Emit MIR producing a JSON `{...}` string for map_val.

        Mirrors v5.39.4's _emit_list_json_body shape but for Map<String, V>.
        Iterates via __mn_map_keys (List<String>) + per-key IndexGet on the
        map (lowered to __mn_map_get). Recurses through _encode_field_to_json
        on the value type so nested Map<String, Struct> / Map<String, List>
        / Map<String, Map> fall through STRUCT / LIST / MAP / primitive
        branches uniformly.

        Loop shape (mutable-Phi pattern; same as the LIST encode helper):
            entry: keys = __mn_map_keys(map); len_v = len(keys); zero=0
                   init = "{"; jump header
            header: counter = phi(zero, new_counter)
                    result  = phi(init, new_result)
                    cmp = counter < len_v
                    branch cmp -> body, exit
            body:   key      = keys[counter]
                    val      = map[key]                ; IndexGet on Map
                    quoted_k = "\"" + key + "\""
                    val_str  = _encode_field_to_json(val, val_type)
                    pair     = quoted_k + ": " + val_str
                    if counter == 0: result_after = result + pair
                    else:            result_after = result + ", " + pair
                    new_counter = counter + 1
                    new_result  = result_after
                    jump header
            exit:   final = result + "}"; return final

        Note: JSON object keys are unordered (RFC 8259 §4); tests must
        assert via `contains` patterns rather than positional equality.
        """
        assert self._block is not None
        entry_label = self._block.label

        # keys = __mn_map_keys(map)
        keys_ty = MIRType(TypeInfo(kind=TypeKind.LIST, args=[TypeInfo(kind=TypeKind.STRING)]))
        keys_val = self._make_value(ty=keys_ty)
        self._emit(Call(dest=keys_val, fn_name="__mn_map_keys", args=[map_val]))

        # len_v = len(keys)
        len_val = self._make_value(ty=mir_int())
        self._emit(Call(dest=len_val, fn_name="len", args=[keys_val]))

        zero = self._make_value(ty=mir_int())
        self._emit(Const(dest=zero, ty=mir_int(), value=0))

        init_str = self._make_value(ty=mir_string())
        self._emit(Const(dest=init_str, ty=mir_string(), value="{"))

        header_bb = self._new_block(self._fresh_block("map_enc_header"))
        body_bb = self._new_block(self._fresh_block("map_enc_body"))
        exit_bb = self._new_block(self._fresh_block("map_enc_exit"))

        self._emit(Jump(target=header_bb.label))

        # Header: phi nodes for counter + accumulator (incoming filled later)
        self._set_block(header_bb)
        counter_phi_dest = self._make_value(ty=mir_int())
        counter_phi = Phi(dest=counter_phi_dest, incoming=[])
        self._emit(counter_phi)
        result_phi_dest = self._make_value(ty=mir_string())
        result_phi = Phi(dest=result_phi_dest, incoming=[])
        self._emit(result_phi)

        cmp = self._make_value(ty=mir_bool())
        self._emit(BinOp(dest=cmp, op=BinOpKind.LT, lhs=counter_phi_dest, rhs=len_val))
        self._emit(Branch(cond=cmp, true_block=body_bb.label, false_block=exit_bb.label))

        # Body
        self._set_block(body_bb)
        key = self._make_value(ty=mir_string())
        self._emit(IndexGet(dest=key, obj=keys_val, index=counter_phi_dest))

        val = self._make_value(ty=val_type)
        self._emit(IndexGet(dest=val, obj=map_val, index=key))

        # quoted_key = "\"" + key + "\""
        q1 = self._make_value(ty=mir_string())
        self._emit(Const(dest=q1, ty=mir_string(), value='"'))
        q2 = self._make_value(ty=mir_string())
        self._emit(Const(dest=q2, ty=mir_string(), value='"'))
        kq1 = self._make_value(ty=mir_string())
        self._emit(BinOp(dest=kq1, op=BinOpKind.ADD, lhs=q1, rhs=key))
        kq2 = self._make_value(ty=mir_string())
        self._emit(BinOp(dest=kq2, op=BinOpKind.ADD, lhs=kq1, rhs=q2))

        # encoded value through recursion
        val_str = self._encode_field_to_json(val, val_type)

        # pair = quoted_key + ": " + val_str
        colon = self._make_value(ty=mir_string())
        self._emit(Const(dest=colon, ty=mir_string(), value=": "))
        with_colon = self._make_value(ty=mir_string())
        self._emit(BinOp(dest=with_colon, op=BinOpKind.ADD, lhs=kq2, rhs=colon))
        pair = self._make_value(ty=mir_string())
        self._emit(BinOp(dest=pair, op=BinOpKind.ADD, lhs=with_colon, rhs=val_str))

        # Separator decision: first iteration vs rest
        is_first = self._make_value(ty=mir_bool())
        self._emit(BinOp(dest=is_first, op=BinOpKind.EQ, lhs=counter_phi_dest, rhs=zero))

        first_bb = self._new_block(self._fresh_block("map_enc_first"))
        rest_bb = self._new_block(self._fresh_block("map_enc_rest"))
        sep_merge_bb = self._new_block(self._fresh_block("map_enc_sep_merge"))
        self._emit(Branch(cond=is_first, true_block=first_bb.label, false_block=rest_bb.label))

        # First-element path: result + pair
        self._set_block(first_bb)
        first_added = self._make_value(ty=mir_string())
        self._emit(BinOp(dest=first_added, op=BinOpKind.ADD, lhs=result_phi_dest, rhs=pair))
        self._emit(Jump(target=sep_merge_bb.label))
        assert self._block is not None
        first_exit = self._block.label

        # Rest path: result + ", " + pair
        self._set_block(rest_bb)
        comma = self._make_value(ty=mir_string())
        self._emit(Const(dest=comma, ty=mir_string(), value=", "))
        with_comma = self._make_value(ty=mir_string())
        self._emit(BinOp(dest=with_comma, op=BinOpKind.ADD, lhs=result_phi_dest, rhs=comma))
        rest_added = self._make_value(ty=mir_string())
        self._emit(BinOp(dest=rest_added, op=BinOpKind.ADD, lhs=with_comma, rhs=pair))
        self._emit(Jump(target=sep_merge_bb.label))
        assert self._block is not None
        rest_exit = self._block.label

        # Merge separator branches
        self._set_block(sep_merge_bb)
        new_result = self._make_value(ty=mir_string())
        self._emit(
            Phi(dest=new_result, incoming=[(first_exit, first_added), (rest_exit, rest_added)])
        )

        # counter++
        one = self._make_value(ty=mir_int())
        self._emit(Const(dest=one, ty=mir_int(), value=1))
        new_counter = self._make_value(ty=mir_int())
        self._emit(BinOp(dest=new_counter, op=BinOpKind.ADD, lhs=counter_phi_dest, rhs=one))

        assert self._block is not None
        body_exit_label = self._block.label
        self._emit(Jump(target=header_bb.label))

        # Patch the header phis now that body's exit label is known
        counter_phi.incoming = [(entry_label, zero), (body_exit_label, new_counter)]
        result_phi.incoming = [(entry_label, init_str), (body_exit_label, new_result)]

        # Exit: append "}"
        self._set_block(exit_bb)
        close = self._make_value(ty=mir_string())
        self._emit(Const(dest=close, ty=mir_string(), value="}"))
        final = self._make_value(ty=mir_string())
        self._emit(BinOp(dest=final, op=BinOpKind.ADD, lhs=result_phi_dest, rhs=close))
        return final

    def _ensure_json_types_registered(self) -> None:
        """v5.39.1 Js.4.B.1 — register JsonValue + JsonError in the
        MIR module so the LLVM emitter sees them as first-class user
        enums/structs and the proper boxed-enum extraction path
        fires (rather than the Result/Option fallback in
        emit_llvm_text._do_enum_payload's else branch, which
        extractvalue's a ptr but stores it as the dest's primitive
        type — invalid IR).

        Layout mirrors stdlib/encoding/json.mn:15-29. If json.mn
        drifts, tests/stdlib/test_struct_json_layout.py fails loudly.
        """
        if "JsonValue" not in self._module.enums:
            jv_enum = MIRType(TypeInfo(kind=TypeKind.ENUM, name="JsonValue"))
            self._module.enums["JsonValue"] = [
                ("Null", []),
                ("Bool", [mir_bool()]),
                ("Int", [mir_int()]),
                ("Float", [MIRType(TypeInfo(kind=TypeKind.FLOAT))]),
                ("Str", [mir_string()]),
                (
                    "Array",
                    [
                        MIRType(
                            TypeInfo(
                                kind=TypeKind.LIST,
                                args=[jv_enum.type_info],
                            )
                        )
                    ],
                ),
                (
                    "Object",
                    [
                        MIRType(
                            TypeInfo(
                                kind=TypeKind.MAP,
                                args=[
                                    TypeInfo(kind=TypeKind.STRING),
                                    jv_enum.type_info,
                                ],
                            )
                        )
                    ],
                ),
            ]
        if "JsonError" not in self._module.structs:
            self._module.structs["JsonError"] = [
                ("message", mir_string()),
                ("line", mir_int()),
                ("col", mir_int()),
            ]

    def _lower_decode_to(self, expr: CallExpr, json_val: Value) -> Value:
        """Lower decode_to::<T>(json_value) — deserialize JsonValue to struct.

        Takes a JsonValue (already parsed), extracts Object variant's map,
        looks up each struct field by key, converts to proper type, constructs struct.
        v5.39.4 Js.4.D.2: factored out _emit_decode_struct_inline so the
        nested-struct field decoder can reuse the field-extraction body
        without the outer Result-wrap + tag-check.
        """
        self._ensure_json_types_registered()
        type_arg = expr.type_args[0]
        struct_name = type_arg.name if hasattr(type_arg, "name") else ""

        # v5.36.0 Js.4: result_ty must carry type args so the user's match
        # arms extract the correct payload shape. Pre-fix this was a bare
        # `Result` with no args; downstream Phi merges + Ok extraction
        # produced `ptr` instead of `{i64, i64, ...}` for the Point payload.
        # Bug stayed latent because tests/stdlib/test_struct_json.py only
        # checked compilation-to-IR-text, never link.
        result_ty = MIRType(
            TypeInfo(
                kind=TypeKind.RESULT,
                name="Result",
                args=[
                    TypeInfo(kind=TypeKind.STRUCT, name=struct_name),
                    TypeInfo(kind=TypeKind.STRUCT, name="JsonError"),
                ],
            )
        )
        err_struct_ty = MIRType(TypeInfo(kind=TypeKind.STRUCT, name="JsonError"))

        # Step 1: Check if json_val is an Object variant
        tag = self._make_value(ty=mir_int())
        self._emit(EnumTag(dest=tag, enum_val=json_val))

        obj_bb = self._new_block("decode_object")
        err_bb = self._new_block("decode_type_err")
        merge_bb = self._new_block("decode_merge")

        self._emit(Switch(tag=tag, cases=[("Object", obj_bb.label)], default_block=err_bb.label))

        # Error path: not an Object
        self._set_block(err_bb)
        err_msg = self._make_value(ty=mir_string())
        self._emit(Const(dest=err_msg, ty=mir_string(), value="expected JSON object"))
        err_line = self._make_value(ty=mir_int())
        self._emit(Const(dest=err_line, ty=mir_int(), value=0))
        err_col = self._make_value(ty=mir_int())
        self._emit(Const(dest=err_col, ty=mir_int(), value=0))
        err_struct = self._make_value(ty=err_struct_ty)
        self._emit(
            StructInit(
                dest=err_struct,
                struct_type=err_struct_ty,
                fields=[("message", err_msg), ("line", err_line), ("col", err_col)],
            )
        )
        self._emit(Move(value=err_msg))
        self._emit(Move(value=err_line))
        self._emit(Move(value=err_col))
        err_result = self._make_value(ty=result_ty)
        self._emit(WrapErr(dest=err_result, val=err_struct))
        self._emit(Move(value=err_struct))
        self._emit(Jump(target=merge_bb.label))
        assert self._block is not None
        err_exit = self._block.label

        # Object path: shared inline decoder
        self._set_block(obj_bb)
        struct_val = self._emit_decode_struct_inline(json_val, struct_name)

        # Wrap in Ok
        ok_result = self._make_value(ty=result_ty)
        self._emit(WrapOk(dest=ok_result, val=struct_val))
        self._emit(Move(value=struct_val))
        self._emit(Jump(target=merge_bb.label))
        assert self._block is not None
        ok_exit = self._block.label

        # Merge block
        self._set_block(merge_bb)
        final = self._make_value(ty=result_ty)
        self._emit(Phi(dest=final, incoming=[(err_exit, err_result), (ok_exit, ok_result)]))
        return final

    def _emit_decode_struct_inline(self, json_val: Value, struct_name: str) -> Value:
        """Emit MIR that extracts a struct of `struct_name` from `json_val`,
        assuming `json_val` is a `JsonValue::Object`. Returns the bare
        struct value (NOT wrapped in Result).

        Shared between top-level decode_to::<T> / from_json::<T> (via
        _lower_decode_to's Object branch) and struct-typed-field recursion
        (via _decode_json_field's STRUCT branch). v5.39.4 Js.4.D.2 —
        sibling to v5.39.3's encode-side _emit_struct_json_body factoring.

        The caller is responsible for any tag-check + error-result wrap;
        this helper is the pure Object → struct conversion.
        """
        struct_ty = MIRType(TypeInfo(kind=TypeKind.STRUCT, name=struct_name))
        fields = self._module.structs.get(struct_name, [])

        # Extract the entries map from the Object variant
        entries = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.MAP)))
        self._emit(EnumPayload(dest=entries, enum_val=json_val, variant="Object", payload_idx=0))

        # Extract each field by name
        field_values: list[tuple[str, Value]] = []
        for fname, ftype in fields:
            key = self._make_value(ty=mir_string())
            self._emit(Const(dest=key, ty=mir_string(), value=fname))

            jval = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.ENUM, name="JsonValue")))
            self._emit(IndexGet(dest=jval, obj=entries, index=key))

            converted = self._decode_json_field(jval, ftype)
            field_values.append((fname, converted))

        # Construct the struct
        struct_val = self._make_value(ty=struct_ty)
        self._emit(StructInit(dest=struct_val, struct_type=struct_ty, fields=field_values))
        for _fn_, _fv_ in field_values:
            self._emit(Move(value=_fv_))
        return struct_val

    def _lower_from_json(self, expr: CallExpr, str_val: Value) -> Value:
        """Lower from_json::<T>(s: String) — parse + decode_to chain.

        v5.36.0 Js.4 (Shape B). Lowers to:
            let r = decode(s)         // Result<JsonValue, JsonError>
            match r {
                Ok(jv)  => decode_to::<T>(jv),
                Err(e)  => Err(e),
            }
        """
        self._ensure_json_types_registered()
        type_arg = expr.type_args[0]
        struct_name = type_arg.name if hasattr(type_arg, "name") else ""
        # Result<T, JsonError> where T is the user-specified type.
        result_ty = MIRType(
            TypeInfo(
                kind=TypeKind.RESULT,
                name="Result",
                args=[
                    TypeInfo(kind=TypeKind.STRUCT, name=struct_name),
                    TypeInfo(kind=TypeKind.STRUCT, name="JsonError"),
                ],
            )
        )
        # decode() returns Result<JsonValue, JsonError>.
        decode_result_ty = MIRType(
            TypeInfo(
                kind=TypeKind.RESULT,
                name="Result",
                args=[
                    TypeInfo(kind=TypeKind.ENUM, name="JsonValue"),
                    TypeInfo(kind=TypeKind.STRUCT, name="JsonError"),
                ],
            )
        )
        json_value_ty = MIRType(TypeInfo(kind=TypeKind.ENUM, name="JsonValue"))
        err_struct_ty = MIRType(TypeInfo(kind=TypeKind.STRUCT, name="JsonError"))

        # Step 1: call decode(s)
        decode_result = self._make_value(ty=decode_result_ty)
        self._emit(Call(dest=decode_result, fn_name="decode", args=[str_val]))

        # Step 2: switch on Ok/Err
        tag = self._make_value(ty=mir_int())
        self._emit(EnumTag(dest=tag, enum_val=decode_result))

        ok_bb = self._new_block("from_json_ok")
        err_bb = self._new_block("from_json_err")
        merge_bb = self._new_block("from_json_merge")
        self._emit(Switch(tag=tag, cases=[("Ok", ok_bb.label)], default_block=err_bb.label))

        # Ok path: extract JsonValue payload, run decode_to
        self._set_block(ok_bb)
        jv = self._make_value(ty=json_value_ty)
        self._emit(EnumPayload(dest=jv, enum_val=decode_result, variant="Ok", payload_idx=0))
        decoded = self._lower_decode_to(expr, jv)
        self._emit(Jump(target=merge_bb.label))
        assert self._block is not None
        ok_exit = self._block.label

        # Err path: pass error through, re-wrap into Result<T, JsonError>
        self._set_block(err_bb)
        err_val = self._make_value(ty=err_struct_ty)
        self._emit(EnumPayload(dest=err_val, enum_val=decode_result, variant="Err", payload_idx=0))
        err_result = self._make_value(ty=result_ty)
        self._emit(WrapErr(dest=err_result, val=err_val))
        self._emit(Move(value=err_val))
        self._emit(Jump(target=merge_bb.label))
        assert self._block is not None
        err_exit = self._block.label

        # Merge
        self._set_block(merge_bb)
        final = self._make_value(ty=result_ty)
        self._emit(Phi(dest=final, incoming=[(ok_exit, decoded), (err_exit, err_result)]))
        return final

    def _decode_json_field(self, jval: Value, target_type: MIRType) -> Value:
        """Generate MIR to extract a typed value from a JsonValue enum."""
        kind = target_type.type_info.kind

        if kind == TypeKind.STRING:
            dest = self._make_value(ty=mir_string())
            self._emit(EnumPayload(dest=dest, enum_val=jval, variant="Str", payload_idx=0))
            return dest

        if kind == TypeKind.INT:
            dest = self._make_value(ty=mir_int())
            self._emit(EnumPayload(dest=dest, enum_val=jval, variant="Int", payload_idx=0))
            return dest

        if kind == TypeKind.FLOAT:
            dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.FLOAT)))
            self._emit(EnumPayload(dest=dest, enum_val=jval, variant="Float", payload_idx=0))
            return dest

        if kind == TypeKind.BOOL:
            dest = self._make_value(ty=mir_bool())
            self._emit(EnumPayload(dest=dest, enum_val=jval, variant="Bool", payload_idx=0))
            return dest

        if kind == TypeKind.OPTION:
            # Check if Null → None, otherwise extract inner value
            tag = self._make_value(ty=mir_int())
            self._emit(EnumTag(dest=tag, enum_val=jval))
            some_bb = self._new_block("field_some")
            none_bb = self._new_block("field_none")
            merge_bb = self._new_block("field_opt_merge")
            self._emit(
                Switch(tag=tag, cases=[("Null", none_bb.label)], default_block=some_bb.label)
            )

            # None path (JSON null)
            self._set_block(none_bb)
            none_val = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.OPTION)))
            self._emit(WrapNone(dest=none_val))
            self._emit(Jump(target=merge_bb.label))
            assert self._block is not None
            none_exit = self._block.label

            # Some path: extract inner value
            self._set_block(some_bb)
            inner_type = (
                MIRType(target_type.type_info.args[0])
                if target_type.type_info.args
                else mir_unknown()
            )
            inner = self._decode_json_field(jval, inner_type)
            some_val = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.OPTION)))
            self._emit(WrapSome(dest=some_val, val=inner))
            self._emit(Jump(target=merge_bb.label))
            assert self._block is not None
            some_exit = self._block.label

            # Merge
            self._set_block(merge_bb)
            result = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.OPTION)))
            self._emit(Phi(dest=result, incoming=[(none_exit, none_val), (some_exit, some_val)]))
            return result

        if kind == TypeKind.STRUCT:
            # v5.39.4 Js.4.D.2 — recurse into nested struct field via shared
            # helper. Pre-fix this fell into the raw-jval fallback below,
            # which returned the JsonValue enum where the struct shape was
            # expected — silent shape mismatch on the consumer side.
            # Trusts that the JsonValue is an Object variant (consistent
            # with the no-tag-check behavior of the primitive branches).
            struct_name = target_type.type_info.name if target_type.type_info else ""
            if struct_name and struct_name in self._module.structs:
                return self._emit_decode_struct_inline(jval, struct_name)

        if kind == TypeKind.LIST:
            # v5.39.5 Js.4.D.3 — symmetric pair to v5.39.4 Js.4.D.1's LIST
            # encode branch. Pre-fix this fell into the raw-jval fallback
            # below, returning the JsonValue::Array enum where a List<X>
            # was expected — silent shape mismatch surfacing as wrong list
            # contents (or downstream segfault on element access).
            inner_type = (
                MIRType(target_type.type_info.args[0])
                if target_type.type_info and target_type.type_info.args
                else mir_unknown()
            )
            return self._emit_list_decode_body(jval, inner_type)

        if kind == TypeKind.MAP:
            # v5.39.6 Js.4.E.2 — symmetric pair to v5.39.6 Js.4.E.1's MAP
            # encode branch. Pre-fix this fell into the raw-jval fallback
            # below, returning the JsonValue::Object enum where a
            # Map<String, V> was expected — silent shape mismatch on the
            # consumer side. JSON object keys must be strings (RFC 8259);
            # non-String K is rejected at compile time per the v5.39.6
            # PLAN invariant decision.
            args = target_type.type_info.args if target_type.type_info else []
            key_kind = args[0].kind if args else TypeKind.UNKNOWN
            if key_kind != TypeKind.STRING:
                raise RuntimeError(
                    f"from_json: Map<K, V> requires K = String (got {key_kind.name})"
                )
            val_type = MIRType(args[1]) if len(args) > 1 else mir_unknown()
            return self._emit_map_decode_body(jval, val_type)

        # Fallback: just return the raw value
        return jval

    def _emit_list_decode_body(self, arr_jval: Value, inner_type: MIRType) -> Value:
        """Emit MIR converting JsonValue::Array(List<JsonValue>) to List<inner>.

        v5.39.5 Js.4.D.3 — sibling to v5.39.4's _emit_list_json_body shape
        but on the decode side: extract the inner List<JsonValue> from the
        Array variant, iterate, recursively decode each element through
        _decode_json_field, accumulate into a typed List<inner>.

        Loop shape (mutable-Phi pattern; same as encode-side, with in-place
        ListPush mirroring _lower_method_call's .push() pattern at
        lower.py:3298 — the dest reuses acc_phi_dest's name so the phi
        alloca acts as the single mutable list slot across iterations):

            entry: inner_arr = EnumPayload(arr_jval, "Array", 0)
                   acc_init = ListInit([])
                   len_v = len(inner_arr); zero=0; jump header
            header: counter = phi(zero, new_counter)
                    acc     = phi(acc_init, new_acc)   ; new_acc.name == acc.name
                    cmp = counter < len_v
                    branch cmp -> body, exit
            body:   elem_jv = inner_arr[counter]
                    decoded = _decode_json_field(elem_jv, inner_type)
                    new_acc = ListPush(acc, decoded)   ; in-place via name reuse
                    new_counter = counter + 1
                    jump header
            exit:   return acc
        """
        assert self._block is not None
        entry_label = self._block.label
        list_ty = MIRType(TypeInfo(kind=TypeKind.LIST, args=[inner_type.type_info]))

        # Extract inner List<JsonValue> from the Array variant
        inner_arr = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.LIST)))
        self._emit(EnumPayload(dest=inner_arr, enum_val=arr_jval, variant="Array", payload_idx=0))

        # Initialize accumulator: empty List<inner>
        acc_init = self._make_value(ty=list_ty)
        self._emit(ListInit(dest=acc_init, elem_type=inner_type, elements=[]))

        # len(inner_arr)
        len_val = self._make_value(ty=mir_int())
        self._emit(Call(dest=len_val, fn_name="len", args=[inner_arr]))

        zero = self._make_value(ty=mir_int())
        self._emit(Const(dest=zero, ty=mir_int(), value=0))

        header_bb = self._new_block(self._fresh_block("list_dec_header"))
        body_bb = self._new_block(self._fresh_block("list_dec_body"))
        exit_bb = self._new_block(self._fresh_block("list_dec_exit"))

        self._emit(Jump(target=header_bb.label))

        # Header: phi nodes for counter + accumulator (incoming filled later)
        self._set_block(header_bb)
        counter_phi_dest = self._make_value(ty=mir_int())
        counter_phi = Phi(dest=counter_phi_dest, incoming=[])
        self._emit(counter_phi)
        acc_phi_dest = self._make_value(ty=list_ty)
        acc_phi = Phi(dest=acc_phi_dest, incoming=[])
        self._emit(acc_phi)

        cmp = self._make_value(ty=mir_bool())
        self._emit(BinOp(dest=cmp, op=BinOpKind.LT, lhs=counter_phi_dest, rhs=len_val))
        self._emit(Branch(cond=cmp, true_block=body_bb.label, false_block=exit_bb.label))

        # Body: extract elem JsonValue, recurse-decode, push into accumulator
        self._set_block(body_bb)
        elem_jval = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.ENUM, name="JsonValue")))
        self._emit(IndexGet(dest=elem_jval, obj=inner_arr, index=counter_phi_dest))

        decoded = self._decode_json_field(elem_jval, inner_type)

        # In-place ListPush: reuse acc_phi_dest's SSA name as the dest so the
        # emitter's phi alloca is the single mutable list slot. Mirrors
        # _lower_method_call's .push() pattern at lower.py:3298.
        new_acc = Value(name=acc_phi_dest.name, ty=list_ty)
        self._emit(ListPush(dest=new_acc, list_val=acc_phi_dest, element=decoded))
        self._emit(Move(value=decoded))

        # counter++
        one = self._make_value(ty=mir_int())
        self._emit(Const(dest=one, ty=mir_int(), value=1))
        new_counter = self._make_value(ty=mir_int())
        self._emit(BinOp(dest=new_counter, op=BinOpKind.ADD, lhs=counter_phi_dest, rhs=one))

        assert self._block is not None
        body_exit_label = self._block.label
        self._emit(Jump(target=header_bb.label))

        # Patch the header phis now that body's exit label is known
        counter_phi.incoming = [(entry_label, zero), (body_exit_label, new_counter)]
        acc_phi.incoming = [(entry_label, acc_init), (body_exit_label, new_acc)]

        # Exit
        self._set_block(exit_bb)
        return acc_phi_dest

    def _emit_map_decode_body(self, obj_jval: Value, val_type: MIRType) -> Value:
        """Emit MIR converting JsonValue::Object(Map<String, JsonValue>) to Map<String, V>.

        v5.39.6 Js.4.E.2 — sibling to v5.39.6 Js.4.E.1's _emit_map_json_body
        on the decode side: extract the inner Map<String, JsonValue> from
        the Object variant, iterate via __mn_map_keys, recursively decode
        each value through _decode_json_field, IndexSet into a typed
        Map<String, V> accumulator.

        Unlike LIST decode, MAP doesn't need an SSA-name-reuse trick — the
        Mapanare Map value is a single ptr to a heap MnMap (see
        emit_llvm_text._rty: MAP → PTR), and __mn_map_set mutates the
        bucket array in place without changing the outer pointer. So the
        accumulator is initialized once and IndexSet'd inside the loop;
        no phi needed for it. The counter still uses a phi.

        Loop shape:
            entry: inner_map = EnumPayload(obj_jval, "Object", 0)
                   acc       = MapInit(empty)
                   keys      = __mn_map_keys(inner_map)
                   len_v     = len(keys); zero=0; jump header
            header: counter = phi(zero, new_counter)
                    cmp = counter < len_v
                    branch cmp -> body, exit
            body:   key      = keys[counter]
                    elem_jv  = inner_map[key]      ; IndexGet on Map
                    decoded  = _decode_json_field(elem_jv, val_type)
                    acc[key] = decoded             ; IndexSet (in-place)
                    new_counter = counter + 1; jump header
            exit:   return acc

        Trusts that the JsonValue is an Object variant (consistent with
        the no-tag-check behavior of the primitive branches and with the
        v5.39.4 STRUCT decode and v5.39.5 LIST decode helpers).
        """
        assert self._block is not None
        entry_label = self._block.label

        map_ty = MIRType(
            TypeInfo(
                kind=TypeKind.MAP,
                args=[TypeInfo(kind=TypeKind.STRING), val_type.type_info],
            )
        )
        # Inner Map<String, JsonValue> from the Object variant
        jv_ti = TypeInfo(kind=TypeKind.ENUM, name="JsonValue")
        inner_map_ty = MIRType(
            TypeInfo(kind=TypeKind.MAP, args=[TypeInfo(kind=TypeKind.STRING), jv_ti])
        )
        inner_map = self._make_value(ty=inner_map_ty)
        self._emit(EnumPayload(dest=inner_map, enum_val=obj_jval, variant="Object", payload_idx=0))

        # Initialize accumulator: empty Map<String, V>. v5.39.2 Js.4.B.2
        # _do_map_init derives ksz/vsz/ktag from key_type/val_type, so the
        # bucket layout is correct for String-key + V-value inserts.
        acc = self._make_value(ty=map_ty)
        self._emit(
            MapInit(
                dest=acc,
                key_type=mir_string(),
                val_type=val_type,
                pairs=[],
            )
        )

        # keys = __mn_map_keys(inner_map)
        keys_ty = MIRType(TypeInfo(kind=TypeKind.LIST, args=[TypeInfo(kind=TypeKind.STRING)]))
        keys_val = self._make_value(ty=keys_ty)
        self._emit(Call(dest=keys_val, fn_name="__mn_map_keys", args=[inner_map]))

        # len_v = len(keys)
        len_val = self._make_value(ty=mir_int())
        self._emit(Call(dest=len_val, fn_name="len", args=[keys_val]))

        zero = self._make_value(ty=mir_int())
        self._emit(Const(dest=zero, ty=mir_int(), value=0))

        header_bb = self._new_block(self._fresh_block("map_dec_header"))
        body_bb = self._new_block(self._fresh_block("map_dec_body"))
        exit_bb = self._new_block(self._fresh_block("map_dec_exit"))

        self._emit(Jump(target=header_bb.label))

        # Header: counter phi only (acc is invariant across iterations).
        self._set_block(header_bb)
        counter_phi_dest = self._make_value(ty=mir_int())
        counter_phi = Phi(dest=counter_phi_dest, incoming=[])
        self._emit(counter_phi)

        cmp = self._make_value(ty=mir_bool())
        self._emit(BinOp(dest=cmp, op=BinOpKind.LT, lhs=counter_phi_dest, rhs=len_val))
        self._emit(Branch(cond=cmp, true_block=body_bb.label, false_block=exit_bb.label))

        # Body: key = keys[counter]; elem_jv = inner_map[key]; decode; insert
        self._set_block(body_bb)
        key = self._make_value(ty=mir_string())
        self._emit(IndexGet(dest=key, obj=keys_val, index=counter_phi_dest))

        elem_jval = self._make_value(ty=MIRType(jv_ti))
        self._emit(IndexGet(dest=elem_jval, obj=inner_map, index=key))

        decoded = self._decode_json_field(elem_jval, val_type)

        self._emit(IndexSet(obj=acc, index=key, val=decoded))

        # counter++
        one = self._make_value(ty=mir_int())
        self._emit(Const(dest=one, ty=mir_int(), value=1))
        new_counter = self._make_value(ty=mir_int())
        self._emit(BinOp(dest=new_counter, op=BinOpKind.ADD, lhs=counter_phi_dest, rhs=one))

        assert self._block is not None
        body_exit_label = self._block.label
        self._emit(Jump(target=header_bb.label))

        # Patch the header phi now that body's exit label is known
        counter_phi.incoming = [(entry_label, zero), (body_exit_label, new_counter)]

        # Exit
        self._set_block(exit_bb)
        return acc

    def _lower_method_call(self, expr: MethodCallExpr) -> Value:
        """Lower a method call: `obj.method(args)`."""
        obj = self._lower_expr(expr.object)
        args = [self._lower_expr(a) for a in expr.args]

        # Check if this is a stream operation
        stream_op = _STREAM_OP_MAP.get(expr.method)
        if stream_op is not None:
            dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.STREAM)))
            # For collect, the result is a list, not a stream
            if stream_op == StreamOpKind.COLLECT:
                dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.LIST)))
            # Resolve lambda function name from args if the first arg is a lambda
            fn_name = ""
            if expr.args and isinstance(expr.args[0], LambdaExpr):
                # The lambda was lowered and its function name is stored
                fn_name = args[0].name if args else ""
                # Look up the actual MIR function name from lambda vars
                for var_name, lambda_fn in self._lambda_vars.items():
                    if var_name == fn_name.lstrip("%"):
                        fn_name = lambda_fn
                        break
            self._emit(
                StreamOp(dest=dest, op_kind=stream_op, source=obj, args=args, fn_name=fn_name)
            )
            return dest

        # Check if this is a signal .value access
        if expr.method == "value" and not args:
            dest = self._make_value()
            self._emit(SignalGet(dest=dest, signal=obj))
            return dest

        # Tensor reduction methods (v4.45.0)
        _TENSOR_REDUCTIONS_SCALAR = {"sum", "mean", "max", "min"}
        _TENSOR_REDUCTIONS_IDX = {"argmax", "argmin"}
        if obj.ty.kind == TypeKind.TENSOR and expr.method in (
            _TENSOR_REDUCTIONS_SCALAR | _TENSOR_REDUCTIONS_IDX
        ):
            elem_ti = (
                obj.ty.type_info.args[0] if obj.ty.type_info.args else TypeInfo(kind=TypeKind.FLOAT)
            )
            ty_suffix = "i64" if elem_ti.kind == TypeKind.INT else "f64"
            fn_name = f"__mn_tensor_{expr.method}_{ty_suffix}"
            if expr.method in _TENSOR_REDUCTIONS_SCALAR:
                if elem_ti.kind == TypeKind.INT:
                    dest = self._make_value(ty=mir_int())
                else:
                    dest = self._make_value(ty=mir_float())
            else:
                dest = self._make_value(ty=mir_int())
            self._emit(Call(dest=dest, fn_name=fn_name, args=[obj]))
            return dest

        # List .push() — emit ListPush instruction and update the variable binding
        if expr.method == "push" and args and obj.ty.kind in (TypeKind.LIST, TypeKind.UNKNOWN):
            # Use the same value as the source list for in-place mutation
            # This avoids SSA aliasing issues in C where the dest might be
            # referenced before the push branch executes
            dest = Value(name=obj.name, ty=obj.ty)
            self._emit(ListPush(dest=dest, list_val=obj, element=args[0]))
            # v5.4.4 — list.push copies the element into the list buffer;
            # the list owns it now. Drop glue must skip the caller's slot.
            self._emit(Move(value=args[0]))
            # Update the variable so subsequent reads see the modified list
            if isinstance(expr.object, Identifier):
                self._update_var(expr.object.name, dest)
            elif isinstance(expr.object, FieldAccessExpr):
                # s.field.push(x) → need to write updated list back to struct field
                self._emit(
                    FieldSet(
                        obj=self._lower_expr(expr.object.object),
                        field_name=expr.object.field_name,
                        val=dest,
                    )
                )
            return dest

        # General method call → Call with self as first arg
        # Infer return type for known string methods so LLVM codegen uses correct types
        _str_method_ret: dict[str, TypeKind] = {
            "char_at": TypeKind.STRING,
            "byte_at": TypeKind.INT,
            "substr": TypeKind.STRING,
            "starts_with": TypeKind.BOOL,
            "ends_with": TypeKind.BOOL,
            "find": TypeKind.INT,
            "contains": TypeKind.BOOL,
            "trim": TypeKind.STRING,
            "trim_start": TypeKind.STRING,
            "trim_end": TypeKind.STRING,
            "to_upper": TypeKind.STRING,
            "to_lower": TypeKind.STRING,
            "replace": TypeKind.STRING,
            "split": TypeKind.LIST,
        }
        ret_kind = _str_method_ret.get(expr.method)
        if ret_kind is not None and obj.ty.kind == TypeKind.STRING:
            dest = self._make_value(ty=MIRType(TypeInfo(kind=ret_kind)))
        else:
            dest = self._make_value()

        # Resolve impl method: if obj has a struct/enum type, check _impl_methods
        call_name = expr.method
        obj_type_name = obj.ty.type_info.name if obj.ty.type_info.name else ""
        if obj_type_name:
            mangled = self._impl_methods.get((obj_type_name, expr.method))
            if mangled:
                call_name = mangled
                # Use registered return type for the mangled method
                impl_ret = self._fn_return_types.get(mangled)
                if impl_ret is not None:
                    dest = self._make_value(ty=impl_ret)

        self._emit(Call(dest=dest, fn_name=call_name, args=[obj] + args))
        return dest

    def _infer_payload_type(
        self, subject_ty: MIRType, variant_name: str, payload_idx: int
    ) -> MIRType:
        """Infer the type of a match arm payload binding from the subject's type."""
        kind = subject_ty.kind
        args = subject_ty.type_info.args

        # Result<T, E>: Ok → T, Err → E
        if kind == TypeKind.RESULT:
            if variant_name == "Ok" and len(args) >= 1:
                return MIRType(args[0])
            if variant_name == "Err" and len(args) >= 2:
                return MIRType(args[1])

        # Option<T>: Some → T
        if kind == TypeKind.OPTION:
            if variant_name == "Some" and len(args) >= 1:
                return MIRType(args[0])

        # User-defined enum: look up variant payload types
        enum_name = subject_ty.type_info.name
        if enum_name:
            variants = self._module.enums.get(enum_name)
            if variants:
                for vname, payload_types in variants:
                    if vname == variant_name and payload_idx < len(payload_types):
                        return payload_types[payload_idx]

        # STRUCT kind that might actually be an enum (lowerer tags user enums as STRUCT)
        if kind == TypeKind.STRUCT and enum_name:
            variants = self._module.enums.get(enum_name)
            if variants:
                for vname, payload_types in variants:
                    if vname == variant_name and payload_idx < len(payload_types):
                        return payload_types[payload_idx]

        # Check imported enum definitions (cross-module types)
        if enum_name and self._imported_enum_defs:
            variants = self._imported_enum_defs.get(enum_name)
            if not variants:
                for ename, evariants in self._imported_enum_defs.items():
                    if ename.endswith("__" + enum_name):
                        variants = evariants
                        break
            if variants:
                for vname, payload_types in variants:
                    if vname == variant_name and payload_idx < len(payload_types):
                        return payload_types[payload_idx]

        return mir_unknown()

    def _infer_iterable_elem_type(self, iter_ty: MIRType) -> MIRType:
        """Infer the element type from an iterable's MIR type."""
        args = iter_ty.type_info.args
        if iter_ty.kind == TypeKind.LIST and args:
            return MIRType(args[0])
        if iter_ty.kind == TypeKind.MAP and args:
            return MIRType(args[0])  # key type for map iteration
        if iter_ty.kind == TypeKind.STRING:
            return mir_string()  # iterating over chars → strings
        if iter_ty.kind == TypeKind.RANGE:
            return mir_int()  # range produces integers
        return mir_unknown()

    def _infer_field_type(self, obj_ty: MIRType, field_name: str) -> MIRType:
        """Look up the MIR type of a struct field from the module's struct registry."""
        struct_name = obj_ty.type_info.name
        if struct_name and self._module:
            fields = self._module.structs.get(struct_name)
            if fields:
                for fname, fty in fields:
                    if fname == field_name:
                        return fty
        # Check imported struct definitions (cross-module types)
        if struct_name and self._imported_struct_defs:
            fields = self._imported_struct_defs.get(struct_name)
            if not fields:
                # Try suffix match (e.g. "Program" → "parser__Program")
                for sname, sfields in self._imported_struct_defs.items():
                    if sname.endswith("__" + struct_name):
                        fields = sfields
                        break
            if fields:
                for fname, fty in fields:
                    if fname == field_name:
                        return fty
        return mir_unknown()

    def _lower_field_access(self, expr: FieldAccessExpr) -> Value:
        """Lower field access: `obj.field`."""
        obj = self._lower_expr(expr.object)

        # Check for signal .value — only if the object is actually a signal type
        if expr.field_name == "value" and obj.ty.kind == TypeKind.SIGNAL:
            dest = self._make_value()
            self._emit(SignalGet(dest=dest, signal=obj))
            return dest

        # Infer field type from struct definition
        field_ty = self._infer_field_type(obj.ty, expr.field_name)
        dest = self._make_value(ty=field_ty)
        self._emit(FieldGet(dest=dest, obj=obj, field_name=expr.field_name))
        return dest

    def _lower_namespace_access(self, expr: NamespaceAccessExpr) -> Value:
        """Lower namespace access: `Enum::Variant` or `Module::name`."""
        ns = expr.namespace
        member = expr.member
        # Check if this is a namespace-qualified enum variant (no payload)
        if ns in self._enum_variants and member in self._enum_variants[ns]:
            enum_ty = MIRType(TypeInfo(kind=TypeKind.ENUM, name=ns))
            dest = self._make_value(ty=enum_ty)
            self._emit(EnumInit(dest=dest, enum_type=enum_ty, variant=member, payload=[]))
            return dest
        # General namespace access — try to look up return type
        fn_name = f"{ns}_{member}"
        ret_ty = self._fn_return_types.get(
            fn_name, self._fn_return_types.get(member, mir_unknown())
        )
        dest = self._make_value(ty=ret_ty)
        self._emit(Call(dest=dest, fn_name=fn_name, args=[]))
        return dest

    def _lower_index(self, expr: IndexExpr) -> Value:
        """Lower index access: `arr[i]`, `tensor[i, j]`, or `tensor[0..2, :]` (v4.43–v4.45)."""
        from mapanare.ast_nodes import IndexItem

        obj = self._lower_expr(expr.object)
        obj_kind = obj.ty.kind

        # Check for slicing (v4.45.0) — any range or wildcard item
        has_slice = any(
            isinstance(it, IndexItem) and it.kind in ("range", "wildcard") for it in expr.indices
        )
        if obj_kind == TypeKind.TENSOR and has_slice:
            return self._lower_tensor_slice(obj, expr.indices)

        # Scalar indices — extract Expr from IndexItem
        scalar_exprs: list[Value] = []
        for it in expr.indices:
            if isinstance(it, IndexItem) and it.kind == "scalar" and it.expr:
                scalar_exprs.append(self._lower_expr(it.expr))
            elif isinstance(it, Expr):
                scalar_exprs.append(self._lower_expr(it))
        indices = scalar_exprs

        # Tensor: emit Call to __mn_tensor_get_*_nd (v4.43.0)
        if obj_kind == TypeKind.TENSOR:
            return self._lower_tensor_get(obj, indices)

        # List/Map/String: single-index via IndexGet
        index = indices[0] if indices else self._make_value()
        elem_ty = mir_unknown()
        if obj_kind == TypeKind.LIST and obj.ty.type_info.args:
            elem_ty = MIRType(obj.ty.type_info.args[0])
        elif obj_kind == TypeKind.MAP and len(obj.ty.type_info.args) >= 2:
            elem_ty = MIRType(obj.ty.type_info.args[1])
        elif obj_kind == TypeKind.STRING:
            elem_ty = MIRType(type_info=TypeInfo(name="String", kind=TypeKind.STRING))
        dest = self._make_value(ty=elem_ty)
        self._emit(IndexGet(dest=dest, obj=obj, index=index))
        return dest

    def _lower_tensor_get(self, obj: Value, indices: list[Value]) -> Value:
        """Lower tensor[i, j, ...] to __mn_tensor_get_*_nd call (v4.43.0)."""
        elem_ti = (
            obj.ty.type_info.args[0] if obj.ty.type_info.args else TypeInfo(kind=TypeKind.FLOAT)
        )
        elem_ty = MIRType(elem_ti)
        rank = len(indices)

        # Determine which runtime function to call
        if elem_ti.kind == TypeKind.INT:
            fn_name = "__mn_tensor_get_i64_nd"
        else:
            fn_name = "__mn_tensor_get_f64_nd"

        # Build index array Value — emit as consecutive stores
        dest = self._make_value(ty=elem_ty, prefix="tget")
        rank_val = self._make_value(ty=mir_int(), prefix="trank")
        self._emit(Const(dest=rank_val, ty=mir_int(), value=str(rank)))
        self._emit(Call(dest=dest, fn_name=fn_name, args=[obj, rank_val] + indices))
        return dest

    def _lower_tensor_set(self, obj: Value, indices: list[Value], val: Value) -> None:
        """Lower tensor[i, j] = val to __mn_tensor_set_*_nd call (v4.43.0)."""
        elem_ti = (
            obj.ty.type_info.args[0] if obj.ty.type_info.args else TypeInfo(kind=TypeKind.FLOAT)
        )
        rank = len(indices)

        if elem_ti.kind == TypeKind.INT:
            fn_name = "__mn_tensor_set_i64_nd"
        else:
            fn_name = "__mn_tensor_set_f64_nd"

        rank_val = self._make_value(ty=mir_int(), prefix="trank")
        self._emit(Const(dest=rank_val, ty=mir_int(), value=str(rank)))
        void_dest = self._make_value(ty=mir_void(), prefix="tset")
        self._emit(Call(dest=void_dest, fn_name=fn_name, args=[obj, rank_val] + indices + [val]))

    def _lower_tensor_slice(self, obj: Value, items: list[Any]) -> Value:
        """Lower tensor[0..2, :] to __mn_tensor_slice call (v4.45.0)."""
        from mapanare.ast_nodes import IndexItem

        rank = len(items)
        # Build starts and ends arrays
        start_vals: list[Value] = []
        end_vals: list[Value] = []

        for d, it in enumerate(items):
            if isinstance(it, IndexItem):
                if it.kind == "range":
                    start_vals.append(
                        self._lower_expr(it.start) if it.start else self._const_int(0)
                    )
                    end_vals.append(self._lower_expr(it.end) if it.end else self._const_int(0))
                elif it.kind == "wildcard":
                    start_vals.append(self._const_int(0))
                    # End = shape[d] — use tensor_shape_dim runtime call
                    dim_val = self._const_int(d)
                    shape_dest = self._make_value(ty=mir_int(), prefix="sdim")
                    self._emit(
                        Call(dest=shape_dest, fn_name="tensor_shape_dim", args=[obj, dim_val])
                    )
                    end_vals.append(shape_dest)
                else:  # scalar in slice context — treat as start..start+1
                    sv = self._lower_expr(it.expr) if it.expr else self._const_int(0)
                    start_vals.append(sv)
                    one = self._const_int(1)
                    end_dest = self._make_value(ty=mir_int(), prefix="send")
                    self._emit(BinOp(dest=end_dest, op=BinOpKind.ADD, lhs=sv, rhs=one))
                    end_vals.append(end_dest)

        # Build result tensor type
        elem_ti = (
            obj.ty.type_info.args[0] if obj.ty.type_info.args else TypeInfo(kind=TypeKind.FLOAT)
        )
        result_ty = MIRType(TypeInfo(kind=TypeKind.TENSOR, args=[elem_ti]))
        dest = self._make_value(ty=result_ty, prefix="tslice")
        rank_val = self._const_int(rank)
        self._emit(
            Call(
                dest=dest,
                fn_name="__mn_tensor_slice",
                args=[obj] + start_vals + end_vals + [rank_val],
            )
        )
        return dest

    def _const_int(self, val: int) -> Value:
        """Emit a constant integer value."""
        dest = self._make_value(ty=mir_int(), prefix="ci")
        self._emit(Const(dest=dest, ty=mir_int(), value=str(val)))
        return dest

    def _lower_tensor_binop(self, op: str, lhs: Value, rhs: Value) -> Value:
        """Lower tensor binary op to broadcast runtime call (v4.44.0)."""
        _OP_SUFFIX = {"+": "add", "-": "sub", "*": "mul", "/": "div"}
        op_suffix = _OP_SUFFIX.get(op, "add")

        # Determine element type suffix
        tensor_val = lhs if lhs.ty.kind == TypeKind.TENSOR else rhs
        elem_ti = (
            tensor_val.ty.type_info.args[0]
            if tensor_val.ty.type_info.args
            else TypeInfo(kind=TypeKind.FLOAT)
        )
        ty_suffix = "i64" if elem_ti.kind == TypeKind.INT else "f64"

        # Determine if tensor+tensor or tensor+scalar
        both_tensor = lhs.ty.kind == TypeKind.TENSOR and rhs.ty.kind == TypeKind.TENSOR
        if both_tensor:
            fn_name = f"__mn_tensor_{op_suffix}_broadcast_{ty_suffix}"
            dest = self._make_value(ty=tensor_val.ty, prefix="tbop")
            self._emit(Call(dest=dest, fn_name=fn_name, args=[lhs, rhs]))
        else:
            # tensor + scalar or scalar + tensor
            if lhs.ty.kind == TypeKind.TENSOR:
                # tensor op scalar — straightforward
                fn_name = f"__mn_tensor_{op_suffix}_scalar_{ty_suffix}"
                dest = self._make_value(ty=lhs.ty, prefix="tsop")
                self._emit(Call(dest=dest, fn_name=fn_name, args=[lhs, rhs]))
            else:
                # scalar op tensor
                if op in ("+", "*"):
                    # Commutative — swap safely: tensor op scalar
                    fn_name = f"__mn_tensor_{op_suffix}_scalar_{ty_suffix}"
                    dest = self._make_value(ty=rhs.ty, prefix="tsop")
                    self._emit(Call(dest=dest, fn_name=fn_name, args=[rhs, lhs]))
                else:
                    # Non-commutative (- /) — use reverse scalar fn (v4.47.0 fix)
                    fn_name = f"__mn_tensor_r{op_suffix}_scalar_{ty_suffix}"
                    dest = self._make_value(ty=rhs.ty, prefix="tsop")
                    self._emit(Call(dest=dest, fn_name=fn_name, args=[lhs, rhs]))
        return dest

    def _lower_pipe(self, expr: PipeExpr) -> Value:
        """Lower pipe expression: `a |> f`."""
        arg = self._lower_expr(expr.left)
        if isinstance(expr.right, Identifier):
            dest = self._make_value()
            self._emit(Call(dest=dest, fn_name=expr.right.name, args=[arg]))
            return dest
        if isinstance(expr.right, CallExpr) and isinstance(expr.right.callee, Identifier):
            extra_args = [self._lower_expr(a) for a in expr.right.args]
            dest = self._make_value()
            self._emit(Call(dest=dest, fn_name=expr.right.callee.name, args=[arg] + extra_args))
            return dest
        fn_val = self._lower_expr(expr.right)
        dest = self._make_value()
        self._emit(Call(dest=dest, fn_name=fn_val.name, args=[arg]))
        return dest

    def _lower_range(self, expr: RangeExpr) -> Value:
        """Lower a range expression."""
        start = self._lower_expr(expr.start)
        end = self._lower_expr(expr.end)
        dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.RANGE)))
        fn_name = "__mn_range_inclusive" if expr.inclusive else "__mn_range"
        self._emit(Call(dest=dest, fn_name=fn_name, args=[start, end]))
        return dest

    def _lower_lambda(self, expr: LambdaExpr) -> Value:
        """Lower a lambda expression.

        Creates an anonymous function in the module and returns a reference.
        If the lambda body references variables from the enclosing scope,
        a closure is created with an environment struct containing captured values.
        """
        lambda_name = self._fresh_tmp("lambda")
        from mapanare.ast_nodes import Block as _Block
        from mapanare.ast_nodes import FnDef as _FnDef
        from mapanare.ast_nodes import Param as _Param

        body_block: Block
        if isinstance(expr.body, Block):
            body_block = expr.body
        else:
            body_block = _Block(stmts=[ReturnStmt(value=expr.body)])

        # Analyze free variables in the lambda body
        param_names = {p.name for p in expr.params}
        free_vars = self._analyze_free_vars(expr.body, param_names)

        # Collect captured values from current scope
        captures: list[tuple[str, Value]] = []
        for var_name in free_vars:
            var_val = self._lookup_var(var_name)
            if var_val is not None:
                captures.append((var_name, var_val))

        if not captures:
            # v4.103.0: no-capture lambdas used to be lowered as a
            # plain function-pointer Const. That was fine when the
            # lambda was only ever invoked directly (the call site
            # looked up the function name in `_lambda_vars`), but it
            # blocked docket #5: passing `double` to a parameter
            # `f: fn(Int) -> Int`. Inside the callee, `f` has type
            # FN in MIR — which must be a `{ptr, ptr}` closure struct
            # for the indirect-call (ClosureCall) path to work. The
            # no-capture lambda now always produces a ClosureCreate
            # with an empty captures list; the emitter handles that
            # case by emitting `{@fn_ptr, null}` inline. Direct calls
            # still go through `_lambda_vars`, so nothing regresses.
            env_param = _Param(name="__env_ptr")
            modified_params = [env_param] + list(expr.params)
            fn_def = _FnDef(
                name=lambda_name,
                params=modified_params,
                body=body_block,
            )
            self._pending_captures = []
            self._lower_fn(fn_def)
            dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.FN)))
            self._emit(
                ClosureCreate(
                    dest=dest,
                    fn_name=lambda_name,
                    captures=[],
                    capture_types=[],
                )
            )
            return dest

        # Has captures — create a closure
        # Add __env_ptr as first parameter
        env_param = _Param(name="__env_ptr")
        modified_params = [env_param] + list(expr.params)

        fn_def = _FnDef(
            name=lambda_name,
            params=modified_params,
            body=body_block,
        )

        # Set pending captures so _lower_fn injects EnvLoad instructions
        capture_info = [(name, val.ty) for name, val in captures]
        self._pending_captures = capture_info
        self._lower_fn(fn_def)

        # Emit ClosureCreate instruction
        captured_values = [val for _, val in captures]
        capture_types = [val.ty for _, val in captures]
        dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.FN)))
        self._emit(
            ClosureCreate(
                dest=dest,
                fn_name=lambda_name,
                captures=captured_values,
                capture_types=capture_types,
            )
        )
        return dest

    def _lower_comprehension(self, expr: Comprehension) -> Value:
        """Lower a list/map comprehension by synthesizing the equivalent
        let + nested-for + push (or insert) AST and recursing through the
        existing statement lowerers (v5.15.0 Te.2.B/C).

        For range iterables (``for x in 0..n``) we emit a direct ForLoop
        which lowers to the regular range-iter calls. For non-range
        iterables (lists, etc.) we synthesize an index-based loop —
        ``for __i in 0..len(xs) { let x = xs[__i]; ... }`` — because
        ``for x in some_list`` is not yet supported by the generic
        ForLoop lowering (the runtime ``__iter_*`` shims only know about
        ranges). The result IR is identical to a hand-written loop in
        the same style modulo SSA naming.
        """
        span: Span = expr.span if expr.span is not None else Span()
        comp_n = self._tmp_counter
        self._tmp_counter += 1
        result_name = f"__mn_comp_{comp_n}"

        if expr.kind == "list":
            init: Expr = ListLiteral(elements=[], span=span)
            inner_call: Expr = MethodCallExpr(
                object=Identifier(name=result_name, span=span),
                method="push",
                args=[expr.element if expr.element is not None else Expr()],
                span=span,
            )
        else:
            from mapanare.ast_nodes import AssignExpr as _AssignExpr
            from mapanare.ast_nodes import IndexItem as _IndexItem

            init = MapLiteral(entries=[], span=span)
            # Map insertion uses ``m[k] = v`` rather than a method call —
            # ``insert`` isn't a runtime export; ``IndexSet`` handles
            # both list[i] and map[k] writes.
            inner_call = _AssignExpr(
                target=IndexExpr(
                    object=Identifier(name=result_name, span=span),
                    indices=[
                        _IndexItem(
                            kind="scalar",
                            expr=expr.key if expr.key is not None else Expr(),
                            span=span,
                        )
                    ],
                    span=span,
                ),
                op="=",
                value=expr.value if expr.value is not None else Expr(),
                span=span,
            )

        # Bind the result accumulator in the current scope. Forward any
        # element-type hint set by the surrounding `_lower_let` so the
        # internal list's elem_type matches the user-declared
        # ``List<T>`` / ``Map<K, V>``.
        type_hint = getattr(self, "_comp_type_hint", None)
        let_stmt = LetBinding(
            name=result_name,
            mutable=True,
            type_annotation=type_hint,
            value=init,
            span=span,
        )
        # Clear the hint before recursing so nested comprehensions inside
        # the element expression don't accidentally inherit it.
        self._comp_type_hint = None
        self._lower_let(let_stmt)

        # Build the loop body innermost-out, applying filters then for-clauses
        # in reverse source order.
        body: Block = Block(stmts=[ExprStmt(expr=inner_call, span=span)], span=span)
        for clause in reversed(expr.clauses):
            for cond in reversed(clause.conditions):
                body = Block(
                    stmts=[
                        ExprStmt(
                            expr=IfExpr(
                                condition=cond,
                                then_block=body,
                                else_block=None,
                                span=span,
                            ),
                            span=span,
                        )
                    ],
                    span=span,
                )
            body = self._wrap_comp_for(clause, body, span)

        for stmt in body.stmts:
            self._lower_stmt(stmt)

        result_val = self._lookup_var(result_name)
        if result_val is None:  # pragma: no cover — defensive
            return self._make_value(prefix="comp_missing")
        return result_val

    def _wrap_comp_for(self, clause: CompClause, inner: Block, span: Span) -> Block:
        """Wrap ``inner`` in a for-loop that iterates ``clause.iter`` and
        binds ``clause.target`` (v5.15.0 Te.2.B/C helper).

        Range iterables get a direct ForLoop; everything else gets the
        index-based pattern with a hoisted source binding so the iterable
        expression is evaluated exactly once per clause.
        """
        if isinstance(clause.iter, RangeExpr):
            return Block(
                stmts=[
                    ForLoop(
                        var_name=clause.target,
                        iterable=clause.iter,
                        body=inner,
                        span=span,
                    )
                ],
                span=span,
            )

        idx_n = self._tmp_counter
        self._tmp_counter += 1
        src_name = f"__mn_comp_src_{idx_n}"
        idx_name = f"__mn_comp_i_{idx_n}"

        let_src = LetBinding(
            name=src_name,
            mutable=False,
            type_annotation=None,
            value=clause.iter,
            span=span,
        )
        len_call = CallExpr(
            callee=Identifier(name="len", span=span),
            args=[Identifier(name=src_name, span=span)],
            span=span,
        )
        range_expr = RangeExpr(
            start=IntLiteral(value=0, span=span),
            end=len_call,
            inclusive=False,
            span=span,
        )
        from mapanare.ast_nodes import (
            IndexItem,
        )  # local import — already used elsewhere in this file

        get_elem = IndexExpr(
            object=Identifier(name=src_name, span=span),
            indices=[
                IndexItem(
                    kind="scalar",
                    expr=Identifier(name=idx_name, span=span),
                    span=span,
                )
            ],
            span=span,
        )
        bind_target = LetBinding(
            name=clause.target,
            mutable=False,
            type_annotation=None,
            value=get_elem,
            span=span,
        )
        new_body = Block(stmts=[bind_target] + list(inner.stmts), span=span)
        return Block(
            stmts=[
                let_src,
                ForLoop(
                    var_name=idx_name,
                    iterable=range_expr,
                    body=new_body,
                    span=span,
                ),
            ],
            span=span,
        )

    def _lower_spawn(self, expr: SpawnExpr) -> Value:
        """Lower spawn expression: `spawn Agent(args)`."""
        args = [self._lower_expr(a) for a in expr.args]
        agent_name = ""
        if isinstance(expr.callee, Identifier):
            agent_name = expr.callee.name

        agent_ty = MIRType(TypeInfo(kind=TypeKind.AGENT, name=agent_name))
        dest = self._make_value(ty=agent_ty)
        self._emit(AgentSpawn(dest=dest, agent_type=agent_ty, args=args))
        return dest

    def _lower_sync(self, expr: SyncExpr) -> Value:
        """Lower sync expression: `sync agent.output`."""
        if isinstance(expr.expr, FieldAccessExpr):
            agent = self._lower_expr(expr.expr.object)
            channel = expr.expr.field_name
            dest = self._make_value()
            self._emit(AgentSync(dest=dest, agent=agent, channel=channel))
            return dest
        # Generic sync
        val = self._lower_expr(expr.expr)
        dest = self._make_value()
        self._emit(AgentSync(dest=dest, agent=val, channel=""))
        return dest

    def _lower_send(self, expr: SendExpr) -> Value:
        """Lower send expression: `agent.input <- value`."""
        val = self._lower_expr(expr.value)
        if isinstance(expr.target, FieldAccessExpr):
            agent = self._lower_expr(expr.target.object)
            channel = expr.target.field_name
            self._emit(AgentSend(agent=agent, channel=channel, val=val))
        else:
            target = self._lower_expr(expr.target)
            self._emit(AgentSend(agent=target, channel="", val=val))
        dest = self._make_value(ty=mir_void())
        self._emit(Const(dest=dest, ty=mir_void(), value=None))
        return dest

    def _lower_error_prop(self, expr: ErrorPropExpr) -> Value:
        """Lower `expr?` — tag-check + branch (early return on Err/None).

        Generates:
            %val = <lower expr>
            %tag = enum_tag %val
            branch %tag == ok, ok_block, err_block
        err_block:
            ret %val  (propagate error)
        ok_block:
            %unwrapped = unwrap %val
        """
        val = self._lower_expr(expr.expr)

        tag = self._make_value(ty=mir_bool(), prefix="tag")
        self._emit(EnumTag(dest=tag, enum_val=val))

        ok_block = self._new_block(self._fresh_block("prop_ok"))
        err_block = self._new_block(self._fresh_block("prop_err"))

        self._emit(Branch(cond=tag, true_block=ok_block.label, false_block=err_block.label))

        # Error path: return the error
        self._set_block(err_block)
        self._emit(Return(val=val))

        # Ok path: unwrap — infer inner type from Option/Result
        self._set_block(ok_block)
        unwrap_ty = mir_unknown()
        val_args = val.ty.type_info.args
        if val.ty.kind == TypeKind.OPTION and val_args:
            unwrap_ty = MIRType(val_args[0])
        elif val.ty.kind == TypeKind.RESULT and val_args:
            unwrap_ty = MIRType(val_args[0])  # Ok type
        dest = self._make_value(ty=unwrap_ty)
        self._emit(Unwrap(dest=dest, val=val))
        return dest

    def _lower_list(self, expr: ListLiteral, expected_elem_type: MIRType | None = None) -> Value:
        """Lower a list literal."""
        elements = [self._lower_expr(e) for e in expr.elements]
        if elements:
            elem_type = elements[0].ty
        elif expected_elem_type is not None:
            elem_type = expected_elem_type
        else:
            elem_type = mir_unknown()
        list_ty = MIRType(TypeInfo(kind=TypeKind.LIST, args=[elem_type.type_info]))
        dest = self._make_value(ty=list_ty)
        self._emit(ListInit(dest=dest, elem_type=elem_type, elements=elements))
        return dest

    def _lower_tensor_literal(self, expr: TensorLiteral) -> Value:
        """Lower a tensor literal (v4.42.0).

        Emits a TensorInit instruction that the LLVM emitter translates to:
          1. Stack-allocate shape array
          2. Call __mn_tensor_alloc(rank, shape_ptr, elem_size)
          3. Call __mn_tensor_store_f64/i64 for each element
        """
        elements = [self._lower_expr(e) for e in expr.elements]

        # Determine element MIR type
        elem_name = getattr(expr.element_type, "name", "")
        if elem_name in ("Float", "float"):
            elem_type = mir_float()
        elif elem_name in ("Int", "int"):
            elem_type = mir_int()
        elif elem_name in ("Bool", "bool"):
            elem_type = mir_bool()
        else:
            elem_type = mir_float()  # default

        shape_tuple = tuple(expr.shape) if expr.shape else None
        tensor_ty = MIRType(
            TypeInfo(kind=TypeKind.TENSOR, args=[elem_type.type_info], tensor_shape=shape_tuple)
        )
        dest = self._make_value(ty=tensor_ty)
        self._emit(
            TensorInit(dest=dest, elem_type=elem_type, shape=list(expr.shape), elements=elements)
        )
        return dest

    def _patch_list_elem_types_for_struct(
        self, struct_name: str, field_names: list[str], args: list[Value]
    ) -> None:
        """Patch empty ListInit elem_types using struct field type info."""
        struct_def = self._module.structs.get(struct_name)
        if not struct_def:
            # Try imported struct defs
            struct_def = self._imported_struct_defs.get(struct_name)
        if not struct_def:
            return
        # struct_def is [(field_name, MIRType), ...]
        field_type_map = {fname: ftype for fname, ftype in struct_def}
        for i, (fname, arg_val) in enumerate(zip(field_names, args)):
            ftype = field_type_map.get(fname)
            if ftype and ftype.kind == TypeKind.LIST and ftype.type_info.args:
                self._patch_listinit_for_value(arg_val, ftype.type_info.args[0])

    def _patch_list_elem_types_for_enum(
        self, enum_name: str, variant_name: str, args: list[Value]
    ) -> None:
        """Patch empty ListInit elem_types using enum payload type info."""
        enum_def = self._module.enums.get(enum_name)
        if not enum_def:
            enum_def = self._imported_enum_defs.get(enum_name)
        if not enum_def:
            return
        # enum_def is [(variant_name, [MIRType, ...]), ...]
        for vname, payload_types in enum_def:
            if vname == variant_name:
                for i, (ptype, arg_val) in enumerate(zip(payload_types, args)):
                    if ptype.kind == TypeKind.LIST and ptype.type_info.args:
                        self._patch_listinit_for_value(arg_val, ptype.type_info.args[0])
                break

    def _patch_list_elem_types_for_fn_call(self, fn_name: str, args: list[Value]) -> None:
        """Patch empty ListInit elem_types using function parameter type info."""
        param_types = self._fn_param_types.get(fn_name)
        if not param_types:
            return
        for i, (ptype, arg_val) in enumerate(zip(param_types, args)):
            if ptype.kind == TypeKind.LIST and ptype.type_info.args:
                self._patch_listinit_for_value(arg_val, ptype.type_info.args[0])

    def _patch_arg_types_from_params(self, fn_name: str, args: list[Value]) -> None:
        """Patch argument types using function parameter type info.

        Fixes bare Option/Result args (no inner type) by copying the expected
        inner type from the function's parameter type declaration.
        Also patches struct constructor field types.
        """
        param_types = self._fn_param_types.get(fn_name)
        if not param_types:
            return
        for ptype, arg_val in zip(param_types, args):
            arg_kind = arg_val.ty.type_info.kind
            param_kind = ptype.kind
            # Patch bare Option args: Option() → Option<T> from param
            if (
                arg_kind == TypeKind.OPTION
                and not arg_val.ty.type_info.args
                and param_kind == TypeKind.OPTION
                and ptype.type_info.args
            ):
                arg_val.ty = MIRType(
                    TypeInfo(kind=TypeKind.OPTION, args=list(ptype.type_info.args))
                )
                # Also patch the WrapNone/WrapSome instruction
                self._patch_wrap_inst(arg_val, arg_val.ty)
            # Patch bare Result args
            elif (
                arg_kind == TypeKind.RESULT
                and not arg_val.ty.type_info.args
                and param_kind == TypeKind.RESULT
                and ptype.type_info.args
            ):
                arg_val.ty = MIRType(
                    TypeInfo(kind=TypeKind.RESULT, args=list(ptype.type_info.args))
                )
                self._patch_wrap_inst(arg_val, arg_val.ty)
            # Patch list element types
            if ptype.kind == TypeKind.LIST and ptype.type_info.args:
                self._patch_listinit_for_value(arg_val, ptype.type_info.args[0])

    def _patch_wrap_inst(self, val: Value, new_ty: MIRType) -> None:
        """Update the WrapNone/WrapSome instruction that produced val."""
        target_name = val.name
        for bb in self._fn.blocks if self._fn else []:
            for inst in bb.instructions:
                if isinstance(inst, (WrapNone, WrapSome)) and inst.dest.name == target_name:
                    inst.dest = Value(name=target_name, ty=new_ty)
                    if isinstance(inst, WrapNone) and hasattr(inst, "ty"):
                        inst.ty = new_ty
                    return

    def _patch_listinit_for_value(self, val: Value, elem_type_info: TypeInfo) -> None:
        """Find the ListInit instruction that produced `val` and patch its elem_type.

        Only patches if the val was directly produced by a ListInit with UNKNOWN type.
        Uses identity comparison (is) to avoid matching values with same name/type.
        """
        for bb in self._fn.blocks if self._fn else []:
            for inst in bb.instructions:
                if isinstance(inst, ListInit) and inst.dest is val and not inst.elements:
                    if inst.elem_type.kind == TypeKind.UNKNOWN:
                        inst.elem_type = MIRType(elem_type_info)
                    return

    def _lower_map(self, expr: MapLiteral) -> Value:
        """Lower a map literal."""
        pairs = [(self._lower_expr(e.key), self._lower_expr(e.value)) for e in expr.entries]
        key_type = pairs[0][0].ty if pairs else mir_unknown()
        val_type = pairs[0][1].ty if pairs else mir_unknown()
        dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.MAP)))
        self._emit(MapInit(dest=dest, key_type=key_type, val_type=val_type, pairs=pairs))
        # v5.4.4 — map owns each key/value pair.
        for _k, _v in pairs:
            self._emit(Move(value=_k))
            self._emit(Move(value=_v))
        return dest

    def _lower_construct(self, expr: ConstructExpr) -> Value:
        """Lower struct construction: `Point { x: 1.0, y: 2.0 }`."""
        fields = [(f.name, self._lower_expr(f.value)) for f in expr.fields]
        field_vals = [v for _, v in fields]

        # Monomorphize generic struct if needed
        struct_name = expr.name
        mangled = self._monomorphize_struct(struct_name, field_vals)
        if mangled is not None:
            struct_name = mangled

        struct_ty = MIRType(TypeInfo(kind=TypeKind.STRUCT, name=struct_name))
        dest = self._make_value(ty=struct_ty)
        self._emit(StructInit(dest=dest, struct_type=struct_ty, fields=fields))
        # v5.4.4 — StructInit takes ownership of each field value.
        for _v in field_vals:
            self._emit(Move(value=_v))
        self._patch_arg_types_from_params(struct_name, field_vals)
        return dest

    def _lower_struct_update(self, expr: StructUpdate) -> Value:
        """Lower struct update: `new Point { x: 5, ..base }`. v5.20.0 Te.5.C.

        Resolves the struct's full field list, lowers `base` into a fresh
        local, then synthesizes a regular ConstructExpr filling overrides
        from `expr.overrides` and the rest from `base.<field>` accesses.
        Reuses _lower_construct for the actual emission.
        """
        struct_name = expr.name

        # Resolve the full field list (local definitions or imported)
        field_names: list[str] | None = self._struct_fields.get(struct_name)
        if field_names is None and self._imported_struct_defs:
            imported = self._imported_struct_defs.get(struct_name)
            if imported is not None:
                field_names = [f for f, _ in imported]
        if field_names is None:
            raise RuntimeError(
                f"struct update: unknown struct '{struct_name}' "
                f"(no field list available; ensure the struct is defined or imported)"
            )

        # Build override map; reject unknown override fields up-front.
        override_map: dict[str, Expr] = {}
        for fi in expr.overrides:
            if fi.name not in field_names:
                raise RuntimeError(f"struct update: '{struct_name}' has no field '{fi.name}'")
            override_map[fi.name] = fi.value

        # Lower `base` once into a tmp, register it under a synthesized
        # name so that synthesized Identifier(name=base_tmp_name) lookups
        # in the field-access fallback hit the same Value.
        # Use a dedicated counter so we don't perturb the global %tN
        # sequence — keeps IR byte-identical to the manual long form.
        base_idx = self._struct_update_counter
        self._struct_update_counter += 1
        base_tmp_name = f"__mn_base_{base_idx}"
        base_val = self._lower_expr(expr.base)
        self._define_var(base_tmp_name, base_val, mutable=False)

        # Synthesize a full ConstructExpr matching the struct's field order.
        full_fields: list[FieldInit] = []
        for fname in field_names:
            if fname in override_map:
                value_expr = override_map[fname]
            else:
                value_expr = FieldAccessExpr(
                    object=Identifier(name=base_tmp_name),
                    field_name=fname,
                )
            full_fields.append(FieldInit(name=fname, value=value_expr))

        synthetic = ConstructExpr(name=struct_name, fields=full_fields)
        return self._lower_construct(synthetic)

    def _lower_signal_expr(self, expr: SignalExpr) -> Value:
        """Lower signal expression: `signal(value)`."""
        init_val = self._lower_expr(expr.value)
        sig_ty = MIRType(TypeInfo(kind=TypeKind.SIGNAL))
        dest = self._make_value(ty=sig_ty)
        self._emit(SignalInit(dest=dest, signal_type=sig_ty, initial_val=init_val))
        return dest

    def _lower_assign(self, expr: AssignExpr) -> Value:
        """Lower assignment: `x = 5` or `x += 1`."""
        val = self._lower_expr(expr.value)

        if isinstance(expr.target, Identifier):
            if expr.op != "=":
                # Compound assignment: x += 1 → x = x + 1
                old_val = self._lower_identifier(expr.target)
                op_str = expr.op[:-1]  # "+=" → "+"
                binop = _BINOP_MAP.get(op_str)
                if binop is not None:
                    result = self._make_value(ty=old_val.ty)
                    self._emit(BinOp(dest=result, op=binop, lhs=old_val, rhs=val))
                    val = result

            # Reuse the same variable name for mutable reassignment so that
            # the Python emitter produces correct code for loops. This breaks
            # strict SSA uniqueness but the MIR optimizer must handle this.
            new_val = Value(name=f"%{expr.target.name}", ty=val.ty)
            self._emit(Copy(dest=new_val, src=val))
            self._update_var(expr.target.name, new_val)
            return new_val

        if isinstance(expr.target, FieldAccessExpr):
            obj = self._lower_expr(expr.target.object)
            # Signal .value assignment → emit SignalSet for reactivity
            if expr.target.field_name == "value" and obj.ty.kind == TypeKind.SIGNAL:
                self._emit(SignalSet(signal=obj, val=val))
                return val
            self._emit(FieldSet(obj=obj, field_name=expr.target.field_name, val=val))
            return val

        if isinstance(expr.target, IndexExpr):
            from mapanare.ast_nodes import IndexItem as _II

            obj = self._lower_expr(expr.target.object)
            indices = []
            for it in expr.target.indices:
                if isinstance(it, _II) and it.kind == "scalar" and it.expr:
                    indices.append(self._lower_expr(it.expr))
                elif isinstance(it, Expr):
                    indices.append(self._lower_expr(it))
            # Tensor assignment: emit Call to __mn_tensor_set_*_nd (v4.43.0)
            if obj.ty.kind == TypeKind.TENSOR:
                self._lower_tensor_set(obj, indices, val)
                return val
            index = indices[0] if indices else self._make_value()
            self._emit(IndexSet(obj=obj, index=index, val=val))
            # v5.4.4 — map_set / list_set memcpy key+val into the container.
            self._emit(Move(value=index))
            self._emit(Move(value=val))
            # Write back: if the list came from a struct field, the IndexSet
            # only modifies a local copy.  Emit FieldSet to persist the change.
            if isinstance(expr.target.object, FieldAccessExpr):
                base = self._lower_expr(expr.target.object.object)
                self._emit(FieldSet(obj=base, field_name=expr.target.object.field_name, val=obj))
            return val

        return val

    def _lower_if(self, expr: IfExpr) -> Value:
        """Lower if/else to basic blocks with Branch terminator.

        Structure:
            %cond = <condition>
            branch %cond, then_bb, else_bb
        then_bb:
            %then_val = <then block>
            jump merge_bb
        else_bb:
            %else_val = <else block>
            jump merge_bb
        merge_bb:
            %result = phi [then_bb: %then_val, else_bb: %else_val]
        """
        cond = self._lower_expr(expr.condition)

        then_bb = self._new_block(self._fresh_block("if_then"))
        else_bb = self._new_block(self._fresh_block("if_else"))
        merge_bb = self._new_block(self._fresh_block("if_merge"))

        self._emit(Branch(cond=cond, true_block=then_bb.label, false_block=else_bb.label))

        # Then block
        self._set_block(then_bb)
        then_val = self._lower_block(expr.then_block)
        then_exit_bb = self._block  # may have changed due to nested control flow
        if not self._block_terminated():
            self._emit(Jump(target=merge_bb.label))

        # Else block
        self._set_block(else_bb)
        else_val: Value | None = None
        if isinstance(expr.else_block, Block):
            else_val = self._lower_block(expr.else_block)
        elif isinstance(expr.else_block, IfExpr):
            else_val = self._lower_if(expr.else_block)
        else_exit_bb = self._block
        if not self._block_terminated():
            self._emit(Jump(target=merge_bb.label))

        # Merge block with phi
        self._set_block(merge_bb)
        if then_val is not None or else_val is not None:
            tv = then_val if then_val is not None else Value(name="%void", ty=mir_void())
            ev = else_val if else_val is not None else Value(name="%void", ty=mir_void())
            assert then_exit_bb is not None
            assert else_exit_bb is not None
            phi_ty = tv.ty
            # Only fall back to function return type when the then-value
            # type is unknown/void — otherwise use the actual expression
            # type.  The old unconditional override caused string
            # if-expressions inside struct-returning functions to get the
            # wrong PHI type (e.g., EmitState instead of String).
            if (
                phi_ty.kind in (TypeKind.VOID, TypeKind.UNKNOWN)
                and self._fn
                and self._fn.return_type.kind != TypeKind.VOID
            ):
                phi_ty = self._fn.return_type
            result = self._make_value(ty=phi_ty, prefix="if_result")
            self._emit(
                Phi(
                    dest=result,
                    incoming=[
                        (then_exit_bb.label, tv),
                        (else_exit_bb.label, ev),
                    ],
                )
            )
            return result

        # Neither branch produced a value — this is a void if-statement.
        # Use VOID type to match the self-hosted lowerer's convention, so
        # match arm void detection treats the result correctly.
        result = self._make_value(ty=mir_void(), prefix="if_result")
        self._emit(Const(dest=result, ty=mir_void(), value=None))
        return result

    # -- Match lowering (decision-tree, Maranget 2008) -----------------------

    def _lower_match(self, expr: MatchExpr) -> Value:
        """Lower match expression using decision-tree compilation.

        Builds a Maranget decision tree, then emits MIR blocks:
        - Flat tree (single-level switch): Switch targets action blocks directly
        - Nested tree: intermediate switch blocks for inner pattern splits
        See docs/roadmap/v4/v4.34.0/DESIGN.md.
        """
        from mapanare.pattern_matching import (
            DTFail,
            DTLeaf,
            DTSwitch,
            PatternMatrix,
            PatternRow,
            build_decision_tree,
        )

        subject = self._lower_expr(expr.subject)
        ctx = self._match_type_context(subject.ty)

        rows = [PatternRow(patterns=[arm.pattern], action_idx=i) for i, arm in enumerate(expr.arms)]
        matrix = PatternMatrix(rows=rows, type_contexts=[ctx])
        tree = build_decision_tree(matrix)

        # Create merge block and action blocks (one per arm)
        merge_bb = self._new_block(self._fresh_block("match_merge"))
        action_blocks: list[BasicBlock] = []
        for _ in expr.arms:
            action_blocks.append(self._new_block(self._fresh_block("match_arm")))

        # Emit switch structure from the decision tree
        if isinstance(tree, DTLeaf):
            self._emit(Jump(target=action_blocks[tree.action_idx].label))
        elif isinstance(tree, DTFail):
            self._emit(Jump(target=merge_bb.label))
        elif isinstance(tree, DTSwitch) and self._is_flat_switch(tree):
            self._emit_flat_switch(tree, subject, action_blocks, merge_bb)
        elif isinstance(tree, DTSwitch):
            self._emit_nested_switch(tree, [subject], action_blocks, merge_bb)

        # Lower each arm body.
        # Mirror the self-hosted convention: void/unknown arm values are replaced
        # with zeroinitializer sentinels. If ALL entries are zeroinitializer,
        # skip the PHI and emit the unreachable merge pattern.
        arm_results: list[tuple[str, Value]] = []
        for i, arm in enumerate(expr.arms):
            self._set_block(action_blocks[i])
            self._push_scope()
            self._bind_match_arm(arm.pattern, subject)

            # v4.35.0: guard fall-through — evaluate guard, branch on result
            if arm.guard is not None:
                guard_val = self._lower_expr(arm.guard)
                body_bb = self._new_block(self._fresh_block("guard_pass"))
                fallback_bb = self._new_block(self._fresh_block("guard_fail"))
                self._emit(
                    Branch(cond=guard_val, true_block=body_bb.label, false_block=fallback_bb.label)
                )
                # Emit fallback: decision tree from remaining rows
                self._set_block(fallback_bb)
                remaining_rows = [
                    PatternRow(patterns=[expr.arms[j].pattern], action_idx=j)
                    for j in range(i + 1, len(expr.arms))
                ]
                if remaining_rows:
                    remaining_matrix = PatternMatrix(rows=remaining_rows, type_contexts=[ctx])
                    remaining_tree = build_decision_tree(remaining_matrix)
                    self._emit_decision_tree(remaining_tree, [subject], action_blocks, merge_bb)
                else:
                    self._emit(Jump(target=merge_bb.label))
                # Continue body in the guard_pass block
                self._set_block(body_bb)

            if isinstance(arm.body, Block):
                arm_val = self._lower_block(arm.body)
            else:
                arm_val = self._lower_expr(arm.body)
            exit_bb = self._block
            if not self._block_terminated():
                assert exit_bb is not None  # _block_terminated returns True when _block is None
                self._emit(Jump(target=merge_bb.label))
                # Mirror self-hosted: void/unknown → zeroinitializer (Rule 4)
                is_void = (
                    arm_val is None
                    or arm_val.ty.kind in (TypeKind.VOID, TypeKind.UNKNOWN)
                    or arm_val.name == "%void"
                )
                if is_void:
                    zty = arm_val.ty if arm_val is not None else mir_void()
                    arm_results.append((exit_bb.label, Value(name="zeroinitializer", ty=zty)))
                elif arm_val is not None:
                    arm_results.append((exit_bb.label, arm_val))
            self._pop_scope()

        # Merge block — mirrors self-hosted all_zero check.
        self._set_block(merge_bb)

        has_real_value = any(val.name != "zeroinitializer" for _, val in arm_results)

        if arm_results and has_real_value:
            phi_ty = arm_results[0][1].ty
            if self._fn and self._fn.return_type.kind != TypeKind.VOID:
                phi_ty = self._fn.return_type
            result = self._make_value(ty=phi_ty, prefix="match_result")
            self._emit(Phi(dest=result, incoming=arm_results))
            return result

        # All arms terminated or all void — unreachable merge
        ret_ty = self._fn.return_type if self._fn else mir_void()
        result = self._make_value(ty=ret_ty, prefix="match_result")
        self._emit(Const(dest=result, ty=ret_ty, value=None))
        return result

    def _match_type_context(self, ty: MIRType) -> Any:
        """Build a TypeContext for pattern matching from a MIR type."""
        from mapanare.pattern_matching import TypeContext

        kind = ty.kind
        args = ty.type_info.args

        # Cycle guard: recursive types (e.g., Expr with BinOp(Expr, Expr))
        type_key = ty.type_info.name or ""
        if type_key and type_key in self._match_ctx_stack:
            return TypeContext(is_closed=False)
        if type_key:
            self._match_ctx_stack.add(type_key)
        try:
            return self._match_type_context_inner(ty, kind, args)
        finally:
            self._match_ctx_stack.discard(type_key)

    def _match_type_context_inner(self, ty: MIRType, kind: TypeKind, args: list[Any]) -> Any:
        from mapanare.pattern_matching import ConstructorInfo, TypeContext

        if kind == TypeKind.OPTION:
            some_sub = [self._match_type_context(MIRType(args[0]))] if args else []
            return TypeContext(
                is_closed=True,
                all_constructors=[ConstructorInfo("Some", 1), ConstructorInfo("None", 0)],
                sub_contexts={"Some": some_sub},
            )

        if kind == TypeKind.RESULT:
            ok_sub = [self._match_type_context(MIRType(args[0]))] if args else []
            err_sub = [self._match_type_context(MIRType(args[1]))] if len(args) >= 2 else []
            return TypeContext(
                is_closed=True,
                all_constructors=[ConstructorInfo("Ok", 1), ConstructorInfo("Err", 1)],
                sub_contexts={"Ok": ok_sub, "Err": err_sub},
            )

        enum_name = ty.type_info.name
        if enum_name and (
            kind == TypeKind.ENUM or (kind == TypeKind.STRUCT and enum_name in self._enum_variants)
        ):
            variants = self._module.enums.get(enum_name, [])
            ctors: list[ConstructorInfo] = []
            sub_ctxs: dict[str, list[TypeContext]] = {}
            for vname, payload_types in variants:
                arity = len(payload_types)
                ctors.append(ConstructorInfo(vname, arity))
                if arity > 0:
                    sub_ctxs[vname] = [self._match_type_context(pt) for pt in payload_types]
            return TypeContext(is_closed=True, all_constructors=ctors, sub_contexts=sub_ctxs)

        if kind == TypeKind.BOOL:
            return TypeContext(
                is_closed=True,
                all_constructors=[ConstructorInfo("true", 0), ConstructorInfo("false", 0)],
            )

        return TypeContext(is_closed=False)

    @staticmethod
    def _is_flat_switch(tree: Any) -> bool:
        """True if the tree is single-level: all children are DTLeaf."""
        from mapanare.pattern_matching import DTLeaf

        for _, subtree in tree.cases:
            if not isinstance(subtree, DTLeaf):
                return False
        if tree.default is not None and not isinstance(tree.default, DTLeaf):
            return False
        return True

    def _emit_flat_switch(
        self,
        tree: Any,
        subject: Value,
        action_blocks: list[BasicBlock],
        merge_bb: BasicBlock,
    ) -> None:
        """Emit a flat switch: Switch instruction targets action blocks directly."""
        from mapanare.pattern_matching import DTLeaf

        cases: list[tuple[Any, str]] = []
        default_block = merge_bb.label

        for tag, subtree in tree.cases:
            assert isinstance(subtree, DTLeaf)
            cases.append((tag, action_blocks[subtree.action_idx].label))

        if tree.default is not None:
            assert isinstance(tree.default, DTLeaf)
            default_block = action_blocks[tree.default.action_idx].label

        if cases:
            tag_val = self._make_value(ty=subject.ty, prefix="tag")
            self._emit(EnumTag(dest=tag_val, enum_val=subject))
            self._emit(Switch(tag=tag_val, cases=cases, default_block=default_block))
        elif action_blocks:
            self._emit(Jump(target=action_blocks[0].label))

    def _emit_nested_switch(
        self,
        tree: Any,
        col_values: list[Value],
        action_blocks: list[BasicBlock],
        merge_bb: BasicBlock,
    ) -> None:
        """Emit a nested decision tree with intermediate switch blocks."""
        from mapanare.pattern_matching import DTFail, DTLeaf, DTSwitch

        col_val = col_values[tree.column_idx]

        # Pre-create case blocks
        case_block_info: list[tuple[str, Any, BasicBlock]] = []
        switch_cases: list[tuple[Any, str]] = []
        for tag, subtree in tree.cases:
            case_bb = self._new_block(self._fresh_block(f"match_case_{tag}"))
            switch_cases.append((tag, case_bb.label))
            case_block_info.append((tag, subtree, case_bb))

        # Default block
        default_label = merge_bb.label
        default_info: tuple[Any, BasicBlock] | None = None
        if tree.default is not None:
            default_bb = self._new_block(self._fresh_block("match_default"))
            default_label = default_bb.label
            default_info = (tree.default, default_bb)

        # Emit tag extraction + switch in current block
        tag_val = self._make_value(ty=col_val.ty, prefix="tag")
        self._emit(EnumTag(dest=tag_val, enum_val=col_val))
        self._emit(Switch(tag=tag_val, cases=switch_cases, default_block=default_label))

        # Emit each case block
        for tag, subtree, case_bb in case_block_info:
            self._set_block(case_bb)

            if isinstance(subtree, DTLeaf):
                self._emit(Jump(target=action_blocks[subtree.action_idx].label))
            elif isinstance(subtree, DTFail):
                self._emit(Jump(target=merge_bb.label))
            elif isinstance(subtree, DTSwitch):
                # Extract payloads for sub-columns, then recurse
                ctor_arity = self._ctor_arity(col_val.ty, tag)
                sub_values: list[Value] = []
                for j in range(ctor_arity):
                    payload_ty = self._infer_payload_type(col_val.ty, tag, j)
                    payload = self._make_value(ty=payload_ty, prefix=f"pay_{j}")
                    self._emit(
                        EnumPayload(dest=payload, enum_val=col_val, variant=tag, payload_idx=j)
                    )
                    sub_values.append(payload)
                new_col_values = (
                    col_values[: tree.column_idx] + sub_values + col_values[tree.column_idx + 1 :]
                )
                self._emit_nested_switch(subtree, new_col_values, action_blocks, merge_bb)

        # Emit default block
        if default_info is not None:
            subtree, def_bb = default_info
            self._set_block(def_bb)
            new_col_values = col_values[: tree.column_idx] + col_values[tree.column_idx + 1 :]
            if isinstance(subtree, DTLeaf):
                self._emit(Jump(target=action_blocks[subtree.action_idx].label))
            elif isinstance(subtree, DTFail):
                self._emit(Jump(target=merge_bb.label))
            elif isinstance(subtree, DTSwitch):
                self._emit_nested_switch(subtree, new_col_values, action_blocks, merge_bb)

    def _emit_decision_tree(
        self,
        tree: Any,
        col_values: list[Value],
        action_blocks: list[BasicBlock],
        merge_bb: BasicBlock,
    ) -> None:
        """Emit code for a decision tree (v4.35.0 — used by guard fall-through)."""
        from mapanare.pattern_matching import DTFail, DTLeaf, DTSwitch

        if isinstance(tree, DTLeaf):
            self._emit(Jump(target=action_blocks[tree.action_idx].label))
        elif isinstance(tree, DTFail):
            self._emit(Jump(target=merge_bb.label))
        elif isinstance(tree, DTSwitch):
            if self._is_flat_switch(tree):
                self._emit_flat_switch(tree, col_values[0], action_blocks, merge_bb)
            else:
                self._emit_nested_switch(tree, col_values, action_blocks, merge_bb)

    def _bind_match_arm(self, pat: Any, subject: Value) -> None:
        """Bind pattern variables from a match arm, handling nested constructors."""
        from mapanare.ast_nodes import OrPattern

        if isinstance(pat, ConstructorPattern):
            for j, arg_pat in enumerate(pat.args):
                if isinstance(arg_pat, (IdentPattern, ConstructorPattern)):
                    payload_ty = self._infer_payload_type(subject.ty, pat.name, j)
                    pfx = (
                        arg_pat.name if isinstance(arg_pat, IdentPattern) else f"pay_{pat.name}_{j}"
                    )
                    payload = self._make_value(ty=payload_ty, prefix=pfx)
                    self._emit(
                        EnumPayload(dest=payload, enum_val=subject, variant=pat.name, payload_idx=j)
                    )
                    if isinstance(arg_pat, IdentPattern):
                        self._define_var(arg_pat.name, payload)
                    else:
                        # Nested constructor — recurse
                        self._bind_match_arm(arg_pat, payload)
        elif isinstance(pat, IdentPattern):
            self._define_var(pat.name, subject)
        elif isinstance(pat, OrPattern):
            # v4.35.0: bind from first alternative (all have same names)
            self._bind_match_arm(pat.alternatives[0], subject)

    def _ctor_arity(self, ty: MIRType, tag: str) -> int:
        """Get the arity of a constructor for a given type."""
        kind = ty.kind
        if kind == TypeKind.OPTION:
            return 1 if tag == "Some" else 0
        if kind == TypeKind.RESULT:
            return 1
        enum_name = ty.type_info.name
        if enum_name:
            variants = self._module.enums.get(enum_name, [])
            for vname, payload_types in variants:
                if vname == tag:
                    return len(payload_types)
        return 0

    def _lower_interp_string(self, expr: InterpString) -> Value:
        """Lower string interpolation."""
        parts = []
        for part in expr.parts:
            val = self._lower_expr(part)
            if not isinstance(part, StringLiteral):
                # Cast non-string parts to string
                str_val = self._make_value(ty=mir_string())
                self._emit(Cast(dest=str_val, src=val, target_type=mir_string()))
                parts.append(str_val)
            else:
                parts.append(val)

        dest = self._make_value(ty=mir_string())
        self._emit(InterpConcat(dest=dest, parts=parts))
        return dest


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def lower(
    program: Program,
    module_name: str = "",
    source_file: str = "",
    source_directory: str = "",
    imported_return_types: dict[str, MIRType] | None = None,
    imported_struct_defs: dict[str, list[tuple[str, MIRType]]] | None = None,
    imported_enum_defs: dict[str, list[tuple[str, list[MIRType]]]] | None = None,
) -> MIRModule:
    """Lower an AST program to MIR.

    Args:
        program: The typed AST (after semantic analysis).
        module_name: Optional module name.
        source_file: Original source file name (for debug info).
        source_directory: Directory of the source file (for debug info).
        imported_return_types: fn_name → MIRType for imported functions.
        imported_struct_defs: struct_name → [(field_name, MIRType)] for imported structs.
        imported_enum_defs: enum_name → [(variant, [MIRType])] for imported enums.

    Returns:
        A MIRModule containing the lowered MIR.
    """
    return MIRLowerer(
        imported_return_types=imported_return_types,
        imported_struct_defs=imported_struct_defs,
        imported_enum_defs=imported_enum_defs,
    ).lower(
        program,
        module_name,
        source_file=source_file,
        source_directory=source_directory,
    )
