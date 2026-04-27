#!/usr/bin/env python3
"""v5.8.4 Wb.2 helper — wraps explicit emit_call_ir/emit_call_void
runtime fn call sites in mapanare/self/emit_llvm.mn with the new
target-aware emit_rt_call/emit_rt_call_void helpers.

The transformation:

    emit_line(<state>, emit_call_ir(<dn>, <ret>, "<fn>", <args>))
        -> emit_rt_call(<state>, <dn>, <ret>, "<fn>", <args>)

    emit_line(<state>, emit_call_void("<fn>", <args>))
        -> emit_rt_call_void(<state>, "<fn>", <args>)

We only transform sites where the called function is a runtime fn
(starts with __mn_ or is in a known runtime allowlist). User-fn calls
through emit_mir_call's generic find_function path are NOT touched —
they already go through use_sret_return which is now Win64-aware.

Idempotent. Run multiple times safely.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Runtime fns that need wrapping. All start with __mn_ except a few
# C-stdlib helpers (abort, free, malloc) and lowered builtins.
RUNTIME_PREFIXES = ("__mn_",)
EXTRA_RUNTIMES = {
    "abort",
    "malloc",
    "free",
    "printf",
}


def find_matching_paren(text: str, start: int) -> int:
    """Given text[start] == '(', return the index of the matching ')'.
    Respects nested parens and skips over string literals."""
    assert text[start] == "(", f"expected '(' at {start}, got {text[start]!r}"
    depth = 1
    i = start + 1
    while i < len(text) and depth > 0:
        ch = text[i]
        if ch == '"':
            # skip string literal
            i += 1
            while i < len(text) and text[i] != '"':
                if text[i] == "\\":
                    i += 2
                    continue
                i += 1
            i += 1
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError(f"no matching ')' for '(' at {start}")


def split_top_args(args_text: str) -> list[str]:
    """Split a comma-separated arg list at depth 0, respecting parens
    and brackets."""
    out: list[str] = []
    depth = 0
    bracket = 0
    start = 0
    i = 0
    while i < len(args_text):
        ch = args_text[i]
        if ch == '"':
            i += 1
            while i < len(args_text) and args_text[i] != '"':
                if args_text[i] == "\\":
                    i += 2
                    continue
                i += 1
            i += 1
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "[":
            bracket += 1
        elif ch == "]":
            bracket -= 1
        elif ch == "," and depth == 0 and bracket == 0:
            out.append(args_text[start:i].strip())
            start = i + 1
        i += 1
    last = args_text[start:].strip()
    if last:
        out.append(last)
    return out


def is_runtime_fn(name_literal: str) -> bool:
    """name_literal is a quoted Mapanare string token (with quotes)."""
    if not (name_literal.startswith('"') and name_literal.endswith('"')):
        return False
    name = name_literal[1:-1]
    if any(name.startswith(p) for p in RUNTIME_PREFIXES):
        return True
    return name in EXTRA_RUNTIMES


def transform_call_ir_emit_line(text: str) -> tuple[str, int]:
    """Find every `emit_line(<state>, emit_call_ir(<args>))` where the
    fn name is a runtime fn, and rewrite to
    `emit_rt_call(<state>, <args>)`.

    Returns (new_text, count_changed).
    """
    out_chunks: list[str] = []
    cursor = 0
    pattern = re.compile(r"\bemit_line\(")
    count = 0
    for m in pattern.finditer(text):
        # Find the inside of emit_line(...)
        outer_open = m.end() - 1
        try:
            outer_close = find_matching_paren(text, outer_open)
        except ValueError:
            continue
        inner = text[outer_open + 1 : outer_close]
        # First arg is the state expression; second is the inner call expr.
        # Use top-level comma split.
        args = split_top_args(inner)
        if len(args) != 2:
            continue
        state_arg, inner_call = args
        # We want inner_call to be `emit_call_ir(<args>)` or `emit_call_void(<args>)`.
        for fn in ("emit_call_ir", "emit_call_void"):
            prefix = fn + "("
            if not inner_call.startswith(prefix):
                continue
            if not inner_call.endswith(")"):
                continue
            inner_args = inner_call[len(prefix) : -1]
            inner_parts = split_top_args(inner_args)
            if fn == "emit_call_ir":
                # (dn, ret, fn_name, args)
                if len(inner_parts) != 4:
                    break
                fn_name_literal = inner_parts[2]
            else:
                # (fn_name, args)
                if len(inner_parts) != 2:
                    break
                fn_name_literal = inner_parts[0]
            if not is_runtime_fn(fn_name_literal):
                break
            # Build replacement.
            if fn == "emit_call_ir":
                p0, p1, p2, p3 = inner_parts
                replacement = f"emit_rt_call({state_arg}, {p0}, {p1}, {p2}, {p3})"
            else:
                p0, p1 = inner_parts
                replacement = f"emit_rt_call_void({state_arg}, {p0}, {p1})"
            # Append unchanged prefix + replacement.
            out_chunks.append(text[cursor : m.start()])
            out_chunks.append(replacement)
            cursor = outer_close + 1
            count += 1
            break
    out_chunks.append(text[cursor:])
    return "".join(out_chunks), count


def main(argv: list[str]) -> int:
    target = Path("mapanare/self/emit_llvm.mn")
    src = target.read_text(encoding="utf-8")
    new_src, changed = transform_call_ir_emit_line(src)
    if changed == 0:
        print("no changes (already ported or no matching call sites)")
        return 0
    target.write_text(new_src, encoding="utf-8")
    print(f"wrote {target} — {changed} call site(s) wrapped")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
