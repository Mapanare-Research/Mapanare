"""Workspace-wide symbol index for cross-module LSP features (v4.37.0).

Scans all .mn files in a workspace root, parses each, extracts top-level
symbols, and provides O(1) lookup by (module, name). Rebuilt incrementally
on save events.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

from mapanare.ast_nodes import (
    AgentDef,
    Block,
    CallExpr,
    ConstructExpr,
    EnumDef,
    Expr,
    ExprStmt,
    ExternFnDef,
    FieldAccessExpr,
    FnDef,
    ForLoop,
    Identifier,
    IfExpr,
    ImportDef,
    LetBinding,
    MatchExpr,
    MethodCallExpr,
    ModuleLetDef,
    NamedType,
    PipeDef,
    Program,
    ReturnStmt,
    Span,
    StructDef,
    TraitDef,
    TypeAlias,
)

logger = logging.getLogger("mapanare-lsp")


@dataclass
class SymbolDef:
    """A top-level symbol definition in the workspace."""

    module: str
    name: str
    kind: Literal["fn", "struct", "enum", "trait", "let", "type", "agent", "pipe", "extern_fn"]
    path: Path
    span: Span
    visibility: Literal["pub", "internal"] = "internal"
    doc_comment: str = ""
    detail: str = ""  # signature or brief summary


@dataclass
class ReferenceSite:
    """A location where a symbol is referenced (v4.38.0)."""

    path: Path
    span: Span
    kind: Literal["call", "read", "type_use", "import", "pattern"] = "read"


@dataclass
class FileEntry:
    """Cached state for a single .mn file in the workspace."""

    path: Path
    last_mtime: float = 0.0
    ast: Optional[Program] = None
    symbols: list[SymbolDef] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)  # module paths


class WorkspaceIndex:
    """Multi-file symbol index. The foundation for cross-module go-to-def."""

    def __init__(self) -> None:
        self.files: dict[Path, FileEntry] = {}
        self._by_name: dict[tuple[str, str], SymbolDef] = {}  # (module, name) -> SymbolDef
        self._by_unqualified: dict[str, list[SymbolDef]] = {}  # name -> [SymbolDef, ...]
        self.refs_by_symbol: dict[tuple[str, str], list[ReferenceSite]] = {}  # v4.38.0
        self.root: Optional[Path] = None

    def scan_root(self, root_path: Path) -> None:
        """Walk the workspace root and index all .mn files."""
        self.root = root_path
        self.files.clear()
        self._by_name.clear()
        self._by_unqualified.clear()
        self.refs_by_symbol.clear()

        for dirpath, _dirnames, filenames in os.walk(root_path):
            for fname in filenames:
                if fname.endswith(".mn"):
                    fpath = Path(dirpath) / fname
                    self.rebuild_file(fpath)

        # v4.38.0: second pass to collect cross-module references
        # (first pass misses refs to symbols not yet indexed)
        self.refs_by_symbol.clear()
        for entry in self.files.values():
            if entry.ast:
                refs = _collect_references(entry.ast, entry.path, self)
                for key, site in refs:
                    self.refs_by_symbol.setdefault(key, []).append(site)

    def rebuild_file(self, path: Path, source: str | None = None) -> None:
        """Parse a file and update its symbols in the index."""
        # Remove old symbols and references for this file
        old_entry = self.files.get(path)
        if old_entry:
            for sym in old_entry.symbols:
                self._by_name.pop((sym.module, sym.name), None)
                unq = self._by_unqualified.get(sym.name, [])
                self._by_unqualified[sym.name] = [s for s in unq if s.path != path]
            # v4.38.0: remove old reference sites from this file
            for key, sites in list(self.refs_by_symbol.items()):
                self.refs_by_symbol[key] = [s for s in sites if s.path != path]

        # Parse and extract symbols
        try:
            if source is None:
                source = path.read_text(encoding="utf-8")
            from mapanare.parser import parse

            ast = parse(source, filename=str(path))
            module_name = path.stem
            symbols = _extract_top_level_symbols(ast, module_name, path)
            imports = _extract_imports(ast)

            entry = FileEntry(
                path=path,
                last_mtime=path.stat().st_mtime if path.exists() else 0.0,
                ast=ast,
                symbols=symbols,
                imports=imports,
            )
            self.files[path] = entry

            for sym in symbols:
                self._by_name[(sym.module, sym.name)] = sym
                self._by_unqualified.setdefault(sym.name, []).append(sym)

            # v4.38.0: collect references from this file
            refs = _collect_references(ast, path, self)
            for key, site in refs:
                self.refs_by_symbol.setdefault(key, []).append(site)

        except Exception as e:
            logger.warning("Failed to index %s: %s", path, e)
            # Keep a stub entry so we don't re-try on every query
            self.files[path] = FileEntry(path=path)

    def lookup(self, module: str, name: str) -> Optional[SymbolDef]:
        """O(1) lookup by (module, name)."""
        return self._by_name.get((module, name))

    def lookup_by_name(self, name: str) -> list[SymbolDef]:
        """Lookup all symbols with a given name (across all modules)."""
        return self._by_unqualified.get(name, [])

    def symbols_in_file(self, path: Path) -> list[SymbolDef]:
        """Return all top-level symbols in a file."""
        entry = self.files.get(path)
        return entry.symbols if entry else []

    def find_references(
        self, module: str, name: str, include_declaration: bool = False
    ) -> list[ReferenceSite]:
        """Return all reference sites for a symbol (v4.38.0)."""
        sites = list(self.refs_by_symbol.get((module, name), []))
        if include_declaration:
            sym = self._by_name.get((module, name))
            if sym:
                sites.insert(0, ReferenceSite(path=sym.path, span=sym.span, kind="read"))
        return sites

    def all_symbols(self) -> list[SymbolDef]:
        """Return all symbols in the workspace."""
        return list(self._by_name.values())


def _collect_references(
    program: Program, path: Path, index: WorkspaceIndex
) -> list[tuple[tuple[str, str], ReferenceSite]]:
    """Walk an AST and collect references to known symbols (v4.38.0)."""
    refs: list[tuple[tuple[str, str], ReferenceSite]] = []
    known_names = set(index._by_unqualified.keys())

    def _walk_expr(expr: object) -> None:
        if expr is None:
            return
        if isinstance(expr, Identifier):
            if expr.name in known_names:
                for sym in index.lookup_by_name(expr.name):
                    if sym.path != path or sym.span != expr.span:
                        refs.append(
                            (
                                (sym.module, sym.name),
                                ReferenceSite(path=path, span=expr.span, kind="read"),
                            )
                        )
                        break
        elif isinstance(expr, CallExpr):
            if isinstance(expr.callee, Identifier) and expr.callee.name in known_names:
                for sym in index.lookup_by_name(expr.callee.name):
                    refs.append(
                        (
                            (sym.module, sym.name),
                            ReferenceSite(path=path, span=expr.callee.span, kind="call"),
                        )
                    )
                    break
            for arg in expr.args:
                _walk_expr(arg)
        elif isinstance(expr, MethodCallExpr):
            _walk_expr(expr.object)
            for arg in expr.args:
                _walk_expr(arg)
        elif isinstance(expr, FieldAccessExpr):
            _walk_expr(expr.object)
        elif isinstance(expr, IfExpr):
            _walk_expr(expr.condition)
            _walk_block(expr.then_block)
            if isinstance(expr.else_block, Block):
                _walk_block(expr.else_block)
            elif isinstance(expr.else_block, IfExpr):
                _walk_expr(expr.else_block)
        elif isinstance(expr, MatchExpr):
            _walk_expr(expr.subject)
            for arm in expr.arms:
                if isinstance(arm.body, Block):
                    _walk_block(arm.body)
                elif isinstance(arm.body, Expr):
                    _walk_expr(arm.body)
        elif isinstance(expr, ConstructExpr):
            if expr.name in known_names:
                for sym in index.lookup_by_name(expr.name):
                    refs.append(
                        (
                            (sym.module, sym.name),
                            ReferenceSite(path=path, span=expr.span, kind="type_use"),
                        )
                    )
                    break
            for fi in expr.fields:
                _walk_expr(fi.value)
        elif isinstance(expr, NamedType):
            if expr.name in known_names:
                for sym in index.lookup_by_name(expr.name):
                    refs.append(
                        (
                            (sym.module, sym.name),
                            ReferenceSite(path=path, span=expr.span, kind="type_use"),
                        )
                    )
                    break

    def _walk_block(block: Block) -> None:
        if block is None:
            return
        for stmt in block.stmts:
            _walk_stmt(stmt)

    def _walk_stmt(stmt: object) -> None:
        if isinstance(stmt, ExprStmt):
            _walk_expr(stmt.expr)
        elif isinstance(stmt, LetBinding):
            _walk_expr(stmt.value)
        elif isinstance(stmt, ReturnStmt):
            if stmt.value:
                _walk_expr(stmt.value)
        elif isinstance(stmt, ForLoop):
            _walk_expr(stmt.iterable)
            _walk_block(stmt.body)

    for defn in program.definitions:
        if isinstance(defn, FnDef):
            _walk_block(defn.body)
        elif isinstance(defn, AgentDef):
            for method in defn.methods:
                _walk_block(method.body)

    return refs


def _extract_top_level_symbols(program: Program, module_name: str, path: Path) -> list[SymbolDef]:
    """Extract top-level symbol definitions from a parsed program."""
    symbols: list[SymbolDef] = []

    for defn in program.definitions:
        if isinstance(defn, FnDef):
            sig = _fn_sig(defn)
            symbols.append(
                SymbolDef(
                    module=module_name,
                    name=defn.name,
                    kind="fn",
                    path=path,
                    span=defn.span,
                    visibility="pub" if defn.public else "internal",
                    detail=sig,
                )
            )
        elif isinstance(defn, StructDef):
            fields = ", ".join(f.name for f in defn.fields) if defn.fields else ""
            symbols.append(
                SymbolDef(
                    module=module_name,
                    name=defn.name,
                    kind="struct",
                    path=path,
                    span=defn.span,
                    visibility="pub" if defn.public else "internal",
                    detail=f"struct {defn.name} {{ {fields} }}",
                )
            )
        elif isinstance(defn, EnumDef):
            variants = ", ".join(v.name for v in defn.variants) if defn.variants else ""
            symbols.append(
                SymbolDef(
                    module=module_name,
                    name=defn.name,
                    kind="enum",
                    path=path,
                    span=defn.span,
                    visibility="pub" if defn.public else "internal",
                    detail=f"enum {defn.name} {{ {variants} }}",
                )
            )
        elif isinstance(defn, TraitDef):
            symbols.append(
                SymbolDef(
                    module=module_name,
                    name=defn.name,
                    kind="trait",
                    path=path,
                    span=defn.span,
                    visibility="pub" if defn.public else "internal",
                    detail=f"trait {defn.name}",
                )
            )
        elif isinstance(defn, AgentDef):
            symbols.append(
                SymbolDef(
                    module=module_name,
                    name=defn.name,
                    kind="agent",
                    path=path,
                    span=defn.span,
                    visibility="pub" if defn.public else "internal",
                    detail=f"agent {defn.name}",
                )
            )
        elif isinstance(defn, PipeDef):
            symbols.append(
                SymbolDef(
                    module=module_name,
                    name=defn.name,
                    kind="pipe",
                    path=path,
                    span=defn.span,
                    visibility="pub" if defn.public else "internal",
                    detail=f"pipe {defn.name}",
                )
            )
        elif isinstance(defn, TypeAlias):
            symbols.append(
                SymbolDef(
                    module=module_name,
                    name=defn.name,
                    kind="type",
                    path=path,
                    span=defn.span,
                    visibility="pub" if defn.public else "internal",
                )
            )
        elif isinstance(defn, ExternFnDef):
            symbols.append(
                SymbolDef(
                    module=module_name,
                    name=defn.name,
                    kind="extern_fn",
                    path=path,
                    span=defn.span,
                    visibility="pub",
                )
            )
        elif isinstance(defn, ModuleLetDef):
            symbols.append(
                SymbolDef(
                    module=module_name,
                    name=defn.name,
                    kind="let",
                    path=path,
                    span=defn.span,
                    visibility="internal",
                )
            )

    return symbols


def _extract_imports(program: Program) -> list[str]:
    """Extract import module paths from a program."""
    imports: list[str] = []
    for defn in program.definitions:
        if isinstance(defn, ImportDef):
            imports.append(".".join(defn.path))
    return imports


def _fn_sig(fn: FnDef) -> str:
    """Build a short function signature string."""
    from mapanare.lsp.analysis import _type_expr_display

    params = ", ".join(
        f"{p.name}: {_type_expr_display(p.type_annotation)}" if p.type_annotation else p.name
        for p in fn.params
    )
    ret = f" -> {_type_expr_display(fn.return_type)}" if fn.return_type else ""
    pub = "pub " if fn.public else ""
    return f"{pub}fn {fn.name}({params}){ret}"
