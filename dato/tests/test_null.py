"""Dato data engine — Null handling tests.

Tests verify that the null module compiles to valid LLVM IR via the MIR-based
emitter. All dato module sources are inlined since cross-module compilation
is not yet ready.

Covers:
  - drop_nulls removes null rows
  - fill_null_int replaces nulls
  - fill_forward propagates last non-null value
  - null_count
"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path

import pytest

try:
    from llvmlite import ir  # noqa: F401

    HAS_LLVMLITE = True
except ImportError:
    HAS_LLVMLITE = False

from mapanare.cli import _compile_to_llvm_ir

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DATO_DIR = Path(__file__).resolve().parent.parent / "src"

_COL_MN = _DATO_DIR.joinpath("col.mn").read_text(encoding="utf-8")
_TABLE_MN = _DATO_DIR.joinpath("table.mn").read_text(encoding="utf-8")
_NULL_MN = _DATO_DIR.joinpath("null.mn").read_text(encoding="utf-8")

_IMPORT_RE = re.compile(r"^import\s+.*$", re.MULTILINE)


def _strip_imports(src: str) -> str:
    return _IMPORT_RE.sub("", src)


_BASE_SRC = (
    _strip_imports(_COL_MN) + "\n\n" + _strip_imports(_TABLE_MN) + "\n\n" + _strip_imports(_NULL_MN)
)


def _compile_mir(source: str) -> str:
    return _compile_to_llvm_ir(source, "test_dato_null.mn", use_mir=True)


def _dato_with_main(main_body: str) -> str:
    return _BASE_SRC + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


def _make_nullable_table_src() -> str:
    """Build a 4-row table where 'val' column has a null at index 1."""
    return """\
        let data: List<Int> = [10, 0, 30, 40]
        let mask: List<Bool> = [true, false, true, true]
        let val_col: Col = col_i64_masked("val", data, mask)
        let name_col: Col = col_str("name", ["a", "b", "c", "d"])
        let result: Result<Table, DatoError> = table([val_col, name_col])
    """


# ---------------------------------------------------------------------------
# drop_nulls
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestDropNulls:
    def test_drop_nulls_removes_null_rows(self) -> None:
        """drop_nulls removes rows where given column is null."""
        src = _dato_with_main(f"""\
            {_make_nullable_table_src()}
            match result {{
                Ok(t) => {{
                    let cleaned: Table = drop_nulls(t, "val")
                    println(str(nrows(cleaned)))
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# fill_null_int
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestFillNull:
    def test_fill_null_int_replaces(self) -> None:
        """fill_null_int replaces null values with given default."""
        src = _dato_with_main(f"""\
            {_make_nullable_table_src()}
            match result {{
                Ok(t) => {{
                    let filled: Table = fill_null_int(t, "val", -1)
                    println(str(nrows(filled)))
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# fill_forward
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestFillForward:
    def test_fill_forward_propagates(self) -> None:
        """fill_forward carries last non-null value into null positions."""
        src = _dato_with_main(f"""\
            {_make_nullable_table_src()}
            match result {{
                Ok(t) => {{
                    let filled: Table = fill_forward(t, "val")
                    println(str(nrows(filled)))
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# null_count
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestNullCount:
    def test_null_count(self) -> None:
        """null_count returns the number of null values in a column."""
        src = _dato_with_main(f"""\
            {_make_nullable_table_src()}
            match result {{
                Ok(t) => {{
                    let nc: Int = null_count(t, "val")
                    println(str(nc))
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
