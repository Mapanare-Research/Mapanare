"""Semantic analysis -- type checking and scope resolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mapanare.modules import ModuleExport, ModuleResolver

from mapanare.ast_nodes import (
    AgentDef,
    AssertStmt,
    AssignExpr,
    ASTNode,
    BinaryExpr,
    Block,
    BoolLiteral,
    BreakStmt,
    CallExpr,
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
    TensorType,
    TraitDef,
    TypeAlias,
    TypeExpr,
    UnaryExpr,
    WhileLoop,
)
from mapanare.types import (
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
# Semantic error
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SemanticError:
    """A single semantic error with source location."""

    message: str
    line: int = 0
    column: int = 0
    filename: str = "<input>"
    severity: str = "error"

    def __str__(self) -> str:
        prefix = "warning" if self.severity == "warning" else "error"
        return f"{self.filename}:{self.line}:{self.column}: {prefix}: {self.message}"


class SemanticErrors(Exception):
    """Raised when semantic analysis finds errors."""

    def __init__(self, errors: list[SemanticError]) -> None:
        self.errors = errors
        msgs = "\n".join(str(e) for e in errors)
        super().__init__(f"Semantic analysis found {len(errors)} error(s):\n{msgs}")


# ---------------------------------------------------------------------------
# Symbol table / Scope
# ---------------------------------------------------------------------------


@dataclass
class Symbol:
    """A declared symbol (variable, function, type, agent, etc.)."""

    name: str
    kind: str  # "variable", "function", "agent", "struct", "enum",
    # "type_alias", "pipe", "param", "trait"
    type_info: TypeInfo = field(default_factory=lambda: UNKNOWN_TYPE)
    mutable: bool = False
    node: ASTNode | None = None


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
_ARITHMETIC_KINDS = frozenset({TypeKind.INT, TypeKind.FLOAT, TypeKind.STRING, TypeKind.UNKNOWN})
_TENSOR_ARITH_KINDS = frozenset({TypeKind.UNKNOWN, TypeKind.TENSOR, TypeKind.INT, TypeKind.FLOAT})


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
                    kind="trait",
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
                    kind="function",
                    type_info=TypeInfo(
                        kind=TypeKind.BUILTIN_FN,
                        is_function=True,
                        return_type=ret_type,
                    ),
                ),
            )

    # -- Error helpers --------------------------------------------------

    def _error(self, message: str, node: ASTNode) -> None:
        self.errors.append(
            SemanticError(
                message=message,
                line=node.span.line,
                column=node.span.column,
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
            k = kind_from_name(te.name)
            if k != TypeKind.UNKNOWN:
                return TypeInfo(kind=k)
            # User-defined type — look up in scope to determine kind
            sym = self.global_scope.lookup(te.name)
            if sym is not None:
                if sym.kind == "struct":
                    return TypeInfo(kind=TypeKind.STRUCT, name=te.name)
                elif sym.kind == "enum":
                    return TypeInfo(kind=TypeKind.ENUM, name=te.name)
                elif sym.kind == "agent":
                    return TypeInfo(kind=TypeKind.AGENT, name=te.name)
                elif sym.kind == "type_alias":
                    return sym.type_info
            # Unknown user type — default to struct-like
            return TypeInfo(kind=TypeKind.STRUCT, name=te.name)
        if isinstance(te, GenericType):
            args = [self._resolve_type_expr(a) for a in te.args]
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
            if sym and sym.kind == "agent" and sym.node and isinstance(sym.node, AgentDef):
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
            obj_type = self._infer_expr(expr.object)
            self._infer_expr(expr.index)
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
        if isinstance(expr, SendExpr):
            self._check_send(expr)
            return VOID_TYPE
        if isinstance(expr, ErrorPropExpr):
            self._infer_expr(expr.expr)
            return UNKNOWN_TYPE
        if isinstance(expr, ListLiteral):
            if expr.elements:
                elem_type = self._infer_expr(expr.elements[0])
                for e in expr.elements[1:]:
                    self._infer_expr(e)
                return TypeInfo(kind=TypeKind.LIST, args=[elem_type])
            return TypeInfo(kind=TypeKind.LIST, args=[UNKNOWN_TYPE])
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
                if sym.kind == "struct":
                    return TypeInfo(kind=TypeKind.STRUCT, name=expr.name)
                elif sym.kind == "enum":
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
                # Compile-time shape validation for element-wise ops
                result_shape: tuple[int, ...] | None = None
                if left.kind == TypeKind.TENSOR and right.kind == TypeKind.TENSOR:
                    if left.tensor_shape is not None and right.tensor_shape is not None:
                        if left.tensor_shape != right.tensor_shape:
                            self._error(
                                f"Shape mismatch for element-wise '{expr.op}': "
                                f"{_type_display(left)} vs {_type_display(right)}",
                                expr,
                            )
                        else:
                            result_shape = left.tensor_shape
                elif left.kind == TypeKind.TENSOR:
                    result_shape = left.tensor_shape
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
                    expr.trait_dispatch = "eq"  # type: ignore[attr-defined]
                elif expr.op in comparison_ops and self._type_implements_trait(left.name, "Ord"):
                    expr.trait_dispatch = "cmp"  # type: ignore[attr-defined]
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

        if isinstance(expr.callee, Identifier):
            sym = self.current_scope.lookup(expr.callee.name)
            if sym is None:
                self._error(f"Undefined function '{expr.callee.name}'", expr.callee)
                return UNKNOWN_TYPE
            if sym.kind == "function":
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
                    # Check argument types
                    for i, (expected, actual) in enumerate(
                        zip(sym.type_info.param_types, arg_types)
                    ):
                        if not expected.is_compatible_with(actual):
                            fname = expr.callee.name
                            exp_s = _type_display(expected)
                            act_s = _type_display(actual)
                            self._error(
                                f"Argument {i + 1} of '{fname}' " f"expects {exp_s}, got {act_s}",
                                expr,
                            )
                    return sym.type_info.return_type
                return UNKNOWN_TYPE
            if sym.kind == "agent":
                return TypeInfo(kind=TypeKind.AGENT, name=sym.name)
            if sym.kind == "struct":
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
            if not sym.mutable:
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
            if isinstance(arm.body, Block):
                self._check_block(arm.body)
            elif isinstance(arm.body, Expr):
                self._infer_expr(arm.body)
            self._pop_scope()

        # Exhaustiveness check for enum subjects
        self._check_match_exhaustiveness(expr, subject_type)

        return UNKNOWN_TYPE

    def _check_match_exhaustiveness(self, expr: MatchExpr, subject_type: TypeInfo) -> None:
        """Error if a match on an enum type does not cover all variants."""
        from mapanare.ast_nodes import ConstructorPattern, IdentPattern, WildcardPattern

        if subject_type.kind != TypeKind.ENUM or not subject_type.name:
            return

        # Look up the enum definition to get all variant names
        sym = self.current_scope.lookup(subject_type.name)
        if sym is None or sym.node is None or not isinstance(sym.node, EnumDef):
            return

        all_variants = {v.name for v in sym.node.variants}

        # Check for wildcard patterns — if any arm has a wildcard, the match
        # is trivially exhaustive
        has_wildcard = False
        covered_variants: set[str] = set()
        for arm in expr.arms:
            if isinstance(arm.pattern, WildcardPattern):
                has_wildcard = True
                break
            if isinstance(arm.pattern, ConstructorPattern):
                covered_variants.add(arm.pattern.name)
            elif isinstance(arm.pattern, IdentPattern) and arm.pattern.name in all_variants:
                covered_variants.add(arm.pattern.name)

        if has_wildcard:
            return

        missing = all_variants - covered_variants
        if missing:
            names = ", ".join(sorted(missing))
            self._error(
                f"Non-exhaustive match on '{subject_type.name}': " f"missing variant(s) {names}",
                expr,
            )

    def _bind_pattern(self, pattern: object, subject_type: TypeInfo | None = None) -> None:
        """Bind names introduced by a pattern into the current scope."""
        from mapanare.ast_nodes import (
            ConstructorPattern,
            IdentPattern,
        )

        if isinstance(pattern, IdentPattern):
            ty = subject_type if subject_type is not None else UNKNOWN_TYPE
            self.current_scope.define(
                pattern.name,
                Symbol(name=pattern.name, kind="variable", type_info=ty),
            )
        elif isinstance(pattern, ConstructorPattern):
            field_types = self._resolve_variant_fields(subject_type, pattern.name)
            for i, arg in enumerate(pattern.args):
                arg_type = field_types[i] if i < len(field_types) else None
                self._bind_pattern(arg, arg_type)

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
        if sym is not None and sym.kind == "enum":
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
                Symbol(name=p.name, kind="param", type_info=pt),
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

    # -- Spawn / Send ---------------------------------------------------

    def _check_spawn(self, expr: SpawnExpr) -> TypeInfo:
        if isinstance(expr.callee, Identifier):
            sym = self.current_scope.lookup(expr.callee.name)
            if sym is None:
                self._error(f"Undefined agent '{expr.callee.name}'", expr.callee)
                return UNKNOWN_TYPE
            if sym.kind not in ("agent", "variable"):
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
        if sym and sym.kind == "agent" and sym.node and isinstance(sym.node, AgentDef):
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
                if sym.kind == "agent" and sym.node and isinstance(sym.node, AgentDef):
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
            if sym.kind == "function" and sym.type_info.is_function:
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
            if sym.kind == "agent":
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

                if sym.kind == "agent" and sym.node and isinstance(sym.node, AgentDef):
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
                elif sym.kind == "function" and sym.type_info.is_function:
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
                kind="variable",
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
            Symbol(name=loop.var_name, kind="variable", type_info=elem_type),
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
            Symbol(name=decl.name, kind="variable", type_info=sig_type, mutable=decl.mutable),
        )

    def _check_stream_decl(self, decl: StreamDecl) -> None:
        value_type = self._infer_expr(decl.value)
        ann_type = self._resolve_type_expr(decl.type_annotation)
        resolved = ann_type if ann_type.kind != TypeKind.UNKNOWN else value_type
        stream_type = TypeInfo(kind=TypeKind.STREAM, args=[resolved])
        self.current_scope.define(
            decl.name,
            Symbol(name=decl.name, kind="variable", type_info=stream_type),
        )

    # -- Definition registration (first pass) ---------------------------

    def _register_definitions(self, program: Program) -> None:
        """First pass: register all top-level names so they can reference each other."""
        for defn in program.definitions:
            self._register_def(defn)

    def _register_def(self, defn: Definition) -> None:
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
                defn.name,
                Symbol(name=defn.name, kind="function", type_info=fn_type, node=defn),
            )
        elif isinstance(defn, AgentDef):
            self.global_scope.define(
                defn.name,
                Symbol(
                    name=defn.name,
                    kind="agent",
                    type_info=TypeInfo(kind=TypeKind.AGENT, name=defn.name),
                    node=defn,
                ),
            )
        elif isinstance(defn, StructDef):
            self.global_scope.define(
                defn.name,
                Symbol(
                    name=defn.name,
                    kind="struct",
                    type_info=TypeInfo(kind=TypeKind.STRUCT, name=defn.name),
                    node=defn,
                ),
            )
        elif isinstance(defn, EnumDef):
            self.global_scope.define(
                defn.name,
                Symbol(
                    name=defn.name,
                    kind="enum",
                    type_info=TypeInfo(kind=TypeKind.ENUM, name=defn.name),
                    node=defn,
                ),
            )
            # Register enum variants as constructors (both short and qualified names)
            for variant in defn.variants:
                variant_sym = Symbol(
                    name=variant.name,
                    kind="function",
                    type_info=TypeInfo(
                        kind=TypeKind.FN,
                        is_function=True,
                        return_type=TypeInfo(kind=TypeKind.ENUM, name=defn.name),
                    ),
                )
                self.global_scope.define(variant.name, variant_sym)
                # Also register the qualified name (EnumName_VariantName)
                qualified = f"{defn.name}_{variant.name}"
                self.global_scope.define(
                    qualified,
                    Symbol(
                        name=qualified,
                        kind="function",
                        type_info=variant_sym.type_info,
                    ),
                )
        elif isinstance(defn, ExternFnDef):
            if defn.abi not in ("C", "Python"):
                self._error(
                    f'Unsupported ABI \'{defn.abi}\'; only "C" and "Python" are supported', defn
                )
            if defn.abi == "Python" and not defn.module:
                self._error(
                    'extern "Python" requires module qualifier: '
                    'extern "Python" fn module::name(...)',
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
                Symbol(name=defn.name, kind="function", type_info=fn_type, node=defn),
            )
        elif isinstance(defn, PipeDef):
            self.global_scope.define(
                defn.name,
                Symbol(
                    name=defn.name,
                    kind="pipe",
                    type_info=UNKNOWN_TYPE,
                    node=defn,
                ),
            )
        elif isinstance(defn, TypeAlias):
            resolved = self._resolve_type_expr(defn.type_expr)
            self.global_scope.define(
                defn.name,
                Symbol(name=defn.name, kind="type_alias", type_info=resolved, node=defn),
            )
        elif isinstance(defn, TraitDef):
            self.global_scope.define(
                defn.name,
                Symbol(
                    name=defn.name,
                    kind="trait",
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
                        Symbol(name=item, kind="variable", type_info=UNKNOWN_TYPE),
                    )
            else:
                mod_name = defn.path[-1] if defn.path else ""
                if mod_name:
                    self.global_scope.define(
                        mod_name,
                        Symbol(
                            name=mod_name,
                            kind="module",
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
                    kind="module",
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
                Symbol(name=name, kind="function", type_info=fn_type, node=defn),
            )
        elif isinstance(defn, AgentDef):
            self.global_scope.define(
                name,
                Symbol(
                    name=name,
                    kind="agent",
                    type_info=TypeInfo(kind=TypeKind.AGENT, name=name),
                    node=defn,
                ),
            )
        elif isinstance(defn, StructDef):
            self.global_scope.define(
                name,
                Symbol(
                    name=name,
                    kind="struct",
                    type_info=TypeInfo(kind=TypeKind.STRUCT, name=name),
                    node=defn,
                ),
            )
        elif isinstance(defn, EnumDef):
            self.global_scope.define(
                name,
                Symbol(
                    name=name,
                    kind="enum",
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
                        kind="function",
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
                Symbol(name=name, kind="pipe", type_info=UNKNOWN_TYPE, node=defn),
            )
        elif isinstance(defn, TypeAlias):
            resolved_type = self._resolve_type_expr(defn.type_expr)
            self.global_scope.define(
                name,
                Symbol(name=name, kind="type_alias", type_info=resolved_type, node=defn),
            )
        else:
            # Fallback — register as unknown
            self.global_scope.define(
                name,
                Symbol(name=name, kind="variable", type_info=UNKNOWN_TYPE),
            )

    # -- Definition checking (second pass) ------------------------------

    def _check_definitions(self, program: Program) -> None:
        """Second pass: check bodies of all definitions."""
        for defn in program.definitions:
            self._check_def(defn)

    def _check_def(self, defn: Definition) -> None:
        if isinstance(defn, FnDef):
            self._check_fn(defn)
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
        self._push_scope()
        for p in fn.params:
            pt = self._resolve_type_expr(p.type_annotation)
            self.current_scope.define(
                p.name,
                Symbol(name=p.name, kind="param", type_info=pt),
            )
        self._check_block(fn.body)
        self._pop_scope()

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
                kind="variable",
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
                Symbol(name=inp.name, kind="variable", type_info=inp_type),
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
                Symbol(name=out.name, kind="variable", type_info=out_type),
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
            if trait_sym is None or trait_sym.kind != "trait":
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
                "struct",
                "enum",
                "agent",
                "type_alias",
                "trait",
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
