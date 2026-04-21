#!/usr/bin/env python3
"""scripts/check_struct_registry.py — Reg.1 CI gate (v4.143.0).

Cross-checks ``mapanare/self/emit_llvm.mn::build_internal_struct_list`` against
the live struct definitions in the self-hosted ``mapanare/self/*.mn`` modules.

Background
----------
``build_internal_struct_list`` and ``register_all_internal_structs`` in
``mapanare/self/emit_llvm.mn`` hand-maintain ``make_entry`` / ``register_internal_struct``
calls naming each internal struct's field names in order. The self-hosted
emitter consults this list to generate ``insertvalue`` / ``extractvalue`` GEP
indices for struct field access.

Ge.1 (v4.132.0 → v4.142.0) was in large part caused by this list drifting
from the actual struct definitions — ``MIRModule`` was missing the
``consts`` field; ``LowerState`` missed five fields; ``MatchBuildResult``,
``VarInfo``, ``StructFieldInfo``, ``EnumVariantNames``, ``LambdaEntry``,
``ImplEntry``, ``AgentInfo`` all had wrong or stale field names — which
silently miscompiled ~half the self-hosted emitter's internal data flow for
months without any byte-identity check catching it (both stage2 and stage3
miscompiled the same way).

This gate reads every ``struct Name { field: Type, ... }`` definition in
``mapanare/self/*.mn`` (skipping the concatenated ``mnc_all.mn``) and
compares its field-name list against the registry hand-maintained in
``build_internal_struct_list`` and ``register_all_internal_structs``.

Any divergence fails the gate with a named per-struct report. The fix is
either to update the registry or to justify the omission with an inline
comment (``// registry:omit — <reason>``).

Exit 0 on clean, 1 on drift.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SELF_DIR = Path(__file__).resolve().parent.parent / "mapanare" / "self"
SKIP_FILES = {"mnc_all.mn", "stage2.ll", "stage3.ll", "main.ll"}

# Matches ``struct Name {`` (with or without leading ``pub``).
STRUCT_HEADER_RE = re.compile(r"^(?:pub\s+)?struct\s+([A-Z][A-Za-z0-9_]*)\s*\{")

# Matches a struct field: ``field_name: TypeExpr`` (with optional ``mut``,
# optional trailing comma). Stops at the first token that isn't a valid
# field identifier, which handles embedded nested structs safely.
FIELD_RE = re.compile(r"^\s*(?:mut\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*:")

# Matches ``list.push(make_entry("Name", ["field", ...]))``.
MAKE_ENTRY_RE = re.compile(
    r"""make_entry\(
        \s*"([A-Z][A-Za-z0-9_]*)"\s*,       # struct name
        \s*\[\s*(.*?)\s*\]\s*               # [ "f1", "f2", ... ]
        \)""",
    re.VERBOSE | re.DOTALL,
)

# Matches ``register_internal_struct(s, "Name", ["field", ...])``.
REGISTER_RE = re.compile(
    r"""register_internal_struct\(\s*\w+\s*,
        \s*"([A-Z][A-Za-z0-9_]*)"\s*,
        \s*\[\s*(.*?)\s*\]\s*\)""",
    re.VERBOSE | re.DOTALL,
)

# Extracts the quoted strings from a list literal body.
QUOTED_RE = re.compile(r'"([^"]*)"')

# Internal structs that live in pipelines the registry does not need to
# track (emitter-private or test scaffolding). Match the struct name by regex;
# inline-commented ``// registry:omit`` on the struct header also exempts it.
REGISTRY_OMIT = {"StringBuilder", "MessagePart"}


def parse_struct_defs(path: Path) -> dict[str, list[str]]:
    """Return a ``{struct_name: [field_names]}`` map for ``path``."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    out: dict[str, list[str]] = {}
    i = 0
    while i < len(lines):
        m = STRUCT_HEADER_RE.match(lines[i])
        if not m:
            i += 1
            continue
        name = m.group(1)
        # ``// registry:omit`` on the same or preceding line skips the struct.
        header_line = lines[i]
        if "registry:omit" in header_line:
            i += 1
            continue
        if i > 0 and "registry:omit" in lines[i - 1]:
            i += 1
            continue
        fields: list[str] = []
        j = i + 1
        depth = 1
        while j < len(lines) and depth > 0:
            line = lines[j]
            # Track brace depth so nested ``{ ... }`` in default values don't
            # falsely close the struct.
            for ch in line:
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
            if depth == 0:
                break
            field_m = FIELD_RE.match(line)
            if field_m:
                fields.append(field_m.group(1))
            j += 1
        out[name] = fields
        i = j + 1
    return out


