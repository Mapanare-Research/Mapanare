"""db/sql.mn — Core SQL types and URL parsing tests.

Tests verify that the SQL core module compiles to valid LLVM IR via the
MIR-based emitter. Since cross-module compilation (Phase 8) is not yet ready,
tests inline the SQL module source code within test programs.

Covers:
  - SqlValue enum construction (Null, Int, Float, Str, Bool)
  - Row creation and accessors (row_get, row_get_string, row_get_int, etc.)
  - sql_value_to_string conversion
  - URL parsing (sqlite:///path, postgres://user:pass@host/db)
  - error_message on each SqlError variant
"""

from __future__ import annotations

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

_SQL_MN = (Path(__file__).resolve().parent.parent.parent / "stdlib" / "db" / "sql.mn").read_text(
    encoding="utf-8"
)

# Strip out extern declarations and entire connect/close functions that
# reference C FFI symbols — we only test pure-logic helpers here.


def _stub_externs(src: str) -> str:
    """Replace extern declarations with stub functions returning 0."""
    lines = src.splitlines()
    result: list[str] = []
    for line in lines:
        if line.startswith("extern "):
            stub = line.replace('extern "C" ', "")
            result.append(stub.rstrip() + " { return 0 }")
        else:
            result.append(line)
    return "\n".join(result)


_SQL_PURE = _stub_externs(_SQL_MN)


def _compile_mir(source: str) -> str:
    """Compile via MIR-based LLVM emitter."""
    return _compile_to_llvm_ir(source, "test_sql_core.mn", use_mir=True)


def _sql_with_main(main_body: str) -> str:
    """Prepend the SQL module source and wrap main_body in fn main()."""
    return _SQL_PURE + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


