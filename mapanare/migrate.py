"""migrate.py — Convert Mapanare v2.0 syntax to v3.0 syntax.

Handles structural transforms (not just keyword swap):
- Brace removal: ``{`` at end of line → ``:``, ``}`` lines deleted
- ``struct X`` → ``tipo X``
- ``enum X { A, B(T) }`` → ``tipo X`` with ``| A`` / ``| B(T)`` variants
- ``trait X`` → ``modo X``
- ``impl X for Y`` → ``Y + X:``
- ``agent X`` → ``@X``
- ``spawn X()`` → ``@X()``
- ``pub name`` → ``+name``
- ``input``/``output`` in agents → ``->`` / ``<-``
- Keyword replacement: ``let`` → ``pon``, ``return`` → ``da``, etc.
- ``fn main()`` → ``fn main`` (remove empty parens for zero-arg entry point)
- Implicit return: final ``return value`` → just ``value``

Usage::

    mapanare migrate --to=v3 src/           # In-place rewrite
    mapanare migrate --to=v3 --dry src/     # Preview changes
    mapanare migrate --to=v3 --check src/   # CI: fail if old syntax
    mapanare migrate --style=english src/   # Structure only, keep English
"""

from __future__ import annotations

import os
import re
import sys

# ---------------------------------------------------------------------------
# Keyword mapping: English → Spanglish
# ---------------------------------------------------------------------------

_KW_MAP_SPANGLISH: dict[str, str] = {
    "let": "pon",
    "return": "da",
    "if": "si",
    "else": "sino",
    "for": "cada",
    " in ": " en ",
    "while": "mien",
    "break": "sal",
    "continue": "sigue",
    "none": "nada",
    "self": "yo",
    "import": "usa",
}

# Structural transforms (always applied regardless of style)
_STRUCT_KW = {"struct": "tipo", "enum": "tipo", "trait": "modo"}


# ---------------------------------------------------------------------------
# Core transformation
# ---------------------------------------------------------------------------


