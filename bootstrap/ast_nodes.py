"""AST node dataclasses for the Mapanare language."""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


@dataclass
class Span:
    """Source location info attached to AST nodes."""

    line: int = 0
    column: int = 0
    end_line: int = 0
    end_column: int = 0


@dataclass
class ASTNode:
    """Base class for all AST nodes."""

    span: Span = field(default_factory=Span)


# ---------------------------------------------------------------------------
# Program (root)
# ---------------------------------------------------------------------------


@dataclass
class Program(ASTNode):
    """Top-level program: a list of definitions."""

    definitions: list[Definition] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Type annotations
# ---------------------------------------------------------------------------


@dataclass
class TypeExpr(ASTNode):
    """Base for type expressions."""


@dataclass
class NamedType(TypeExpr):
    """A simple named type like `Int`, `String`, `MyStruct`."""

    name: str = ""


@dataclass
class GenericType(TypeExpr):
    """A generic type like `List<Int>`, `Map<String, Int>`."""

    name: str = ""
    args: list[TypeExpr] = field(default_factory=list)


@dataclass
class TensorType(TypeExpr):
    """Tensor type with shape: `Tensor<Float>[3, 3]`."""

    element_type: TypeExpr = field(default_factory=lambda: NamedType())
    shape: list[Expr] = field(default_factory=list)


@dataclass
class FnType(TypeExpr):
    """Function type: `fn(Int, Int) -> Bool`."""

    param_types: list[TypeExpr] = field(default_factory=list)
    return_type: TypeExpr = field(default_factory=lambda: NamedType(name="Void"))


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------


@dataclass
class Expr(ASTNode):
    """Base for all expressions."""


@dataclass
class IntLiteral(Expr):
    """Integer literal."""

    value: int = 0


@dataclass
class FloatLiteral(Expr):
    """Float literal."""

    value: float = 0.0


@dataclass
class StringLiteral(Expr):
    """String literal."""

    value: str = ""


@dataclass
class InterpString(Expr):
    """Interpolated string: `"Hello, ${name}!"`.

    Parts alternate between literal strings and expressions.
    Each part is either a StringLiteral (text) or an arbitrary Expr (interpolated).
    """

    parts: list[Expr] = field(default_factory=list)


@dataclass
class CharLiteral(Expr):
    """Character literal."""

    value: str = ""


@dataclass
class BoolLiteral(Expr):
    """Boolean literal."""

    value: bool = False


@dataclass
class NoneLiteral(Expr):
    """The `none` literal."""


@dataclass
class Identifier(Expr):
    """A variable or name reference."""

    name: str = ""


@dataclass
class BinaryExpr(Expr):
    """Binary operation: `a + b`, `a |> b`, etc."""

    left: Expr = field(default_factory=Expr)
    op: str = ""
    right: Expr = field(default_factory=Expr)


@dataclass
class UnaryExpr(Expr):
    """Unary operation: `-x`, `!flag`."""

    op: str = ""
    operand: Expr = field(default_factory=Expr)


@dataclass
class CallExpr(Expr):
    """Function call: `foo(a, b)`."""

    callee: Expr = field(default_factory=Expr)
    args: list[Expr] = field(default_factory=list)


@dataclass
class MethodCallExpr(Expr):
    """Method call: `obj.method(a, b)`."""

    object: Expr = field(default_factory=Expr)
    method: str = ""
    args: list[Expr] = field(default_factory=list)


@dataclass
class FieldAccessExpr(Expr):
    """Field access: `obj.field`."""

    object: Expr = field(default_factory=Expr)
    field_name: str = ""


@dataclass
class NamespaceAccessExpr(Expr):
    """Namespace access: `Math::sqrt`."""

    namespace: str = ""
    member: str = ""


@dataclass
class IndexExpr(Expr):
    """Index expression: `arr[i]`."""

    object: Expr = field(default_factory=Expr)
    index: Expr = field(default_factory=Expr)


@dataclass
class PipeExpr(Expr):
    """Pipe expression: `a |> b |> c`."""

    left: Expr = field(default_factory=Expr)
    right: Expr = field(default_factory=Expr)


@dataclass
class RangeExpr(Expr):
    """Range expression: `a..b` or `a..=b`."""

    start: Expr = field(default_factory=Expr)
    end: Expr = field(default_factory=Expr)
    inclusive: bool = False


@dataclass
class LambdaExpr(Expr):
    """Lambda expression: `(x) => x + 1`."""

    params: list[Param] = field(default_factory=list)
    body: Expr | Block = field(default_factory=Expr)


@dataclass
class SpawnExpr(Expr):
    """Spawn expression: `spawn Agent()`."""

    callee: Expr = field(default_factory=Expr)
    args: list[Expr] = field(default_factory=list)


@dataclass
class SyncExpr(Expr):
    """Sync expression: `sync agent.output`."""

    expr: Expr = field(default_factory=Expr)


@dataclass
class SendExpr(Expr):
    """Send expression: `agent.input <- value`."""

    target: Expr = field(default_factory=Expr)
    value: Expr = field(default_factory=Expr)


