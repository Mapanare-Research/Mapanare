"""Dato data engine — Aggregation tests.

Tests verify that the agg module compiles to valid LLVM IR via the MIR-based
emitter. All dato module sources are inlined since cross-module compilation
is not yet ready.

Covers:
  - sum_col, mean_col, min_col, max_col
  - count
  - group by string column
  - group_sum, group_mean, group_count
  - describe produces summary stats
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
_AGG_MN = _DATO_DIR.joinpath("agg.mn").read_text(encoding="utf-8")

_IMPORT_RE = re.compile(r"^import\s+.*$", re.MULTILINE)


def _strip_imports(src: str) -> str:
    return _IMPORT_RE.sub("", src)


_BASE_SRC = (
    _strip_imports(_COL_MN) + "\n\n" + _strip_imports(_TABLE_MN) + "\n\n" + _strip_imports(_AGG_MN)
)


def _compile_mir(source: str) -> str:
    return _compile_to_llvm_ir(source, "test_dato_agg.mn", use_mir=True)


def _dato_with_main(main_body: str) -> str:
    return _BASE_SRC + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


def _make_table_src() -> str:
    """Helper: 4-row table with 'dept' (Str) and 'salary' (Int) columns."""
    return """\
        let dept_col: Col = col_str("dept", ["eng", "eng", "sales", "sales"])
        let salary_col: Col = col_i64("salary", [100, 200, 150, 250])
        let result: Result<Table, DatoError> = table([dept_col, salary_col])
    """


# ---------------------------------------------------------------------------
# Scalar aggregates
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestScalarAgg:
    def test_sum_col(self) -> None:
        """sum_col sums integer column values."""
        src = _dato_with_main(f"""\
            {_make_table_src()}
            match result {{
                Ok(t) => {{
                    let s: Int = sum_col(t, "salary")
                    println(str(s))
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_mean_col(self) -> None:
        """mean_col computes arithmetic mean."""
        src = _dato_with_main(f"""\
            {_make_table_src()}
            match result {{
                Ok(t) => {{
                    let m: Float = mean_col(t, "salary")
                    println(str(m))
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_min_col(self) -> None:
        """min_col finds minimum value."""
        src = _dato_with_main(f"""\
            {_make_table_src()}
            match result {{
                Ok(t) => {{
                    let mn: Int = min_col(t, "salary")
                    println(str(mn))
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_max_col(self) -> None:
        """max_col finds maximum value."""
        src = _dato_with_main(f"""\
            {_make_table_src()}
            match result {{
                Ok(t) => {{
                    let mx: Int = max_col(t, "salary")
                    println(str(mx))
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_count(self) -> None:
        """count returns number of rows."""
        src = _dato_with_main(f"""\
            {_make_table_src()}
            match result {{
                Ok(t) => {{
                    let c: Int = count(t)
                    println(str(c))
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Group by
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestGroupBy:
    def test_group_by_string(self) -> None:
        """group by string column produces Grouped struct."""
        src = _dato_with_main(f"""\
            {_make_table_src()}
            match result {{
                Ok(t) => {{
                    let gr: Result<Grouped, DatoError> = group(t, "dept")
                    match gr {{
                        Ok(g) => {{ println(str(len(g.key_values))) }},
                        Err(e) => {{ println("err") }}
                    }}
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_group_sum(self) -> None:
        """group_sum aggregates sum per group."""
        src = _dato_with_main(f"""\
            {_make_table_src()}
            match result {{
                Ok(t) => {{
                    let gr: Result<Grouped, DatoError> = group(t, "dept")
                    match gr {{
                        Ok(g) => {{
                            let agg: Table = group_sum(g, "salary")
                            println(str(nrows(agg)))
                        }},
                        Err(e) => {{ println("err") }}
                    }}
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_group_mean(self) -> None:
        """group_mean aggregates mean per group."""
        src = _dato_with_main(f"""\
            {_make_table_src()}
            match result {{
                Ok(t) => {{
                    let gr: Result<Grouped, DatoError> = group(t, "dept")
                    match gr {{
                        Ok(g) => {{
                            let agg: Table = group_mean(g, "salary")
                            println(str(nrows(agg)))
                        }},
                        Err(e) => {{ println("err") }}
                    }}
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_group_count(self) -> None:
        """group_count counts rows per group."""
        src = _dato_with_main(f"""\
            {_make_table_src()}
            match result {{
                Ok(t) => {{
                    let gr: Result<Grouped, DatoError> = group(t, "dept")
                    match gr {{
                        Ok(g) => {{
                            let agg: Table = group_count(g)
                            println(str(nrows(agg)))
                        }},
                        Err(e) => {{ println("err") }}
                    }}
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Describe
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestDescribe:
    def test_describe_produces_stats(self) -> None:
        """describe returns summary stats table for numeric columns."""
        src = _dato_with_main(f"""\
            {_make_table_src()}
            match result {{
                Ok(t) => {{
                    let desc: Table = describe(t)
                    println(str(ncols(desc)))
                    println(str(nrows(desc)))
                }},
                Err(e) => {{ println("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
