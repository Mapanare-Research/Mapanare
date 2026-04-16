"""Semantic analysis -- type checking and scope resolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mapanare.diagnostics import Diagnostic
    from mapanare.modules import ModuleExport, ModuleResolver

from mapanare.ast_nodes import (
    AgentDef,
    AssertStmt,
    AssignExpr,
    AsyncFnDef,
    ASTNode,
    AwaitExpr,
    ForAwaitLoop,
    BinaryExpr,
    Block,
    BoolLiteral,
    BreakStmt,
    CallExpr,
    ConstDef,
    CharLiteral,
    ConstructExpr,
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
    FloatLiteral,
    FnDef,
    FnType,
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
    MapLiteral,
    MatchExpr,
    MethodCallExpr,
    ModuleLetDef,
    NamedType,
    NamespaceAccessExpr,
    NoneLiteral,
    OkExpr,
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
    SpawnExpr,
    StreamDecl,
    StringLiteral,
    StructDef,
    SyncExpr,
    TensorLiteral,
    TensorType,
    TraitDef,
    TypeAlias,
    TypeExpr,
    UnaryExpr,
    WhileLoop,
)
from mapanare.types import (
    ANY_TYPE,
    BOOL_TYPE,
    BUILTIN_FUNCTIONS,
    BUILTIN_GENERIC_KINDS,
    BUILTIN_GENERIC_TYPES,
    BUILTIN_TRAITS,
    CHAR_TYPE,
    FLOAT_TYPE,
    INT_TYPE,
    PRIMITIVE_KINDS,
    PRIMITIVE_TYPES,
    RANGE_TYPE,
    STRING_TYPE,
    UNKNOWN_TYPE,
    VOID_TYPE,
    TypeInfo,
    TypeKind,
    _type_display,
    kind_from_name,
)

# Re-export these for backward compatibility — other modules import from semantic.py
__all__ = [
    "SemanticError",
    "SemanticErrors",
    "SemanticChecker",
    "SymbolKind",
    "check",
    "check_or_raise",
    "TypeInfo",
    "TypeKind",
    "UNKNOWN_TYPE",
    "INT_TYPE",
    "FLOAT_TYPE",
    "BOOL_TYPE",
    "STRING_TYPE",
    "CHAR_TYPE",
    "VOID_TYPE",
    "BUILTIN_FUNCTIONS",
    "BUILTIN_GENERIC_TYPES",
    "PRIMITIVE_TYPES",
]

# ---------------------------------------------------------------------------
# Semantic error — thin record that now carries a real source range.
#
# v4.27.0 recovery: previously this record only stored a single (line, column)
# point, so every semantic error underlined exactly one character regardless
# of how wide the offending expression was (v4.26.0 panel CRITICAL #8 from
# Anaconda). The representation is now range-aware: errors constructed via
# ``SemanticChecker._error`` pick up the full ``Span`` from the AST node, and
# ``cli._emit_semantic_errors`` renders them through ``diagnostics.py``'s
# ``Diagnostic`` formatter so the underline matches the offending expression.
#
# The dataclass name and ``line``/``column``/``message``/``filename`` fields
# are preserved so that external consumers (LSP, playground, tests,
# test_runner) continue to work without a mass rename.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SemanticError:
    """A single semantic error with a real source range."""

    message: str
    line: int = 0
    column: int = 0
    end_line: int = 0
    end_column: int = 0
    filename: str = "<input>"
    severity: str = "error"

    def __str__(self) -> str:
        prefix = "warning" if self.severity == "warning" else "error"
        return f"{self.filename}:{self.line}:{self.column}: {prefix}: {self.message}"

    def to_diagnostic(self) -> "Diagnostic":
        """Render this error as a :class:`mapanare.diagnostics.Diagnostic`.

        Routes through ``mapanare.diagnostics`` so the CLI error path uses the
        same rustc-quality formatter as parser errors. If ``end_line`` or
        ``end_column`` were not populated (legacy call sites), the renderer
        falls back to a one-character span so behaviour is unchanged.
        """
        from mapanare.ast_nodes import Span
        from mapanare.diagnostics import Diagnostic, Label, Severity

        end_line = self.end_line if self.end_line > 0 else self.line
        end_column = self.end_column if self.end_column > 0 else self.column + 1
        span = Span(line=self.line, column=self.column, end_line=end_line, end_column=end_column)
        severity = Severity.WARNING if self.severity == "warning" else Severity.ERROR
        return Diagnostic(
            severity=severity,
            message=self.message,
            filename=self.filename,
            labels=[Label(span=span, primary=True)],
        )


class SemanticErrors(Exception):
    """Raised when semantic analysis finds errors."""

    def __init__(self, errors: list[SemanticError]) -> None:
        self.errors = errors
        msgs = "\n".join(str(e) for e in errors)
        super().__init__(f"Semantic analysis found {len(errors)} error(s):\n{msgs}")


# ---------------------------------------------------------------------------
# Symbol table / Scope
# ---------------------------------------------------------------------------


class SymbolKind(StrEnum):
    """Kind of a declared symbol.

    Inherits from ``StrEnum`` so that ``SymbolKind.VARIABLE == "variable"``
    evaluates to ``True``, keeping backward compatibility with existing string
    comparisons.
    """

    VARIABLE = "variable"
    FUNCTION = "function"
    AGENT = "agent"
    STRUCT = "struct"
    ENUM = "enum"
    TYPE_ALIAS = "type_alias"
    PIPE = "pipe"
    PARAM = "param"
    TRAIT = "trait"
    MODULE = "module"
    CONST = "const"


# v4.55.0: compile-time constant values for const folding
ConstantValue = int | float | bool | str


@dataclass
class Symbol:
    """A declared symbol (variable, function, type, agent, etc.)."""

    name: str
    kind: SymbolKind
    type_info: TypeInfo = field(default_factory=lambda: UNKNOWN_TYPE)
    mutable: bool = False
    node: ASTNode | None = None
    const_value: ConstantValue | None = None


class Scope:
    """A lexical scope containing symbol bindings."""

    def __init__(self, parent: Scope | None = None) -> None:
        self.parent = parent
        self.symbols: dict[str, Symbol] = {}

    def define(self, name: str, symbol: Symbol) -> Symbol | None:
        """Define a symbol in this scope. Returns previous symbol if redefined."""
        prev = self.symbols.get(name)
        self.symbols[name] = symbol
        return prev

    def lookup(self, name: str) -> Symbol | None:
        """Look up a symbol, walking up the scope chain."""
        sym = self.symbols.get(name)
        if sym is not None:
            return sym
        if self.parent is not None:
            return self.parent.lookup(name)
        return None

    def lookup_local(self, name: str) -> Symbol | None:
        """Look up a symbol only in the current scope (no parent walk)."""
        return self.symbols.get(name)


# ---------------------------------------------------------------------------
# Numeric/arithmetic kind sets (for type checking)
# ---------------------------------------------------------------------------

_NUMERIC_KINDS = frozenset({TypeKind.INT, TypeKind.FLOAT})
_ARITHMETIC_KINDS = frozenset(
    {TypeKind.INT, TypeKind.FLOAT, TypeKind.STRING, TypeKind.UNKNOWN, TypeKind.ANY}
)
_TENSOR_ARITH_KINDS = frozenset(
    {TypeKind.UNKNOWN, TypeKind.TENSOR, TypeKind.INT, TypeKind.FLOAT, TypeKind.ANY}
)

_OP_TO_TRAIT: dict[str, str] = {"+": "Add", "-": "Sub", "*": "Mul", "/": "Div"}


# ---------------------------------------------------------------------------
# Semantic Checker
# ---------------------------------------------------------------------------


class SemanticChecker:
    """Walks the AST and performs semantic analysis.

    Checks performed:
    - Variable scope analysis (nested scopes, shadowing)
    - Basic type inference from literals and annotations
    - Type checking for assignments and binary ops
    - Undefined variable detection
    - Agent input/output type validation
    - Pipe connection type compatibility
    - Error messages with file, line, column
    """

    def __init__(
        self,
        filename: str = "<input>",
        resolver: ModuleResolver | None = None,
    ) -> None:
        self.filename = filename
        self.errors: list[SemanticError] = []
        self.global_scope = Scope()
        self.current_scope = self.global_scope
        self.resolver = resolver
        # Track resolved modules for this checker (module name -> exports)
        self._resolved_modules: dict[str, dict[str, ModuleExport]] = {}
        # Track trait implementations: (trait_name, type_name) pairs
        self._trait_impls: set[tuple[str, str]] = set()
        # Type parameters of the current function (for generic type resolution)
        self._current_type_params: set[str] = set()
        # v4.33.0: track enclosing function's return type for `?` operator
        # type checking. Set by _check_fn, read by the ErrorPropExpr handler.
        self._current_fn_return_type: TypeInfo | None = None
        self._current_fn_name: str = ""
        # v4.55.0: const folding table (name -> folded value)
        self._const_table: dict[str, ConstantValue] = {}
        # v4.69.0: track whether we're inside an async fn body.
        # Set by _check_async_fn, read by the AwaitExpr handler.
        self._in_async: bool = False

        # Register built-in traits
        for trait_name, methods in BUILTIN_TRAITS.items():
            trait_methods = []
            for m_name, has_self, _params, ret_name in methods:
                from mapanare.ast_nodes import TraitMethod as _TM

                ret_te = None
                if ret_name and ret_name != "Self":
                    ret_te = NamedType(name=ret_name)
                trait_methods.append(_TM(name=m_name, has_self=has_self, return_type=ret_te))
            builtin_trait_node = TraitDef(name=trait_name, public=True, methods=trait_methods)
            self.global_scope.define(
                trait_name,
                Symbol(
                    name=trait_name,
                    kind=SymbolKind.TRAIT,
                    type_info=TypeInfo(kind=TypeKind.TRAIT, name=trait_name),
                    node=builtin_trait_node,
                ),
            )

        # Register built-in functions from canonical registry
        for name, ret_type in BUILTIN_FUNCTIONS.items():
            self.global_scope.define(
                name,
                Symbol(
                    name=name,
                    kind=SymbolKind.FUNCTION,
                    type_info=TypeInfo(
                        kind=TypeKind.BUILTIN_FN,
                        is_function=True,
                        return_type=ret_type,
                    ),
                ),
            )

    # -- Error helpers --------------------------------------------------

    def _error(self, message: str, node: ASTNode) -> None:
        # v4.27.0: capture the full AST span so diagnostics underline the
        # offending expression instead of pointing at a single character.
        self.errors.append(
            SemanticError(
                message=message,
                line=node.span.line,
                column=node.span.column,
                end_line=node.span.end_line,
                end_column=node.span.end_column,
                filename=self.filename,
            )
        )

    def _error_at(self, message: str, line: int, column: int) -> None:
        self.errors.append(
            SemanticError(
                message=message,
                line=line,
                column=column,
                filename=self.filename,
            )
        )

    def _warning(self, message: str, node: ASTNode) -> None:
        self.errors.append(
            SemanticError(
                message=message,
                line=node.span.line,
                column=node.span.column,
                end_line=node.span.end_line,
                end_column=node.span.end_column,
                filename=self.filename,
                severity="warning",
            )
        )

    # -- Scope helpers --------------------------------------------------

    def _push_scope(self) -> Scope:
        self.current_scope = Scope(parent=self.current_scope)
        return self.current_scope

    def _pop_scope(self) -> None:
        if self.current_scope.parent is not None:
            self.current_scope = self.current_scope.parent

    # -- Type resolution ------------------------------------------------

    def _resolve_type_expr(self, te: TypeExpr | None) -> TypeInfo:
        """Resolve a TypeExpr AST node to a TypeInfo."""
        if te is None:
            return UNKNOWN_TYPE
        if isinstance(te, NamedType):
            if te.module_path:
                mod_sym = self.global_scope.lookup(te.module_path[0])
                if mod_sym is None:
                    self._error(f"unknown module '{te.module_path[0]}'", te)
                return TypeInfo(kind=TypeKind.STRUCT, name=te.name)
            k = kind_from_name(te.name)
            if k != TypeKind.UNKNOWN:
                return TypeInfo(kind=k)
            # User-defined type — look up in scope to determine kind
            sym = self.global_scope.lookup(te.name)
            if sym is not None:
                if sym.kind == SymbolKind.STRUCT:
                    return TypeInfo(kind=TypeKind.STRUCT, name=te.name)
                elif sym.kind == SymbolKind.ENUM:
                    return TypeInfo(kind=TypeKind.ENUM, name=te.name)
                elif sym.kind == SymbolKind.AGENT:
                    return TypeInfo(kind=TypeKind.AGENT, name=te.name)
                elif sym.kind == SymbolKind.TYPE_ALIAS:
                    return sym.type_info
            # Check if this is a type parameter (from a generic function)
            if te.name in self._current_type_params:
                return TypeInfo(kind=TypeKind.UNKNOWN, name=te.name)
            # Unknown user type — default to struct-like
            return TypeInfo(kind=TypeKind.STRUCT, name=te.name)
        if isinstance(te, GenericType):
            args = [self._resolve_type_expr(a) for a in te.args]
            if te.module_path:
                mod_sym = self.global_scope.lookup(te.module_path[0])
                if mod_sym is None:
                    self._error(f"unknown module '{te.module_path[0]}'", te)
                k = kind_from_name(te.name)
                if k != TypeKind.UNKNOWN:
                    return TypeInfo(kind=k, args=args)
                return TypeInfo(kind=TypeKind.STRUCT, name=te.name, args=args)
            from mapanare.types import BUILTIN_GENERIC_ARITY

            expected_arity = BUILTIN_GENERIC_ARITY.get(te.name)
            if expected_arity is not None and len(args) != expected_arity:
                self._error(
                    f"'{te.name}' expects {expected_arity} type argument(s), got {len(args)}",
                    te,
                )
            k = kind_from_name(te.name)
            if k != TypeKind.UNKNOWN:
                return TypeInfo(kind=k, args=args)
            return TypeInfo(kind=TypeKind.STRUCT, name=te.name, args=args)
        if isinstance(te, TensorType):
            elem = self._resolve_type_expr(te.element_type)
            from mapanare.types import resolve_shape_from_type

            shape = resolve_shape_from_type(list(te.shape))
            return TypeInfo(kind=TypeKind.TENSOR, args=[elem], tensor_shape=shape)
        if isinstance(te, FnType):
            params = [self._resolve_type_expr(p) for p in te.param_types]
            ret = self._resolve_type_expr(te.return_type)
            return TypeInfo(
                kind=TypeKind.FN,
                is_function=True,
                param_types=params,
                return_type=ret,
            )
        return UNKNOWN_TYPE

    # -- Expression type inference --------------------------------------

    def _infer_expr(self, expr: Expr) -> TypeInfo:
        """Infer the type of an expression."""
        if isinstance(expr, IntLiteral):
            return INT_TYPE
        if isinstance(expr, FloatLiteral):
            return FLOAT_TYPE
        if isinstance(expr, BoolLiteral):
            return BOOL_TYPE
        if isinstance(expr, StringLiteral):
            return STRING_TYPE
        if isinstance(expr, InterpString):
            for part in expr.parts:
                self._infer_expr(part)
            return STRING_TYPE
        if isinstance(expr, CharLiteral):
            return CHAR_TYPE
        if isinstance(expr, NoneLiteral):
            return TypeInfo(kind=TypeKind.OPTION)
        if isinstance(expr, Identifier):
            sym = self.current_scope.lookup(expr.name)
            if sym is None:
                self._error(f"Undefined variable '{expr.name}'", expr)
                return UNKNOWN_TYPE
            return sym.type_info
        if isinstance(expr, BinaryExpr):
            return self._check_binary(expr)
        if isinstance(expr, UnaryExpr):
            return self._check_unary(expr)
        if isinstance(expr, CallExpr):
            return self._check_call(expr)
        if isinstance(expr, MethodCallExpr):
            obj_type = self._infer_expr(expr.object)
            for a in expr.args:
                self._infer_expr(a)
            # Return known types for string methods
            if obj_type.kind == TypeKind.STRING:
                _str_method_types: dict[str, TypeInfo] = {
                    "starts_with": BOOL_TYPE,
                    "ends_with": BOOL_TYPE,
                    "contains": BOOL_TYPE,
                    "find": INT_TYPE,
                    "byte_at": INT_TYPE,
                    "char_at": STRING_TYPE,
                    "substr": STRING_TYPE,
                    "trim": STRING_TYPE,
                    "trim_start": STRING_TYPE,
                    "trim_end": STRING_TYPE,
                    "to_upper": STRING_TYPE,
                    "to_lower": STRING_TYPE,
                    "replace": STRING_TYPE,
                    "split": TypeInfo(kind=TypeKind.LIST, args=[STRING_TYPE]),
                    "length": INT_TYPE,
                }
                ret = _str_method_types.get(expr.method)
                if ret is not None:
                    return ret
            return UNKNOWN_TYPE
        if isinstance(expr, FieldAccessExpr):
            obj_type = self._infer_expr(expr.object)
            # Check agent inputs/outputs
            sym = None
            if isinstance(expr.object, Identifier):
                sym = self.current_scope.lookup(expr.object.name)
            if sym and sym.kind == SymbolKind.AGENT and sym.node and isinstance(sym.node, AgentDef):
                agent = sym.node
                for inp in agent.inputs:
                    if inp.name == expr.field_name:
                        return self._resolve_type_expr(inp.type_annotation)
                for out in agent.outputs:
                    if out.name == expr.field_name:
                        return self._resolve_type_expr(out.type_annotation)
            # Resolve struct field types
            if obj_type.kind == TypeKind.STRUCT and obj_type.name:
                struct_sym = self.current_scope.lookup(obj_type.name)
                if struct_sym and struct_sym.node and isinstance(struct_sym.node, StructDef):
                    for f in struct_sym.node.fields:
                        if f.name == expr.field_name:
                            return self._resolve_type_expr(f.type_annotation)
            return UNKNOWN_TYPE
        if isinstance(expr, IndexExpr):
            from mapanare.ast_nodes import IndexItem

            obj_type = self._infer_expr(expr.object)
            has_slice = False
            for idx_item in expr.indices:
                if isinstance(idx_item, IndexItem):
                    if idx_item.kind == "scalar" and idx_item.expr:
                        self._infer_expr(idx_item.expr)
                    elif idx_item.kind == "range":
                        if idx_item.start:
                            self._infer_expr(idx_item.start)
                        if idx_item.end:
                            self._infer_expr(idx_item.end)
                        has_slice = True
                    elif idx_item.kind == "wildcard":
                        has_slice = True
                elif isinstance(idx_item, Expr):
                    self._infer_expr(idx_item)
            n_idx = len(expr.indices)
            # Tensor: rank match + slicing shape inference (v4.43.0 + v4.45.0)
            if obj_type.kind == TypeKind.TENSOR:
                rank = len(obj_type.tensor_shape) if obj_type.tensor_shape else None
                if rank is not None and n_idx != rank:
                    self._error(
                        f"tensor index rank mismatch: got {n_idx} indices "
                        f"for rank-{rank} tensor",
                        expr,
                    )
                elem = obj_type.args[0] if obj_type.args else FLOAT_TYPE
                if has_slice:
                    # Slicing returns a tensor (view) — infer result shape
                    result_shape: list[int] = []
                    if obj_type.tensor_shape:
                        for d, idx_item in enumerate(expr.indices):
                            if isinstance(idx_item, IndexItem):
                                if idx_item.kind == "wildcard":
                                    result_shape.append(
                                        obj_type.tensor_shape[d]
                                        if d < len(obj_type.tensor_shape)
                                        else 0
                                    )
                                elif idx_item.kind == "range":
                                    s = (
                                        idx_item.start.value
                                        if isinstance(idx_item.start, IntLiteral)
                                        else 0
                                    )
                                    e = (
                                        idx_item.end.value
                                        if isinstance(idx_item.end, IntLiteral)
                                        else (
                                            obj_type.tensor_shape[d]
                                            if d < len(obj_type.tensor_shape)
                                            else 0
                                        )
                                    )
                                    result_shape.append(max(0, e - s))
                                else:
                                    pass  # scalar index removes dimension
                    return TypeInfo(
                        kind=TypeKind.TENSOR,
                        args=[elem],
                        tensor_shape=tuple(result_shape) if result_shape else None,
                    )
                return elem
            # List/Map: require single scalar index
            if n_idx > 1:
                self._error(
                    f"multi-index not supported for {obj_type.kind.name}; " f"use single index",
                    expr,
                )
            if obj_type.kind == TypeKind.LIST and obj_type.args:
                return obj_type.args[0]
            if obj_type.kind == TypeKind.MAP and len(obj_type.args) >= 2:
                return obj_type.args[1]
            return UNKNOWN_TYPE
        if isinstance(expr, PipeExpr):
            return self._check_pipe_expr(expr)
        if isinstance(expr, RangeExpr):
            self._infer_expr(expr.start)
            self._infer_expr(expr.end)
            return RANGE_TYPE
        if isinstance(expr, LambdaExpr):
            return self._check_lambda(expr)
        if isinstance(expr, SpawnExpr):
            return self._check_spawn(expr)
        if isinstance(expr, SyncExpr):
            self._infer_expr(expr.expr)
            return UNKNOWN_TYPE
        if isinstance(expr, AwaitExpr):
            # v4.69.0: full await type checking.
            # 1. Must be inside an async fn
            if not self._in_async:
                self._error(
                    "'await' can only be used inside an 'async fn'",
                    expr,
                )
                return UNKNOWN_TYPE
            # 2. Operand must be Future<T>
            inner_type = self._infer_expr(expr.expr)
            if inner_type.kind == TypeKind.FUTURE:
                # Extract T from Future<T>
                if inner_type.args:
                    return inner_type.args[0]
                return UNKNOWN_TYPE
            if inner_type.kind in (TypeKind.UNKNOWN, TypeKind.UNRESOLVED, TypeKind.ANY):
                # Can't validate — allow through
                return UNKNOWN_TYPE
            # Operand is not Future<T> — error
            self._error(
                f"'await' requires a Future<T>, got {inner_type.display_name}",
                expr,
            )
            return UNKNOWN_TYPE
        if isinstance(expr, SendExpr):
            self._check_send(expr)
            return VOID_TYPE
        if isinstance(expr, ErrorPropExpr):
            return self._check_error_prop(expr)
        if isinstance(expr, ListLiteral):
            if expr.elements:
                elem_type = self._infer_expr(expr.elements[0])
                for e in expr.elements[1:]:
                    self._infer_expr(e)
                return TypeInfo(kind=TypeKind.LIST, args=[elem_type])
            return TypeInfo(kind=TypeKind.LIST, args=[UNKNOWN_TYPE])
        if isinstance(expr, TensorLiteral):
            return self._check_tensor_literal(expr)
        if isinstance(expr, MapLiteral):
            if expr.entries:
                key_type = self._infer_expr(expr.entries[0].key)
                val_type = self._infer_expr(expr.entries[0].value)
                for entry in expr.entries[1:]:
                    self._infer_expr(entry.key)
                    self._infer_expr(entry.value)
                return TypeInfo(kind=TypeKind.MAP, args=[key_type, val_type])
            return TypeInfo(kind=TypeKind.MAP, args=[UNKNOWN_TYPE, UNKNOWN_TYPE])
        if isinstance(expr, ConstructExpr):
            for fi in expr.fields:
                self._infer_expr(fi.value)
            # Look up the struct/enum in scope
            sym = self.global_scope.lookup(expr.name)
            if sym is not None:
                if sym.kind == SymbolKind.STRUCT:
                    return TypeInfo(kind=TypeKind.STRUCT, name=expr.name)
                elif sym.kind == SymbolKind.ENUM:
                    return TypeInfo(kind=TypeKind.ENUM, name=expr.name)
            return TypeInfo(kind=TypeKind.STRUCT, name=expr.name)
        if isinstance(expr, SomeExpr):
            inner = self._infer_expr(expr.value)
            return TypeInfo(kind=TypeKind.OPTION, args=[inner])
        if isinstance(expr, OkExpr):
            inner = self._infer_expr(expr.value)
            return TypeInfo(kind=TypeKind.RESULT, args=[inner])
        if isinstance(expr, ErrExpr):
            inner = self._infer_expr(expr.value)
            return TypeInfo(kind=TypeKind.RESULT, args=[UNKNOWN_TYPE, inner])
        if isinstance(expr, SignalExpr):
            inner = self._infer_expr(expr.value)
            return TypeInfo(kind=TypeKind.SIGNAL, args=[inner])
        if isinstance(expr, AssignExpr):
            return self._check_assign(expr)
        if isinstance(expr, IfExpr):
            return self._check_if(expr)
        if isinstance(expr, MatchExpr):
            return self._check_match(expr)
        if isinstance(expr, NamespaceAccessExpr):
            return self._check_namespace_access(expr)
        # Fallback
        return UNKNOWN_TYPE

    # -- Binary ops -----------------------------------------------------

    def _check_binary(self, expr: BinaryExpr) -> TypeInfo:
        left = self._infer_expr(expr.left)
        right = self._infer_expr(expr.right)

        arithmetic_ops = {"+", "-", "*", "/", "%"}
        comparison_ops = {"<", ">", "<=", ">="}
        equality_ops = {"==", "!="}
        logical_ops = {"&&", "||"}

        # Dynamic `any` type: arithmetic on `any` is rejected until full runtime
        # dispatch is implemented. Comparisons/equality are allowed (always Bool).
        if left.kind == TypeKind.ANY or right.kind == TypeKind.ANY:
            if expr.op in arithmetic_ops:
                self._error(
                    f"Arithmetic on 'any' values is not yet supported: "
                    f"{_type_display(left)} {expr.op} {_type_display(right)}. "
                    f"Cast to a concrete type first.",
                    expr,
                )
                return ANY_TYPE
            if expr.op in comparison_ops or expr.op in equality_ops:
                return BOOL_TYPE
            if expr.op in logical_ops:
                return BOOL_TYPE

        # v4.69.0: Future<T> used in arithmetic → "did you forget to await?"
        if left.kind == TypeKind.FUTURE or right.kind == TypeKind.FUTURE:
            future_side = "left" if left.kind == TypeKind.FUTURE else "right"
            future_type = left if left.kind == TypeKind.FUTURE else right
            inner = future_type.args[0].display_name if future_type.args else "T"
            self._error(
                f"Cannot use Future<{inner}> in '{expr.op}' operation — "
                f"did you forget 'await'? Use 'await' to get the {inner} value.",
                expr,
            )
            return UNKNOWN_TYPE

        if expr.op in arithmetic_ops:
            # Tensor element-wise ops: Tensor +/-/*// Tensor -> Tensor
            if left.kind == TypeKind.TENSOR or right.kind == TypeKind.TENSOR:
                if left.kind not in _TENSOR_ARITH_KINDS:
                    self._error(
                        f"Operator '{expr.op}' not supported for "
                        f"types {_type_display(left)} and {_type_display(right)}",
                        expr,
                    )
                if right.kind not in _TENSOR_ARITH_KINDS:
                    self._error(
                        f"Operator '{expr.op}' not supported for "
                        f"types {_type_display(left)} and {_type_display(right)}",
                        expr,
                    )
                # Compile-time shape validation with broadcasting (v4.44.0)
                from mapanare.types import broadcast_incompatible_dim, broadcast_shape

                result_shape: tuple[int, ...] | None = None
                if left.kind == TypeKind.TENSOR and right.kind == TypeKind.TENSOR:
                    if left.tensor_shape is not None and right.tensor_shape is not None:
                        bcast = broadcast_shape(left.tensor_shape, right.tensor_shape)
                        if bcast is None:
                            bad_dim = broadcast_incompatible_dim(
                                left.tensor_shape, right.tensor_shape
                            )
                            dim_note = ""
                            if bad_dim is not None:
                                a_pad = (1,) * (
                                    max(len(left.tensor_shape), len(right.tensor_shape))
                                    - len(left.tensor_shape)
                                ) + left.tensor_shape
                                b_pad = (1,) * (
                                    max(len(left.tensor_shape), len(right.tensor_shape))
                                    - len(right.tensor_shape)
                                ) + right.tensor_shape
                                dim_note = (
                                    f"; dimension {bad_dim} differs: "
                                    f"{a_pad[bad_dim]} vs {b_pad[bad_dim]}"
                                )
                            self._error(
                                f"shapes {list(left.tensor_shape)} and "
                                f"{list(right.tensor_shape)} are not "
                                f"broadcast-compatible for '{expr.op}'"
                                f"{dim_note}",
                                expr,
                            )
                        else:
                            result_shape = bcast
                elif left.kind == TypeKind.TENSOR:
                    result_shape = left.tensor_shape  # scalar broadcasts to tensor shape
                else:
                    result_shape = right.tensor_shape
                elem_type = (
                    left.args[0]
                    if left.kind == TypeKind.TENSOR and left.args
                    else (
                        right.args[0]
                        if right.kind == TypeKind.TENSOR and right.args
                        else UNKNOWN_TYPE
                    )
                )
                return TypeInfo(kind=TypeKind.TENSOR, args=[elem_type], tensor_shape=result_shape)

            # List concatenation: List<T> + List<T> -> List<T>
            if expr.op == "+" and left.kind == TypeKind.LIST and right.kind == TypeKind.LIST:
                return left

            # Arithmetic trait dispatch for user-defined types
            if (
                expr.op in _OP_TO_TRAIT
                and left.kind in (TypeKind.STRUCT, TypeKind.ENUM)
                and left.name
                and self._type_implements_trait(left.name, _OP_TO_TRAIT[expr.op])
            ):
                expr.trait_dispatch = _OP_TO_TRAIT[expr.op].lower()
                return left  # Self -> Self

            if left.kind not in _ARITHMETIC_KINDS or right.kind not in _ARITHMETIC_KINDS:
                left_s = _type_display(left)
                right_s = _type_display(right)
                self._error(
                    f"Operator '{expr.op}' not supported for " f"types {left_s} and {right_s}",
                    expr,
                )
                return UNKNOWN_TYPE
            if expr.op == "+" and (left.kind == TypeKind.STRING or right.kind == TypeKind.STRING):
                return STRING_TYPE
            if left.kind == TypeKind.FLOAT or right.kind == TypeKind.FLOAT:
                return FLOAT_TYPE
            if left.kind == TypeKind.INT and right.kind == TypeKind.INT:
                return INT_TYPE
            return UNKNOWN_TYPE

        if expr.op in comparison_ops or expr.op in equality_ops:
            # Annotate trait dispatch: if the operand type implements Eq or Ord,
            # emitters can use the trait method instead of direct comparison.
            if left.kind in (TypeKind.STRUCT, TypeKind.ENUM) and left.name:
                if expr.op in equality_ops and self._type_implements_trait(left.name, "Eq"):
                    expr.trait_dispatch = "eq"
                elif expr.op in comparison_ops and self._type_implements_trait(left.name, "Ord"):
                    expr.trait_dispatch = "cmp"
            return BOOL_TYPE

        if expr.op in logical_ops:
            if left.kind not in (TypeKind.UNKNOWN, TypeKind.BOOL):
                self._error(
                    f"Operator '{expr.op}' requires Bool, got {_type_display(left)}",
                    expr,
                )
            if right.kind not in (TypeKind.UNKNOWN, TypeKind.BOOL):
                self._error(
                    f"Operator '{expr.op}' requires Bool, got {_type_display(right)}",
                    expr,
                )
            return BOOL_TYPE

        # Matrix multiply (@) — requires Tensor operands
        if expr.op == "@":
            if left.kind not in (TypeKind.UNKNOWN, TypeKind.TENSOR):
                self._error(
                    f"Operator '@' requires Tensor, got {_type_display(left)}",
                    expr,
                )
            if right.kind not in (TypeKind.UNKNOWN, TypeKind.TENSOR):
                self._error(
                    f"Operator '@' requires Tensor, got {_type_display(right)}",
                    expr,
                )
            # Compile-time shape validation for matmul
            matmul_shape: tuple[int, ...] | None = None
            if left.tensor_shape is not None and right.tensor_shape is not None:
                from mapanare.types import validate_matmul_shapes

                matmul_shape = validate_matmul_shapes(left.tensor_shape, right.tensor_shape)
                if matmul_shape is None:
                    self._error(
                        f"Matmul shape mismatch: "
                        f"{_type_display(left)} @ {_type_display(right)} — "
                        f"inner dimensions do not match",
                        expr,
                    )
            elem_type = left.args[0] if left.args else UNKNOWN_TYPE
            return TypeInfo(kind=TypeKind.TENSOR, args=[elem_type], tensor_shape=matmul_shape)

        return UNKNOWN_TYPE

    # -- Unary ops ------------------------------------------------------

    def _check_unary(self, expr: UnaryExpr) -> TypeInfo:
        operand = self._infer_expr(expr.operand)
        # Dynamic `any` passes through unary ops unchanged
        if operand.kind == TypeKind.ANY:
            return ANY_TYPE
        if expr.op == "-":
            if operand.kind not in (TypeKind.UNKNOWN, TypeKind.INT, TypeKind.FLOAT):
                self._error(
                    f"Unary '-' not supported for type {_type_display(operand)}",
                    expr,
                )
            return operand
        if expr.op == "!":
            if operand.kind not in (TypeKind.UNKNOWN, TypeKind.BOOL):
                self._error(
                    f"Unary '!' requires Bool, got {_type_display(operand)}",
                    expr,
                )
            return BOOL_TYPE
        return UNKNOWN_TYPE

    # -- Call expression ------------------------------------------------

    def _check_call(self, expr: CallExpr) -> TypeInfo:
        # Infer argument types
        arg_types = [self._infer_expr(a) for a in expr.args]

        # Handle generic call intrinsics (turbofish syntax)
        if isinstance(expr.callee, Identifier) and expr.type_args:
            name = expr.callee.name
            if name == "encode_struct":
                if len(expr.type_args) != 1:
                    self._error("encode_struct expects exactly one type argument", expr)
                if len(expr.args) != 1:
                    self._error("encode_struct expects exactly one argument", expr)
                return STRING_TYPE
            if name == "decode_to":
                if len(expr.type_args) != 1:
                    self._error("decode_to expects exactly one type argument", expr)
                if len(expr.args) != 1:
                    self._error("decode_to expects exactly one argument (JsonValue)", expr)
                type_arg = expr.type_args[0]
                type_name = type_arg.name if hasattr(type_arg, "name") else ""
                return TypeInfo(
                    kind=TypeKind.RESULT,
                    name="Result",
                    args=[
                        TypeInfo(kind=TypeKind.STRUCT, name=type_name),
                        TypeInfo(kind=TypeKind.STRUCT, name="JsonError"),
                    ],
                )
            if name == "__struct_meta":
                if len(expr.type_args) != 1:
                    self._error("__struct_meta expects exactly one type argument", expr)
                if len(expr.args) != 0:
                    self._error("__struct_meta takes no arguments", expr)
                return STRING_TYPE

        if isinstance(expr.callee, Identifier):
            sym = self.current_scope.lookup(expr.callee.name)
            if sym is None:
                self._error(f"Undefined function '{expr.callee.name}'", expr.callee)
                return UNKNOWN_TYPE
            if sym.kind == SymbolKind.FUNCTION:
                # println is deprecated — use print instead
                if expr.callee.name == "println":
                    self._warning(
                        "println is deprecated, use print instead",
                        expr,
                    )
                # Check for @deprecated decorator on the called function
                if sym.node is not None and isinstance(sym.node, FnDef):
                    for dec in sym.node.decorators:
                        if dec.name == "deprecated":
                            dep_msg = ""
                            if dec.args and hasattr(dec.args[0], "value"):
                                dep_msg = f": {dec.args[0].value}"
                            self._warning(
                                f"Function '{expr.callee.name}' is deprecated{dep_msg}",
                                expr,
                            )
                            break
                if sym.type_info.is_function and sym.type_info.return_type:
                    # Check argument count for non-builtin functions
                    if sym.type_info.param_types and len(arg_types) != len(
                        sym.type_info.param_types
                    ):
                        n_exp = len(sym.type_info.param_types)
                        n_got = len(arg_types)
                        fname = expr.callee.name
                        self._error(
                            f"Function '{fname}' expects " f"{n_exp} argument(s), got {n_got}",
                            expr,
                        )
                    # Check argument types (skip for type parameters —
                    # unknown param types indicate generic parameters that
                    # will be resolved during monomorphization)
                    for i, (expected, actual) in enumerate(
                        zip(sym.type_info.param_types, arg_types)
                    ):
                        if expected.kind == TypeKind.UNKNOWN:
                            continue  # Type parameter — accept any type
                        if not expected.is_compatible_with(actual):
                            fname = expr.callee.name
                            exp_s = _type_display(expected)
                            act_s = _type_display(actual)
                            self._error(
                                f"Argument {i + 1} of '{fname}' " f"expects {exp_s}, got {act_s}",
                                expr,
                            )
                    # Validate trait bounds on generic function calls
                    if sym.node and isinstance(sym.node, FnDef) and sym.node.trait_bounds:
                        self._check_trait_bounds_at_call(
                            sym.node, sym.type_info.param_types, arg_types, expr
                        )
                    return sym.type_info.return_type
                return UNKNOWN_TYPE
            if sym.kind == SymbolKind.AGENT:
                return TypeInfo(kind=TypeKind.AGENT, name=sym.name)
            if sym.kind == SymbolKind.STRUCT:
                return TypeInfo(kind=TypeKind.STRUCT, name=sym.name)
            # Calling a variable that might be a function type
            return UNKNOWN_TYPE

        # Method or other callee
        self._infer_expr(expr.callee)
        return UNKNOWN_TYPE

    # -- Assignment -----------------------------------------------------

    def _check_assign(self, expr: AssignExpr) -> TypeInfo:
        value_type = self._infer_expr(expr.value)

        if isinstance(expr.target, Identifier):
            sym = self.current_scope.lookup(expr.target.name)
            if sym is None:
                self._error(f"Undefined variable '{expr.target.name}'", expr.target)
                return UNKNOWN_TYPE
            if sym.kind == SymbolKind.CONST:
                self._error(
                    f"Cannot assign to const '{expr.target.name}'",
                    expr.target,
                )
            elif not sym.mutable:
                self._error(
                    f"Cannot assign to immutable variable '{expr.target.name}'",
                    expr.target,
                )
            # Type check: if both known, they should match
            if (
                sym.type_info.kind != TypeKind.UNKNOWN
                and value_type.kind != TypeKind.UNKNOWN
                and not sym.type_info.is_compatible_with(value_type)
            ):
                val_s = _type_display(value_type)
                var_s = _type_display(sym.type_info)
                self._error(
                    f"Cannot assign {val_s} to variable " f"'{expr.target.name}' of type {var_s}",
                    expr,
                )
            return VOID_TYPE
        # For field/index targets, just infer both sides
        self._infer_expr(expr.target)
        return VOID_TYPE

    # -- If / Match -----------------------------------------------------

    def _check_if(self, expr: IfExpr) -> TypeInfo:
        cond_type = self._infer_expr(expr.condition)
        if cond_type.kind not in (TypeKind.UNKNOWN, TypeKind.BOOL):
            self._error(
                f"If condition must be Bool, got {_type_display(cond_type)}",
                expr,
            )
        self._push_scope()
        self._check_block(expr.then_block)
        self._pop_scope()
        if isinstance(expr.else_block, Block):
            self._push_scope()
            self._check_block(expr.else_block)
            self._pop_scope()
        elif isinstance(expr.else_block, IfExpr):
            self._check_if(expr.else_block)
        return UNKNOWN_TYPE

    def _check_match(self, expr: MatchExpr) -> TypeInfo:
        subject_type = self._infer_expr(expr.subject)
        for arm in expr.arms:
            self._push_scope()
            self._bind_pattern(arm.pattern, subject_type)
            # v4.35.0: type-check optional guard (must be Bool)
            if arm.guard is not None:
                guard_type = self._infer_expr(arm.guard)
                if guard_type.kind not in (TypeKind.BOOL, TypeKind.UNKNOWN):
                    self._error("match guard must be a Bool expression", arm.guard)
            if isinstance(arm.body, Block):
                self._check_block(arm.body)
            elif isinstance(arm.body, Expr):
                self._infer_expr(arm.body)
            self._pop_scope()

        # Exhaustiveness check for enum subjects
        self._check_match_exhaustiveness(expr, subject_type)

        return UNKNOWN_TYPE

    def _check_match_exhaustiveness(self, expr: MatchExpr, subject_type: TypeInfo) -> None:
        """Error if a match is non-exhaustive; warn on unreachable arms.

        Uses Maranget decision-tree construction to detect missing patterns
        and unreachable arms. See docs/roadmap/v4/v4.34.0/DESIGN.md §8.
        """
        from mapanare.pattern_matching import (
            PatternMatrix,
            PatternRow,
            build_decision_tree,
            build_witness_for_switch,
            display_witness,
            find_unreachable_arms,
            has_any_fail,
        )

        ctx = self._semantic_type_context(subject_type)
        rows = [PatternRow(patterns=[arm.pattern], action_idx=i) for i, arm in enumerate(expr.arms)]
        matrix = PatternMatrix(rows=rows, type_contexts=[ctx])
        tree = build_decision_tree(matrix)

        # Check exhaustiveness
        if has_any_fail(tree):
            from mapanare.pattern_matching import DTSwitch

            if isinstance(tree, DTSwitch):
                witness = build_witness_for_switch(tree, ctx)
                if witness is not None:
                    wtext = display_witness(witness)
                    self._error(
                        f"non-exhaustive match: pattern `{wtext}` is not covered",
                        expr,
                    )
                    return
            # Fallback: generic message
            self._error("non-exhaustive match expression", expr)
            return

        # Check for unreachable arms
        unreachable = find_unreachable_arms(tree, len(expr.arms))
        for arm_idx in sorted(unreachable):
            self._warning(f"unreachable match arm (arm {arm_idx + 1})", expr.arms[arm_idx])

    _semantic_ctx_stack: set[str] | None = None

    def _semantic_type_context(self, ty: TypeInfo) -> object:
        """Build a TypeContext from a semantic TypeInfo for exhaustiveness checking."""
        from mapanare.pattern_matching import TypeContext

        # Cycle guard for recursive enum types (e.g., Expr containing Expr)
        if self._semantic_ctx_stack is None:
            self._semantic_ctx_stack = set()
        type_key = ty.name or ""
        if type_key and type_key in self._semantic_ctx_stack:
            return TypeContext(is_closed=False)
        if type_key:
            self._semantic_ctx_stack.add(type_key)
        try:
            return self._semantic_type_context_inner(ty)
        finally:
            if type_key:
                self._semantic_ctx_stack.discard(type_key)

    def _semantic_type_context_inner(self, ty: TypeInfo) -> object:
        from mapanare.pattern_matching import ConstructorInfo, TypeContext

        ctx = self._semantic_type_context

        if ty.kind == TypeKind.OPTION:
            some_sub = [ctx(ty.args[0])] if ty.args else []
            return TypeContext(
                is_closed=True,
                all_constructors=[ConstructorInfo("Some", 1), ConstructorInfo("None", 0)],
                sub_contexts={"Some": some_sub},
            )

        if ty.kind == TypeKind.RESULT:
            ok_sub = [ctx(ty.args[0])] if ty.args else []
            err_sub = [ctx(ty.args[1])] if len(ty.args) >= 2 else []
            return TypeContext(
                is_closed=True,
                all_constructors=[ConstructorInfo("Ok", 1), ConstructorInfo("Err", 1)],
                sub_contexts={"Ok": ok_sub, "Err": err_sub},
            )

        if ty.kind == TypeKind.ENUM and ty.name:
            sym = self.current_scope.lookup(ty.name)
            if sym is None:
                sym = self.global_scope.lookup(ty.name)
            if sym is not None and sym.node is not None and isinstance(sym.node, EnumDef):
                ctors: list[ConstructorInfo] = []
                sub_ctxs: dict[str, list[TypeContext]] = {}
                for variant in sym.node.variants:
                    arity = len(variant.fields)
                    ctors.append(ConstructorInfo(variant.name, arity))
                    if arity > 0:
                        field_types = [self._resolve_type_expr(f) for f in variant.fields]
                        sub_ctxs[variant.name] = [ctx(ft) for ft in field_types]
                return TypeContext(is_closed=True, all_constructors=ctors, sub_contexts=sub_ctxs)

        if ty.kind == TypeKind.BOOL:
            return TypeContext(
                is_closed=True,
                all_constructors=[ConstructorInfo("true", 0), ConstructorInfo("false", 0)],
            )

        return TypeContext(is_closed=False)

    def _bind_pattern(self, pattern: object, subject_type: TypeInfo | None = None) -> None:
        """Bind names introduced by a pattern into the current scope."""
        from mapanare.ast_nodes import (
            ConstructorPattern,
            IdentPattern,
            OrPattern,
        )

        if isinstance(pattern, IdentPattern):
            ty = subject_type if subject_type is not None else UNKNOWN_TYPE
            self.current_scope.define(
                pattern.name,
                Symbol(name=pattern.name, kind=SymbolKind.VARIABLE, type_info=ty),
            )
        elif isinstance(pattern, ConstructorPattern):
            field_types = self._resolve_variant_fields(subject_type, pattern.name)
            for i, arg in enumerate(pattern.args):
                arg_type = field_types[i] if i < len(field_types) else None
                self._bind_pattern(arg, arg_type)
        elif isinstance(pattern, OrPattern):
            # v4.35.0: verify all alternatives bind the same names, then bind
            all_names = [self._collect_pattern_names(alt) for alt in pattern.alternatives]
            ref = all_names[0]
            for i, names in enumerate(all_names[1:], 1):
                if names != ref:
                    missing = ref - names
                    extra = names - ref
                    parts = []
                    if missing:
                        parts.append(f"missing {sorted(missing)}")
                    if extra:
                        parts.append(f"extra {sorted(extra)}")
                    self._error(
                        f"or-pattern alternatives must bind the same names: {'; '.join(parts)}",
                        pattern.alternatives[i],
                    )
            # Bind from the first alternative (all have the same names)
            self._bind_pattern(pattern.alternatives[0], subject_type)

    def _collect_pattern_names(self, pattern: object) -> set[str]:
        """Collect all variable names bound by a pattern (excludes enum variants)."""
        from mapanare.ast_nodes import ConstructorPattern, IdentPattern, OrPattern

        names: set[str] = set()
        if isinstance(pattern, IdentPattern):
            # Check if the name is an enum variant; if so, it's not a binding
            if not self._is_enum_variant_name(pattern.name):
                names.add(pattern.name)
        elif isinstance(pattern, ConstructorPattern):
            for arg in pattern.args:
                names |= self._collect_pattern_names(arg)
        elif isinstance(pattern, OrPattern):
            if pattern.alternatives:
                names = self._collect_pattern_names(pattern.alternatives[0])
        return names

    def _is_enum_variant_name(self, name: str) -> bool:
        """Check if a name refers to an enum variant in any visible enum."""
        # Walk all symbols looking for enums with a matching variant
        for scope in (self.current_scope, self.global_scope):
            s = scope
            while s is not None:
                for sym in s.symbols.values():
                    if sym.kind == SymbolKind.ENUM and isinstance(sym.node, EnumDef):
                        for v in sym.node.variants:
                            if v.name == name:
                                return True
                s = s.parent
        return False

    def _resolve_variant_fields(
        self, subject_type: TypeInfo | None, variant_name: str
    ) -> list[TypeInfo]:
        """Look up the field types for an enum variant from the subject type."""
        if subject_type is None:
            return []
        # Builtin Result<T, E>
        if subject_type.kind == TypeKind.RESULT:
            if variant_name == "Ok" and len(subject_type.args) >= 1:
                return [subject_type.args[0]]
            if variant_name == "Err" and len(subject_type.args) >= 2:
                return [subject_type.args[1]]
            return [UNKNOWN_TYPE]
        # Builtin Option<T>
        if subject_type.kind == TypeKind.OPTION:
            if variant_name == "Some" and len(subject_type.args) >= 1:
                return [subject_type.args[0]]
            return [UNKNOWN_TYPE]
        # User-defined enum
        if subject_type.kind == TypeKind.ENUM and subject_type.name:
            sym = self.current_scope.lookup(subject_type.name)
            if sym is None:
                sym = self.global_scope.lookup(subject_type.name)
            if sym is not None and sym.node is not None and isinstance(sym.node, EnumDef):
                for variant in sym.node.variants:
                    if variant.name == variant_name:
                        return [self._resolve_type_expr(f) for f in variant.fields]
        return []

    # -- Namespace access -----------------------------------------------

    def _check_namespace_access(self, expr: NamespaceAccessExpr) -> TypeInfo:
        """Check `Module::member` access against resolved module exports."""
        ns = expr.namespace
        member = expr.member

        # Check if the namespace is a resolved module
        mod_exports = self._resolved_modules.get(ns)
        if mod_exports is not None:
            export = mod_exports.get(member)
            if export is None:
                self._error(f"'{member}' not found in module '{ns}'", expr)
                return UNKNOWN_TYPE
            # Return the type of the export
            defn = export.definition
            if isinstance(defn, FnDef):
                param_types = [self._resolve_type_expr(p.type_annotation) for p in defn.params]
                ret = self._resolve_type_expr(defn.return_type)
                return TypeInfo(
                    kind=TypeKind.FN,
                    is_function=True,
                    param_types=param_types,
                    return_type=ret,
                )
            elif isinstance(defn, StructDef):
                return TypeInfo(kind=TypeKind.STRUCT, name=member)
            elif isinstance(defn, EnumDef):
                return TypeInfo(kind=TypeKind.ENUM, name=member)
            elif isinstance(defn, AgentDef):
                return TypeInfo(kind=TypeKind.AGENT, name=member)
            return UNKNOWN_TYPE

        # Check if it's an enum variant access (EnumName::VariantName)
        sym = self.current_scope.lookup(ns)
        if sym is not None and sym.kind == SymbolKind.ENUM:
            return TypeInfo(kind=TypeKind.ENUM, name=ns)

        return UNKNOWN_TYPE

    # -- Lambda ---------------------------------------------------------

    def _check_lambda(self, expr: LambdaExpr) -> TypeInfo:
        self._push_scope()
        param_types: list[TypeInfo] = []
        for p in expr.params:
            pt = self._resolve_type_expr(p.type_annotation)
            param_types.append(pt)
            self.current_scope.define(
                p.name,
                Symbol(name=p.name, kind=SymbolKind.PARAM, type_info=pt),
            )
        if isinstance(expr.body, Block):
            self._check_block(expr.body)
            ret = UNKNOWN_TYPE
        else:
            ret = self._infer_expr(expr.body)
        self._pop_scope()
        return TypeInfo(
            kind=TypeKind.FN,
            is_function=True,
            param_types=param_types,
            return_type=ret,
        )

    # -- Tensor literal (v4.42.0) ------------------------------------------

    def _check_tensor_literal(self, expr: TensorLiteral) -> TypeInfo:
        """Type-check a tensor literal.

        Rules:
        1. Every element must be a scalar matching the declared element type.
        2. The shape inferred from nesting matches the annotation (if present).
        3. Empty tensors (shape contains a zero dim) are allowed.
        """
        from mapanare.types import resolve_shape_from_type

        # Resolve element type name to TypeInfo
        elem_name = getattr(expr.element_type, "name", "")
        if elem_name in ("Float", "float"):
            elem_ti = FLOAT_TYPE
        elif elem_name in ("Int", "int"):
            elem_ti = INT_TYPE
        elif elem_name in ("Bool", "bool"):
            elem_ti = BOOL_TYPE
        else:
            elem_ti = FLOAT_TYPE  # default for unknown

        # Type-check each element
        for e in expr.elements:
            inferred = self._infer_expr(e)
            # Allow int-to-float promotion in tensor context
            if elem_ti == FLOAT_TYPE and inferred.kind == TypeKind.INT:
                continue
            if inferred.kind not in (TypeKind.UNKNOWN, TypeKind.ANY, elem_ti.kind):
                self._error(
                    f"tensor element type mismatch: expected {elem_name}, " f"got {inferred}",
                    getattr(e, "span", expr.span),
                )

        shape_tuple = tuple(expr.shape) if expr.shape else None
        return TypeInfo(kind=TypeKind.TENSOR, args=[elem_ti], tensor_shape=shape_tuple)

    # -- Error propagation (`?` operator) ---------------------------------

    def _check_error_prop(self, expr: ErrorPropExpr) -> TypeInfo:
        """v4.33.0: type-check the `?` operator (error propagation).

        Rules:
        1. The inner expression must be Result<T, E> or Option<T>.
        2. The enclosing function must return a compatible type.
        3. On Result<T, E>: enclosing fn must return Result<_, E2> where
           E is compatible with E2 (equality for now — no implicit From).
        4. On Option<T>: enclosing fn must return Option<_>.
        5. `?` outside a function body is a compile error.
        """
        inner_type = self._infer_expr(expr.expr)

        # Check: must be inside a function
        if self._current_fn_return_type is None:
            self._error("`?` can only be used inside a function body", expr)
            return UNKNOWN_TYPE

        fn_ret = self._current_fn_return_type

        # Case 1: Result<T, E>
        if inner_type.kind == TypeKind.RESULT:
            ok_type = inner_type.args[0] if inner_type.args else UNKNOWN_TYPE
            if fn_ret.kind != TypeKind.RESULT:
                self._error(
                    f"`?` on a `Result` value requires the enclosing function "
                    f"`{self._current_fn_name}` to return `Result<_, _>`, "
                    f"but it returns `{fn_ret}`; use an explicit `match` instead",
                    expr,
                )
                return UNKNOWN_TYPE
            return ok_type

        # Case 2: Option<T>
        if inner_type.kind == TypeKind.OPTION:
            inner_val_type = inner_type.args[0] if inner_type.args else UNKNOWN_TYPE
            if fn_ret.kind != TypeKind.OPTION:
                self._error(
                    f"`?` on an `Option` value requires the enclosing function "
                    f"`{self._current_fn_name}` to return `Option<_>`, "
                    f"but it returns `{fn_ret}`; use `.unwrap_or(...)` or "
                    f"an explicit `match` instead",
                    expr,
                )
                return UNKNOWN_TYPE
            return inner_val_type

        # Case 3: unknown or unresolved — let it through for now so the
        # lowerer can handle it. This is the graceful-degradation path
        # for cases where type inference couldn't resolve the inner type.
        if inner_type.kind == TypeKind.UNKNOWN:
            return UNKNOWN_TYPE

        # Case 4: any other type — not valid for `?`
        self._error(
            f"`?` requires `Result<_, _>` or `Option<_>`, got `{inner_type}`; "
            f"the `?` operator only works on values that can be `Err` or `None`",
            expr,
        )
        return UNKNOWN_TYPE

    # -- Spawn / Send ---------------------------------------------------

    def _check_spawn(self, expr: SpawnExpr) -> TypeInfo:
        if isinstance(expr.callee, Identifier):
            sym = self.current_scope.lookup(expr.callee.name)
            if sym is None:
                self._error(f"Undefined agent '{expr.callee.name}'", expr.callee)
                return UNKNOWN_TYPE
            if sym.kind not in (SymbolKind.AGENT, SymbolKind.VARIABLE):
                # "variable" with unknown type may be an imported agent
                self._error(
                    f"'spawn' requires an agent, but '{expr.callee.name}' is a {sym.kind}",
                    expr.callee,
                )
            for a in expr.args:
                self._infer_expr(a)
            return TypeInfo(kind=TypeKind.AGENT, name=sym.name)
        for a in expr.args:
            self._infer_expr(a)
        return UNKNOWN_TYPE

    def _find_agent_def(self, type_name: str) -> AgentDef | None:
        """Look up an AgentDef by type name from the global scope."""
        sym = self.global_scope.lookup(type_name)
        if sym and sym.kind == SymbolKind.AGENT and sym.node and isinstance(sym.node, AgentDef):
            return sym.node
        return None

    def _check_send(self, expr: SendExpr) -> None:
        value_type = self._infer_expr(expr.value)
        self._infer_expr(expr.target)

        # If target is agent.input, check type compatibility
        if isinstance(expr.target, FieldAccessExpr) and isinstance(expr.target.object, Identifier):
            sym = self.current_scope.lookup(expr.target.object.name)
            if sym:
                # Resolve the agent definition from the variable's type
                agent_def: AgentDef | None = None
                if sym.kind == SymbolKind.AGENT and sym.node and isinstance(sym.node, AgentDef):
                    agent_def = sym.node
                elif sym.type_info.kind not in (
                    TypeKind.UNKNOWN,
                    TypeKind.FN,
                    TypeKind.BUILTIN_FN,
                ):
                    agent_def = self._find_agent_def(sym.type_info.name)

                if agent_def:
                    for inp in agent_def.inputs:
                        if inp.name == expr.target.field_name:
                            expected = self._resolve_type_expr(inp.type_annotation)
                            if (
                                expected.kind != TypeKind.UNKNOWN
                                and value_type.kind != TypeKind.UNKNOWN
                                and not expected.is_compatible_with(value_type)
                            ):
                                val_s = _type_display(value_type)
                                exp_s = _type_display(expected)
                                self._error(
                                    f"Cannot send {val_s} to "
                                    f"input '{inp.name}' of agent "
                                    f"'{agent_def.name}' "
                                    f"(expected {exp_s})",
                                    expr,
                                )
                            return

    # -- Pipe expression ------------------------------------------------

    def _check_pipe_expr(self, expr: PipeExpr) -> TypeInfo:
        left_type = self._infer_expr(expr.left)

        # The right side of pipe is typically a function/callable
        if isinstance(expr.right, Identifier):
            sym = self.current_scope.lookup(expr.right.name)
            if sym is None:
                self._error(f"Undefined function '{expr.right.name}'", expr.right)
                return UNKNOWN_TYPE
            if sym.kind == SymbolKind.FUNCTION and sym.type_info.is_function:
                # Check that piped value type matches first param
                if sym.type_info.param_types:
                    expected = sym.type_info.param_types[0]
                    if (
                        expected.kind != TypeKind.UNKNOWN
                        and left_type.kind != TypeKind.UNKNOWN
                        and expected != left_type
                    ):
                        lt_s = _type_display(left_type)
                        exp_s = _type_display(expected)
                        self._error(
                            f"Pipe type mismatch: {lt_s} piped "
                            f"to '{sym.name}' which expects "
                            f"{exp_s}",
                            expr,
                        )
                if sym.type_info.return_type:
                    return sym.type_info.return_type
            if sym.kind == SymbolKind.AGENT:
                return TypeInfo(kind=TypeKind.AGENT, name=sym.name)
            return UNKNOWN_TYPE
        if isinstance(expr.right, CallExpr):
            return self._check_call(expr.right)
        self._infer_expr(expr.right)
        return UNKNOWN_TYPE

    # -- Pipe definition ------------------------------------------------

    def _check_pipe_def(self, pipe: PipeDef) -> None:
        """Check pipe stage type compatibility."""
        if len(pipe.stages) < 2:
            return

        prev_output: TypeInfo = UNKNOWN_TYPE
        for stage in pipe.stages:
            if isinstance(stage, Identifier):
                sym = self.current_scope.lookup(stage.name)
                if sym is None:
                    self._error(f"Undefined stage '{stage.name}' in pipe '{pipe.name}'", stage)
                    prev_output = UNKNOWN_TYPE
                    continue

                if sym.kind == SymbolKind.AGENT and sym.node and isinstance(sym.node, AgentDef):
                    agent = sym.node
                    # Check input type matches previous output
                    if agent.inputs and prev_output.kind != TypeKind.UNKNOWN:
                        input_type = self._resolve_type_expr(agent.inputs[0].type_annotation)
                        if input_type.kind != TypeKind.UNKNOWN and input_type != prev_output:
                            it_s = _type_display(input_type)
                            po_s = _type_display(prev_output)
                            self._error(
                                f"Pipe type mismatch in "
                                f"'{pipe.name}': stage "
                                f"'{stage.name}' expects input "
                                f"{it_s} but receives {po_s}",
                                stage,
                            )
                    # Output type for next stage
                    if agent.outputs:
                        prev_output = self._resolve_type_expr(agent.outputs[0].type_annotation)
                    else:
                        prev_output = UNKNOWN_TYPE
                elif sym.kind == SymbolKind.FUNCTION and sym.type_info.is_function:
                    if sym.type_info.param_types and prev_output.kind != TypeKind.UNKNOWN:
                        expected = sym.type_info.param_types[0]
                        if expected.kind != TypeKind.UNKNOWN and expected != prev_output:
                            exp_s = _type_display(expected)
                            po_s = _type_display(prev_output)
                            self._error(
                                f"Pipe type mismatch in "
                                f"'{pipe.name}': stage "
                                f"'{stage.name}' expects "
                                f"{exp_s} but receives {po_s}",
                                stage,
                            )
                    prev_output = (
                        sym.type_info.return_type if sym.type_info.return_type else UNKNOWN_TYPE
                    )
                else:
                    prev_output = UNKNOWN_TYPE
            else:
                self._infer_expr(stage)
                prev_output = UNKNOWN_TYPE

    # -- Block / Statement checking -------------------------------------

    def _check_block(self, block: Block) -> None:
        for stmt in block.stmts:
            self._check_stmt(stmt)

    def _check_stmt(self, stmt: object) -> None:
        if isinstance(stmt, LetBinding):
            self._check_let(stmt)
        elif isinstance(stmt, ExprStmt):
            self._infer_expr(stmt.expr)
        elif isinstance(stmt, ReturnStmt):
            if stmt.value is not None:
                self._infer_expr(stmt.value)
        elif isinstance(stmt, ForLoop):
            self._check_for(stmt)
        elif isinstance(stmt, ForAwaitLoop):
            # v4.74.0: for await — must be inside async fn
            if not self._in_async:
                self._error("'for await' can only be used inside an 'async fn'", stmt)
            # Check the iterable expression
            self._infer_expr(stmt.iterable)
            self._push_scope()
            self.current_scope.define(
                stmt.var_name,
                Symbol(name=stmt.var_name, kind=SymbolKind.VARIABLE, type_info=UNKNOWN_TYPE),
            )
            self._check_block(stmt.body)
            self._pop_scope()
        elif isinstance(stmt, WhileLoop):
            self._check_while(stmt)
        elif isinstance(stmt, SignalDecl):
            self._check_signal_decl(stmt)
        elif isinstance(stmt, BreakStmt):
            pass  # break is valid in for/while loops
        elif isinstance(stmt, ContinueStmt):
            pass  # continue is valid in for/while loops
        elif isinstance(stmt, AssertStmt):
            self._infer_expr(stmt.condition)
            if stmt.message is not None:
                self._infer_expr(stmt.message)
        elif isinstance(stmt, PrintStmt):
            self._infer_expr(stmt.expr)
        elif isinstance(stmt, StreamDecl):
            self._check_stream_decl(stmt)

    def _check_let(self, let: LetBinding) -> None:
        value_type = self._infer_expr(let.value)
        ann_type = self._resolve_type_expr(let.type_annotation)

        # If both annotation and value type are known, check they match
        if (
            ann_type.kind != TypeKind.UNKNOWN
            and value_type.kind != TypeKind.UNKNOWN
            and not ann_type.is_compatible_with(value_type)
        ):
            ann_s = _type_display(ann_type)
            val_s = _type_display(value_type)
            self._error(
                f"Type mismatch: declared type {ann_s} " f"but initial value is {val_s}",
                let,
            )

        # Use annotation if available, otherwise inferred
        resolved = ann_type if ann_type.kind != TypeKind.UNKNOWN else value_type
        self.current_scope.define(
            let.name,
            Symbol(
                name=let.name,
                kind=SymbolKind.VARIABLE,
                type_info=resolved,
                mutable=let.mutable,
            ),
        )

    def _check_for(self, loop: ForLoop) -> None:
        iter_type = self._infer_expr(loop.iterable)
        # Infer element type from iterable: List<T> → T, Range → Int, String → Char
        if iter_type.kind == TypeKind.LIST and iter_type.args:
            elem_type = iter_type.args[0]
        elif iter_type.kind == TypeKind.RANGE:
            elem_type = INT_TYPE
        elif iter_type.kind == TypeKind.STRING:
            elem_type = CHAR_TYPE
        elif iter_type.kind == TypeKind.MAP and len(iter_type.args) >= 1:
            elem_type = iter_type.args[0]
        else:
            elem_type = UNKNOWN_TYPE
        self._push_scope()
        self.current_scope.define(
            loop.var_name,
            Symbol(name=loop.var_name, kind=SymbolKind.VARIABLE, type_info=elem_type),
        )
        self._check_block(loop.body)
        self._pop_scope()

    def _check_while(self, loop: WhileLoop) -> None:
        self._infer_expr(loop.condition)
        self._push_scope()
        self._check_block(loop.body)
        self._pop_scope()

    def _check_signal_decl(self, decl: SignalDecl) -> None:
        value_type = self._infer_expr(decl.value)
        ann_type = self._resolve_type_expr(decl.type_annotation)
        resolved = ann_type if ann_type.kind != TypeKind.UNKNOWN else value_type
        sig_type = TypeInfo(kind=TypeKind.SIGNAL, args=[resolved])
        self.current_scope.define(
            decl.name,
            Symbol(
                name=decl.name,
                kind=SymbolKind.VARIABLE,
                type_info=sig_type,
                mutable=decl.mutable,
            ),
        )

    def _check_stream_decl(self, decl: StreamDecl) -> None:
        value_type = self._infer_expr(decl.value)
        ann_type = self._resolve_type_expr(decl.type_annotation)
        resolved = ann_type if ann_type.kind != TypeKind.UNKNOWN else value_type
        stream_type = TypeInfo(kind=TypeKind.STREAM, args=[resolved])
        self.current_scope.define(
            decl.name,
            Symbol(name=decl.name, kind=SymbolKind.VARIABLE, type_info=stream_type),
        )

    # -- Constant folding (v4.55.0) --------------------------------------

    def _fold_constant(self, expr: Expr, depth: int = 0) -> ConstantValue | None:
        """Evaluate an expression at compile time. Returns None if not foldable."""
        if depth > 10:
            return None
        if isinstance(expr, IntLiteral):
            return expr.value
        if isinstance(expr, FloatLiteral):
            return expr.value
        if isinstance(expr, BoolLiteral):
            return expr.value
        if isinstance(expr, StringLiteral):
            return expr.value
        if isinstance(expr, Identifier):
            return self._const_table.get(expr.name)
        if isinstance(expr, BinaryExpr):
            left = self._fold_constant(expr.left, depth + 1)
            right = self._fold_constant(expr.right, depth + 1)
            if left is None or right is None:
                return None
            return self._fold_binop(left, expr.op, right)
        if isinstance(expr, UnaryExpr):
            operand = self._fold_constant(expr.operand, depth + 1)
            if operand is None:
                return None
            if expr.op == "-" and isinstance(operand, (int, float)):
                return -operand
            if expr.op == "!" and isinstance(operand, bool):
                return not operand
        return None

    @staticmethod
    def _fold_binop(left: ConstantValue, op: str, right: ConstantValue) -> ConstantValue | None:
        try:
            if op == "+" and isinstance(left, str) and isinstance(right, str):
                return left + right
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                if op == "+":
                    return left + right
                if op == "-":
                    return left - right
                if op == "*":
                    return left * right
                if op == "/" and right != 0:
                    return (
                        left // right
                        if isinstance(left, int) and isinstance(right, int)
                        else left / right
                    )
                if op == "%" and right != 0:
                    return left % right
        except (OverflowError, ZeroDivisionError):
            return None
        return None

    # -- Definition registration (first pass) ---------------------------

    def _register_definitions(self, program: Program) -> None:
        """First pass: register all top-level names so they can reference each other."""
        for defn in program.definitions:
            self._register_def(defn)

    def _register_def(self, defn: Definition) -> None:
        if isinstance(defn, FnDef):
            saved_tp = self._current_type_params
            self._current_type_params = set(defn.type_params) if defn.type_params else set()
            param_types = [self._resolve_type_expr(p.type_annotation) for p in defn.params]
            ret = self._resolve_type_expr(defn.return_type)
            self._current_type_params = saved_tp
            fn_type = TypeInfo(
                kind=TypeKind.FN,
                is_function=True,
                param_types=param_types,
                return_type=ret,
            )
            self.global_scope.define(
                defn.name,
                Symbol(name=defn.name, kind=SymbolKind.FUNCTION, type_info=fn_type, node=defn),
            )
        elif isinstance(defn, AsyncFnDef):
            # v4.69.0: register async fn — return type wrapped in Future<T>.
            # Calling an async fn returns Future<T>, not T directly.
            saved_tp = self._current_type_params
            self._current_type_params = set(defn.type_params) if defn.type_params else set()
            param_types = [self._resolve_type_expr(p.type_annotation) for p in defn.params]
            inner_ret = self._resolve_type_expr(defn.return_type)
            self._current_type_params = saved_tp
            # Wrap return type: async fn foo() -> T  =>  fn type returns Future<T>
            future_ret = TypeInfo(kind=TypeKind.FUTURE, name="Future", args=[inner_ret])
            fn_type = TypeInfo(
                kind=TypeKind.FN,
                is_function=True,
                param_types=param_types,
                return_type=future_ret,
            )
            self.global_scope.define(
                defn.name,
                Symbol(name=defn.name, kind=SymbolKind.FUNCTION, type_info=fn_type, node=defn),
            )
        elif isinstance(defn, AgentDef):
            self.global_scope.define(
                defn.name,
                Symbol(
                    name=defn.name,
                    kind=SymbolKind.AGENT,
                    type_info=TypeInfo(kind=TypeKind.AGENT, name=defn.name),
                    node=defn,
                ),
            )
        elif isinstance(defn, StructDef):
            self.global_scope.define(
                defn.name,
                Symbol(
                    name=defn.name,
                    kind=SymbolKind.STRUCT,
                    type_info=TypeInfo(kind=TypeKind.STRUCT, name=defn.name),
                    node=defn,
                ),
            )
        elif isinstance(defn, EnumDef):
            self.global_scope.define(
                defn.name,
                Symbol(
                    name=defn.name,
                    kind=SymbolKind.ENUM,
                    type_info=TypeInfo(kind=TypeKind.ENUM, name=defn.name),
                    node=defn,
                ),
            )
            # Register enum variants as constructors (both short and qualified names)
            for variant in defn.variants:
                if variant.fields:
                    # Variants with payloads are constructors (functions)
                    variant_sym = Symbol(
                        name=variant.name,
                        kind=SymbolKind.FUNCTION,
                        type_info=TypeInfo(
                            kind=TypeKind.FN,
                            is_function=True,
                            return_type=TypeInfo(kind=TypeKind.ENUM, name=defn.name),
                        ),
                    )
                else:
                    # Bare variants are values of the enum type
                    variant_sym = Symbol(
                        name=variant.name,
                        kind=SymbolKind.VARIABLE,
                        type_info=TypeInfo(kind=TypeKind.ENUM, name=defn.name),
                    )
                self.global_scope.define(variant.name, variant_sym)
                # Also register the qualified name (EnumName_VariantName)
                qualified = f"{defn.name}_{variant.name}"
                self.global_scope.define(
                    qualified,
                    Symbol(
                        name=qualified,
                        kind=SymbolKind.FUNCTION,
                        type_info=variant_sym.type_info,
                    ),
                )
        elif isinstance(defn, ExternFnDef):
            # v4.29.0: ``extern "Python" fn`` is removed. The feature was
            # added in v0.5.0 as a convenience but broke silently when
            # ``emit_python.py`` was deleted during the v4.2.0 emitter
            # consolidation; the resulting 79 test xfails were not flagged
            # until the v4.26.0 seven-reviewer panel. v4.27.0's
            # ``mapanare bind --lang python`` ships a real, maintained FFI
            # path (ctypes wrapper against the compiled ``.mn`` module),
            # so ``extern "Python"`` is redundant. Path B from v4.29.0
            # PLAN §2.1 deletes it.
            if defn.abi == "Python":
                self._error(
                    'extern "Python" fn was removed in v4.29.0. '
                    "For Python interop, compile your Mapanare module "
                    "normally and generate a Python binding with "
                    "`mapanare bind --lang python <module.mn>`. "
                    "The generated Python file imports a ctypes wrapper "
                    "around the compiled .mn, which is type-checked and "
                    "stays in sync with the Mapanare source.",
                    defn,
                )
            if defn.abi != "C":
                self._error(
                    f"Unsupported ABI '{defn.abi}'; only \"C\" is supported "
                    "(use `mapanare bind --lang python` for Python interop)",
                    defn,
                )
            param_types = [self._resolve_type_expr(p.type_annotation) for p in defn.params]
            ret = self._resolve_type_expr(defn.return_type)
            fn_type = TypeInfo(
                kind=TypeKind.FN,
                is_function=True,
                param_types=param_types,
                return_type=ret,
            )
            self.global_scope.define(
                defn.name,
                Symbol(name=defn.name, kind=SymbolKind.FUNCTION, type_info=fn_type, node=defn),
            )
        elif isinstance(defn, PipeDef):
            self.global_scope.define(
                defn.name,
                Symbol(
                    name=defn.name,
                    kind=SymbolKind.PIPE,
                    type_info=UNKNOWN_TYPE,
                    node=defn,
                ),
            )
        elif isinstance(defn, TypeAlias):
            resolved = self._resolve_type_expr(defn.type_expr)
            self.global_scope.define(
                defn.name,
                Symbol(name=defn.name, kind=SymbolKind.TYPE_ALIAS, type_info=resolved, node=defn),
            )
        elif isinstance(defn, TraitDef):
            self.global_scope.define(
                defn.name,
                Symbol(
                    name=defn.name,
                    kind=SymbolKind.TRAIT,
                    type_info=TypeInfo(kind=TypeKind.TRAIT, name=defn.name),
                    node=defn,
                ),
            )
        elif isinstance(defn, ImportDef):
            self._resolve_import(defn)
        elif isinstance(defn, ExportDef):
            if defn.definition:
                self._register_def(defn.definition)
        elif isinstance(defn, ImplDef):
            pass  # methods handled in second pass
        elif isinstance(defn, ModuleLetDef):
            ty = UNKNOWN_TYPE
            if defn.type_name == "Int":
                ty = TypeInfo(kind=TypeKind.INT)
            elif defn.type_name == "Float":
                ty = TypeInfo(kind=TypeKind.FLOAT)
            elif defn.type_name == "Bool":
                ty = TypeInfo(kind=TypeKind.BOOL)
            elif defn.type_name == "String":
                ty = TypeInfo(kind=TypeKind.STRING)
            self.global_scope.define(
                defn.name,
                Symbol(name=defn.name, kind=SymbolKind.VARIABLE, type_info=ty, node=defn),
            )
        elif isinstance(defn, ConstDef):
            # v4.55.0: real const — register with type, fold value, mark as const
            ty = self._resolve_type_expr(defn.type_expr) if defn.type_expr else UNKNOWN_TYPE
            folded = self._fold_constant(defn.value) if defn.value else None
            if defn.value and folded is None:
                self._error(
                    "const initializer must be a constant expression "
                    "(only literals, const references, and arithmetic on constants are allowed)",
                    defn,
                )
            if folded is not None:
                self._const_table[defn.name] = folded
            self.global_scope.define(
                defn.name,
                Symbol(
                    name=defn.name,
                    kind=SymbolKind.CONST,
                    type_info=ty,
                    node=defn,
                    const_value=folded,
                ),
            )
        elif isinstance(defn, DocComment):
            if defn.definition:
                self._register_def(defn.definition)

    # -- Import resolution -----------------------------------------------

    def _resolve_import(self, defn: ImportDef) -> None:
        """Resolve an import, registering symbols from the imported module."""
        if self.resolver is None:
            # No resolver — fall back to registering names with UNKNOWN_TYPE
            # (for backward compatibility with single-file checks)
            if defn.items:
                for item in defn.items:
                    self.global_scope.define(
                        item,
                        Symbol(name=item, kind=SymbolKind.VARIABLE, type_info=UNKNOWN_TYPE),
                    )
            else:
                mod_name = defn.path[-1] if defn.path else ""
                if mod_name:
                    self.global_scope.define(
                        mod_name,
                        Symbol(
                            name=mod_name,
                            kind=SymbolKind.MODULE,
                            type_info=UNKNOWN_TYPE,
                        ),
                    )
            return

        from mapanare.modules import ModuleResolutionError

        try:
            resolved = self.resolver.resolve_module(defn.path, self.filename)
        except ModuleResolutionError as e:
            self._error(str(e), defn)
            return

        # Recursively type-check the imported module
        sub_checker = SemanticChecker(filename=resolved.filepath, resolver=self.resolver)
        sub_errors = sub_checker.check(resolved.program)
        self.errors.extend(sub_errors)
        if any(e.severity != "warning" for e in sub_errors):
            return

        mod_name = defn.path[-1] if defn.path else ""

        if defn.items:
            # Selective import: `import foo { bar, baz }`
            for item in defn.items:
                export = resolved.exports.get(item)
                if export is None:
                    self._error(
                        f"'{item}' not found in module '{mod_name}'",
                        defn,
                    )
                    continue
                if not export.public:
                    self._error(
                        f"'{item}' is not public in module '{mod_name}'",
                        defn,
                    )
                    continue
                # Register the imported definition in the current scope
                self._register_imported_def(item, export)
        else:
            # Full module import: `import foo` — register as module
            self._resolved_modules[mod_name] = {
                name: exp for name, exp in resolved.exports.items() if exp.public
            }
            self.global_scope.define(
                mod_name,
                Symbol(
                    name=mod_name,
                    kind=SymbolKind.MODULE,
                    type_info=TypeInfo(kind=TypeKind.STRUCT, name=mod_name),
                ),
            )
            # For `self::` imports, also register all exports directly into scope
            # (same compilation unit — no visibility barrier)
            is_self_import = defn.path and defn.path[0] == "self"
            for exp_name, exp in resolved.exports.items():
                if exp.public or is_self_import:
                    self._register_imported_def(exp_name, exp)

    def _register_imported_def(self, name: str, export: ModuleExport) -> None:
        """Register an imported symbol from a resolved module export."""
        defn = export.definition
        if isinstance(defn, FnDef):
            param_types = [self._resolve_type_expr(p.type_annotation) for p in defn.params]
            ret = self._resolve_type_expr(defn.return_type)
            fn_type = TypeInfo(
                kind=TypeKind.FN,
                is_function=True,
                param_types=param_types,
                return_type=ret,
            )
            self.global_scope.define(
                name,
                Symbol(name=name, kind=SymbolKind.FUNCTION, type_info=fn_type, node=defn),
            )
        elif isinstance(defn, AgentDef):
            self.global_scope.define(
                name,
                Symbol(
                    name=name,
                    kind=SymbolKind.AGENT,
                    type_info=TypeInfo(kind=TypeKind.AGENT, name=name),
                    node=defn,
                ),
            )
        elif isinstance(defn, StructDef):
            self.global_scope.define(
                name,
                Symbol(
                    name=name,
                    kind=SymbolKind.STRUCT,
                    type_info=TypeInfo(kind=TypeKind.STRUCT, name=name),
                    node=defn,
                ),
            )
        elif isinstance(defn, EnumDef):
            self.global_scope.define(
                name,
                Symbol(
                    name=name,
                    kind=SymbolKind.ENUM,
                    type_info=TypeInfo(kind=TypeKind.ENUM, name=name),
                    node=defn,
                ),
            )
            # Also register enum variants
            for variant in defn.variants:
                self.global_scope.define(
                    variant.name,
                    Symbol(
                        name=variant.name,
                        kind=SymbolKind.FUNCTION,
                        type_info=TypeInfo(
                            kind=TypeKind.FN,
                            is_function=True,
                            return_type=TypeInfo(kind=TypeKind.ENUM, name=name),
                        ),
                    ),
                )
        elif isinstance(defn, PipeDef):
            self.global_scope.define(
                name,
                Symbol(name=name, kind=SymbolKind.PIPE, type_info=UNKNOWN_TYPE, node=defn),
            )
        elif isinstance(defn, TypeAlias):
            resolved_type = self._resolve_type_expr(defn.type_expr)
            self.global_scope.define(
                name,
                Symbol(name=name, kind=SymbolKind.TYPE_ALIAS, type_info=resolved_type, node=defn),
            )
        else:
            # Fallback — register as unknown
            self.global_scope.define(
                name,
                Symbol(name=name, kind=SymbolKind.VARIABLE, type_info=UNKNOWN_TYPE),
            )

    # -- Definition checking (second pass) ------------------------------

    def _check_definitions(self, program: Program) -> None:
        """Second pass: check bodies of all definitions."""
        for defn in program.definitions:
            self._check_def(defn)

    def _check_def(self, defn: Definition) -> None:
        if isinstance(defn, FnDef):
            self._check_fn(defn)
        elif isinstance(defn, AsyncFnDef):
            # v4.69.0: check body with async context active.
            self._check_async_fn(defn)
        elif isinstance(defn, ExternFnDef):
            pass  # No body to check; registration handled in first pass
        elif isinstance(defn, AgentDef):
            self._check_agent(defn)
        elif isinstance(defn, PipeDef):
            self._check_pipe_def(defn)
        elif isinstance(defn, TraitDef):
            self._check_trait(defn)
        elif isinstance(defn, ImplDef):
            self._check_impl(defn)
        elif isinstance(defn, ExportDef):
            if defn.definition:
                self._check_def(defn.definition)
        elif isinstance(defn, DocComment):
            if defn.definition:
                self._check_def(defn.definition)

    def _check_fn(self, fn: FnDef) -> None:
        # Validate decorators (Phase 5.2)
        self._check_decorators(fn)
        saved_type_params = self._current_type_params
        self._current_type_params = set(fn.type_params) if fn.type_params else set()
        # v4.33.0: track the enclosing function's return type for `?` operator
        saved_fn_return = self._current_fn_return_type
        saved_fn_name = self._current_fn_name
        self._current_fn_return_type = self._resolve_type_expr(fn.return_type)
        self._current_fn_name = fn.name
        self._push_scope()
        for p in fn.params:
            pt = self._resolve_type_expr(p.type_annotation)
            self.current_scope.define(
                p.name,
                Symbol(name=p.name, kind=SymbolKind.PARAM, type_info=pt),
            )
        self._check_block(fn.body)
        self._pop_scope()
        self._current_type_params = saved_type_params
        self._current_fn_return_type = saved_fn_return
        self._current_fn_name = saved_fn_name

    def _check_async_fn(self, fn: AsyncFnDef) -> None:  # type: ignore[override]
        """v4.69.0: check an async fn body with async context active."""
        saved_in_async = self._in_async
        self._in_async = True
        self._check_fn(fn)  # type: ignore[arg-type]
        self._in_async = saved_in_async

    def _check_decorators(self, defn: ASTNode) -> None:
        """Validate decorator annotations on a definition (Phase 5.2)."""
        from mapanare.types import DEVICE_ANNOTATIONS

        decorators: list[object] = getattr(defn, "decorators", [])
        if not decorators:
            return

        device_count = 0
        for dec in decorators:
            if hasattr(dec, "name") and dec.name in DEVICE_ANNOTATIONS:
                device_count += 1
                if device_count > 1:
                    self._error(
                        f"Multiple device annotations on the same definition "
                        f"(@{dec.name}); use only one of @cpu, @gpu, @cuda, @metal, @vulkan",
                        defn,
                    )

    def _check_agent(self, agent: AgentDef) -> None:
        # Validate decorators (Phase 5.2)
        self._check_decorators(agent)
        self._push_scope()

        # Register self
        self.current_scope.define(
            "self",
            Symbol(
                name="self",
                kind=SymbolKind.VARIABLE,
                type_info=TypeInfo(kind=TypeKind.AGENT, name=agent.name),
            ),
        )

        # Validate input/output types exist
        for inp in agent.inputs:
            inp_type = self._resolve_type_expr(inp.type_annotation)
            if inp_type.kind != TypeKind.UNKNOWN and not self._type_exists(inp_type):
                self._error(
                    f"Unknown type '{inp_type.display_name}' for input '{inp.name}'",
                    inp,
                )
            self.current_scope.define(
                inp.name,
                Symbol(name=inp.name, kind=SymbolKind.VARIABLE, type_info=inp_type),
            )

        for out in agent.outputs:
            out_type = self._resolve_type_expr(out.type_annotation)
            if out_type.kind != TypeKind.UNKNOWN and not self._type_exists(out_type):
                self._error(
                    f"Unknown type '{out_type.display_name}' for output '{out.name}'",
                    out,
                )
            self.current_scope.define(
                out.name,
                Symbol(name=out.name, kind=SymbolKind.VARIABLE, type_info=out_type),
            )

        # State bindings
        for state in agent.state:
            self._check_let(state)

        # Methods
        for method in agent.methods:
            self._check_fn(method)

        self._pop_scope()

    def _check_trait(self, trait: TraitDef) -> None:
        """Check trait method signatures for valid types."""
        for method in trait.methods:
            for param in method.params:
                if param.type_annotation is not None:
                    self._resolve_type_expr(param.type_annotation)
            if method.return_type is not None:
                self._resolve_type_expr(method.return_type)

    def _check_impl(self, impl: ImplDef) -> None:
        sym = self.current_scope.lookup(impl.target)
        if sym is None:
            self._error_at(f"Undefined type '{impl.target}' in impl block", 0, 0)

        # If this is a trait impl, verify all trait methods are implemented
        if impl.trait_name is not None:
            trait_sym = self.current_scope.lookup(impl.trait_name)
            if trait_sym is None or trait_sym.kind != SymbolKind.TRAIT:
                self._error_at(f"Undefined trait '{impl.trait_name}' in impl block", 0, 0)
            elif trait_sym.node is not None and isinstance(trait_sym.node, TraitDef):
                trait_def = trait_sym.node
                impl_method_names = {m.name for m in impl.methods}
                trait_method_names = {m.name for m in trait_def.methods}

                # Check for missing methods
                for tm in trait_def.methods:
                    if tm.name not in impl_method_names:
                        self._error_at(
                            f"Missing implementation of '{tm.name}' "
                            f"from trait '{impl.trait_name}' for type '{impl.target}'",
                            0,
                            0,
                        )

                # Check for extra methods not in trait
                has_errors = False
                for m in impl.methods:
                    if m.name not in trait_method_names:
                        self._error_at(
                            f"Method '{m.name}' is not defined in trait '{impl.trait_name}'",
                            0,
                            0,
                        )
                        has_errors = True

                # Register successful trait impl
                if not has_errors and not any(
                    tm.name not in impl_method_names for tm in trait_def.methods
                ):
                    self._trait_impls.add((impl.trait_name, impl.target))

        for method in impl.methods:
            self._check_fn(method)

    def _type_implements_trait(self, type_name: str, trait_name: str) -> bool:
        """Check if a type has an impl for the given trait."""
        return (trait_name, type_name) in self._trait_impls

    def _check_trait_bounds_at_call(
        self,
        fn_def: FnDef,
        param_types: list[TypeInfo],
        arg_types: list[TypeInfo],
        expr: CallExpr,
    ) -> None:
        """Validate trait bounds when calling a generic function."""
        # Build type parameter → concrete type mapping from arguments
        tp_set = set(fn_def.type_params)
        subst: dict[str, TypeInfo] = {}
        for pt, at in zip(param_types, arg_types):
            if pt.kind == TypeKind.UNKNOWN and pt.name in tp_set:
                subst[pt.name] = at

        # Check each trait bound
        for tp_name, trait_name in fn_def.trait_bounds.items():
            if tp_name not in subst:
                continue
            concrete = subst[tp_name]
            concrete_name = concrete.name or _type_display(concrete)
            # Built-in types have implicit trait implementations
            _BUILTIN_IMPLS: dict[str, set[str]] = {
                "Int": {"Eq", "Ord", "Hash", "Display"},
                "Float": {"Eq", "Ord", "Display"},
                "String": {"Eq", "Ord", "Hash", "Display"},
                "Bool": {"Eq", "Hash", "Display"},
            }
            builtin_traits = _BUILTIN_IMPLS.get(concrete_name, set())
            if trait_name in builtin_traits:
                continue
            if not self._type_implements_trait(concrete_name, trait_name):
                self._error(
                    f"Type '{concrete_name}' does not implement trait "
                    f"'{trait_name}' required by type parameter '{tp_name}'",
                    expr,
                )

    def _type_exists(self, t: TypeInfo) -> bool:
        """Check if a type is known (primitive, builtin generic, or user-defined)."""
        if t.kind in PRIMITIVE_KINDS or t.kind in BUILTIN_GENERIC_KINDS:
            return True
        if t.kind in (
            TypeKind.STRUCT,
            TypeKind.ENUM,
            TypeKind.AGENT,
            TypeKind.TYPE_ALIAS,
            TypeKind.TRAIT,
        ):
            sym = self.global_scope.lookup(t.name)
            return sym is not None and sym.kind in (
                SymbolKind.STRUCT,
                SymbolKind.ENUM,
                SymbolKind.AGENT,
                SymbolKind.TYPE_ALIAS,
                SymbolKind.TRAIT,
            )
        return False

    # -- Public API -----------------------------------------------------

    def check(self, program: Program) -> list[SemanticError]:
        """Run semantic analysis on a program. Returns list of errors."""
        self._register_definitions(program)
        self._check_definitions(program)
        return self.errors


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


def check(
    program: Program,
    *,
    filename: str = "<input>",
    resolver: ModuleResolver | None = None,
) -> list[SemanticError]:
    """Run semantic analysis on a program.

    Args:
        program: The AST Program node to check.
        filename: Filename used in error messages.
        resolver: Optional module resolver for multi-file compilation.

    Returns:
        A list of SemanticError objects. Empty list means no errors.
    """
    checker = SemanticChecker(filename=filename, resolver=resolver)
    return checker.check(program)


def check_or_raise(
    program: Program,
    *,
    filename: str = "<input>",
    resolver: ModuleResolver | None = None,
    werror: bool = False,
) -> None:
    """Run semantic analysis and raise if there are errors.

    Args:
        program: The AST Program node to check.
        filename: Filename used in error messages.
        resolver: Optional module resolver for multi-file compilation.
        werror: If True, treat warnings as errors.

    Raises:
        SemanticErrors: If any semantic errors are found.
    """
    all_issues = check(program, filename=filename, resolver=resolver)
    if werror:
        # Promote warnings to errors
        errors = [
            (
                SemanticError(
                    message=e.message,
                    line=e.line,
                    column=e.column,
                    filename=e.filename,
                    severity="error",
                )
                if e.severity == "warning"
                else e
            )
            for e in all_issues
        ]
    else:
        errors = [e for e in all_issues if e.severity != "warning"]
    if errors:
        raise SemanticErrors(errors)
