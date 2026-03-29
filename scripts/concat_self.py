#!/usr/bin/env python3
"""Concatenate self-hosted compiler modules into a single .mn file.

Strips ``import self::*`` lines so the result can be compiled as a single
file without multi-module support.  Modules are ordered by dependency:
ast → lexer → parser → semantic → lower → emit_llvm → main.
"""

import re
import sys
from pathlib import Path

SELF_DIR = Path(__file__).resolve().parent.parent / "mapanare" / "self"

# Dependency order — leaves first, driver last
MODULE_ORDER = [
    "ast.mn",
    "lexer.mn",
    "parser.mn",
    "semantic.mn",
    "mir.mn",
    "lower_state.mn",
    "lower.mn",
    "emit_llvm_ir.mn",
    "emit_llvm.mn",
    "main.mn",
]

IMPORT_RE = re.compile(r"^\s*import\s+self::")


def concat(out_path: str | None = None) -> str:
    parts: list[str] = [
        "// Auto-generated: all self-hosted compiler modules concatenated.",
        "// Do not edit — regenerate with: python scripts/concat_self.py",
        "",
    ]
    for mod in MODULE_ORDER:
        src = (SELF_DIR / mod).read_text(encoding="utf-8")
        lines = [ln for ln in src.splitlines() if not IMPORT_RE.match(ln)]
        parts.append(f"// ===== {mod} =====")
        parts.extend(lines)
        parts.append("")

    result = "\n".join(parts)
    if out_path:
        Path(out_path).write_text(result, encoding="utf-8")
        print(f"Wrote {len(result):,} bytes → {out_path}")
    return result


if __name__ == "__main__":
    default = str(SELF_DIR / "mnc_all.mn")
    out = sys.argv[1] if len(sys.argv) > 1 else default
    concat(out)
