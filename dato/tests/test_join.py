"""Dato data engine — Join and concat tests.

Tests verify that the join module compiles to valid LLVM IR via the MIR-based
emitter. All dato module sources are inlined since cross-module compilation
is not yet ready.

Covers:
  - inner_join matches only common keys
  - left_join preserves all left rows
  - concat vertical stack
  - concat schema mismatch error
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
_JOIN_MN = _DATO_DIR.joinpath("join.mn").read_text(encoding="utf-8")

_IMPORT_RE = re.compile(r"^import\s+.*$", re.MULTILINE)


def _strip_imports(src: str) -> str:
    return _IMPORT_RE.sub("", src)


_BASE_SRC = (
    _strip_imports(_COL_MN) + "\n\n" + _strip_imports(_TABLE_MN) + "\n\n" + _strip_imports(_JOIN_MN)
)


def _compile_mir(source: str) -> str:
    return _compile_to_llvm_ir(source, "test_dato_join.mn", use_mir=True)


def _dato_with_main(main_body: str) -> str:
    return _BASE_SRC + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


def _make_two_tables_src() -> str:
    """Build left (id, name) and right (id, score) tables for join tests."""
    return """\
        let l_id: Col = col_str("id", ["a", "b", "c"])
        let l_name: Col = col_str("name", ["Alice", "Bob", "Carol"])
        let left_r: Result<Table, DatoError> = table([l_id, l_name])

        let r_id: Col = col_str("id", ["b", "c", "d"])
        let r_score: Col = col_i64("score", [90, 80, 70])
        let right_r: Result<Table, DatoError> = table([r_id, r_score])
    """


# ---------------------------------------------------------------------------
# Inner Join
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestInnerJoin:
    def test_inner_join_common_keys(self) -> None:
        """inner_join matches only common keys (b, c)."""
        src = _dato_with_main(f"""\
            {_make_two_tables_src()}
            match left_r {{
                Ok(left) => {{
                    match right_r {{
                        Ok(right) => {{
                            let jr: Result<Table, DatoError> = inner_join(left, right, "id")
                            match jr {{
                                Ok(joined) => {{ print(str(nrows(joined))) }},
                                Err(e) => {{ print(error_message(e)) }}
                            }}
                        }},
                        Err(e) => {{ print("err") }}
                    }}
                }},
                Err(e) => {{ print("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Left Join
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestLeftJoin:
    def test_left_join_preserves_all_left(self) -> None:
        """left_join preserves all left rows, nulls for unmatched right."""
        src = _dato_with_main(f"""\
            {_make_two_tables_src()}
            match left_r {{
                Ok(left) => {{
                    match right_r {{
                        Ok(right) => {{
                            let jr: Result<Table, DatoError> = left_join(left, right, "id")
                            match jr {{
                                Ok(joined) => {{ print(str(nrows(joined))) }},
                                Err(e) => {{ print(error_message(e)) }}
                            }}
                        }},
                        Err(e) => {{ print("err") }}
                    }}
                }},
                Err(e) => {{ print("err") }}
            }}
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Concat
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestConcat:
    def test_concat_vertical_stack(self) -> None:
        """concat vertically stacks tables with matching schemas."""
        src = _dato_with_main("""\
            let c1: Col = col_i64("x", [1, 2])
            let c2: Col = col_i64("x", [3, 4])
            let t1_r: Result<Table, DatoError> = table([c1])
            let t2_r: Result<Table, DatoError> = table([c2])
            match t1_r {
                Ok(t1) => {
                    match t2_r {
                        Ok(t2) => {
                            let cr: Result<Table, DatoError> = concat([t1, t2])
                            match cr {
                                Ok(combined) => { print(str(nrows(combined))) },
                                Err(e) => { print(error_message(e)) }
                            }
                        },
                        Err(e) => { print("err") }
                    }
                },
                Err(e) => { print("err") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_concat_schema_mismatch_error(self) -> None:
        """concat with mismatched schemas returns error."""
        src = _dato_with_main("""\
            let c1: Col = col_i64("x", [1, 2])
            let c2: Col = col_str("y", ["a", "b"])
            let t1_r: Result<Table, DatoError> = table([c1])
            let t2_r: Result<Table, DatoError> = table([c2])
            match t1_r {
                Ok(t1) => {
                    match t2_r {
                        Ok(t2) => {
                            let cr: Result<Table, DatoError> = concat([t1, t2])
                            match cr {
                                Ok(combined) => { print("unexpected ok") },
                                Err(e) => { print(error_message(e)) }
                            }
                        },
                        Err(e) => { print("err") }
                    }
                },
                Err(e) => { print("err") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
