"""Dato data engine — Pivot and melt tests.

Tests verify that the reshape module compiles to valid LLVM IR via the
MIR-based emitter. All dato module sources are inlined since cross-module
compilation is not yet ready.

Covers:
  - pivot long to wide
  - melt wide to long
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
_RESHAPE_MN = _DATO_DIR.joinpath("reshape.mn").read_text(encoding="utf-8")

_IMPORT_RE = re.compile(r"^import\s+.*$", re.MULTILINE)


def _strip_imports(src: str) -> str:
    return _IMPORT_RE.sub("", src)


_BASE_SRC = (
    _strip_imports(_COL_MN)
    + "\n\n"
    + _strip_imports(_TABLE_MN)
    + "\n\n"
    + _strip_imports(_RESHAPE_MN)
)


def _compile_mir(source: str) -> str:
    return _compile_to_llvm_ir(source, "test_dato_reshape.mn", use_mir=True)


def _dato_with_main(main_body: str) -> str:
    return _BASE_SRC + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


# ---------------------------------------------------------------------------
# Pivot
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestPivot:
    def test_pivot_long_to_wide(self) -> None:
        """pivot converts long-format data to wide-format columns.

        Input (long):
          id   | metric | value
          "a"  | "x"    | 10
          "a"  | "y"    | 20
          "b"  | "x"    | 30
          "b"  | "y"    | 40

        Output (wide):
          id  | x  | y
          "a" | 10 | 20
          "b" | 30 | 40
        """
        src = _dato_with_main("""\
            let id_col: Col = col_str("id", ["a", "a", "b", "b"])
            let metric_col: Col = col_str("metric", ["x", "y", "x", "y"])
            let value_col: Col = col_i64("value", [10, 20, 30, 40])
            let tr: Result<Table, DatoError> = table([id_col, metric_col, value_col])
            match tr {
                Ok(t) => {
                    let pr: Result<Table, DatoError> = pivot(t, "id", "metric", "value")
                    match pr {
                        Ok(wide) => {
                            print(str(nrows(wide)))
                            print(str(ncols(wide)))
                        },
                        Err(e) => { print(error_message(e)) }
                    }
                },
                Err(e) => { print("err") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_pivot_missing_column_error(self) -> None:
        """pivot with nonexistent column returns error."""
        src = _dato_with_main("""\
            let c: Col = col_str("a", ["x"])
            let tr: Result<Table, DatoError> = table([c])
            match tr {
                Ok(t) => {
                    let pr: Result<Table, DatoError> = pivot(t, "a", "missing", "also_missing")
                    match pr {
                        Ok(w) => { print("unexpected ok") },
                        Err(e) => { print(error_message(e)) }
                    }
                },
                Err(e) => { print("err") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Melt
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestMelt:
    def test_melt_wide_to_long(self) -> None:
        """melt converts wide-format data to long-format.

        Input (wide):
          name   | score_a | score_b
          "Alice" | 90     | 80
          "Bob"   | 70     | 60

        Output (long):
          name    | variable  | value
          "Alice" | "score_a" | 90
          "Alice" | "score_b" | 80
          "Bob"   | "score_a" | 70
          "Bob"   | "score_b" | 60
        """
        src = _dato_with_main("""\
            let name_col: Col = col_str("name", ["Alice", "Bob"])
            let sa_col: Col = col_i64("score_a", [90, 70])
            let sb_col: Col = col_i64("score_b", [80, 60])
            let tr: Result<Table, DatoError> = table([name_col, sa_col, sb_col])
            match tr {
                Ok(t) => {
                    let mr: Result<Table, DatoError> = melt(t, ["name"], ["score_a", "score_b"])
                    match mr {
                        Ok(long) => {
                            print(str(nrows(long)))
                            print(str(ncols(long)))
                        },
                        Err(e) => { print(error_message(e)) }
                    }
                },
                Err(e) => { print("err") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_melt_missing_column_error(self) -> None:
        """melt with nonexistent value column returns error."""
        src = _dato_with_main("""\
            let c: Col = col_str("a", ["x"])
            let tr: Result<Table, DatoError> = table([c])
            match tr {
                Ok(t) => {
                    let mr: Result<Table, DatoError> = melt(t, ["a"], ["missing"])
                    match mr {
                        Ok(l) => { print("unexpected ok") },
                        Err(e) => { print(error_message(e)) }
                    }
                },
                Err(e) => { print("err") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
