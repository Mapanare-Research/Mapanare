"""Dato data engine — Core transforms (select, filter, sort, etc.) tests.

Tests verify that the ops module compiles to valid LLVM IR via the MIR-based
emitter. All dato module sources are inlined since cross-module compilation
is not yet ready.

Covers:
  - select keeps named columns
  - drop_cols removes columns
  - rename column
  - head/tail/slice
  - sort_by_int ascending/descending
  - filter_by_int above/below threshold
  - filter_by_str exact match
  - unique_by deduplicates
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
_OPS_MN = _DATO_DIR.joinpath("ops.mn").read_text(encoding="utf-8")

_IMPORT_RE = re.compile(r"^import\s+.*$", re.MULTILINE)


def _strip_imports(src: str) -> str:
    return _IMPORT_RE.sub("", src)


_BASE_SRC = (
    _strip_imports(_COL_MN) + "\n\n" + _strip_imports(_TABLE_MN) + "\n\n" + _strip_imports(_OPS_MN)
)


def _compile_mir(source: str) -> str:
    return _compile_to_llvm_ir(source, "test_dato_ops.mn", use_mir=True)


def _dato_with_main(main_body: str) -> str:
    return _BASE_SRC + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


def _make_table_src() -> str:
    """Helper: create a 3-row table with 'name' (Str) and 'age' (Int) columns."""
    return """\
        let name_col: Col = col_str("name", ["Alice", "Bob", "Carol"])
        let age_col: Col = col_i64("age", [30, 25, 28])
        let result: Result<Table, DatoError> = table([name_col, age_col])
    """


# ---------------------------------------------------------------------------
# Select / Drop / Rename
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestColumnOps:
    def test_select_keeps_columns(self) -> None:
        """select keeps named columns."""
        src = _dato_with_main(f"""\
            {_make_table_src()}
            match result {{
                Ok(t) => {{
                    let selected: Table = select(t, ["name"])
                    println(str(ncols(selected)))
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_drop_cols_removes_columns(self) -> None:
        """drop_cols removes named columns."""
        src = _dato_with_main(f"""\
            {_make_table_src()}
            match result {{
                Ok(t) => {{
                    let dropped: Table = drop_cols(t, ["age"])
                    println(str(ncols(dropped)))
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_rename_column(self) -> None:
        """rename changes a column name."""
        src = _dato_with_main(f"""\
            {_make_table_src()}
            match result {{
                Ok(t) => {{
                    let renamed: Table = rename(t, "age", "years")
                    let names: List<String> = col_names(renamed)
                    println(str(len(names)))
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Head / Tail / Slice
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestSlicing:
    def test_head(self) -> None:
        """head returns first N rows."""
        src = _dato_with_main(f"""\
            {_make_table_src()}
            match result {{
                Ok(t) => {{
                    let h: Table = head(t, 2)
                    println(str(nrows(h)))
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_tail(self) -> None:
        """tail returns last N rows."""
        src = _dato_with_main(f"""\
            {_make_table_src()}
            match result {{
                Ok(t) => {{
                    let tl: Table = tail(t, 1)
                    println(str(nrows(tl)))
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_slice(self) -> None:
        """slice returns rows in [start, end)."""
        src = _dato_with_main(f"""\
            {_make_table_src()}
            match result {{
                Ok(t) => {{
                    let s: Table = slice(t, 1, 3)
                    println(str(nrows(s)))
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Sort
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestSort:
    def test_sort_by_int_ascending(self) -> None:
        """sort_by_int ascending order compiles."""
        src = _dato_with_main(f"""\
            {_make_table_src()}
            match result {{
                Ok(t) => {{
                    let sorted: Table = sort_by_int(t, "age", true)
                    println(str(nrows(sorted)))
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_sort_by_int_descending(self) -> None:
        """sort_by_int descending order compiles."""
        src = _dato_with_main(f"""\
            {_make_table_src()}
            match result {{
                Ok(t) => {{
                    let sorted: Table = sort_by_int(t, "age", false)
                    println(str(nrows(sorted)))
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Filter
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestFilter:
    def test_filter_by_int_above(self) -> None:
        """filter_by_int with above=true keeps rows above threshold."""
        src = _dato_with_main(f"""\
            {_make_table_src()}
            match result {{
                Ok(t) => {{
                    let filtered: Table = filter_by_int(t, "age", 26, true)
                    println(str(nrows(filtered)))
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_filter_by_int_below(self) -> None:
        """filter_by_int with above=false keeps rows below threshold."""
        src = _dato_with_main(f"""\
            {_make_table_src()}
            match result {{
                Ok(t) => {{
                    let filtered: Table = filter_by_int(t, "age", 29, false)
                    println(str(nrows(filtered)))
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_filter_by_str_exact(self) -> None:
        """filter_by_str matches exact string value."""
        src = _dato_with_main(f"""\
            {_make_table_src()}
            match result {{
                Ok(t) => {{
                    let filtered: Table = filter_by_str(t, "name", "Bob")
                    println(str(nrows(filtered)))
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Unique
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestUnique:
    def test_unique_by_deduplicates(self) -> None:
        """unique_by removes duplicate rows by column value."""
        src = _dato_with_main("""\
            let name_col: Col = col_str("name", ["Alice", "Bob", "Alice", "Carol"])
            let age_col: Col = col_i64("age", [30, 25, 30, 28])
            let result: Result<Table, DatoError> = table([name_col, age_col])
            match result {
                Ok(t) => {
                    let uniq: Table = unique_by(t, "name")
                    println(str(nrows(uniq)))
                },
                Err(e) => { println("err") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