@dataclass
class ErrorPropExpr(Expr):
    """Error propagation: `expr?`."""

    expr: Expr = field(default_factory=Expr)


@dataclass
class ListLiteral(Expr):
    """List literal: `[1, 2, 3]`."""

    elements: list[Expr] = field(default_factory=list)


@dataclass
class MapEntry(ASTNode):
    """A single key-value pair in a map literal."""

    key: Expr = field(default_factory=Expr)
    value: Expr = field(default_factory=Expr)


@dataclass
class MapLiteral(Expr):
    """Map literal: `{key: value, ...}`."""

    entries: list[MapEntry] = field(default_factory=list)


@dataclass
class ConstructExpr(Expr):
    """Struct construction: `Point { x: 1.0, y: 2.0 }`."""

    name: str = ""
    fields: list[FieldInit] = field(default_factory=list)


@dataclass
class FieldInit(ASTNode):
    """Field initializer in a struct construction."""

    name: str = ""
    value: Expr = field(default_factory=Expr)


@dataclass
class SomeExpr(Expr):
    """Some(value) wrapping expression."""

    value: Expr = field(default_factory=Expr)


@dataclass
class OkExpr(Expr):
    """Ok(value) wrapping expression."""

    value: Expr = field(default_factory=Expr)


@dataclass
class ErrExpr(Expr):
    """Err(value) wrapping expression."""

    value: Expr = field(default_factory=Expr)


@dataclass
class SignalExpr(Expr):
    """Signal expression: `signal(0)` or `signal { expr }`."""

    value: Expr = field(default_factory=Expr)
    is_computed: bool = False


@dataclass
class AssignExpr(Expr):
    """Assignment: `x = 5` or `x += 1`."""

    target: Expr = field(default_factory=Expr)
    op: str = "="
    value: Expr = field(default_factory=Expr)


# ---------------------------------------------------------------------------
# Statements
# ---------------------------------------------------------------------------


@dataclass
class Stmt(ASTNode):
    """Base for all statements."""


@dataclass
class LetBinding(Stmt):
    """Let binding: `let x: Int = 42` or `let mut x = 0`."""

    name: str = ""
    mutable: bool = False
    type_annotation: TypeExpr | None = None
    value: Expr = field(default_factory=Expr)


@dataclass
class ExprStmt(Stmt):
    """Expression used as a statement."""

    expr: Expr = field(default_factory=Expr)


@dataclass
class ReturnStmt(Stmt):
    """Return statement: `return expr`."""

    value: Expr | None = None


@dataclass
class BreakStmt(Stmt):
    """Break statement: `break`."""

    pass


@dataclass
class AssertStmt(Stmt):
    """Assert statement: `assert expr` or `assert expr, "message"`."""

    condition: Expr = field(default_factory=Expr)
    message: Expr | None = None


@dataclass
class ForLoop(Stmt):
    """For loop: `for x in items { ... }`."""

    var_name: str = ""
    iterable: Expr = field(default_factory=Expr)
    body: Block = field(default_factory=lambda: Block())


@dataclass
class WhileLoop(Stmt):
    """While loop: `while cond { ... }`."""

    condition: Expr = field(default_factory=Expr)
    body: Block = field(default_factory=lambda: Block())


@dataclass
class Block(ASTNode):
    """A block of statements: `{ stmt1; stmt2; ... }`."""

    stmts: list[Stmt] = field(default_factory=list)


@dataclass
class IfExpr(Expr):
    """If expression: `if cond { ... } else { ... }`."""

    condition: Expr = field(default_factory=Expr)
    then_block: Block = field(default_factory=lambda: Block())
    else_block: Block | IfExpr | None = None


@dataclass
class MatchArm(ASTNode):
    """A single arm in a match expression."""

    pattern: Pattern = field(default_factory=lambda: Pattern())
    body: Expr | Block = field(default_factory=Expr)


@dataclass
class MatchExpr(Expr):
    """Match expression: `match expr { pat => body, ... }`."""

    subject: Expr = field(default_factory=Expr)
    arms: list[MatchArm] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Patterns (for match)
# ---------------------------------------------------------------------------


@dataclass
class Pattern(ASTNode):
    """Base for patterns."""


@dataclass
class WildcardPattern(Pattern):
    """Wildcard pattern: `_`."""


@dataclass
class IdentPattern(Pattern):
    """Identifier pattern: binds the matched value to a name."""

    name: str = ""


@dataclass
class LiteralPattern(Pattern):
    """Literal pattern: matches a specific literal value."""

    value: Expr = field(default_factory=Expr)


@dataclass
class ConstructorPattern(Pattern):
    """Constructor pattern: `Some(v)`, `Err(e)`, `Circle(r)`."""

    name: str = ""
    args: list[Pattern] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Definitions
# ---------------------------------------------------------------------------


@dataclass
class Decorator(ASTNode):
    """Decorator annotation: `@name` or `@name(args)`."""

    name: str = ""
    args: list[Expr] = field(default_factory=list)