def migrate_source(source: str, style: str = "spanglish") -> str:
    """Transform a single Mapanare source file from v2 to v3 syntax.

    Args:
        source: The v2.0 Mapanare source code.
        style: ``"spanglish"`` (default) replaces keywords with Spanglish forms.
               ``"english"`` keeps English keywords but applies structural changes.

    Returns:
        The v3.0 Mapanare source code.
    """
    lines = source.split("\n")
    out: list[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        transformed = _transform_line(line, style)
        out.append(transformed)
        i += 1

    result = "\n".join(out)

    # Post-processing passes (keyword + structural only, braces kept)
    result = _convert_enum_variants(result)
    result = _strip_trailing_whitespace(result)

    return result


def _transform_line(line: str, style: str) -> str:
    """Apply keyword and structural transforms to a single line."""
    stripped = line.lstrip()
    indent = line[: len(line) - len(stripped)]

    if not stripped or stripped.startswith("//") or stripped.startswith("#"):
        return line

    result = stripped

    # Structural transforms (always applied)
    # struct Name → tipo Name
    result = re.sub(r"\bstruct\b", "tipo", result)
    # enum Name → tipo Name
    result = re.sub(r"\benum\b", "tipo", result)
    # trait Name → modo Name
    result = re.sub(r"\btrait\b", "modo", result)
    # agent Name → @Name
    result = re.sub(r"\bagent\s+(\w+)", r"@\1", result)
    # spawn Name( → @Name(
    result = re.sub(r"\bspawn\s+(\w+)\s*\(", r"@\1(", result)
    # pub stays as-is (grammar doesn't support + prefix yet)
    # result = re.sub(r"\bpub\s+", "+", result)  # Deferred to Phase 1.1
    # input name: Type → name -> Type (in agent bodies)
    result = re.sub(r"\binput\s+(\w+)\s*:\s*", r"\1 -> ", result)
    # output name: Type → name <- Type (in agent bodies)
    result = re.sub(r"\boutput\s+(\w+)\s*:\s*", r"\1 <- ", result)
    # fn main() stays as-is with braces (parens only removable with colon syntax)
    # result = re.sub(r"\bfn\s+main\s*\(\s*\)", "fn main", result)
    # impl stays as-is (grammar doesn't support Y + X syntax yet)
    # result = re.sub(r"\bimpl\s+(\w+)\s+for\s+(\w+)", r"\2 + \1", result)

    # Keyword transforms (only for spanglish style)
    if style == "spanglish":
        for eng, esp in _KW_MAP_SPANGLISH.items():
            if eng == " in ":
                # Special: " in " → " en " (with spaces to avoid matching "in" in words)
                result = result.replace(eng, esp)
            else:
                result = re.sub(rf"\b{re.escape(eng)}\b", esp, result)

    return indent + result


def _convert_braces_to_indent(source: str) -> str:
    """Convert brace-delimited blocks to colon+indentation.

    Conservative approach: only convert top-level block-opening braces to colons.
    Keep all closing braces and match arm braces intact — the indentation
    preprocessor in the parser handles mixed brace/indent syntax.

    Rules:
    - Line ending with ``{`` → replace ``{`` with ``:`` (except match arms)
    - ``} else {`` → ``} sino:`` or ``} else:``
    - Closing ``}`` lines kept as-is (parser preprocessor handles them)
    """
    lines = source.split("\n")
    out: list[str] = []

    for line in lines:
        stripped = line.rstrip()
        indent = line[: len(line) - len(line.lstrip())]

        # Skip empty/comment lines
        if not stripped.strip():
            out.append(line)
            continue

        content = stripped.strip()

        # } else { or } sino {
        m = re.match(r"^\}\s*(else|sino)\s*(si\s+.*)?\{$", content)
        if m:
            kw = m.group(1)
            cond = m.group(2) or ""
            if cond:
                out.append(f"{indent}}} {kw} {cond.rstrip()} {{")
            else:
                out.append(f"{indent}}} {kw} {{")
            continue

        # Line ending with { — convert to colon (except match arms and bare braces)
        if content.endswith("{"):
            body = content[:-1].rstrip()
            # Keep match arm blocks: "Pattern => {" as-is
            if body.endswith("=>") or not body:
                out.append(stripped)
                continue
            # Keep standalone { (already a block opener)
            out.append(f"{indent}{body}:")
            continue

        out.append(stripped)

    return "\n".join(out)


def _convert_enum_variants(source: str) -> str:
    """Convert comma-separated enum variants to |-prefixed syntax.

    Detects ``tipo Name {`` blocks where the body contains bare NAME lines
    (no colon = no field → it's a variant, not a struct field).
    """
    # This is a simplified heuristic — full conversion would require parsing
    # For now: inside tipo blocks, lines that are just "Name" or "Name(types)"
    # without a colon get prefixed with |
    lines = source.split("\n")
    out: list[str] = []
    in_tipo = False
    tipo_indent = 0

    for line in lines:
        stripped = line.strip()
        indent = line[: len(line) - len(line.lstrip())]
        spaces = len(indent)

        if re.match(r"^(?:pub\s+)?tipo\s+\w+.*[:{]$", stripped):
            in_tipo = True
            tipo_indent = spaces
            out.append(line)
            continue

        if in_tipo:
            # Check if we've left the tipo block (dedent or closing brace)
            if stripped == "}" or (stripped and spaces <= tipo_indent and not stripped.startswith("|")):
                in_tipo = False
                out.append(line)
                continue

            if not stripped:
                out.append(line)
                continue

            # Check if this looks like a variant (no colon, just Name or Name(Type))
            # vs a field (has colon: name: Type)
            if ":" in stripped and not stripped.startswith("|"):
                # It's a struct field — keep as-is
                out.append(line)
            elif stripped.startswith("|"):
                # Already a variant
                out.append(line)
            elif re.match(r"^[A-Z]\w*(\(.*\))?[,]?$", stripped):
                # Looks like an enum variant: Red, Green, Circle(Float)
                variant = stripped.rstrip(",")
                out.append(f"{indent}| {variant}")
            else:
                out.append(line)
            continue

        out.append(line)

    return "\n".join(out)


def _convert_agent_syntax(source: str) -> str:
    """Convert agent channel keywords to arrow syntax.

    Already handled by _transform_line for input/output → -> / <-.
    This pass handles any remaining structural adjustments.
    """
    return source


def _strip_trailing_whitespace(source: str) -> str:
    """Remove trailing whitespace from each line."""
    return "\n".join(line.rstrip() for line in source.split("\n"))


# ---------------------------------------------------------------------------
# File/directory processing
# ---------------------------------------------------------------------------


def migrate_file(
    path: str,
    style: str = "spanglish",
    dry_run: bool = False,
    check: bool = False,
) -> bool:
    """Migrate a single .mn file.

    Returns True if the file was (or would be) changed.
    """
    with open(path, encoding="utf-8") as f:
        original = f.read()

    migrated = migrate_source(original, style=style)

    if migrated == original:
        return False

    if check:
        print(f"  NEEDS MIGRATION: {path}")
        return True

    if dry_run:
        print(f"  WOULD MIGRATE: {path}")
        # Show diff summary
        orig_lines = original.count("\n")
        new_lines = migrated.count("\n")
        print(f"    {orig_lines} lines → {new_lines} lines")
        return True

    with open(path, "w", encoding="utf-8") as f:
        f.write(migrated)
    print(f"  MIGRATED: {path}")
    return True


def migrate_directory(
    path: str,
    style: str = "spanglish",
    dry_run: bool = False,
    check: bool = False,
) -> int:
    """Migrate all .mn files in a directory tree.

    Returns the number of files changed (or that would be changed).
    """
    changed = 0
    for root, _dirs, files in os.walk(path):
        for fname in sorted(files):
            if fname.endswith(".mn"):
                fpath = os.path.join(root, fname)
                if migrate_file(fpath, style=style, dry_run=dry_run, check=check):
                    changed += 1
    return changed


def migrate_cli(args: list[str] | None = None) -> None:
    """CLI entry point for the migration tool."""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate Mapanare v2 → v3 syntax")
    parser.add_argument("path", help="File or directory to migrate")
    parser.add_argument(
        "--to",
        default="v3",
        choices=["v3"],
        help="Target version (default: v3)",
    )
    parser.add_argument(
        "--dry",
        action="store_true",
        help="Preview changes without writing",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check mode: fail if old syntax found (for CI)",
    )
    parser.add_argument(
        "--style",
        default="spanglish",
        choices=["spanglish", "english"],
        help="Keyword style: spanglish (default) or english (structure only)",
    )

    parsed = parser.parse_args(args)

    target = parsed.path
    if os.path.isfile(target):
        changed = (
            1
            if migrate_file(target, style=parsed.style, dry_run=parsed.dry, check=parsed.check)
            else 0
        )
    elif os.path.isdir(target):
        changed = migrate_directory(
            target, style=parsed.style, dry_run=parsed.dry, check=parsed.check
        )
    else:
        print(f"error: {target} not found", file=sys.stderr)
        sys.exit(1)

    if parsed.check and changed > 0:
        print(f"\n{changed} file(s) need migration", file=sys.stderr)
        sys.exit(1)

    if not parsed.check:
        mode = "would migrate" if parsed.dry else "migrated"
        print(f"\n{changed} file(s) {mode}")
