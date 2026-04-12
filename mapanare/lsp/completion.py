"""Context-aware LSP completion for Mapanare (v4.39.0).

Provides completions in four contexts:
1. Import path completion (after `import`)
2. Type annotation completion (after `:` in type position)
3. Field/method completion (after `.` on a value)
4. Fallback identifier completion (Ctrl+Space anywhere)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from mapanare.lsp.workspace import SymbolDef, WorkspaceIndex

# Builtin types offered in type context
_BUILTIN_TYPES = [
    ("Int", "Signed 64-bit integer"),
    ("Float", "64-bit floating-point"),
    ("String", "UTF-8 string (heap-allocated)"),
    ("Bool", "Boolean (true/false)"),
    ("Char", "Unicode character"),
    ("Void", "No return value"),
    ("List<T>", "Growable list of T"),
    ("Map<K, V>", "Hash map from K to V"),
    ("Option<T>", "Optional value (Some(T) or None)"),
    ("Result<T, E>", "Success (Ok(T)) or failure (Err(E))"),
    ("Signal<T>", "Reactive signal holding T"),
    ("Stream<T>", "Async stream of T"),
    ("Agent", "Concurrent agent type"),
    ("Tensor", "N-dimensional numeric array"),
]

# Builtin methods for common types
_OPTION_METHODS = [
    ("is_some", "fn() -> Bool", "Returns true if Some"),
    ("is_none", "fn() -> Bool", "Returns true if None"),
    ("unwrap", "fn() -> T", "Returns the inner value or panics"),
    ("map", "fn(f: fn(T) -> U) -> Option<U>", "Transforms the inner value"),
]

_RESULT_METHODS = [
    ("is_ok", "fn() -> Bool", "Returns true if Ok"),
    ("is_err", "fn() -> Bool", "Returns true if Err"),
    ("unwrap", "fn() -> T", "Returns the Ok value or panics"),
    ("map", "fn(f: fn(T) -> U) -> Result<U, E>", "Transforms the Ok value"),
]

_LIST_METHODS = [
    ("len", "fn() -> Int", "Returns the number of elements"),
    ("push", "fn(item: T)", "Appends an element"),
    ("pop", "fn() -> Option<T>", "Removes and returns the last element"),
    ("get", "fn(idx: Int) -> T", "Returns element at index"),
    ("map", "fn(f: fn(T) -> U) -> List<U>", "Transforms each element"),
    ("filter", "fn(f: fn(T) -> Bool) -> List<T>", "Keeps matching elements"),
]

_STRING_METHODS = [
    ("len", "fn() -> Int", "Returns the string length"),
    ("contains", "fn(sub: String) -> Bool", "Checks for substring"),
    ("starts_with", "fn(prefix: String) -> Bool", "Checks prefix"),
    ("ends_with", "fn(suffix: String) -> Bool", "Checks suffix"),
    ("replace", "fn(old: String, new: String) -> String", "Replaces occurrences"),
    ("split", "fn(sep: String) -> List<String>", "Splits by separator"),
    ("trim", "fn() -> String", "Removes leading/trailing whitespace"),
    ("to_upper", "fn() -> String", "Converts to uppercase"),
    ("to_lower", "fn() -> String", "Converts to lowercase"),
    ("substr", "fn(start: Int, len: Int) -> String", "Extracts substring"),
]


@dataclass
class CompletionCandidate:
    """A completion item ready for the LSP layer."""

    label: str
    kind: str  # "function", "variable", "type", "field", "method", "module", "keyword"
    detail: str = ""
    documentation: str = ""
    insert_text: str = ""
    sort_text: str = ""  # for ranking


def complete_import(prefix: str, workspace: WorkspaceIndex) -> list[CompletionCandidate]:
    """Complete after `import`. Offers module names from the workspace."""
    candidates: list[CompletionCandidate] = []
    seen: set[str] = set()

    for entry in workspace.files.values():
        module = entry.path.stem
        if module not in seen and module.startswith(prefix):
            seen.add(module)
            candidates.append(CompletionCandidate(
                label=module,
                kind="module",
                detail=f"Module ({len(entry.symbols)} symbols)",
                sort_text=f"0_{module}",
            ))

    # Add stdlib hint
    if "stdlib".startswith(prefix) and "stdlib" not in seen:
        candidates.append(CompletionCandidate(
            label="stdlib",
            kind="module",
            detail="Standard library",
            sort_text="0_stdlib",
        ))

    return candidates


def complete_type(workspace: WorkspaceIndex) -> list[CompletionCandidate]:
    """Complete in type annotation position. Offers builtin + user types."""
    candidates: list[CompletionCandidate] = []

    # Builtin types (highest priority)
    for name, desc in _BUILTIN_TYPES:
        candidates.append(CompletionCandidate(
            label=name,
            kind="type",
            detail=desc,
            sort_text=f"0_{name}",
        ))

    # User-defined types from workspace
    for sym in workspace.all_symbols():
        if sym.kind in ("struct", "enum", "trait", "type"):
            candidates.append(CompletionCandidate(
                label=sym.name,
                kind=sym.kind,
                detail=sym.detail or f"{sym.kind} {sym.name}",
                documentation=f"Defined in `{sym.module}`",
                sort_text=f"1_{sym.name}",
            ))

    return candidates


def complete_field_method(
    receiver_type: str, workspace: WorkspaceIndex
) -> list[CompletionCandidate]:
    """Complete after `.` on a value. Offers fields and methods based on type."""
    candidates: list[CompletionCandidate] = []

    # Builtin type methods
    type_lower = receiver_type.lower()
    if type_lower.startswith("option"):
        for name, sig, doc in _OPTION_METHODS:
            candidates.append(CompletionCandidate(
                label=name, kind="method", detail=sig, documentation=doc,
                insert_text=f"{name}($1)$0" if "fn(" in sig and sig.count(",") > 0 else f"{name}()",
            ))
    elif type_lower.startswith("result"):
        for name, sig, doc in _RESULT_METHODS:
            candidates.append(CompletionCandidate(
                label=name, kind="method", detail=sig, documentation=doc,
                insert_text=f"{name}($1)$0" if "fn(" in sig and sig.count(",") > 0 else f"{name}()",
            ))
    elif type_lower.startswith("list"):
        for name, sig, doc in _LIST_METHODS:
            candidates.append(CompletionCandidate(
                label=name, kind="method", detail=sig, documentation=doc,
                insert_text=f"{name}($1)$0" if "()" not in sig.split("->")[0] else f"{name}()",
            ))
    elif type_lower == "string":
        for name, sig, doc in _STRING_METHODS:
            candidates.append(CompletionCandidate(
                label=name, kind="method", detail=sig, documentation=doc,
            ))

    # User-defined struct fields
    for sym in workspace.all_symbols():
        if sym.kind == "struct" and sym.name == receiver_type:
            # Parse fields from detail: "struct Point { x, y }"
            detail = sym.detail or ""
            if "{" in detail:
                fields_str = detail.split("{")[1].split("}")[0].strip()
                for field_name in fields_str.split(","):
                    field_name = field_name.strip()
                    if field_name:
                        candidates.append(CompletionCandidate(
                            label=field_name,
                            kind="field",
                            detail=f"field of {receiver_type}",
                        ))
            break

    return candidates


def complete_identifiers(
    workspace: WorkspaceIndex,
    current_module: str = "",
) -> list[CompletionCandidate]:
    """Fallback: offer all identifiers in scope, ranked by proximity."""
    candidates: list[CompletionCandidate] = []

    # Current module symbols first
    for sym in workspace.all_symbols():
        if sym.module == current_module:
            candidates.append(CompletionCandidate(
                label=sym.name,
                kind=_sym_kind_to_completion(sym.kind),
                detail=sym.detail or f"{sym.kind} {sym.name}",
                sort_text=f"0_{sym.name}",
            ))
        elif sym.visibility == "pub":
            candidates.append(CompletionCandidate(
                label=sym.name,
                kind=_sym_kind_to_completion(sym.kind),
                detail=sym.detail or f"{sym.kind} {sym.name}",
                documentation=f"From `{sym.module}`",
                sort_text=f"2_{sym.name}",
            ))

    # Builtin functions
    for name in ("print", "len", "str", "int", "float", "Some", "Ok", "Err", "signal", "stream"):
        candidates.append(CompletionCandidate(
            label=name,
            kind="function",
            detail="builtin",
            sort_text=f"3_{name}",
        ))

    return candidates


def _sym_kind_to_completion(kind: str) -> str:
    """Map SymbolDef kind to completion item kind."""
    return {
        "fn": "function",
        "struct": "struct",
        "enum": "enum",
        "trait": "type",
        "agent": "class",
        "pipe": "function",
        "let": "variable",
        "type": "type",
        "extern_fn": "function",
    }.get(kind, "text")
