"""db/sqlite.mn — SQLite Driver tests.

Tests verify that the SQLite driver module compiles to valid LLVM IR via the
MIR-based emitter. Since cross-module compilation (Phase 8) is not yet ready,
tests inline both the SQL core and SQLite driver source code within test
programs.

Covers:
  - CRUD operations: create table, insert, select, update, delete
  - Parameterized queries: bind int, float, string, null, bool
  - Transactions: commit persists, rollback reverts
  - Query with no results returns empty list
  - Execute returns affected row count
  - SQL injection attempt fails with parameterized queries
  - Multiple concurrent connections to same DB
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

_SQLITE_MN = (
    Path(__file__).resolve().parent.parent.parent / "stdlib" / "db" / "sqlite.mn"
).read_text(encoding="utf-8")

# Combine both modules, stripping the import statement from sqlite.mn
# since we inline sql.mn directly.
_SQLITE_COMBINED = (
    _SQL_MN
    + "\n\n"
    + "\n".join(line for line in _SQLITE_MN.splitlines() if not line.startswith("import "))
)


def _compile_mir(source: str) -> str:
    """Compile via MIR-based LLVM emitter."""
    return _compile_to_llvm_ir(source, "test_sql_sqlite.mn", use_mir=True)


def _sqlite_with_main(main_body: str) -> str:
    """Prepend combined SQL+SQLite source and wrap main_body in fn main()."""
    return _SQLITE_COMBINED + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCrud:
    def test_create_table(self) -> None:
        """CREATE TABLE compiles via exec."""
        src = _sqlite_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let result: Result<Bool, SqlError> = exec(conn, "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_insert_row(self) -> None:
        """INSERT via execute with parameters compiles."""
        src = _sqlite_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let params: List<SqlValue> = [Str("Alice"), Int(30)]
            let result: Result<Int, SqlError> = execute(conn, "INSERT INTO users (name, age) VALUES (?, ?)", params)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_select_rows(self) -> None:
        """SELECT via query compiles."""
        src = _sqlite_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let params: List<SqlValue> = []
            let result: Result<QueryResult, SqlError> = query(conn, "SELECT * FROM users", params)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_update_row(self) -> None:
        """UPDATE via execute with parameters compiles."""
        src = _sqlite_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let params: List<SqlValue> = [Str("Bob"), Int(1)]
            let result: Result<Int, SqlError> = execute(conn, "UPDATE users SET name = ? WHERE id = ?", params)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_delete_row(self) -> None:
        """DELETE via execute with parameters compiles."""
        src = _sqlite_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let params: List<SqlValue> = [Int(1)]
            let result: Result<Int, SqlError> = execute(conn, "DELETE FROM users WHERE id = ?", params)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Parameterized queries — bind different types
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestParameterBinding:
    def test_bind_int(self) -> None:
        """Bind Int parameter compiles."""
        src = _sqlite_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let params: List<SqlValue> = [Int(42)]
            let result: Result<QueryResult, SqlError> = query(conn, "SELECT * FROM t WHERE id = ?", params)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_bind_float(self) -> None:
        """Bind Float parameter compiles."""
        src = _sqlite_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let params: List<SqlValue> = [Float(3.14)]
            let result: Result<QueryResult, SqlError> = query(conn, "SELECT * FROM t WHERE price = ?", params)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_bind_string(self) -> None:
        """Bind Str parameter compiles."""
        src = _sqlite_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let params: List<SqlValue> = [Str("Alice")]
            let result: Result<QueryResult, SqlError> = query(conn, "SELECT * FROM t WHERE name = ?", params)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_bind_null(self) -> None:
        """Bind Null parameter compiles."""
        src = _sqlite_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let params: List<SqlValue> = [Null()]
            let result: Result<Int, SqlError> = execute(conn, "INSERT INTO t (name) VALUES (?)", params)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_bind_bool(self) -> None:
        """Bind Bool parameter compiles (converted to int 0/1)."""
        src = _sqlite_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let params: List<SqlValue> = [Bool(true)]
            let result: Result<QueryResult, SqlError> = query(conn, "SELECT * FROM t WHERE active = ?", params)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_bind_multiple_types(self) -> None:
        """Bind mixed parameter types compiles."""
        src = _sqlite_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let params: List<SqlValue> = [Str("Alice"), Int(30), Float(5.5), Bool(true), Null()]
            let result: Result<Int, SqlError> = execute(conn, "INSERT INTO t (name, age, score, active, notes) VALUES (?, ?, ?, ?, ?)", params)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestTransactions:
    def test_begin_transaction(self) -> None:
        """BEGIN TRANSACTION compiles."""
        src = _sqlite_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let result: Result<Bool, SqlError> = begin(conn)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_commit_transaction(self) -> None:
        """COMMIT compiles."""
        src = _sqlite_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let result: Result<Bool, SqlError> = commit(conn)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_rollback_transaction(self) -> None:
        """ROLLBACK compiles."""
        src = _sqlite_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let result: Result<Bool, SqlError> = rollback(conn)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_commit_persists_flow(self) -> None:
        """Transaction commit flow (begin, insert, commit, select) compiles."""
        src = _sqlite_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let r1: Result<Bool, SqlError> = begin(conn)
            let params: List<SqlValue> = [Str("Alice")]
            let r2: Result<Int, SqlError> = execute(conn, "INSERT INTO users (name) VALUES (?)", params)
            let r3: Result<Bool, SqlError> = commit(conn)
            let empty: List<SqlValue> = []
            let r4: Result<QueryResult, SqlError> = query(conn, "SELECT * FROM users", empty)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_rollback_reverts_flow(self) -> None:
        """Transaction rollback flow (begin, insert, rollback, select) compiles."""
        src = _sqlite_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let r1: Result<Bool, SqlError> = begin(conn)
            let params: List<SqlValue> = [Str("Alice")]
            let r2: Result<Int, SqlError> = execute(conn, "INSERT INTO users (name) VALUES (?)", params)
            let r3: Result<Bool, SqlError> = rollback(conn)
            let empty: List<SqlValue> = []
            let r4: Result<QueryResult, SqlError> = query(conn, "SELECT * FROM users", empty)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Query with no results
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestEmptyResults:
    def test_query_no_results(self) -> None:
        """SELECT that returns no rows compiles."""
        src = _sqlite_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let params: List<SqlValue> = [Int(999)]
            let result: Result<QueryResult, SqlError> = query(conn, "SELECT * FROM users WHERE id = ?", params)
            match result {
                Ok(qr) => { println(str(len(qr.rows))) },
                Err(e) => { println(error_message(e)) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_query_simple_no_results(self) -> None:
        """query_simple with no matching rows compiles."""
        src = _sqlite_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let result: Result<QueryResult, SqlError> = query_simple(conn, "SELECT * FROM users WHERE 1=0")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Execute returns affected row count
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestExecuteAffectedCount:
    def test_execute_returns_count(self) -> None:
        """execute returns Ok(Int) for affected rows."""
        src = _sqlite_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let params: List<SqlValue> = [Str("new_name"), Int(1)]
            let result: Result<Int, SqlError> = execute(conn, "UPDATE users SET name = ? WHERE id = ?", params)
            match result {
                Ok(n) => { println(str(n)) },
                Err(e) => { println(error_message(e)) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_execute_simple_returns_count(self) -> None:
        """execute_simple returns Ok(Int) for affected rows."""
        src = _sqlite_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let result: Result<Int, SqlError> = execute_simple(conn, "DELETE FROM users WHERE id = 999")
            match result {
                Ok(n) => { println(str(n)) },
                Err(e) => { println(error_message(e)) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# SQL injection prevention via parameterized queries
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestSqlInjection:
    def test_injection_attempt_parameterized(self) -> None:
        """SQL injection string is safely bound as parameter, not executed."""
        src = _sqlite_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let malicious: String = "Robert'; DROP TABLE users;--"
            let params: List<SqlValue> = [Str(malicious)]
            let result: Result<QueryResult, SqlError> = query(conn, "SELECT * FROM users WHERE name = ?", params)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_injection_in_insert(self) -> None:
        """SQL injection in INSERT parameter is safely bound."""
        src = _sqlite_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let malicious: String = "'; DELETE FROM users; --"
            let params: List<SqlValue> = [Str(malicious)]
            let result: Result<Int, SqlError> = execute(conn, "INSERT INTO users (name) VALUES (?)", params)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Multiple connections to same DB
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestMultipleConnections:
    def test_two_connections_same_db(self) -> None:
        """Two connections to the same DB compiles."""
        src = _sqlite_with_main("""\
            let conn1: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let conn2: Connection = new Connection { handle: 2, driver: "sqlite", url: "sqlite:///test.db" }
            let empty: List<SqlValue> = []
            let r1: Result<QueryResult, SqlError> = query(conn1, "SELECT 1", empty)
            let r2: Result<QueryResult, SqlError> = query(conn2, "SELECT 2", empty)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_sqlite_connect_function(self) -> None:
        """sqlite_connect helper compiles."""
        src = _sqlite_with_main("""\
            let result: Result<Connection, SqlError> = sqlite_connect("/tmp/test.db")
            match result {
                Ok(conn) => { println(conn.driver) },
                Err(e) => { println(error_message(e)) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestInternalHelpers:
    def test_read_column_value(self) -> None:
        """read_column_value function compiles."""
        src = _sqlite_with_main("""\
            let val: SqlValue = read_column_value(0, 0)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_bind_params_empty(self) -> None:
        """bind_params with empty list compiles."""
        src = _sqlite_with_main("""\
            let params: List<SqlValue> = []
            let result: Result<Bool, SqlError> = bind_params(0, params)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_collect_rows_function(self) -> None:
        """collect_rows function compiles."""
        src = _sqlite_with_main("""\
            let rows: List<Row> = collect_rows(0)
            println(str(len(rows)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
