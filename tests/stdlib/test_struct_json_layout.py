"""v5.39.1 Js.4.B.1 — JsonValue / JsonError layout-drift guard.

The fix in ``mapanare/lower.py::_ensure_json_types_registered``
hardcodes the canonical layout of ``JsonValue`` (enum, 7 variants)
and ``JsonError`` (struct, 3 fields). The injection only fires
when the user does NOT import ``stdlib/encoding/json``; with the
import, the parser registers the real definitions and the
hardcoded layout is bypassed.

If ``stdlib/encoding/json.mn`` ever drifts (variant rename, field
reorder, type change), the no-import path silently emits IR
against the wrong shape — the with-import path keeps working,
masking the divergence. This test fails loudly when that happens
so the lower.py-injected layout can be updated in the same PR.

Pin: ``stdlib/encoding/json.mn:15-29`` (committed at v5.39.0).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mapanare.ast_nodes import DocComment, EnumDef, StructDef
from mapanare.parser import parse

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
JSON_MN = REPO_ROOT / "stdlib" / "encoding" / "json.mn"


# Canonical layouts as injected by mapanare/lower.py::_ensure_json_types_registered.
# (variant_name, [(arg_outer_name, [arg_inner_name_or_None, ...]), ...])
EXPECTED_JSON_VALUE_VARIANTS: list[tuple[str, list[tuple[str, list[str | None]]]]] = [
    ("Null", []),
    ("Bool", [("Bool", [])]),
    ("Int", [("Int", [])]),
    ("Float", [("Float", [])]),
    ("Str", [("String", [])]),
    ("Array", [("List", ["JsonValue"])]),
    ("Object", [("Map", ["String", "JsonValue"])]),
]

# (field_name, type_name)
EXPECTED_JSON_ERROR_FIELDS: list[tuple[str, str]] = [
    ("message", "String"),
    ("line", "Int"),
    ("col", "Int"),
]


def _shape_of(t) -> tuple[str, list[str | None]]:
    """Reduce a type expression to (outer_name, [inner_arg_names])."""
    name = getattr(t, "name", None)
    args = getattr(t, "args", None) or []
    inner = []
    for a in args:
        inner.append(getattr(a, "name", None))
    return (name, inner)


@pytest.fixture(scope="module")
def json_ast():
    if not JSON_MN.exists():
        pytest.skip(f"json.mn not found at {JSON_MN}")
    src = JSON_MN.read_text()
    return parse(src, filename="json.mn")


def _find_def(ast, kind, name):
    for d in ast.definitions:
        if isinstance(d, DocComment) and d.definition is not None:
            d = d.definition
        if isinstance(d, kind) and d.name == name:
            return d
    return None


def test_json_value_layout_matches_lower_py_injection(json_ast) -> None:
    """JsonValue variants in json.mn match _ensure_json_types_registered."""
    enum_def = _find_def(json_ast, EnumDef, "JsonValue")
    assert enum_def is not None, "JsonValue enum missing from stdlib/encoding/json.mn"

    actual = []
    for v in enum_def.variants:
        actual.append((v.name, [_shape_of(f) for f in v.fields]))

    if actual != EXPECTED_JSON_VALUE_VARIANTS:
        pytest.fail(
            "stdlib/encoding/json.mn JsonValue layout drifted from "
            "mapanare/lower.py::_ensure_json_types_registered injection.\n"
            f"  expected: {EXPECTED_JSON_VALUE_VARIANTS}\n"
            f"  actual:   {actual}\n"
            "Update the lower.py injection to match (and bump SESSION_REPORT)."
        )


def test_json_error_layout_matches_lower_py_injection(json_ast) -> None:
    """JsonError fields in json.mn match _ensure_json_types_registered."""
    struct_def = _find_def(json_ast, StructDef, "JsonError")
    assert struct_def is not None, "JsonError struct missing from stdlib/encoding/json.mn"

    actual = [(f.name, getattr(f.type_annotation, "name", None)) for f in struct_def.fields]

    if actual != EXPECTED_JSON_ERROR_FIELDS:
        pytest.fail(
            "stdlib/encoding/json.mn JsonError layout drifted from "
            "mapanare/lower.py::_ensure_json_types_registered injection.\n"
            f"  expected: {EXPECTED_JSON_ERROR_FIELDS}\n"
            f"  actual:   {actual}\n"
            "Update the lower.py injection to match (and bump SESSION_REPORT)."
        )
