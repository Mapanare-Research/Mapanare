"""Dato data engine — Table construction and accessor tests.

Tests verify that the core table/column modules compile to valid LLVM IR via
the MIR-based emitter. Since cross-module compilation is not yet ready, tests
inline the dato module source code within test programs.

Covers:
  - table() construction with valid columns
  - table() with mismatched column lengths (error)
  - Empty table
  - ncols, nrows accessors
  - get_col by name, returns None for missing
  - col_names, dtypes
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

# Strip import lines so we can inline sources
_IMPORT_RE = re.compile(r"^import\s+.*$", re.MULTILINE)


def _strip_imports(src: str) -> str:
    return _IMPORT_RE.sub("", src)


# Combined source: col + table (table depends on col)
_BASE_SRC = _strip_imports(_COL_MN) + "\n\n" + _strip_imports(_TABLE_MN)


def _compile_mir(source: str) -> str:
    return _compile_to_llvm_ir(source, "test_dato_table.mn", use_mir=True)


def _dato_with_main(main_body: str) -> str:
    return _BASE_SRC + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


# ---------------------------------------------------------------------------
# Table construction
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestTableConstruction:
    def test_table_valid_columns(self) -> None:
        """table() with valid columns compiles."""
        src = _dato_with_main("""\
            let c1: Col = col_i64("age", [10, 20, 30])
            let c2: Col = col_str("name", ["Alice", "Bob", "Carol"])
            let cols: List<Col> = [c1, c2]
            let result: Result<Table, DatoError> = table(cols)
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_table_mismatched_lengths(self) -> None:
        """table() with mismatched column lengths compiles error path."""
        src = _dato_with_main("""\
            let c1: Col = col_i64("x", [1, 2, 3])
            let c2: Col = col_str("y", ["a", "b"])
            let cols: List<Col> = [c1, c2]
            let result: Result<Table, DatoError> = table(cols)
            match result {
                Ok(t) => { print("unexpected ok") },
                Err(e) => { print(error_message(e)) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_empty_table(self) -> None:
        """empty() creates a table with zero rows and columns."""
        src = _dato_with_main("""\
            let t: Table = empty()
            print(str(nrows(t)))
            print(str(ncols(t)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestAccessors:
    def test_ncols(self) -> None:
        """ncols returns the number of columns."""
        src = _dato_with_main("""\
            let c1: Col = col_i64("a", [1, 2])
            let c2: Col = col_i64("b", [3, 4])
            let result: Result<Table, DatoError> = table([c1, c2])
            match result {
                Ok(t) => { print(str(ncols(t))) },
                Err(e) => { print("err") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_nrows(self) -> None:
        """nrows returns the number of rows."""
        src = _dato_with_main("""\
            let c1: Col = col_i64("a", [1, 2, 3])
            let result: Result<Table, DatoError> = table([c1])
            match result {
                Ok(t) => { print(str(nrows(t))) },
                Err(e) => { print("err") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_get_col_found(self) -> None:
        """get_col returns Some for existing column."""
        src = _dato_with_main("""\
            let c1: Col = col_i64("age", [10, 20])
            let result: Result<Table, DatoError> = table([c1])
            match result {
                Ok(t) => {
                    let maybe: Option<Col> = get_col(t, "age")
                    match maybe {
                        Some(c) => { print(c.name) },
                        None => { print("not found") }
                    }
                },
                Err(e) => { print("err") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_get_col_missing(self) -> None:
        """get_col returns None for missing column."""
        src = _dato_with_main("""\
            let c1: Col = col_i64("age", [10, 20])
            let result: Result<Table, DatoError> = table([c1])
            match result {
                Ok(t) => {
                    let maybe: Option<Col> = get_col(t, "name")
                    match maybe {
                        Some(c) => { print("unexpected") },
                        None => { print("not found") }
                    }
                },
                Err(e) => { print("err") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_col_names(self) -> None:
        """col_names returns list of column names."""
        src = _dato_with_main("""\
            let c1: Col = col_i64("x", [1])
            let c2: Col = col_str("y", ["a"])
            let result: Result<Table, DatoError> = table([c1, c2])
            match result {
                Ok(t) => {
                    let names: List<String> = col_names(t)
                    print(str(len(names)))
                },
                Err(e) => { print("err") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_dtypes(self) -> None:
        """dtypes returns list of dtype name strings."""
        src = _dato_with_main("""\
            let c1: Col = col_i64("a", [1])
            let c2: Col = col_f64("b", [1.0])
            let c3: Col = col_str("c", ["x"])
            let result: Result<Table, DatoError> = table([c1, c2, c3])
            match result {
                Ok(t) => {
                    let dts: List<String> = dtypes(t)
                    print(str(len(dts)))
                },
                Err(e) => { print("err") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