def parse_registry(emit_llvm_path: Path) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Return (``make_entry`` map, ``register_internal_struct`` map)."""
    text = emit_llvm_path.read_text(encoding="utf-8")
    make_map: dict[str, list[str]] = {}
    for m in MAKE_ENTRY_RE.finditer(text):
        name = m.group(1)
        fields = QUOTED_RE.findall(m.group(2))
        make_map[name] = fields
    reg_map: dict[str, list[str]] = {}
    for m in REGISTER_RE.finditer(text):
        name = m.group(1)
        fields = QUOTED_RE.findall(m.group(2))
        reg_map[name] = fields
    return make_map, reg_map


def diff_fields(expected: list[str], actual: list[str]) -> list[str]:
    """Return a list of human-readable diff lines, empty on match."""
    if expected == actual:
        return []
    diffs: list[str] = []
    if len(expected) != len(actual):
        diffs.append(f"  arity: source has {len(expected)} fields, registry has {len(actual)}")
    for idx in range(max(len(expected), len(actual))):
        exp = expected[idx] if idx < len(expected) else "<missing>"
        act = actual[idx] if idx < len(actual) else "<missing>"
        if exp != act:
            diffs.append(f"  [{idx}] source={exp!r}  registry={act!r}")
    return diffs


def main(argv: list[str]) -> int:
    if not SELF_DIR.exists():
        print(f"error: {SELF_DIR} does not exist", file=sys.stderr)
        return 2

    # Collect all struct defs across the modular self-hosted sources.
    all_structs: dict[str, tuple[Path, list[str]]] = {}
    for mn in sorted(SELF_DIR.glob("*.mn")):
        if mn.name in SKIP_FILES:
            continue
        defs = parse_struct_defs(mn)
        for name, fields in defs.items():
            if name in REGISTRY_OMIT:
                continue
            # The first-wins rule matches Mapanare's concat+compile semantics.
            if name not in all_structs:
                all_structs[name] = (mn, fields)

    registry_path = SELF_DIR / "emit_llvm.mn"
    if not registry_path.exists():
        print(f"error: {registry_path} does not exist", file=sys.stderr)
        return 2

    make_map, reg_map = parse_registry(registry_path)

    violations: list[str] = []

    # Rule 1: every registered struct must exist in source with matching fields.
    for name, registry_fields in make_map.items():
        if name not in all_structs:
            violations.append(
                f"{registry_path.name}: registry lists {name!r} in "
                f"build_internal_struct_list, but no matching struct definition "
                f"found in mapanare/self/*.mn"
            )
            continue
        source_path, source_fields = all_structs[name]
        diffs = diff_fields(source_fields, registry_fields)
        if diffs:
            violations.append(
                f"{source_path.name}: struct {name} drift "
                f"(registry at emit_llvm.mn::build_internal_struct_list):"
            )
            violations.extend(diffs)

    # Rule 2: register_all_internal_structs must match build_internal_struct_list
    # for every name present in both.
    for name in sorted(set(make_map) & set(reg_map)):
        if make_map[name] != reg_map[name]:
            violations.append(
                f"emit_llvm.mn: struct {name} registered with different field lists "
                f"in build_internal_struct_list vs register_all_internal_structs"
            )

    # Summary / gate.
    checked_make = len(make_map)
    checked_reg = len(reg_map)
    checked_defs = len(all_structs)

    if violations:
        for line in violations:
            print(line)
        print(
            f"\ncheck_struct_registry: {len(violations)} violation(s). "
            f"build_internal_struct_list / register_all_internal_structs must "
            f"match the field order of each struct definition in "
            f"mapanare/self/*.mn. To intentionally omit an internal struct, "
            f"add ``// registry:omit`` on its header line or name it in "
            f"REGISTRY_OMIT.",
            file=sys.stderr,
        )
        return 1

    print(
        f"check_struct_registry: clean "
        f"({checked_make} make_entry / {checked_reg} register_internal_struct "
        f"cross-checked against {checked_defs} source struct(s))"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
