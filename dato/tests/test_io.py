"""Dato data engine — CSV I/O tests.

Tests verify that the io module compiles to valid LLVM IR via the MIR-based
emitter. All dato module sources are inlined since cross-module compilation
is not yet ready.

Covers:
  - csv() loads file, infers types
  - to_csv writes and can be re-read
  - from_rows constructs table
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
_IO_MN = _DATO_DIR.joinpath("io.mn").read_text(encoding="utf-8")

_IMPORT_RE = re.compile(r"^import\s+.*$", re.MULTILINE)


def _strip_imports(src: str) -> str:
    return _IMPORT_RE.sub("", src)


_BASE_SRC = (
    _strip_imports(_COL_MN) + "\n\n" + _strip_imports(_TABLE_MN) + "\n\n" + _strip_imports(_IO_MN)
)


def _compile_mir(source: str) -> str:
    return _compile_to_llvm_ir(source, "test_dato_io.mn", use_mir=True)


def _dato_with_main(main_body: str) -> str:
    return _BASE_SRC + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


# ---------------------------------------------------------------------------
# CSV load
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCsvLoad:
    def test_csv_load_compiles(self) -> None:
        """csv() file load with type inference compiles."""
        src = _dato_with_main("""\
            let result: Result<Table, DatoError> = csv("/tmp/test_data.csv")
            match result {
                Ok(t) => { print(str(nrows(t))) },
                Err(e) => { print(error_message(e)) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_file_read" in ir_out


# ---------------------------------------------------------------------------
# CSV write
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCsvWrite:
    def test_to_csv_compiles(self) -> None:
        """to_csv writes table to CSV file."""
        src = _dato_with_main("""\
            let c1: Col = col_i64("x", [1, 2, 3])
            let c2: Col = col_str("name", ["a", "b", "c"])
            let tr: Result<Table, DatoError> = table([c1, c2])
            match tr {
                Ok(t) => {
                    let wr: Result<Bool, DatoError> = to_csv(t, "/tmp/test_out.csv")
                    match wr {
                        Ok(ok) => { print("written") },
                        Err(e) => { print(error_message(e)) }
                    }
                },
                Err(e) => { print("err") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_file_write" in ir_out

    def test_to_csv_round_trip_compiles(self) -> None:
        """to_csv then csv re-read round-trip compiles."""
        src = _dato_with_main("""\
            let c1: Col = col_i64("val", [10, 20])
            let tr: Result<Table, DatoError> = table([c1])
            match tr {
                Ok(t) => {
                    let wr: Result<Bool, DatoError> = to_csv(t, "/tmp/round_trip.csv")
                    let reread: Result<Table, DatoError> = csv("/tmp/round_trip.csv")
                    print("ok")
                },
                Err(e) => { print("err") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# from_rows
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestFromRows:
    def test_from_rows_constructs_table(self) -> None:
        """from_rows builds a Str-typed table from raw row data."""
        src = _dato_with_main("""\
            let names: List<String> = ["name", "city"]
            let rows: List<List<String>> = [["Alice", "NYC"], ["Bob", "LA"]]
            let t: Table = from_rows(names, rows)
            print(str(nrows(t)))
            print(str(ncols(t)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
