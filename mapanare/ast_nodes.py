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
    """A named type like `Int`, `String`, `MyStruct`, or `mod.Type`."""

    name: str = ""
    module_path: list[str] = field(default_factory=list)


@dataclass
class GenericType(TypeExpr):
    """A generic type like `List<Int>`, `mod.List<Int>`."""

    name: str = ""
    module_path: list[str] = field(default_factory=list)
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
    trait_dispatch: str | None = (
        None  # Set by semantic checker for trait-based ops (e.g., "add", "eq")
    )


@dataclass
class ChainedCompare(Expr):
    """Chained comparison: `0 < x < 10` (3+ operands).

    v5.21.0 Te.6: parses 3+ comparison operands into a single node.
    `len(ops) == len(operands) - 1`; each `ops[i]` is one of
    `< <= > >= == !=`. Lowered to `&&`-joined pairwise comparisons
    with non-trivial interior operands bound to a fresh temp so
    each subexpression is evaluated exactly once.

    2-element comparisons (`a < b`) keep the existing `BinaryExpr`
    AST shape — byte-identical IR before and after v5.21.0.

    `pair_trait_dispatches` mirrors `BinaryExpr.trait_dispatch`
    per pair; populated by the semantic checker so the lowerer
    can route each synthesized pair through the right trait method.
    """

    operands: list[Expr] = field(default_factory=list)
    ops: list[str] = field(default_factory=list)
    pair_trait_dispatches: list[str | None] = field(default_factory=list)


@dataclass
class UnaryExpr(Expr):
    """Unary operation: `-x`, `!flag`."""

    op: str = ""
    operand: Expr = field(default_factory=Expr)


@dataclass
class CallExpr(Expr):
    """Function call: `foo(a, b)` or generic call: `foo::<T>(a, b)`."""

    callee: Expr = field(default_factory=Expr)
    args: list[Expr] = field(default_factory=list)
    type_args: list[TypeExpr] = field(default_factory=list)


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
class IndexItem(ASTNode):
    """An item in a multi-index: scalar, range (N..M), or wildcard (:).

    v4.45.0: Added for tensor slicing.
    kind: "scalar" | "range" | "wildcard"
    """

    kind: str = "scalar"
    expr: Expr | None = None  # scalar value
    start: Expr | None = None  # range start
    end: Expr | None = None  # range end


@dataclass
class IndexExpr(Expr):
    """Index expression: `arr[i]`, `tensor[i, j]`, or `tensor[0..2, :]`.

    v4.43.0: multi-index. v4.45.0: range and wildcard items.
    indices: list of IndexItem (scalar wraps an Expr).
    """

    object: Expr = field(default_factory=Expr)
    indices: list[IndexItem] = field(default_factory=list)


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


# v4.68.0: ``AwaitExpr`` restored (Arc 8). Backed by v4.67.0/DESIGN.md §3.
# Lowering to LLVM coroutine intrinsics arrives at v4.70.0; until then
# the lowerer emits a rustc-quality "under construction" diagnostic.


@dataclass
class AwaitExpr(Expr):
    """Await expression: `await future_expr`.

    Suspends the current coroutine until the operand Future<T> is ready.
    Only valid inside ``async fn`` bodies (enforced at semantic time, v4.69.0).
    See v4.67.0/DESIGN.md §3.2.
    """

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
class CompClause(ASTNode):
    """One `for x in iter (if cond)*` clause in a comprehension (v5.15.0)."""

    target: str = ""
    iter: Expr = field(default_factory=Expr)
    conditions: list[Expr] = field(default_factory=list)


@dataclass
class Comprehension(Expr):
    """List or map comprehension (v5.15.0 Te.2.B/C).

    Sugar over `let mut __r = []; for x in xs { if c { __r.push(e) } }; __r`.
    Lowered by AST synthesis in lower.py — no new MIR ops.
    """

    kind: str = "list"  # "list" or "map"
    element: Expr | None = None  # for list comp
    key: Expr | None = None  # for map comp
    value: Expr | None = None  # for map comp
    clauses: list[CompClause] = field(default_factory=list)


@dataclass
class TensorLiteral(Expr):
    """Tensor literal: `Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]`.

    v4.42.0: elements is flattened to row-major order by the parser.
    shape is inferred from nesting depth + per-level element counts.
    """

    element_type: TypeExpr = field(default_factory=lambda: NamedType())
    shape: list[int] = field(default_factory=list)
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
class StructUpdate(Expr):
    """Struct update: `new Point { x: 5, ..old }`. v5.20.0 Te.5.C.

    Lowers to a `ConstructExpr` with overrides plus per-field
    accesses on the base for any field not in `overrides`. Single
    `base` only (D2). Field list must be completed at lower time
    when the struct definition is in scope.
    """

    name: str = ""
    overrides: list[FieldInit] = field(default_factory=list)
    base: Expr = field(default_factory=Expr)


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
class LetDestructure(Stmt):
    """v5.20.0 Te.5.D: `let <StructPattern> [: T] = <expr>`.

    Lowers to `let __mn_dst_N = expr` followed by per-field lets;
    when `value` is a bare Identifier, the tmp is skipped and the
    field accesses run on the source name directly. `mutable`
    here is the outer `let mut` — applies to every bound name
    that doesn't have its own `mut` already.
    """

    pattern: StructPattern = field(default_factory=lambda: StructPattern())
    mutable: bool = False
    type_annotation: TypeExpr | None = None
    value: Expr = field(default_factory=Expr)


