"""Mapanare LSP analysis — symbol extraction, hover, go-to-def, find-refs, completion."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from mapa.ast_nodes import (
    AgentDef,
    BinaryExpr,
    Block,
    CallExpr,
    ConstructExpr,
    Definition,
    EnumDef,
    ExportDef,
    Expr,
    ExprStmt,
    FieldAccessExpr,
    FnDef,
    ForLoop,
    GenericType,
    Identifier,
    IfExpr,
    ImplDef,
    ImportDef,
    IndexExpr,
    LambdaExpr,
    LetBinding,
    MatchExpr,
    MethodCallExpr,
    NamedType,
    PipeDef,
    PipeExpr,
    Program,
    ReturnStmt,
    SendExpr,
    SignalDecl,
    SignalExpr,
    Span,
    SpawnExpr,
    Stmt,
    StructDef,
    SyncExpr,
    TypeAlias,
    TypeExpr,
    UnaryExpr,
)
from mapa.semantic import (
    BUILTIN_FUNCTIONS,
    BUILTIN_GENERIC_TYPES,
    PRIMITIVE_TYPES,
    SemanticError,
)


@dataclass
class SymbolLocation:
    """A source location for a symbol definition or reference."""

    uri: str
    line: int  # 0-based
    column: int  # 0-based
    end_line: int  # 0-based
    end_column: int  # 0-based


@dataclass
class SymbolInfo:
    """Information about a symbol found during analysis."""

    name: str
    kind: str  # "function", "agent", "variable", "struct", "enum", "pipe", "param", "field", etc.
    type_display: str  # Human-readable type string
    detail: str  # Additional detail (e.g. function signature)
    definition: SymbolLocation
    references: list[SymbolLocation] = field(default_factory=list)
    doc: str = ""  # Documentation / hover text


def _span_to_location(span: Span, uri: str) -> SymbolLocation:
    """Convert an AST Span to a SymbolLocation (0-based lines)."""
    return SymbolLocation(
        uri=uri,
        line=max(0, span.line - 1),
        column=max(0, span.column - 1),
        end_line=max(0, span.end_line - 1) if span.end_line else max(0, span.line - 1),
        end_column=max(0, span.end_column - 1) if span.end_column else max(0, span.column - 1),
    )


def _type_expr_display(te: TypeExpr | None) -> str:
    """Render a TypeExpr as a human-readable string."""
    if te is None:
        return ""
    if isinstance(te, NamedType):
        return te.name
    if isinstance(te, GenericType):
        args = ", ".join(_type_expr_display(a) for a in te.args)
        return f"{te.name}<{args}>"
    return str(te)


def _fn_signature(fn: FnDef) -> str:
    """Build a human-readable function signature string."""
    params = ", ".join(
        f"{p.name}: {_type_expr_display(p.type_annotation)}" if p.type_annotation else p.name
        for p in fn.params
    )
    ret = f" -> {_type_expr_display(fn.return_type)}" if fn.return_type else ""
    pub = "pub " if fn.public else ""
    tparams = f"<{', '.join(fn.type_params)}>" if fn.type_params else ""
    return f"{pub}fn {fn.name}{tparams}({params}){ret}"


def _agent_signature(agent: AgentDef) -> str:
    """Build a human-readable agent summary."""
    inputs = ", ".join(f"{i.name}: {_type_expr_display(i.type_annotation)}" for i in agent.inputs)
    outputs = ", ".join(f"{o.name}: {_type_expr_display(o.type_annotation)}" for o in agent.outputs)
    pub = "pub " if agent.public else ""
    parts = [f"{pub}agent {agent.name}"]
    if inputs:
        parts.append(f"  input {inputs}")
    if outputs:
        parts.append(f"  output {outputs}")
    methods = [m.name for m in agent.methods]
    if methods:
        parts.append(f"  methods: {', '.join(methods)}")
    return "\n".join(parts)


class DocumentAnalysis:
    """Analyzes a single Mapanare document for LSP features.

    Extracts symbol definitions, references, types, and provides:
    - hover info
    - go-to-definition
    - find-references
    - completions
    """

    def __init__(self, uri: str, source: str, program: Program) -> None:
        self.uri = uri
        self.source = source
        self.program = program
        self.symbols: dict[str, SymbolInfo] = {}
        self._references: list[tuple[str, SymbolLocation]] = []
        self._all_locations: list[tuple[str, str, SymbolLocation]] = []  # (name, kind, loc)

        self._extract_symbols()

    def _extract_symbols(self) -> None:
        """Walk the AST and collect all symbol definitions and references."""
        for defn in self.program.definitions:
            self._visit_definition(defn)

    def _add_symbol(self, info: SymbolInfo) -> None:
        self.symbols[info.name] = info

    def _add_reference(self, name: str, loc: SymbolLocation) -> None:
        self._references.append((name, loc))
        if name in self.symbols:
            self.symbols[name].references.append(loc)

    def _visit_definition(self, defn: Definition) -> None:
        if isinstance(defn, FnDef):
            self._visit_fn_def(defn)
        elif isinstance(defn, AgentDef):
            self._visit_agent_def(defn)
        elif isinstance(defn, StructDef):
            self._visit_struct_def(defn)
        elif isinstance(defn, EnumDef):
            self._visit_enum_def(defn)
        elif isinstance(defn, PipeDef):
            self._visit_pipe_def(defn)
        elif isinstance(defn, TypeAlias):
            self._visit_type_alias(defn)
        elif isinstance(defn, ImplDef):
            self._visit_impl_def(defn)
        elif isinstance(defn, ImportDef):
            pass  # imports don't create local definitions from source
        elif isinstance(defn, ExportDef):
            if defn.definition:
                self._visit_definition(defn.definition)

    def _visit_fn_def(self, fn: FnDef) -> None:
        loc = _span_to_location(fn.span, self.uri)
        sig = _fn_signature(fn)
        self._add_symbol(
            SymbolInfo(
                name=fn.name,
                kind="function",
                type_display=sig,
                detail=sig,
                definition=loc,
                doc=f"Function `{fn.name}`",
            )
        )
        for p in fn.params:
            if p.span.line > 0:
                ploc = _span_to_location(p.span, self.uri)
            else:
                ploc = loc
            self._add_symbol(
                SymbolInfo(
                    name=p.name,
                    kind="param",
                    type_display=_type_expr_display(p.type_annotation),
                    detail=f"parameter {p.name}: {_type_expr_display(p.type_annotation)}",
                    definition=ploc,
                )
            )
        self._visit_block(fn.body)

    def _visit_agent_def(self, agent: AgentDef) -> None:
        loc = _span_to_location(agent.span, self.uri)
        sig = _agent_signature(agent)
        self._add_symbol(
            SymbolInfo(
                name=agent.name,
                kind="agent",
                type_display=f"agent {agent.name}",
                detail=sig,
                definition=loc,
                doc=f"Agent `{agent.name}`",
            )
        )
        for inp in agent.inputs:
            if inp.span.line > 0:
                iloc = _span_to_location(inp.span, self.uri)
            else:
                iloc = loc
            self._add_symbol(
                SymbolInfo(
                    name=inp.name,
                    kind="field",
                    type_display=_type_expr_display(inp.type_annotation),
                    detail=f"input {inp.name}: {_type_expr_display(inp.type_annotation)}",
                    definition=iloc,
                )
            )
        for out in agent.outputs:
            if out.span.line > 0:
                oloc = _span_to_location(out.span, self.uri)
            else:
                oloc = loc
            self._add_symbol(
                SymbolInfo(
                    name=out.name,
                    kind="field",
                    type_display=_type_expr_display(out.type_annotation),
                    detail=f"output {out.name}: {_type_expr_display(out.type_annotation)}",
                    definition=oloc,
                )
            )
        for s in agent.state:
            self._visit_stmt(s)
        for m in agent.methods:
            self._visit_fn_def(m)

    def _visit_struct_def(self, s: StructDef) -> None:
        loc = _span_to_location(s.span, self.uri)
        fields_str = ", ".join(
            f"{f.name}: {_type_expr_display(f.type_annotation)}" for f in s.fields
        )
        self._add_symbol(
            SymbolInfo(
                name=s.name,
                kind="struct",
                type_display=f"struct {s.name}",
                detail=f"struct {s.name} {{ {fields_str} }}",
                definition=loc,
                doc=f"Struct `{s.name}`",
            )
        )
        for fld in s.fields:
            if fld.span.line > 0:
                floc = _span_to_location(fld.span, self.uri)
            else:
                floc = loc
            self._add_symbol(
                SymbolInfo(
                    name=f"{s.name}.{fld.name}",
                    kind="field",
                    type_display=_type_expr_display(fld.type_annotation),
                    detail=f"{fld.name}: {_type_expr_display(fld.type_annotation)}",
                    definition=floc,
                )
            )

    def _visit_enum_def(self, e: EnumDef) -> None:
        loc = _span_to_location(e.span, self.uri)
        variants_str = ", ".join(v.name for v in e.variants)
        self._add_symbol(
            SymbolInfo(
                name=e.name,
                kind="enum",
                type_display=f"enum {e.name}",
                detail=f"enum {e.name} {{ {variants_str} }}",
                definition=loc,
                doc=f"Enum `{e.name}`",
            )
        )
        for v in e.variants:
            if v.fields:
                fields_str = ", ".join(_type_expr_display(f) for f in v.fields)
                detail = f"{v.name}({fields_str})"
            else:
                detail = v.name
            self._add_symbol(
                SymbolInfo(
                    name=v.name,
                    kind="enum_variant",
                    type_display=e.name,
                    detail=detail,
                    definition=loc,
                )
            )

    def _visit_pipe_def(self, p: PipeDef) -> None:
        loc = _span_to_location(p.span, self.uri)
        stages = " |> ".join(e.name if isinstance(e, Identifier) else "..." for e in p.stages)
        self._add_symbol(
            SymbolInfo(
                name=p.name,
                kind="pipe",
                type_display=f"pipe {p.name}",
                detail=f"pipe {p.name} {{ {stages} }}",
                definition=loc,
                doc=f"Pipe `{p.name}`",
            )
        )
        for stage in p.stages:
            self._visit_expr(stage)

    def _visit_type_alias(self, ta: TypeAlias) -> None:
        loc = _span_to_location(ta.span, self.uri)
        self._add_symbol(
            SymbolInfo(
                name=ta.name,
                kind="type_alias",
                type_display=_type_expr_display(ta.type_expr),
                detail=f"type {ta.name} = {_type_expr_display(ta.type_expr)}",
                definition=loc,
            )
        )

    def _visit_impl_def(self, impl: ImplDef) -> None:
        for m in impl.methods:
            self._visit_fn_def(m)

    def _visit_block(self, block: Block) -> None:
        for stmt in block.stmts:
            self._visit_stmt(stmt)

    def _visit_stmt(self, stmt: Stmt) -> None:
        if isinstance(stmt, LetBinding):
            loc = _span_to_location(stmt.span, self.uri)
            mut = "mut " if stmt.mutable else ""
            type_str = _type_expr_display(stmt.type_annotation)
            self._add_symbol(
                SymbolInfo(
                    name=stmt.name,
                    kind="variable",
                    type_display=type_str,
                    detail=f"let {mut}{stmt.name}: {type_str}"
                    if type_str
                    else f"let {mut}{stmt.name}",
                    definition=loc,
                )
            )
            self._visit_expr(stmt.value)
        elif isinstance(stmt, ExprStmt):
            self._visit_expr(stmt.expr)
        elif isinstance(stmt, ReturnStmt):
            if stmt.value:
                self._visit_expr(stmt.value)
        elif isinstance(stmt, ForLoop):
            self._visit_expr(stmt.iterable)
            self._visit_block(stmt.body)
        elif isinstance(stmt, SignalDecl):
            loc = _span_to_location(stmt.span, self.uri)
            self._add_symbol(
                SymbolInfo(
                    name=stmt.name,
                    kind="variable",
                    type_display=f"Signal<{_type_expr_display(stmt.type_annotation)}>",
                    detail=f"signal {stmt.name}",
                    definition=loc,
                )
            )
            self._visit_expr(stmt.value)

    def _visit_expr(self, expr: Expr) -> None:
        if isinstance(expr, Identifier):
            if expr.span.line > 0:
                loc = _span_to_location(expr.span, self.uri)
                self._add_reference(expr.name, loc)
        elif isinstance(expr, BinaryExpr):
            self._visit_expr(expr.left)
            self._visit_expr(expr.right)
        elif isinstance(expr, UnaryExpr):
            self._visit_expr(expr.operand)
        elif isinstance(expr, CallExpr):
            self._visit_expr(expr.callee)
            for a in expr.args:
                self._visit_expr(a)
        elif isinstance(expr, MethodCallExpr):
            self._visit_expr(expr.object)
            for a in expr.args:
                self._visit_expr(a)
        elif isinstance(expr, FieldAccessExpr):
            self._visit_expr(expr.object)
        elif isinstance(expr, IndexExpr):
            self._visit_expr(expr.object)
            self._visit_expr(expr.index)
        elif isinstance(expr, PipeExpr):
            self._visit_expr(expr.left)
            self._visit_expr(expr.right)
        elif isinstance(expr, IfExpr):
            self._visit_expr(expr.condition)
            self._visit_block(expr.then_block)
            if isinstance(expr.else_block, Block):
                self._visit_block(expr.else_block)
            elif isinstance(expr.else_block, IfExpr):
                self._visit_expr(expr.else_block)
        elif isinstance(expr, MatchExpr):
            self._visit_expr(expr.subject)
            for arm in expr.arms:
                if isinstance(arm.body, Block):
                    self._visit_block(arm.body)
                elif isinstance(arm.body, Expr):
                    self._visit_expr(arm.body)
        elif isinstance(expr, LambdaExpr):
            if isinstance(expr.body, Block):
                self._visit_block(expr.body)
            elif isinstance(expr.body, Expr):
                self._visit_expr(expr.body)
        elif isinstance(expr, SpawnExpr):
            self._visit_expr(expr.callee)
            for a in expr.args:
                self._visit_expr(a)
        elif isinstance(expr, SyncExpr):
            self._visit_expr(expr.expr)
        elif isinstance(expr, SendExpr):
            self._visit_expr(expr.target)
            self._visit_expr(expr.value)
        elif isinstance(expr, SignalExpr):
            self._visit_expr(expr.value)
        elif isinstance(expr, ConstructExpr):
            self._add_reference(
                expr.name,
                _span_to_location(expr.span, self.uri),
            )
            for fi in expr.fields:
                self._visit_expr(fi.value)

    def hover_at(self, line: int, col: int) -> Optional[str]:
        """Return hover info at the given 0-based position."""
        for sym in self.symbols.values():
            d = sym.definition
            if d.uri == self.uri and d.line == line:
                if d.column <= col <= d.end_column + len(sym.name):
                    return f"```mapanare\n{sym.detail}\n```"
        # Check references
        for name, loc in self._references:
            if loc.uri == self.uri and loc.line == line:
                if loc.column <= col <= loc.end_column + len(name):
                    if name in self.symbols:
                        return f"```mapanare\n{self.symbols[name].detail}\n```"
        # Check builtins
        source_lines = self.source.split("\n")
        if 0 <= line < len(source_lines):
            line_text = source_lines[line]
            word = _word_at(line_text, col)
            if word in BUILTIN_FUNCTIONS:
                ret = BUILTIN_FUNCTIONS[word]
                return f"```mapanare\nbuiltin fn {word}(...) -> {ret}\n```"
            if word in PRIMITIVE_TYPES:
                return f"```mapanare\ntype {word}\n```"
            if word in BUILTIN_GENERIC_TYPES:
                return f"```mapanare\ntype {word}<T>\n```"
        return None

    def definition_at(self, line: int, col: int) -> Optional[SymbolLocation]:
        """Return the definition location for the symbol at the given 0-based position."""
        name = self._symbol_name_at(line, col)
        if name and name in self.symbols:
            return self.symbols[name].definition
        return None

    def references_at(self, line: int, col: int) -> list[SymbolLocation]:
        """Return all reference locations for the symbol at the given 0-based position."""
        name = self._symbol_name_at(line, col)
        if not name:
            return []
        refs: list[SymbolLocation] = []
        if name in self.symbols:
            refs.append(self.symbols[name].definition)
            refs.extend(self.symbols[name].references)
        return refs

    def completions_at(self, line: int, col: int) -> list[CompletionItem]:
        """Return completion candidates at the given 0-based position."""
        items: list[CompletionItem] = []

        # Add all symbols from this document
        for sym in self.symbols.values():
            items.append(
                CompletionItem(
                    label=sym.name,
                    kind=_symbol_kind_to_completion(sym.kind),
                    detail=sym.detail,
                    documentation=sym.doc,
                )
            )

        # Add keywords
        for kw in _KEYWORDS:
            items.append(CompletionItem(label=kw, kind="keyword", detail="keyword"))

        # Add builtin functions
        for name, ret in BUILTIN_FUNCTIONS.items():
            items.append(
                CompletionItem(
                    label=name,
                    kind="function",
                    detail=f"builtin fn {name}(...) -> {ret}",
                )
            )

        # Add primitive types
        for t in sorted(PRIMITIVE_TYPES):
            items.append(CompletionItem(label=t, kind="type", detail=f"type {t}"))

        # Add generic types
        for t in sorted(BUILTIN_GENERIC_TYPES):
            items.append(CompletionItem(label=t, kind="type", detail=f"type {t}<T>"))

        return items

    def _symbol_name_at(self, line: int, col: int) -> Optional[str]:
        """Get the symbol name at the given position."""
        # Check definitions
        for name, sym in self.symbols.items():
            d = sym.definition
            if d.uri == self.uri and d.line == line:
                if d.column <= col <= d.end_column + len(name):
                    return name
        # Check references
        for name, loc in self._references:
            if loc.uri == self.uri and loc.line == line:
                if loc.column <= col <= loc.end_column + len(name):
                    return name
        # Fall back to word under cursor
        source_lines = self.source.split("\n")
        if 0 <= line < len(source_lines):
            word = _word_at(source_lines[line], col)
            if word:
                return word
        return None


@dataclass
class CompletionItem:
    """A completion candidate."""

    label: str
    kind: str  # "function", "variable", "keyword", "type", "struct", etc.
    detail: str = ""
    documentation: str = ""


_KEYWORDS = [
    "let",
    "mut",
    "fn",
    "return",
    "pub",
    "agent",
    "spawn",
    "sync",
    "signal",
    "stream",
    "pipe",
    "if",
    "else",
    "match",
    "for",
    "in",
    "type",
    "struct",
    "enum",
    "impl",
    "import",
    "export",
    "true",
    "false",
    "none",
    "input",
    "output",
]


def _symbol_kind_to_completion(kind: str) -> str:
    return {
        "function": "function",
        "agent": "class",
        "variable": "variable",
        "struct": "struct",
        "enum": "enum",
        "enum_variant": "enum_member",
        "pipe": "function",
        "param": "variable",
        "field": "field",
        "type_alias": "type",
    }.get(kind, "text")


def _word_at(line: str, col: int) -> str:
    """Extract the word at the given column position."""
    if col < 0 or col >= len(line):
        return ""
    # Walk left to find word start
    start = col
    while start > 0 and (line[start - 1].isalnum() or line[start - 1] == "_"):
        start -= 1
    # Walk right to find word end
    end = col
    while end < len(line) and (line[end].isalnum() or line[end] == "_"):
        end += 1
    return line[start:end]


def analyze_document(uri: str, source: str) -> tuple[DocumentAnalysis | None, list[SemanticError]]:
    """Parse and analyze a Mapanare document.

    Returns (analysis, errors). Analysis may be None if parsing fails.
    Errors are always returned for diagnostics.
    """
    from mapa.parser import ParseError, parse
    from mapa.semantic import check

    errors: list[SemanticError] = []

    try:
        program = parse(source, filename=uri)
    except ParseError as e:
        errors.append(
            SemanticError(
                message=e.message,
                line=e.line,
                column=e.column,
                filename=uri,
            )
        )
        return None, errors

    semantic_errors = check(program, filename=uri)
    errors.extend(semantic_errors)

    analysis = DocumentAnalysis(uri, source, program)
    return analysis, errors
