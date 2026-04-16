"""Rename refactoring for Mapanare LSP (v4.38.0).

Validates rename targets and builds WorkspaceEdit for atomic multi-file renames.
"""

from __future__ import annotations

import keyword
import re
from pathlib import Path
from typing import Optional

from mapanare.lsp.workspace import ReferenceSite, SymbolDef, WorkspaceIndex

# Valid Mapanare identifier: starts with letter/underscore, then alnum/underscore
_IDENT_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

# Mapanare keywords (cannot be used as symbol names)
_KEYWORDS = frozenset(
    {
        "fn",
        "let",
        "mut",
        "if",
        "else",
        "match",
        "for",
        "while",
        "loop",
        "return",
        "break",
        "continue",
        "struct",
        "enum",
        "trait",
        "impl",
        "type",
        "import",
        "export",
        "pub",
        "agent",
        "pipe",
        "spawn",
        "sync",
        "send",
        "signal",
        "stream",
        "true",
        "false",
        "in",
        "as",
        "self",
        "extern",
        "async",
        "await",
        "try",
        "assert",
        # Bilingual keywords
        "pon",
        "si",
        "sino",
        "para",
        "mientras",
        "retorna",
        "tipo",
        "importar",
        "exportar",
    }
)


def validate_rename(
    symbol: SymbolDef,
    new_name: str,
    workspace: WorkspaceIndex,
) -> Optional[str]:
    """Check if a rename is valid. Returns error message if invalid, None if OK."""
    # Rule 1: new_name must be a valid identifier
    if not _IDENT_RE.match(new_name):
        return f"'{new_name}' is not a valid identifier"

    # Rule 2: cannot rename to a keyword
    if new_name in _KEYWORDS:
        return f"'{new_name}' is a keyword and cannot be used as a symbol name"

    # Rule 3: cannot conflict with existing top-level name in same module
    existing = workspace.lookup(symbol.module, new_name)
    if existing is not None:
        return f"'{new_name}' already exists in module '{symbol.module}'"

    return None


def apply_rename(
    symbol: SymbolDef,
    new_name: str,
    workspace: WorkspaceIndex,
) -> dict[str, list[dict]]:
    """Build a WorkspaceEdit changes map for renaming a symbol.

    Returns: dict[uri, list[TextEdit]] where TextEdit = {"range": ..., "newText": ...}
    """
    changes: dict[str, list[dict]] = {}

    # Add the definition site
    _add_edit(changes, symbol.path, symbol.span, new_name)

    # Add all reference sites
    key = (symbol.module, symbol.name)
    for site in workspace.refs_by_symbol.get(key, []):
        _add_edit(changes, site.path, site.span, new_name)

    return changes


def _add_edit(changes: dict[str, list[dict]], path: Path, span: object, new_name: str) -> None:
    """Add a text edit to the changes map."""
    uri = f"file://{path}"
    edit = {
        "range": {
            "start": {"line": max(0, span.line - 1), "character": max(0, span.column - 1)},
            "end": {
                "line": max(0, (span.end_line or span.line) - 1),
                "character": max(0, (span.end_column or span.column) - 1),
            },
        },
        "newText": new_name,
    }
    changes.setdefault(uri, []).append(edit)