@dataclass
class LetElseStmt(Stmt):
    """v5.20.0 Te.5.E: `let <ConstructorPattern> = <scrutinee> else { ... }`.

    Refutable binding with mandatory diverging else block. Pattern is
    one of: ConstructorPattern (Some/Ok/Err with single ident or
    wildcard arg) or WildcardPattern. Else block must diverge — D5.
    Lowered as: `let bound_name = match scrutinee { pat => bound_name,
    _ => { else_block } }`.
    """

    pattern: "Pattern" = field(default_factory=lambda: Pattern())
    scrutinee: Expr = field(default_factory=Expr)
    else_block: Block = field(default_factory=lambda: Block())


@dataclass
class WhileLetStmt(Stmt):
    """v5.20.0 Te.5.E: `while let <pattern> = <scrutinee> { body }`.

    Desugars to `while true { match scrutinee { pat => body,
    _ => break } }`. Scrutinee is re-evaluated each iteration
    (matches Rust).
    """

    pattern: "Pattern" = field(default_factory=lambda: Pattern())
    scrutinee: Expr = field(default_factory=Expr)
    body: Block = field(default_factory=lambda: Block())


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
    """Break statement: `break` / `sal`."""

    pass


@dataclass
class ContinueStmt(Stmt):
    """Continue statement: `continue` / `sigue`."""

    pass


@dataclass
class PassStmt(Stmt):
    """Pass statement: `pass` — explicit no-op (v5.14.0 Te.1).

    Required by colon-block syntax to mark empty bodies
    (``fn empty(): pass``). Also legal as a stand-alone stmt in
    brace blocks. Emits zero MIR / no LLVM output.
    """

    pass


@dataclass
class AssertStmt(Stmt):
    """Assert statement: `assert expr` or `assert expr, "message"`."""

    condition: Expr = field(default_factory=Expr)
    message: Expr | None = None


@dataclass
class PrintStmt(Stmt):
    """Print statement: `di expr`."""

    expr: Expr = field(default_factory=Expr)


@dataclass
class ForLoop(Stmt):
    """For loop: `for x in items { ... }`."""

    var_name: str = ""
    iterable: Expr = field(default_factory=Expr)
    body: Block = field(default_factory=lambda: Block())


@dataclass
class ForAwaitLoop(Stmt):
    """Async for loop: `for await x in stream { ... }`.

    Desugars to a loop calling `await stream.next()` and matching
    `Some(x)` / `None`. See v4.67.0/DESIGN.md §3.6.
    """

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
class IfLetExpr(Expr):
    """v5.20.0 Te.5.E: `if let <pattern> = <scrutinee> { ... } [else { ... }]`.

    Desugars to a match: success arm runs then_block; wildcard arm
    runs else_block (or `()` when omitted).
    """

    pattern: "Pattern" = field(default_factory=lambda: Pattern())
    scrutinee: Expr = field(default_factory=Expr)
    then_block: Block = field(default_factory=lambda: Block())
    else_block: Block | "IfExpr | IfLetExpr | None" = None


@dataclass
class MatchArm(ASTNode):
    """A single arm in a match expression."""

    pattern: Pattern = field(default_factory=lambda: Pattern())
    body: Expr | Block = field(default_factory=Expr)
    guard: Expr | None = None


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


@dataclass
class OrPattern(Pattern):
    """Or-pattern: matches if any alternative matches. `A | B | C`."""

    alternatives: list[Pattern] = field(default_factory=list)


@dataclass
class FieldPattern(ASTNode):
    """v5.20.0 Te.5.D: a single field within a StructPattern.

    `name`            — shorthand binds the field to a local of the
                        same name; sub_pattern is None.
    `mut name`        — same as above, mutable.
    `name: <pattern>` — destructure the field into a nested pattern;
                        the outer name is NOT bound.
    `mut` is meaningful only when sub_pattern is None.
    """

    name: str = ""
    mutable: bool = False
    sub_pattern: Pattern | None = None


@dataclass
class StructPattern(Pattern):
    """v5.20.0 Te.5.D: `Name { field, field, .. }` in a `let` binding.

    `has_rest=True` means the pattern ended in `..` — fields not
    listed are not bound (and not validated against the struct).
    """

    name: str = ""
    fields: list[FieldPattern] = field(default_factory=list)
    has_rest: bool = False


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
class AsyncFnDef(Definition):
    """Async function definition: `async fn name(params) -> RetType { body }`.

    The declared return type T is sugar for Future<T>. Lowering to LLVM
    coroutine intrinsics arrives at v4.70.0; until then the lowerer emits
    a rustc-quality "under construction" diagnostic. See v4.67.0/DESIGN.md §3.1.
    """

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
    type_params: list[str] = field(default_factory=list)


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
class ModuleLetDef(Definition):
    """Module-level constant: `let NAME: TYPE = EXPR`."""

    name: str = ""
    type_name: str = ""
    value: Expr | None = None


@dataclass
class ConstDef(Definition):
    """v4.55.0: Real const definition — ``const NAME: TYPE = EXPR``.

    Distinct from ``ModuleLetDef``:
    - ``type_expr`` is the full ``TypeExpr`` (not collapsed to a string)
    - Requires a compile-time constant initializer
    - Immutability enforced by the semantic checker
    - Can be used in tensor shape positions
    """

    name: str = ""
    type_expr: TypeExpr | None = None  # full TypeExpr, not collapsed to .name
    value: Expr | None = None


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