@dataclass
class Definition(ASTNode):
    """Base for top-level definitions."""


@dataclass
class DocComment(Definition):
    """Doc comment block: one or more `///` lines attached to a definition."""

    text: str = ""
    definition: "Definition | None" = None


@dataclass
class TypeParam(ASTNode):
    """Type parameter with optional trait bound: `T` or `T: Ord`."""

    name: str = ""
    bound: str | None = None


@dataclass
class Param(ASTNode):
    """Function parameter: `name: Type`."""

    name: str = ""
    type_annotation: TypeExpr | None = None


@dataclass
class FnDef(Definition):
    """Function definition: `fn name(params) -> RetType { body }`."""

    name: str = ""
    public: bool = False
    type_params: list[str] = field(default_factory=list)
    params: list[Param] = field(default_factory=list)
    return_type: TypeExpr | None = None
    body: Block = field(default_factory=lambda: Block())
    decorators: list[Decorator] = field(default_factory=list)
    trait_bounds: dict[str, str] = field(default_factory=dict)


@dataclass
class ExternFnDef(Definition):
    """External function declaration: `extern "C" fn name(params) -> RetType`.

    For Python interop: `extern "Python" fn module::name(params) -> RetType`.
    The `module` field holds the Python module name (e.g. "math").
    """

    name: str = ""
    abi: str = "C"
    params: list[Param] = field(default_factory=list)
    return_type: TypeExpr | None = None
    module: str | None = None


@dataclass
class AgentInput(ASTNode):
    """Agent input channel: `input name: Type`."""

    name: str = ""
    type_annotation: TypeExpr = field(default_factory=lambda: NamedType())


@dataclass
class AgentOutput(ASTNode):
    """Agent output channel: `output name: Type`."""

    name: str = ""
    type_annotation: TypeExpr = field(default_factory=lambda: NamedType())


@dataclass
class AgentDef(Definition):
    """Agent definition."""

    name: str = ""
    public: bool = False
    inputs: list[AgentInput] = field(default_factory=list)
    outputs: list[AgentOutput] = field(default_factory=list)
    state: list[LetBinding] = field(default_factory=list)
    methods: list[FnDef] = field(default_factory=list)
    decorators: list[Decorator] = field(default_factory=list)


@dataclass
class PipeDef(Definition):
    """Pipe definition: `pipe Name { A |> B |> C }`."""

    name: str = ""
    public: bool = False
    stages: list[Expr] = field(default_factory=list)


@dataclass
class StructField(ASTNode):
    """Struct field: `name: Type`."""

    name: str = ""
    type_annotation: TypeExpr = field(default_factory=lambda: NamedType())


@dataclass
class StructDef(Definition):
    """Struct definition: `struct Name { fields }`."""

    name: str = ""
    public: bool = False
    type_params: list[str] = field(default_factory=list)
    fields: list[StructField] = field(default_factory=list)


@dataclass
class EnumVariant(ASTNode):
    """Enum variant: `Name` or `Name(Type, ...)`."""

    name: str = ""
    fields: list[TypeExpr] = field(default_factory=list)


@dataclass
class EnumDef(Definition):
    """Enum definition: `enum Name { variants }`."""

    name: str = ""
    public: bool = False
    type_params: list[str] = field(default_factory=list)
    variants: list[EnumVariant] = field(default_factory=list)


@dataclass
class TypeAlias(Definition):
    """Type alias: `type Name = Type`."""

    name: str = ""
    public: bool = False
    type_expr: TypeExpr = field(default_factory=lambda: NamedType())


@dataclass
class TraitMethod(ASTNode):
    """Method signature in a trait definition (no body)."""

    name: str = ""
    params: list[Param] = field(default_factory=list)
    has_self: bool = False
    return_type: TypeExpr | None = None


@dataclass
class TraitDef(Definition):
    """Trait definition: `trait Name { method_signatures }`."""

    name: str = ""
    public: bool = False
    methods: list[TraitMethod] = field(default_factory=list)


@dataclass
class ImplDef(Definition):
    """Impl block: `impl Name { methods }` or `impl Trait for Type { methods }`."""

    target: str = ""
    trait_name: str | None = None
    methods: list[FnDef] = field(default_factory=list)


@dataclass
class ImportDef(Definition):
    """Import: `import module::item` or `import module`."""

    path: list[str] = field(default_factory=list)
    items: list[str] = field(default_factory=list)


@dataclass
class ExportDef(Definition):
    """Export: `export fn ...` or `export item`."""

    definition: Definition | None = None
    names: list[str] = field(default_factory=list)


@dataclass
class SignalDecl(Stmt):
    """Signal declaration as a statement (inside agent or fn)."""

    name: str = ""
    mutable: bool = False
    type_annotation: TypeExpr | None = None
    value: Expr = field(default_factory=Expr)
    is_computed: bool = False


@dataclass
class StreamDecl(Stmt):
    """Stream declaration."""

    name: str = ""
    type_annotation: TypeExpr | None = None
    value: Expr = field(default_factory=Expr)
