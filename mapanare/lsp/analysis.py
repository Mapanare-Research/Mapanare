"""Mapanare LSP analysis — symbol extraction, hover, go-to-def, find-refs, completion.

Supports incremental parsing, semantic-aware completion, cross-module go-to-def,
and inline diagnostics with fix suggestions.
"""

from __future__ import annotations

import difflib
import hashlib
import os
import re
from dataclasses import dataclass, field
from typing import Optional

from mapanare.ast_nodes import (
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
    ExternFnDef,
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
    TraitDef,
    TypeAlias,
    TypeExpr,
    UnaryExpr,
    WhileLoop,
)
from mapanare.semantic import (
    BUILTIN_FUNCTIONS,
    BUILTIN_GENERIC_TYPES,
    PRIMITIVE_TYPES,
    SemanticError,
)

# ---------------------------------------------------------------------------
# Top-level chunk splitting regex (mirrors parser._TOPLEVEL_RE)
# ---------------------------------------------------------------------------

_TOPLEVEL_RE = re.compile(
    r"^(?:pub\s+)?(?:fn|struct|enum|agent|pipe|trait|impl|import|export|type|let|extern)\b",
    re.MULTILINE,
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


@dataclass
class LspDiagnostic:
    """An enriched diagnostic for LSP with optional fix suggestions."""

    message: str
    line: int  # 1-based
    column: int  # 1-based
    end_line: int = 0  # 1-based, 0 means same as line
    end_column: int = 0  # 1-based, 0 means column+1
    severity: str = "error"  # "error", "warning", "info", "hint"
    suggestions: list[FixSuggestion] = field(default_factory=list)


@dataclass
class FixSuggestion:
    """A suggested code fix for a diagnostic."""

    message: str
    replacement: str = ""
    line: int = 0  # 1-based
    column: int = 0  # 1-based
    end_line: int = 0  # 1-based
    end_column: int = 0  # 1-based


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


# ---------------------------------------------------------------------------
# Incremental parsing cache
# ---------------------------------------------------------------------------


@dataclass
class _ChunkCache:
    """Caches parsed definitions per source chunk for incremental re-parsing."""

    chunk_hashes: list[str] = field(default_factory=list)
    chunk_defs: list[list[Definition]] = field(default_factory=list)


def _split_toplevel_chunks(source: str) -> list[tuple[str, int]]:
    """Split source into top-level chunks at definition boundaries.

    Returns list of (chunk_text, start_line_1based).
    """
    matches = list(_TOPLEVEL_RE.finditer(source))
    if len(matches) <= 1:
        return [(source, 1)]

    chunks: list[tuple[str, int]] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(source)
        chunk = source[start:end]
        line_offset = source[:start].count("\n") + 1
        chunks.append((chunk.rstrip(), line_offset))
    return chunks


def _chunk_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _parse_chunk(chunk_text: str, filename: str) -> list[Definition]:
    """Parse a single top-level chunk and return its definitions."""
    from mapanare.parser import ParseError, parse

    try:
        program = parse(chunk_text, filename=filename)
        return list(program.definitions)
    except ParseError:
        return []


class IncrementalParser:
    """Parses source incrementally by caching per-chunk results.

    On re-parse, only chunks whose text changed are re-parsed.
    Unchanged chunks reuse cached AST definitions.
    """

    def __init__(self) -> None:
        self._cache: dict[str, _ChunkCache] = {}  # uri -> cache

    def parse(self, uri: str, source: str) -> tuple[Program, list["SemanticError"], bool]:
        """Parse source, reusing cached chunks where possible.

        Returns (program, parse_errors, was_incremental).
        was_incremental is True if some chunks were reused from cache.
        """
        from mapanare.parser import ParseError, parse

        # Try full parse first (fast path)
        try:
            program = parse(source, filename=uri)
            # Update cache with new chunk hashes
            chunks = _split_toplevel_chunks(source)
            cache = _ChunkCache()
            for chunk_text, _ in chunks:
                h = _chunk_hash(chunk_text)
                cache.chunk_hashes.append(h)
                # Assign definitions from full parse result to chunks
                # Simple approach: parse each chunk to know its defs for cache
                defs = _parse_chunk(chunk_text, uri)
                cache.chunk_defs.append(defs)
            self._cache[uri] = cache
            return program, [], False
        except ParseError:
            pass

        # Full parse failed — try incremental with cache
        chunks = _split_toplevel_chunks(source)
        prev_cache = self._cache.get(uri)
        new_cache = _ChunkCache()
        all_defs: list[Definition] = []
        errors: list[SemanticError] = []
        was_incremental = False

        for i, (chunk_text, line_offset) in enumerate(chunks):
            h = _chunk_hash(chunk_text)
            new_cache.chunk_hashes.append(h)

            # Reuse cached result if chunk unchanged
            if prev_cache and i < len(prev_cache.chunk_hashes) and prev_cache.chunk_hashes[i] == h:
                defs = prev_cache.chunk_defs[i]
                was_incremental = True
            else:
                defs = _parse_chunk(chunk_text, uri)
                if not defs:
                    # Chunk failed to parse — record error
                    errors.append(
                        SemanticError(
                            message=f"Syntax error in definition at line {line_offset}",
                            line=line_offset,
                            column=1,
                            filename=uri,
                        )
                    )

            new_cache.chunk_defs.append(defs)
            all_defs.extend(defs)

        self._cache[uri] = new_cache
        program = Program(definitions=all_defs)
        return program, errors, was_incremental

    def invalidate(self, uri: str) -> None:
        """Remove cached data for a document."""
        self._cache.pop(uri, None)


# Global incremental parser instance
_incremental_parser = IncrementalParser()


# ---------------------------------------------------------------------------
# Document analysis
# ---------------------------------------------------------------------------


class DocumentAnalysis:
    """Analyzes a single Mapanare document for LSP features.

    Extracts symbol definitions, references, types, and provides:
    - hover info
    - go-to-definition (including cross-module)
    - find-references
    - semantic-aware completions
    """

    def __init__(
        self,
        uri: str,
        source: str,
        program: Program,
        *,
        imported_symbols: dict[str, SymbolInfo] | None = None,
        import_defs: list[ImportDef] | None = None,
        struct_fields: dict[str, list[tuple[str, str]]] | None = None,
        trait_methods: dict[str, list[tuple[str, str]]] | None = None,
        impl_map: dict[str, list[str]] | None = None,
    ) -> None:
        self.uri = uri
        self.source = source
        self.program = program
        self.symbols: dict[str, SymbolInfo] = {}
        self._references: list[tuple[str, SymbolLocation]] = []
        self._all_locations: list[tuple[str, str, SymbolLocation]] = []  # (name, kind, loc)
        self._imported_symbols: dict[str, SymbolInfo] = imported_symbols or {}
        self._import_defs: list[ImportDef] = import_defs or []
        # struct_name -> [(field_name, type_display)]
        self._struct_fields: dict[str, list[tuple[str, str]]] = struct_fields or {}
        # trait_name -> [(method_name, signature)]
        self._trait_methods: dict[str, list[tuple[str, str]]] = trait_methods or {}
        # type_name -> [trait_name, ...] (impls)
        self._impl_map: dict[str, list[str]] = impl_map or {}

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
        elif isinstance(defn, TraitDef):
            self._visit_trait_def(defn)
        elif isinstance(defn, ImportDef):
            pass  # handled externally via imported_symbols
        elif isinstance(defn, ExportDef):
            if defn.definition:
                self._visit_definition(defn.definition)
        elif isinstance(defn, ExternFnDef):
            self._visit_extern_fn_def(defn)

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
        # Cache struct fields for dot-completion
        field_list: list[tuple[str, str]] = []
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
            field_list.append((fld.name, _type_expr_display(fld.type_annotation)))
        self._struct_fields[s.name] = field_list

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
        # Track trait implementations for semantic-aware completion
        if impl.trait_name:
            impls = self._impl_map.setdefault(impl.target, [])
            if impl.trait_name not in impls:
                impls.append(impl.trait_name)
        for m in impl.methods:
            self._visit_fn_def(m)

    def _visit_trait_def(self, trait: TraitDef) -> None:
        loc = _span_to_location(trait.span, self.uri)
        method_names = [m.name for m in trait.methods]
        self._add_symbol(
            SymbolInfo(
                name=trait.name,
                kind="trait",
                type_display=f"trait {trait.name}",
                detail=f"trait {trait.name} {{ {', '.join(method_names)} }}",
                definition=loc,
                doc=f"Trait `{trait.name}`",
            )
        )
        # Cache trait methods for semantic-aware completion
        method_list: list[tuple[str, str]] = []
        for m in trait.methods:
            params = ", ".join(
                (
                    f"{p.name}: {_type_expr_display(p.type_annotation)}"
                    if p.type_annotation
                    else p.name
                )
                for p in m.params
            )
            ret = f" -> {_type_expr_display(m.return_type)}" if m.return_type else ""
            sig = f"fn {m.name}({params}){ret}"
            method_list.append((m.name, sig))
        self._trait_methods[trait.name] = method_list

    def _visit_extern_fn_def(self, fn: ExternFnDef) -> None:
        loc = _span_to_location(fn.span, self.uri)
        params = ", ".join(
            f"{p.name}: {_type_expr_display(p.type_annotation)}" if p.type_annotation else p.name
            for p in fn.params
        )
        ret = f" -> {_type_expr_display(fn.return_type)}" if fn.return_type else ""
        sig = f'extern "{fn.abi}" fn {fn.name}({params}){ret}'
        self._add_symbol(
            SymbolInfo(
                name=fn.name,
                kind="function",
                type_display=sig,
                detail=sig,
                definition=loc,
                doc=f"External function `{fn.name}` (ABI: {fn.abi})",
            )
        )

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
                    detail=(
                        f"let {mut}{stmt.name}: {type_str}" if type_str else f"let {mut}{stmt.name}"
                    ),
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
        elif isinstance(stmt, WhileLoop):
            self._visit_expr(stmt.condition)
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

    # -- Hover ---------------------------------------------------------------

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
                    if name in self._imported_symbols:
                        return f"```mapanare\n{self._imported_symbols[name].detail}\n```"
        # Check builtins
        source_lines = self.source.split("\n")
        if 0 <= line < len(source_lines):
            line_text = source_lines[line]
            word = _word_at(line_text, col)
            if word in self._imported_symbols:
                return f"```mapanare\n{self._imported_symbols[word].detail}\n```"
            if word in BUILTIN_FUNCTIONS:
                ret = BUILTIN_FUNCTIONS[word]
                return f"```mapanare\nbuiltin fn {word}(...) -> {ret}\n```"
            if word in PRIMITIVE_TYPES:
                return f"```mapanare\ntype {word}\n```"
            if word in BUILTIN_GENERIC_TYPES:
                return f"```mapanare\ntype {word}<T>\n```"
        return None

    # -- Go to definition ----------------------------------------------------

    def definition_at(self, line: int, col: int) -> Optional[SymbolLocation]:
        """Return the definition location for the symbol at the given 0-based position.

        Supports cross-module go-to-definition for imported symbols.
        """
        name = self._symbol_name_at(line, col)
        if not name:
            return None
        # Check local symbols first
        if name in self.symbols:
            return self.symbols[name].definition
        # Check imported symbols (cross-module go-to-def)
        if name in self._imported_symbols:
            return self._imported_symbols[name].definition
        return None

    # -- Find references -----------------------------------------------------

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

    # -- Completion ----------------------------------------------------------

    def completions_at(self, line: int, col: int) -> list[CompletionItem]:
        """Return completion candidates at the given 0-based position.

        Semantic-aware: after '.' provides struct fields and trait methods.
        Includes imported module exports.
        """
        # Check if we're in a dot-completion context
        source_lines = self.source.split("\n")
        if 0 <= line < len(source_lines):
            line_text = source_lines[line]
            dot_items = self._dot_completions(line_text, col)
            if dot_items is not None:
                return dot_items

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

        # Add imported symbols (module exports)
        for sym in self._imported_symbols.values():
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

    def _dot_completions(self, line_text: str, col: int) -> list[CompletionItem] | None:
        """If cursor is right after 'expr.', return field/method completions.

        Returns None if not in a dot-completion context.
        """
        # Find the dot before the cursor
        dot_col = col - 1
        # Skip any partial identifier after the dot
        while dot_col >= 0 and (line_text[dot_col].isalnum() or line_text[dot_col] == "_"):
            dot_col -= 1
        if dot_col < 0 or line_text[dot_col] != ".":
            return None

        # Extract the word before the dot (the object name)
        obj_end = dot_col
        obj_start = obj_end - 1
        while obj_start >= 0 and (line_text[obj_start].isalnum() or line_text[obj_start] == "_"):
            obj_start -= 1
        obj_start += 1
        obj_name = line_text[obj_start:obj_end]
        if not obj_name:
            return None

        # Find the type of the object
        type_name = self._resolve_type_name(obj_name)
        if not type_name:
            return None

        items: list[CompletionItem] = []

        # Add struct fields
        if type_name in self._struct_fields:
            for fname, ftype in self._struct_fields[type_name]:
                items.append(
                    CompletionItem(
                        label=fname,
                        kind="field",
                        detail=f"{fname}: {ftype}",
                    )
                )

        # Add trait methods from implemented traits
        if type_name in self._impl_map:
            for trait_name in self._impl_map[type_name]:
                if trait_name in self._trait_methods:
                    for mname, msig in self._trait_methods[trait_name]:
                        items.append(
                            CompletionItem(
                                label=mname,
                                kind="function",
                                detail=msig,
                                documentation=f"From trait `{trait_name}`",
                            )
                        )

        # Add builtin trait methods
        from mapanare.types import BUILTIN_TRAITS

        if type_name in self._impl_map:
            for trait_name in self._impl_map[type_name]:
                if trait_name in BUILTIN_TRAITS:
                    for method_info in BUILTIN_TRAITS[trait_name]:
                        mname = method_info[0]
                        ret_type = method_info[3] or "Void"
                        items.append(
                            CompletionItem(
                                label=mname,
                                kind="function",
                                detail=f"fn {mname}() -> {ret_type}",
                                documentation=f"From builtin trait `{trait_name}`",
                            )
                        )

        # If we found the type but it has no fields/methods, return empty list
        # (not None, so we don't fall through to general completions)
        return items

    def _resolve_type_name(self, name: str) -> str | None:
        """Resolve a variable/param name to its type name for dot-completion."""
        if name in self.symbols:
            sym = self.symbols[name]
            type_display = sym.type_display
            # For variables and params, type_display is the type name
            if sym.kind in ("variable", "param", "field"):
                return type_display if type_display else None
            # For struct instances, the kind would be the struct name
            if sym.kind == "struct":
                return sym.name
        return None

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
    "while",
    "extern",
    "trait",
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
        "trait": "class",
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


# ---------------------------------------------------------------------------
# Cross-module symbol resolution
# ---------------------------------------------------------------------------


def _uri_to_filepath(uri: str) -> str | None:
    """Convert a file:// URI to a filesystem path."""
    if uri.startswith("file:///"):
        # file:///C:/... on Windows or file:///home/... on Unix
        path = uri[len("file:///") :]
        # On Unix the path starts with /, on Windows it starts with drive letter
        if len(path) >= 2 and path[1] == ":":
            return path  # Windows absolute path
        return "/" + path  # Unix absolute path
    if uri.startswith("file://"):
        return uri[len("file://") :]
    return None


def _filepath_to_uri(path: str) -> str:
    """Convert a filesystem path to a file:// URI."""
    path = os.path.abspath(path)
    # Normalize separators
    path = path.replace("\\", "/")
    if path.startswith("/"):
        return f"file://{path}"
    return f"file:///{path}"


def _resolve_imported_symbols(
    uri: str,
    program: Program,
) -> tuple[dict[str, SymbolInfo], list[ImportDef]]:
    """Resolve imported symbols from other modules.

    Returns (imported_symbols, import_defs).
    """
    from mapanare.modules import ModuleResolutionError, ModuleResolver

    filepath = _uri_to_filepath(uri)
    if not filepath:
        return {}, []

    resolver = ModuleResolver()
    imported: dict[str, SymbolInfo] = {}
    import_defs: list[ImportDef] = []

    for defn in program.definitions:
        if not isinstance(defn, ImportDef):
            continue
        import_defs.append(defn)

        try:
            module = resolver.resolve_module(defn.path, filepath)
        except (ModuleResolutionError, Exception):
            continue

        module_uri = _filepath_to_uri(module.filepath)

        # Determine which symbols to import
        if defn.items:
            # Selective import: import foo { bar, baz }
            names_to_import = defn.items
        else:
            # Full module import: import foo — import all public exports
            names_to_import = list(module.exports.keys())

        for name in names_to_import:
            export = module.exports.get(name)
            if not export:
                continue

            # Build SymbolInfo for the imported definition
            export_def = export.definition
            if hasattr(export_def, "span") and export_def.span.line > 0:
                loc = _span_to_location(export_def.span, module_uri)
            else:
                loc = SymbolLocation(uri=module_uri, line=0, column=0, end_line=0, end_column=0)

            kind = "function"
            detail = name
            if isinstance(export_def, FnDef):
                kind = "function"
                detail = _fn_signature(export_def)
            elif isinstance(export_def, AgentDef):
                kind = "agent"
                detail = _agent_signature(export_def)
            elif isinstance(export_def, StructDef):
                kind = "struct"
                fields = ", ".join(
                    f"{f.name}: {_type_expr_display(f.type_annotation)}" for f in export_def.fields
                )
                detail = f"struct {name} {{ {fields} }}"
            elif isinstance(export_def, EnumDef):
                kind = "enum"
                variants = ", ".join(v.name for v in export_def.variants)
                detail = f"enum {name} {{ {variants} }}"
            elif isinstance(export_def, PipeDef):
                kind = "pipe"
                detail = f"pipe {name}"
            elif isinstance(export_def, TypeAlias):
                kind = "type_alias"
                detail = f"type {name} = {_type_expr_display(export_def.type_expr)}"

            imported[name] = SymbolInfo(
                name=name,
                kind=kind,
                type_display=detail,
                detail=detail,
                definition=loc,
                doc=f"Imported from `{'::'.join(defn.path)}`",
            )

    return imported, import_defs


# ---------------------------------------------------------------------------
# Diagnostic enrichment with fix suggestions
# ---------------------------------------------------------------------------


def _enrich_diagnostics(
    errors: list[SemanticError],
    source: str,
    all_symbols: dict[str, SymbolInfo],
) -> list[LspDiagnostic]:
    """Convert SemanticErrors to LspDiagnostics with fix suggestions."""
    diagnostics: list[LspDiagnostic] = []
    all_names = (
        set(all_symbols.keys())
        | set(BUILTIN_FUNCTIONS.keys())
        | PRIMITIVE_TYPES
        | BUILTIN_GENERIC_TYPES
    )

    for err in errors:
        diag = LspDiagnostic(
            message=err.message,
            line=err.line,
            column=err.column,
            severity="error",
        )

        # Try to add fix suggestions based on error patterns
        _add_suggestions(diag, err.message, all_names, source)
        diagnostics.append(diag)

    return diagnostics


def _add_suggestions(
    diag: LspDiagnostic,
    message: str,
    all_names: set[str],
    source: str,
) -> None:
    """Add fix suggestions based on common error patterns."""
    # Undefined variable — suggest similar names
    m = re.match(r"Undefined (?:variable|function) '(\w+)'", message)
    if m:
        name = m.group(1)
        close = difflib.get_close_matches(name, all_names, n=3, cutoff=0.6)
        for suggestion in close:
            diag.suggestions.append(
                FixSuggestion(
                    message=f"Did you mean `{suggestion}`?",
                    replacement=suggestion,
                    line=diag.line,
                    column=diag.column,
                )
            )
        return

    # Type mismatch — suggest conversion
    m = re.match(r"Type mismatch.*expected '?(\w+)'?.*got '?(\w+)'?", message, re.IGNORECASE)
    if m:
        expected, got = m.group(1), m.group(2)
        conversions = {
            ("Int", "Float"): "float()",
            ("Float", "Int"): "int()",
            ("String", "Int"): "int()",
            ("String", "Float"): "float()",
            ("Int", "String"): "str()",
            ("Float", "String"): "str()",
        }
        conv = conversions.get((expected, got))
        if conv:
            diag.suggestions.append(
                FixSuggestion(
                    message=f"Convert with `{conv}`",
                    replacement=conv,
                )
            )
        return

    # Undefined agent — suggest similar names
    m = re.match(r"Undefined agent '(\w+)'", message)
    if m:
        name = m.group(1)
        close = difflib.get_close_matches(name, all_names, n=3, cutoff=0.6)
        for suggestion in close:
            diag.suggestions.append(
                FixSuggestion(
                    message=f"Did you mean `{suggestion}`?",
                    replacement=suggestion,
                )
            )


# ---------------------------------------------------------------------------
# Main analysis entry points
# ---------------------------------------------------------------------------


def analyze_document(
    uri: str,
    source: str,
    *,
    incremental: bool = True,
) -> tuple[DocumentAnalysis | None, list[LspDiagnostic]]:
    """Parse and analyze a Mapanare document.

    Returns (analysis, diagnostics). Analysis may be None if parsing fails completely.
    Diagnostics include fix suggestions for common errors.

    When incremental=True, uses cached parse results for unchanged chunks.
    """
    from mapanare.parser import ParseError, parse
    from mapanare.semantic import check

    parse_errors: list[SemanticError] = []
    program: Program | None = None

    if incremental:
        program, parse_errors, _ = _incremental_parser.parse(uri, source)
        if not program.definitions and parse_errors:
            # Complete parse failure
            diagnostics = _enrich_diagnostics(parse_errors, source, {})
            return None, diagnostics
    else:
        try:
            program = parse(source, filename=uri)
        except ParseError as e:
            parse_errors.append(
                SemanticError(
                    message=e.message,
                    line=e.line,
                    column=e.column,
                    filename=uri,
                )
            )

    if program is None:
        diagnostics = _enrich_diagnostics(parse_errors, source, {})
        return None, diagnostics

    # Resolve imported symbols for cross-module features
    imported_symbols, import_defs = _resolve_imported_symbols(uri, program)

    # Run semantic check with module resolver
    semantic_errors = check(program, filename=uri)
    all_errors = parse_errors + semantic_errors

    analysis = DocumentAnalysis(
        uri,
        source,
        program,
        imported_symbols=imported_symbols,
        import_defs=import_defs,
    )

    # Build enriched diagnostics with suggestions
    all_symbols = dict(analysis.symbols)
    all_symbols.update(imported_symbols)
    diagnostics = _enrich_diagnostics(all_errors, source, all_symbols)

    return analysis, diagnostics


def invalidate_document(uri: str) -> None:
    """Remove cached parse data for a document."""
    _incremental_parser.invalidate(uri)