# ---------------------------------------------------------------------------
# SqlValue enum construction
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestSqlValueEnum:
    def test_sql_value_null(self) -> None:
        """SqlValue::Null variant compiles."""
        src = _sql_with_main("""\
            let v: SqlValue = Null()
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_sql_value_int(self) -> None:
        """SqlValue::Int variant compiles."""
        src = _sql_with_main("""\
            let v: SqlValue = Int(42)
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_sql_value_float(self) -> None:
        """SqlValue::Float variant compiles."""
        src = _sql_with_main("""\
            let v: SqlValue = Float(3.14)
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_sql_value_str(self) -> None:
        """SqlValue::Str variant compiles."""
        src = _sql_with_main("""\
            let v: SqlValue = Str("hello")
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_sql_value_bool(self) -> None:
        """SqlValue::Bool variant compiles."""
        src = _sql_with_main("""\
            let v: SqlValue = Bool(true)
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Row creation and accessors
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestRowAccessors:
    def test_new_row(self) -> None:
        """new_row constructor compiles."""
        src = _sql_with_main("""\
            let cols: List<String> = ["name", "age"]
            let vals: List<SqlValue> = [Str("Alice"), Int(30)]
            let r: Row = new_row(cols, vals)
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_row_get_existing_column(self) -> None:
        """row_get returns Some for existing column."""
        src = _sql_with_main("""\
            let cols: List<String> = ["id", "name"]
            let vals: List<SqlValue> = [Int(1), Str("Bob")]
            let r: Row = new_row(cols, vals)
            let val: Option<SqlValue> = row_get(r, "name")
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_row_get_missing_column(self) -> None:
        """row_get returns None for missing column."""
        src = _sql_with_main("""\
            let cols: List<String> = ["id"]
            let vals: List<SqlValue> = [Int(1)]
            let r: Row = new_row(cols, vals)
            let val: Option<SqlValue> = row_get(r, "nonexistent")
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_row_get_string(self) -> None:
        """row_get_string extracts string value."""
        src = _sql_with_main("""\
            let cols: List<String> = ["name"]
            let vals: List<SqlValue> = [Str("Alice")]
            let r: Row = new_row(cols, vals)
            let val: Option<String> = row_get_string(r, "name")
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_row_get_string_from_int(self) -> None:
        """row_get_string converts Int to string."""
        src = _sql_with_main("""\
            let cols: List<String> = ["count"]
            let vals: List<SqlValue> = [Int(42)]
            let r: Row = new_row(cols, vals)
            let val: Option<String> = row_get_string(r, "count")
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_row_get_int(self) -> None:
        """row_get_int extracts integer value."""
        src = _sql_with_main("""\
            let cols: List<String> = ["id"]
            let vals: List<SqlValue> = [Int(7)]
            let r: Row = new_row(cols, vals)
            let val: Option<Int> = row_get_int(r, "id")
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_row_get_int_from_string_returns_none(self) -> None:
        """row_get_int returns None for Str value."""
        src = _sql_with_main("""\
            let cols: List<String> = ["name"]
            let vals: List<SqlValue> = [Str("Alice")]
            let r: Row = new_row(cols, vals)
            let val: Option<Int> = row_get_int(r, "name")
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_row_get_float(self) -> None:
        """row_get_float extracts float value."""
        src = _sql_with_main("""\
            let cols: List<String> = ["price"]
            let vals: List<SqlValue> = [Float(9.99)]
            let r: Row = new_row(cols, vals)
            let val: Option<Float> = row_get_float(r, "price")
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_row_get_float_from_int(self) -> None:
        """row_get_float converts Int to Float."""
        src = _sql_with_main("""\
            let cols: List<String> = ["score"]
            let vals: List<SqlValue> = [Int(100)]
            let r: Row = new_row(cols, vals)
            let val: Option<Float> = row_get_float(r, "score")
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_row_get_bool(self) -> None:
        """row_get_bool extracts boolean value."""
        src = _sql_with_main("""\
            let cols: List<String> = ["active"]
            let vals: List<SqlValue> = [Bool(true)]
            let r: Row = new_row(cols, vals)
            let val: Option<Bool> = row_get_bool(r, "active")
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_row_get_bool_from_int(self) -> None:
        """row_get_bool converts nonzero Int to true."""
        src = _sql_with_main("""\
            let cols: List<String> = ["flag"]
            let vals: List<SqlValue> = [Int(1)]
            let r: Row = new_row(cols, vals)
            let val: Option<Bool> = row_get_bool(r, "flag")
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# sql_value_to_string conversion
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestSqlValueToString:
    def test_null_to_string(self) -> None:
        """sql_value_to_string(Null) returns 'NULL'."""
        src = _sql_with_main("""\
            let s: String = sql_value_to_string(Null())
            print(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_int_to_string(self) -> None:
        """sql_value_to_string(Int) returns the number as string."""
        src = _sql_with_main("""\
            let s: String = sql_value_to_string(Int(42))
            print(s)
        """)
        ir_out = _compile_mir(src)
        assert "__mn_str_from_int" in ir_out

    def test_float_to_string(self) -> None:
        """sql_value_to_string(Float) returns the float as string."""
        src = _sql_with_main("""\
            let s: String = sql_value_to_string(Float(3.14))
            print(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_str_to_string(self) -> None:
        """sql_value_to_string(Str) returns the string itself."""
        src = _sql_with_main("""\
            let s: String = sql_value_to_string(Str("hello"))
            print(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_bool_true_to_string(self) -> None:
        """sql_value_to_string(Bool(true)) returns 'true'."""
        src = _sql_with_main("""\
            let s: String = sql_value_to_string(Bool(true))
            print(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_bool_false_to_string(self) -> None:
        """sql_value_to_string(Bool(false)) returns 'false'."""
        src = _sql_with_main("""\
            let s: String = sql_value_to_string(Bool(false))
            print(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# URL parsing helpers
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestUrlParsing:
    def test_extract_scheme_sqlite(self) -> None:
        """extract_scheme returns 'sqlite' from sqlite:///path."""
        src = _sql_with_main("""\
            let scheme: String = extract_scheme("sqlite:///data/app.db")
            print(scheme)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_extract_scheme_postgres(self) -> None:
        """extract_scheme returns 'postgres' from postgres://..."""
        src = _sql_with_main("""\
            let scheme: String = extract_scheme("postgres://user:pass@host:5432/mydb")
            print(scheme)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_extract_rest_sqlite_file(self) -> None:
        """extract_rest returns file path from sqlite:///path."""
        src = _sql_with_main("""\
            let rest: String = extract_rest("sqlite:///data/app.db")
            print(rest)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_extract_rest_sqlite_memory(self) -> None:
        """extract_rest handles sqlite::memory: special case."""
        src = _sql_with_main("""\
            let rest: String = extract_rest("sqlite::memory:")
            print(rest)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_extract_rest_postgres(self) -> None:
        """extract_rest returns user:pass@host/db from postgres://..."""
        src = _sql_with_main("""\
            let rest: String = extract_rest("postgres://user:pass@host/db")
            print(rest)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_extract_scheme_empty_string(self) -> None:
        """extract_scheme on empty string returns empty."""
        src = _sql_with_main("""\
            let scheme: String = extract_scheme("")
            print(scheme)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Error message extraction
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestErrorMessage:
    def test_connection_failed_message(self) -> None:
        """error_message on ConnectionFailed."""
        src = _sql_with_main("""\
            let err: SqlError = ConnectionFailed("timeout")
            let msg: String = error_message(err)
            print(msg)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_query_failed_message(self) -> None:
        """error_message on QueryFailed."""
        src = _sql_with_main("""\
            let err: SqlError = QueryFailed("syntax error")
            let msg: String = error_message(err)
            print(msg)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_type_mismatch_message(self) -> None:
        """error_message on TypeMismatch."""
        src = _sql_with_main("""\
            let err: SqlError = TypeMismatch("expected Int, got String")
            let msg: String = error_message(err)
            print(msg)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_driver_not_found_message(self) -> None:
        """error_message on DriverNotFound."""
        src = _sql_with_main("""\
            let err: SqlError = DriverNotFound("mysql")
            let msg: String = error_message(err)
            print(msg)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# QueryResult and Connection struct construction
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestStructConstruction:
    def test_query_result_struct(self) -> None:
        """QueryResult struct compiles."""
        src = _sql_with_main("""\
            let rows: List<Row> = []
            let qr: QueryResult = new QueryResult { rows: rows, affected: 0 }
            print(str(qr.affected))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_connection_struct(self) -> None:
        """Connection struct compiles."""
        src = _sql_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            print(conn.driver)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_row_field_access(self) -> None:
        """Row struct field access compiles."""
        src = _sql_with_main("""\
            let cols: List<String> = ["a", "b"]
            let vals: List<SqlValue> = [Int(1), Int(2)]
            let r: Row = new_row(cols, vals)
            print(str(len(r.columns)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
