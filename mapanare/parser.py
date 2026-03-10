"""Mapanare parser -- builds AST from token stream."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lark import Lark, Token, Transformer
from lark.exceptions import UnexpectedCharacters, UnexpectedToken

from mapanare.ast_nodes import (
    AgentDef,
    AgentInput,
    AgentOutput,
    AssignExpr,
    BinaryExpr,
    Block,
    BoolLiteral,
    CallExpr,
    CharLiteral,
    ConstructExpr,
    ConstructorPattern,
    Decorator,
    Definition,
    EnumDef,
    EnumVariant,
    ErrorPropExpr,
    ExportDef,
    Expr,
    ExprStmt,
    FieldAccessExpr,
    FieldInit,
    FloatLiteral,
    FnDef,
    FnType,
    ForLoop,
    GenericType,
    Identifier,
    IdentPattern,
    IfExpr,
    ImplDef,
    ImportDef,
    IndexExpr,
    IntLiteral,
    LambdaExpr,
    LetBinding,
    ListLiteral,
    LiteralPattern,
    MapEntry,
    MapLiteral,
    MatchArm,
    MatchExpr,
    MethodCallExpr,
    NamedType,
    NamespaceAccessExpr,
    NoneLiteral,
    Param,
    PipeDef,
    PipeExpr,
    Program,
    RangeExpr,
    ReturnStmt,
    SendExpr,
    SignalExpr,
    Span,
    SpawnExpr,
    Stmt,
    StringLiteral,
    StructDef,
    StructField,
    SyncExpr,
    TensorType,
    TraitDef,
    TraitMethod,
    TypeAlias,
    TypeExpr,
    TypeParam,
    UnaryExpr,
    WhileLoop,
    WildcardPattern,
)


class ParseError(Exception):
    """Raised when parsing fails."""

    def __init__(
        self,
        message: str,
        line: int = 0,
        column: int = 0,
        filename: str = "<input>",
    ) -> None:
        self.message = message
        self.line = line
        self.column = column
        self.filename = filename
        super().__init__(f"{filename}:{line}:{column}: {message}")


def _span_from_token(t: Token) -> Span:
    return Span(
        line=t.line or 0,
        column=t.column or 0,
        end_line=t.end_line or t.line or 0,
        end_column=t.end_column or (t.column or 0) + len(str(t)),
    )


def _parse_int_token(t: Token) -> int:
    s = str(t).replace("_", "")
    if t.type == "HEX_INT":
        return int(s, 16)
    if t.type == "BIN_INT":
        return int(s, 2)
    if t.type == "OCT_INT":
        return int(s, 8)
    return int(s)


# Tokens to filter out when processing children
_SKIP = frozenset(
    {
        "KW_FN",
        "KW_LET",
        "KW_AGENT",
        "KW_PIPE",
        "KW_STRUCT",
        "KW_ENUM",
        "KW_TYPE",
        "KW_IMPL",
        "KW_TRAIT",
        "KW_FOR",
        "KW_IF",
        "KW_ELSE",
        "KW_MATCH",
        "KW_FOR",
        "KW_WHILE",
        "KW_IN",
        "KW_RETURN",
        "KW_IMPORT",
        "KW_EXPORT",
        "KW_SPAWN",
        "KW_SYNC",
        "KW_SIGNAL",
        "KW_STREAM",
        "KW_INPUT",
        "KW_OUTPUT",
        "KW_TENSOR",
        "KW_WILDCARD",
        "KW_TRUE",
        "KW_FALSE",
        "KW_NONE",
        "LPAREN",
        "RPAREN",
        "LBRACE",
        "RBRACE",
        "LBRACKET",
        "RBRACKET",
        "COMMA",
        "COLON",
        "SEMICOLON",
        "ASSIGN",
        "ARROW",
        "FAT_ARROW",
        "PIPE_OP",
        "DOUBLE_COLON",
        "DOT",
        "QUESTION",
        "SEND",
        "PLUS_ASSIGN",
        "MINUS_ASSIGN",
        "STAR_ASSIGN",
        "SLASH_ASSIGN",
        "RANGE",
        "RANGE_INCL",
        "LT",
        "GT",
        "LE",
        "GE",
        "EQ",
        "NE",
        "AND",
        "OR",
        "PLUS",
        "MINUS",
        "STAR",
        "SLASH",
        "PERCENT",
        "BANG",
        "AT",
    }
)

# Tokens we keep: KW_PUB, KW_MUT, KW_SELF, NAME, literal tokens
_KEEP = frozenset(
    {
        "KW_PUB",
        "KW_MUT",
        "KW_SELF",
        "NAME",
        "DEC_INT",
        "HEX_INT",
        "BIN_INT",
        "OCT_INT",
        "FLOAT_LIT",
        "STRING_LIT",
        "CHAR_LIT",
    }
)


def _filter(args: tuple[Any, ...] | list[Any]) -> list[Any]:
    """Keep NAME, KW_PUB, KW_MUT tokens and all non-token children."""
    return [a for a in args if not isinstance(a, Token) or a.type in _KEEP]


class MapanareTransformer(Transformer):  # type: ignore[type-arg]
    """Transforms Lark parse tree into Mapanare AST nodes."""

    # ------------------------------------------------------------------
    # Program
    # ------------------------------------------------------------------

    def start(self, children: list[Any]) -> Program:
        definitions: list[Definition] = []
        top_level_stmts: list[Stmt] = []

        for child in children:
            if isinstance(child, Definition):
                definitions.append(child)
            elif isinstance(child, Stmt):
                top_level_stmts.append(child)
            elif isinstance(child, Expr):
                top_level_stmts.append(ExprStmt(expr=child))

        has_main = any(isinstance(d, FnDef) and d.name == "main" for d in definitions)

        if top_level_stmts and has_main:
            raise ParseError("cannot mix top-level statements with explicit fn main()")

        if top_level_stmts and not has_main:
            synthetic_main = FnDef(
                name="main",
                public=False,
                type_params=[],
                params=[],
                return_type=None,
                body=Block(stmts=top_level_stmts),
                decorators=[],
            )
            definitions.append(synthetic_main)

        return Program(definitions=definitions)

    # ------------------------------------------------------------------
    # Literals
    # ------------------------------------------------------------------

    def int_lit(self, children: list[Any]) -> IntLiteral:
        t = children[0]
        return IntLiteral(value=_parse_int_token(t), span=_span_from_token(t))

    def float_lit(self, children: list[Any]) -> FloatLiteral:
        t = children[0]
        return FloatLiteral(value=float(str(t).replace("_", "")), span=_span_from_token(t))

    def string_lit(self, children: list[Any]) -> StringLiteral:
        t = children[0]
        return StringLiteral(value=str(t)[1:-1], span=_span_from_token(t))

    def char_lit(self, children: list[Any]) -> CharLiteral:
        t = children[0]
        return CharLiteral(value=str(t)[1:-1], span=_span_from_token(t))

    def bool_true(self, children: list[Any]) -> BoolLiteral:
        return BoolLiteral(value=True)

    def bool_false(self, children: list[Any]) -> BoolLiteral:
        return BoolLiteral(value=False)

    def none_lit(self, children: list[Any]) -> NoneLiteral:
        return NoneLiteral()

    def ident(self, children: list[Any]) -> Identifier:
        t = children[0]
        return Identifier(name=str(t), span=_span_from_token(t))

    # ------------------------------------------------------------------
    # Type expressions
    # ------------------------------------------------------------------

    def named_type(self, children: list[Any]) -> NamedType:
        return NamedType(name=str(children[0]))

    def generic_type(self, children: list[Any]) -> GenericType:
        items = _filter(children)
        name = str(items[0])
        args = [a for a in items[1:] if isinstance(a, TypeExpr)]
        return GenericType(name=name, args=args)

    def tensor_type(self, children: list[Any]) -> TensorType:
        items = _filter(children)
        elem = items[0]
        dims = [a for a in items[1:] if isinstance(a, Expr)]
        return TensorType(element_type=elem, shape=dims)

    def fn_type(self, children: list[Any]) -> FnType:
        items = _filter(children)
        types = [a for a in items if isinstance(a, TypeExpr)]
        if not types:
            return FnType()
        return FnType(param_types=types[:-1], return_type=types[-1])

    def type_params(self, children: list[Any]) -> list[TypeParam]:
        return [c for c in children if isinstance(c, TypeParam)]

    def type_param(self, children: list[Any]) -> TypeParam:
        items = _filter(children)
        name = str(items[0])
        bound: str | None = None
        if len(items) > 1 and isinstance(items[1], Token) and items[1].type == "NAME":
            bound = str(items[1])
        return TypeParam(name=name, bound=bound)

    # ------------------------------------------------------------------
    # Parameters
    # ------------------------------------------------------------------

    def param(self, children: list[Any]) -> Param:
        items = _filter(children)
        return Param(name=str(items[0]), type_annotation=items[1])

    def param_list(self, children: list[Any]) -> list[Param]:
        result: list[Param] = []
        for c in children:
            if isinstance(c, Param):
                result.append(c)
            elif isinstance(c, Token) and c.type == "KW_SELF":
                result.append(Param(name="self"))
        return result

    def self_typed_param(self, children: list[Any]) -> Param:
        items = _filter(children)
        # items = [KW_SELF token, TypeExpr]
        type_ann = next((i for i in items if isinstance(i, TypeExpr)), None)
        return Param(name="self", type_annotation=type_ann)

    # ------------------------------------------------------------------
    # Block and statements
    # ------------------------------------------------------------------

    def block(self, children: list[Any]) -> Block:
        stmts: list[Stmt] = []
        for c in children:
            if isinstance(c, Expr):
                stmts.append(ExprStmt(expr=c))
            elif isinstance(c, Stmt):
                stmts.append(c)
        return Block(stmts=stmts)

    def let_stmt(self, children: list[Any]) -> LetBinding:
        items = _filter(children)
        mutable = False
        idx = 0
        if isinstance(items[idx], Token) and items[idx].type == "KW_MUT":
            mutable = True
            idx += 1
        name = str(items[idx])
        idx += 1
        type_ann: TypeExpr | None = None
        if idx < len(items) - 1 and isinstance(items[idx], TypeExpr):
            type_ann = items[idx]
            idx += 1
        value = items[idx]
        return LetBinding(name=name, mutable=mutable, type_annotation=type_ann, value=value)

    def return_stmt(self, children: list[Any]) -> ReturnStmt:
        items = _filter(children)
        value = items[0] if items else None
        return ReturnStmt(value=value)

    def for_stmt(self, children: list[Any]) -> ForLoop:
        items = _filter(children)
        name = str(items[0])
        iterable = items[1]
        body = items[2]
        return ForLoop(var_name=name, iterable=iterable, body=body)

    def while_stmt(self, children: list[Any]) -> WhileLoop:
        items = _filter(children)
        condition = items[0]
        body = items[1]
        return WhileLoop(condition=condition, body=body)

    def expr_stmt(self, children: list[Any]) -> ExprStmt:
        return ExprStmt(expr=children[0])

    # ------------------------------------------------------------------
    # Binary operators
    # ------------------------------------------------------------------

    def add_op(self, children: list[Any]) -> BinaryExpr:
        items = _filter(children)
        return BinaryExpr(left=items[0], op="+", right=items[1])

    def sub_op(self, children: list[Any]) -> BinaryExpr:
        items = _filter(children)
        return BinaryExpr(left=items[0], op="-", right=items[1])

    def mul_op(self, children: list[Any]) -> BinaryExpr:
        items = _filter(children)
        return BinaryExpr(left=items[0], op="*", right=items[1])

    def div_op(self, children: list[Any]) -> BinaryExpr:
        items = _filter(children)
        return BinaryExpr(left=items[0], op="/", right=items[1])

    def mod_op(self, children: list[Any]) -> BinaryExpr:
        items = _filter(children)
        return BinaryExpr(left=items[0], op="%", right=items[1])

    def matmul_op(self, children: list[Any]) -> BinaryExpr:
        items = _filter(children)
        return BinaryExpr(left=items[0], op="@", right=items[1])

    def eq_op(self, children: list[Any]) -> BinaryExpr:
        items = _filter(children)
        return BinaryExpr(left=items[0], op="==", right=items[1])

    def ne_op(self, children: list[Any]) -> BinaryExpr:
        items = _filter(children)
        return BinaryExpr(left=items[0], op="!=", right=items[1])

    def lt_op(self, children: list[Any]) -> BinaryExpr:
        items = _filter(children)
        return BinaryExpr(left=items[0], op="<", right=items[1])

    def gt_op(self, children: list[Any]) -> BinaryExpr:
        items = _filter(children)
        return BinaryExpr(left=items[0], op=">", right=items[1])

    def le_op(self, children: list[Any]) -> BinaryExpr:
        items = _filter(children)
        return BinaryExpr(left=items[0], op="<=", right=items[1])

    def ge_op(self, children: list[Any]) -> BinaryExpr:
        items = _filter(children)
        return BinaryExpr(left=items[0], op=">=", right=items[1])

    def and_op(self, children: list[Any]) -> BinaryExpr:
        items = _filter(children)
        return BinaryExpr(left=items[0], op="&&", right=items[1])

    def or_op(self, children: list[Any]) -> BinaryExpr:
        items = _filter(children)
        return BinaryExpr(left=items[0], op="||", right=items[1])

    def pipe_op(self, children: list[Any]) -> PipeExpr:
        items = _filter(children)
        return PipeExpr(left=items[0], right=items[1])

    def range_op(self, children: list[Any]) -> RangeExpr:
        items = _filter(children)
        return RangeExpr(start=items[0], end=items[1], inclusive=False)

    def range_incl_op(self, children: list[Any]) -> RangeExpr:
        items = _filter(children)
        return RangeExpr(start=items[0], end=items[1], inclusive=True)

    # ------------------------------------------------------------------
    # Unary
    # ------------------------------------------------------------------

    def neg_op(self, children: list[Any]) -> UnaryExpr:
        items = _filter(children)
        return UnaryExpr(op="-", operand=items[0])

    def not_op(self, children: list[Any]) -> UnaryExpr:
        items = _filter(children)
        return UnaryExpr(op="!", operand=items[0])

    # ------------------------------------------------------------------
    # Postfix
    # ------------------------------------------------------------------

    def call_expr(self, children: list[Any]) -> CallExpr:
        items = _filter(children)
        callee = items[0]
        call_args = self._flatten_args(items[1:])
        return CallExpr(callee=callee, args=call_args)

    def method_call_expr(self, children: list[Any]) -> MethodCallExpr:
        items = _filter(children)
        obj = items[0]
        method = str(items[1])
        call_args = self._flatten_args(items[2:])
        return MethodCallExpr(object=obj, method=method, args=call_args)

    def field_access(self, children: list[Any]) -> FieldAccessExpr:
        items = _filter(children)
        return FieldAccessExpr(object=items[0], field_name=str(items[1]))

    def index_expr(self, children: list[Any]) -> IndexExpr:
        items = _filter(children)
        return IndexExpr(object=items[0], index=items[1])

    def error_prop(self, children: list[Any]) -> ErrorPropExpr:
        items = _filter(children)
        return ErrorPropExpr(expr=items[0])

    def arg_list(self, children: list[Any]) -> list[Expr]:
        return [c for c in children if isinstance(c, Expr)]

    # ------------------------------------------------------------------
    # Assignment / Send
    # ------------------------------------------------------------------

    def assign(self, children: list[Any]) -> AssignExpr:
        items = _filter(children)
        return AssignExpr(target=items[0], op="=", value=items[1])

    def assign_add(self, children: list[Any]) -> AssignExpr:
        items = _filter(children)
        return AssignExpr(target=items[0], op="+=", value=items[1])

    def assign_sub(self, children: list[Any]) -> AssignExpr:
        items = _filter(children)
        return AssignExpr(target=items[0], op="-=", value=items[1])

    def assign_mul(self, children: list[Any]) -> AssignExpr:
        items = _filter(children)
        return AssignExpr(target=items[0], op="*=", value=items[1])

    def assign_div(self, children: list[Any]) -> AssignExpr:
        items = _filter(children)
        return AssignExpr(target=items[0], op="/=", value=items[1])

    def send_expr(self, children: list[Any]) -> SendExpr:
        items = _filter(children)
        return SendExpr(target=items[0], value=items[1])

    # ------------------------------------------------------------------
    # Namespace, list, paren
    # ------------------------------------------------------------------

    def namespace_access(self, children: list[Any]) -> NamespaceAccessExpr:
        names = [c for c in children if isinstance(c, Token) and c.type == "NAME"]
        return NamespaceAccessExpr(namespace=str(names[0]), member=str(names[1]))

    def list_lit(self, children: list[Any]) -> ListLiteral:
        return ListLiteral(elements=[c for c in children if isinstance(c, Expr)])

    def map_lit(self, children: list[Any]) -> MapLiteral:
        return MapLiteral(entries=[c for c in children if isinstance(c, MapEntry)])

    def map_entry(self, children: list[Any]) -> MapEntry:
        exprs = [c for c in children if isinstance(c, Expr)]
        return MapEntry(key=exprs[0], value=exprs[1])

    def construct_expr(self, children: list[Any]) -> ConstructExpr:
        items = _filter(children)
        name = str(items[0])
        fields = [c for c in items[1:] if isinstance(c, FieldInit)]
        return ConstructExpr(name=name, fields=fields)

    def field_init(self, children: list[Any]) -> FieldInit:
        items = _filter(children)
        name = str(items[0])
        value = items[1] if len(items) > 1 else Identifier(name=name)
        return FieldInit(name=name, value=value)

    def paren_expr(self, children: list[Any]) -> Expr:
        items = _filter(children)
        result: Expr = items[0]
        return result

    def tuple_expr(self, children: list[Any]) -> ListLiteral:
        return ListLiteral(elements=[c for c in children if isinstance(c, Expr)])

    # ------------------------------------------------------------------
    # Spawn / Sync / Signal
    # ------------------------------------------------------------------

    def spawn_expr(self, children: list[Any]) -> SpawnExpr:
        items = _filter(children)
        name = str(items[0])
        call_args = self._flatten_args(items[1:])
        return SpawnExpr(callee=Identifier(name=name), args=call_args)

    def self_expr(self, children: list[Any]) -> Identifier:
        return Identifier(name="self")

    def stream_expr(self, children: list[Any]) -> CallExpr:
        items = _filter(children)
        return CallExpr(callee=Identifier(name="stream"), args=[items[0]] if items else [])

    def decorated_def(self, children: list[Any]) -> Definition:
        items = _filter(children)
        decorators: list[Decorator] = []
        defn: Definition | None = None
        for item in items:
            if isinstance(item, Decorator):
                decorators.append(item)
            elif isinstance(item, Definition):
                defn = item
        if defn is None:
            result: Definition = items[-1]
            return result
        # Attach decorators to the definition
        if isinstance(defn, (FnDef, AgentDef)):
            defn.decorators = decorators
        return defn

    def decorator(self, children: list[Any]) -> Decorator:
        items = _filter(children)
        name = str(items[0])
        dec_args: list[Expr] = []
        for item in items[1:]:
            if isinstance(item, list):
                dec_args.extend(item)
            elif isinstance(item, Expr):
                dec_args.append(item)
        return Decorator(name=name, args=dec_args)

    def sync_expr(self, children: list[Any]) -> SyncExpr:
        items = _filter(children)
        return SyncExpr(expr=items[0])

    def signal_value(self, children: list[Any]) -> SignalExpr:
        items = _filter(children)
        return SignalExpr(value=items[0], is_computed=False)

    def signal_computed(self, children: list[Any]) -> SignalExpr:
        items = _filter(children)
        return SignalExpr(value=items[0], is_computed=True)

    # ------------------------------------------------------------------
    # Lambda — parsed as `expr => expr`, converted here
    # ------------------------------------------------------------------

    def lambda_expr_rule(self, children: list[Any]) -> LambdaExpr:
        items = _filter(children)
        left = items[0]
        body = items[1]
        params = self._expr_to_params(left)
        return LambdaExpr(params=params, body=body)

    @staticmethod
    def _expr_to_params(expr: Any) -> list[Param]:
        if isinstance(expr, Identifier):
            return [Param(name=expr.name)]
        if isinstance(expr, ListLiteral):
            # tuple_expr was parsed as ListLiteral
            return [MapanareTransformer._single_to_param(e) for e in expr.elements]
        return [MapanareTransformer._single_to_param(expr)]

    @staticmethod
    def _single_to_param(expr: Any) -> Param:
        if isinstance(expr, Identifier):
            return Param(name=expr.name)
        raise ParseError(f"Invalid lambda parameter: {expr}")

    # ------------------------------------------------------------------
    # If / Match
    # ------------------------------------------------------------------

    def if_simple(self, children: list[Any]) -> IfExpr:
        items = _filter(children)
        cond = items[0]
        then = items[1]
        else_block = items[2] if len(items) > 2 else None
        return IfExpr(condition=cond, then_block=then, else_block=else_block)

    def if_elseif(self, children: list[Any]) -> IfExpr:
        items = _filter(children)
        return IfExpr(condition=items[0], then_block=items[1], else_block=items[2])

    def match_expr(self, children: list[Any]) -> MatchExpr:
        items = _filter(children)
        subject = items[0]
        arms = items[1] if len(items) > 1 and isinstance(items[1], list) else []
        return MatchExpr(subject=subject, arms=arms)

    def match_arms(self, children: list[Any]) -> list[MatchArm]:
        return [c for c in children if isinstance(c, MatchArm)]

    def match_arm(self, children: list[Any]) -> MatchArm:
        items = _filter(children)
        return MatchArm(pattern=items[0], body=items[1])

    # ------------------------------------------------------------------
    # Patterns
    # ------------------------------------------------------------------

    def wildcard_pattern(self, children: list[Any]) -> WildcardPattern:
        return WildcardPattern()

    def constructor_pattern(self, children: list[Any]) -> ConstructorPattern:
        items = _filter(children)
        name = str(items[0])
        args = [a for a in items[1:] if not isinstance(a, Token)]
        return ConstructorPattern(name=name, args=args)

    def literal_pattern(self, children: list[Any]) -> LiteralPattern:
        t = children[0]
        s = str(t)
        if t.type == "DEC_INT":
            return LiteralPattern(value=IntLiteral(value=int(s.replace("_", ""))))
        if t.type == "FLOAT_LIT":
            return LiteralPattern(value=FloatLiteral(value=float(s.replace("_", ""))))
        if t.type == "STRING_LIT":
            return LiteralPattern(value=StringLiteral(value=s[1:-1]))
        if t.type == "KW_TRUE":
            return LiteralPattern(value=BoolLiteral(value=True))
        if t.type == "KW_FALSE":
            return LiteralPattern(value=BoolLiteral(value=False))
        return LiteralPattern(value=Identifier(name=s))

    def ident_pattern(self, children: list[Any]) -> IdentPattern:
        return IdentPattern(name=str(children[0]))

    # ------------------------------------------------------------------
    # Function definition
    # ------------------------------------------------------------------

    def fn_def(self, children: list[Any]) -> FnDef:
        items = _filter(children)
        public = False
        idx = 0
        if isinstance(items[idx], Token) and items[idx].type == "KW_PUB":
            public = True
            idx += 1
        name = str(items[idx])
        idx += 1
        type_params: list[str] = []
        trait_bounds: dict[str, str] = {}
        if (
            idx < len(items)
            and isinstance(items[idx], list)
            and items[idx]
            and isinstance(items[idx][0], (str, TypeParam))
        ):
            raw_tps = items[idx]
            if raw_tps and isinstance(raw_tps[0], TypeParam):
                type_params = [tp.name for tp in raw_tps]
                trait_bounds = {tp.name: tp.bound for tp in raw_tps if tp.bound}
            else:
                type_params = raw_tps
            idx += 1
        params: list[Param] = []
        if (
            idx < len(items)
            and isinstance(items[idx], list)
            and (not items[idx] or isinstance(items[idx][0], Param))
        ):
            params = items[idx]
            idx += 1
        return_type: TypeExpr | None = None
        if idx < len(items) and isinstance(items[idx], TypeExpr):
            return_type = items[idx]
            idx += 1
        body = items[idx] if idx < len(items) else Block()
        return FnDef(
            name=name,
            public=public,
            type_params=type_params,
            params=params,
            return_type=return_type,
            body=body,
            trait_bounds=trait_bounds,
        )

    # ------------------------------------------------------------------
    # Agent definition
    # ------------------------------------------------------------------

    def agent_def(self, children: list[Any]) -> AgentDef:
        items = _filter(children)
        public = False
        idx = 0
        if isinstance(items[idx], Token) and items[idx].type == "KW_PUB":
            public = True
            idx += 1
        name = str(items[idx])
        idx += 1
        members = items[idx] if idx < len(items) and isinstance(items[idx], list) else []

        inputs: list[AgentInput] = []
        outputs: list[AgentOutput] = []
        state: list[LetBinding] = []
        methods: list[FnDef] = []
        for m in members:
            if isinstance(m, AgentInput):
                inputs.append(m)
            elif isinstance(m, AgentOutput):
                outputs.append(m)
            elif isinstance(m, LetBinding):
                state.append(m)
            elif isinstance(m, FnDef):
                methods.append(m)
        return AgentDef(
            name=name,
            public=public,
            inputs=inputs,
            outputs=outputs,
            state=state,
            methods=methods,
        )

    def agent_body(self, children: list[Any]) -> list[Any]:
        return [c for c in children if c is not None and not isinstance(c, Token)]

    def agent_input(self, children: list[Any]) -> AgentInput:
        items = _filter(children)
        return AgentInput(name=str(items[0]), type_annotation=items[1])

    def agent_output(self, children: list[Any]) -> AgentOutput:
        items = _filter(children)
        return AgentOutput(name=str(items[0]), type_annotation=items[1])

    def agent_state(self, children: list[Any]) -> LetBinding:
        items = _filter(children)
        mutable = False
        idx = 0
        if isinstance(items[idx], Token) and items[idx].type == "KW_MUT":
            mutable = True
            idx += 1
        name = str(items[idx])
        idx += 1
        type_ann: TypeExpr | None = None
        if idx < len(items) - 1 and isinstance(items[idx], TypeExpr):
            type_ann = items[idx]
            idx += 1
        value = items[idx]
        return LetBinding(name=name, mutable=mutable, type_annotation=type_ann, value=value)

    # ------------------------------------------------------------------
    # Pipe definition
    # ------------------------------------------------------------------

    def pipe_def(self, children: list[Any]) -> PipeDef:
        items = _filter(children)
        public = False
        idx = 0
        if isinstance(items[idx], Token) and items[idx].type == "KW_PUB":
            public = True
            idx += 1
        name = str(items[idx])
        idx += 1
        stages = items[idx] if idx < len(items) else []
        return PipeDef(name=name, public=public, stages=stages)

    def pipe_chain(self, children: list[Any]) -> list[Identifier]:
        names = [c for c in children if isinstance(c, Token) and c.type == "NAME"]
        return [Identifier(name=str(n)) for n in names]

    # ------------------------------------------------------------------
    # Struct definition
    # ------------------------------------------------------------------

    def struct_def(self, children: list[Any]) -> StructDef:
        items = _filter(children)
        public = False
        idx = 0
        if isinstance(items[idx], Token) and items[idx].type == "KW_PUB":
            public = True
            idx += 1
        name = str(items[idx])
        idx += 1
        type_params: list[str] = []
        if (
            idx < len(items)
            and isinstance(items[idx], list)
            and items[idx]
            and isinstance(items[idx][0], (str, TypeParam))
        ):
            raw_tps = items[idx]
            if raw_tps and isinstance(raw_tps[0], TypeParam):
                type_params = [tp.name for tp in raw_tps]
            else:
                type_params = raw_tps
            idx += 1
        fields = items[idx] if idx < len(items) and isinstance(items[idx], list) else []
        return StructDef(name=name, public=public, type_params=type_params, fields=fields)

    def struct_fields(self, children: list[Any]) -> list[StructField]:
        return [c for c in children if isinstance(c, StructField)]

    def struct_field(self, children: list[Any]) -> StructField:
        items = _filter(children)
        return StructField(name=str(items[0]), type_annotation=items[1])

    # ------------------------------------------------------------------
    # Enum definition
    # ------------------------------------------------------------------

    def enum_def(self, children: list[Any]) -> EnumDef:
        items = _filter(children)
        public = False
        idx = 0
        if isinstance(items[idx], Token) and items[idx].type == "KW_PUB":
            public = True
            idx += 1
        name = str(items[idx])
        idx += 1
        type_params: list[str] = []
        if (
            idx < len(items)
            and isinstance(items[idx], list)
            and items[idx]
            and isinstance(items[idx][0], (str, TypeParam))
        ):
            raw_tps = items[idx]
            if raw_tps and isinstance(raw_tps[0], TypeParam):
                type_params = [tp.name for tp in raw_tps]
            else:
                type_params = raw_tps
            idx += 1
        variants = items[idx] if idx < len(items) and isinstance(items[idx], list) else []
        return EnumDef(name=name, public=public, type_params=type_params, variants=variants)

    def enum_variants(self, children: list[Any]) -> list[EnumVariant]:
        return [c for c in children if isinstance(c, EnumVariant)]

    def enum_variant(self, children: list[Any]) -> EnumVariant:
        items = _filter(children)
        name = str(items[0])
        fields = items[1] if len(items) > 1 and isinstance(items[1], list) else []
        return EnumVariant(name=name, fields=fields)

    def type_list(self, children: list[Any]) -> list[TypeExpr]:
        return [c for c in children if isinstance(c, TypeExpr)]

    # ------------------------------------------------------------------
    # Type alias
    # ------------------------------------------------------------------

    def type_alias(self, children: list[Any]) -> TypeAlias:
        items = _filter(children)
        public = False
        idx = 0
        if isinstance(items[idx], Token) and items[idx].type == "KW_PUB":
            public = True
            idx += 1
        return TypeAlias(name=str(items[idx]), public=public, type_expr=items[idx + 1])

    # ------------------------------------------------------------------
    # Trait definition
    # ------------------------------------------------------------------

    def trait_def(self, children: list[Any]) -> TraitDef:
        items = _filter(children)
        public = False
        idx = 0
        if isinstance(items[idx], Token) and items[idx].type == "KW_PUB":
            public = True
            idx += 1
        name = str(items[idx])
        methods = [m for m in items[idx + 1 :] if isinstance(m, TraitMethod)]
        return TraitDef(name=name, public=public, methods=methods)

    def trait_method(self, children: list[Any]) -> TraitMethod:
        items = _filter(children)
        name = str(items[0])
        has_self = False
        params: list[Param] = []
        return_type: TypeExpr | None = None
        for item in items[1:]:
            if isinstance(item, list):
                for p in item:
                    if isinstance(p, Param):
                        params.append(p)
                    elif isinstance(p, Token) and p.type == "KW_SELF":
                        has_self = True
            elif isinstance(item, TypeExpr):
                return_type = item
        return TraitMethod(name=name, params=params, has_self=has_self, return_type=return_type)

    def trait_param_list(self, children: list[Any]) -> list[Param | Token]:
        return [c for c in children if isinstance(c, (Param, Token))]

    # ------------------------------------------------------------------
    # Impl block
    # ------------------------------------------------------------------

    def impl_trait_def(self, children: list[Any]) -> ImplDef:
        items = _filter(children)
        trait_name = str(items[0])
        target = str(items[1])
        methods = [m for m in items[2:] if isinstance(m, FnDef)]
        return ImplDef(target=target, trait_name=trait_name, methods=methods)

    def impl_def(self, children: list[Any]) -> ImplDef:
        items = _filter(children)
        name = str(items[0])
        methods = [m for m in items[1:] if isinstance(m, FnDef)]
        return ImplDef(target=name, methods=methods)

    # ------------------------------------------------------------------
    # Import / Export
    # ------------------------------------------------------------------

    def import_def(self, children: list[Any]) -> ImportDef:
        items = _filter(children)
        path = items[0] if isinstance(items[0], list) else [str(items[0])]
        item_names = items[1] if len(items) > 1 and isinstance(items[1], list) else []
        return ImportDef(path=path, items=item_names)

    def import_path(self, children: list[Any]) -> list[str]:
        return [str(c) for c in children if isinstance(c, Token) and c.type == "NAME"]

    def import_items(self, children: list[Any]) -> list[str]:
        return [str(c) for c in children if isinstance(c, Token) and c.type == "NAME"]

    def export_def(self, children: list[Any]) -> ExportDef:
        items = _filter(children)
        if items and isinstance(items[0], Definition):
            return ExportDef(definition=items[0])
        if items and isinstance(items[0], list):
            return ExportDef(names=items[0])
        return ExportDef()

    def export_names(self, children: list[Any]) -> list[str]:
        return [str(c) for c in children if isinstance(c, Token) and c.type == "NAME"]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _flatten_args(args: list[Any]) -> list[Expr]:
        result: list[Expr] = []
        for a in args:
            if isinstance(a, list):
                result.extend(a)
            elif isinstance(a, Expr):
                result.append(a)
        return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_GRAMMAR_PATH = Path(__file__).parent / "mapanare.lark"
_parser = Lark(
    _GRAMMAR_PATH.read_text(encoding="utf-8"),
    parser="lalr",
    transformer=MapanareTransformer(),
)


def parse(source: str, *, filename: str = "<input>") -> Program:
    """Parse Mapanare source code into an AST Program node.

    Args:
        source: The Mapanare source code to parse.
        filename: Filename used in error messages.

    Returns:
        A Program AST node.

    Raises:
        ParseError: If the source has syntax errors.
    """
    try:
        result = _parser.parse(source)
        if isinstance(result, Program):
            return result
        return Program(definitions=[result] if isinstance(result, Definition) else [])
    except UnexpectedCharacters as exc:
        raise ParseError(
            f"Unexpected character: {exc.char!r}",
            line=exc.line,
            column=exc.column,
            filename=filename,
        ) from None
    except UnexpectedToken as exc:
        line = getattr(exc, "line", 0)
        column = getattr(exc, "column", 0)
        msg = _friendly_token_error(exc)
        raise ParseError(
            msg,
            line=line,
            column=column,
            filename=filename,
        ) from None


# Map raw Lark token types to user-friendly names
_TOKEN_NAMES: dict[str, str] = {
    "MAP_OPEN": "'#{'",
    "LBRACE": "'{'",
    "RBRACE": "'}'",
    "LPAREN": "'('",
    "RPAREN": "')'",
    "LBRACKET": "'['",
    "RBRACKET": "']'",
    "COMMA": "','",
    "COLON": "':'",
    "SEMICOLON": "';'",
    "ASSIGN": "'='",
    "ARROW": "'->'",
    "FAT_ARROW": "'=>'",
    "PIPE_OP": "'|>'",
    "NEWLINE": "newline",
    "NAME": "identifier",
    "DEC_INT": "integer",
    "FLOAT_LIT": "float",
    "STRING_LIT": "string",
    "KW_FN": "'fn'",
    "KW_LET": "'let'",
    "KW_IF": "'if'",
    "KW_ELSE": "'else'",
    "KW_FOR": "'for'",
    "KW_WHILE": "'while'",
    "KW_IN": "'in'",
    "KW_RETURN": "'return'",
    "KW_MATCH": "'match'",
    "KW_STRUCT": "'struct'",
    "KW_ENUM": "'enum'",
    "KW_TRAIT": "'trait'",
    "KW_IMPORT": "'import'",
    "KW_EXPORT": "'export'",
    "KW_AGENT": "'agent'",
    "KW_SPAWN": "'spawn'",
    "KW_SIGNAL": "'signal'",
    "KW_STREAM": "'stream'",
    "KW_TRUE": "'true'",
    "KW_FALSE": "'false'",
    "KW_NONE": "'none'",
    "$END": "end of file",
}


def _friendly_token_name(tok_type: str) -> str:
    """Convert a Lark token type to a user-friendly name."""
    return _TOKEN_NAMES.get(tok_type, tok_type.lower().replace("_", " "))


def _friendly_token_error(exc: UnexpectedToken) -> str:
    """Build a user-friendly parse error message from a Lark UnexpectedToken."""
    token = exc.token
    token_val = str(token).strip()

    # Describe what was found
    if hasattr(token, "type"):
        found = _friendly_token_name(token.type)
        if token_val and found != f"'{token_val}'":
            found = f"{found} ({token_val!r})"
    else:
        found = repr(token_val)

    # Describe what was expected (limit to avoid huge messages)
    expected_set: set[str] = getattr(exc, "expected", set())
    if expected_set:
        friendly = sorted({_friendly_token_name(e) for e in expected_set})
        if len(friendly) <= 5:
            expected_str = ", ".join(friendly)
        else:
            expected_str = ", ".join(friendly[:5]) + ", ..."
        return f"Unexpected {found} — expected {expected_str}"

    return f"Unexpected {found}"
