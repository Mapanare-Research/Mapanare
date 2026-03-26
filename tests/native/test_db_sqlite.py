"""Tests for the C-level SQLite3 bindings in mapanare_db.c.

Compiles the database runtime as a shared library and tests the SQLite3
handle-based API via ctypes: open/close, exec, prepare/bind/step/column,
error messages, and SQL injection safety with parameterized queries.

All tests are skipped if:
  - No C compiler is available
  - libsqlite3 is not installed on the system
"""

from __future__ import annotations

import ctypes
import os
import platform
import shutil
import subprocess

import pytest

# ---------------------------------------------------------------------------
# Compiler and path detection
# ---------------------------------------------------------------------------

_CC = os.environ.get("CC") or shutil.which("gcc") or shutil.which("clang") or shutil.which("cc")
_IS_WINDOWS = platform.system() == "Windows"

_TEST_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_TEST_DIR, "..", ".."))
_RUNTIME_DIR = os.path.join(_REPO_ROOT, "runtime", "native")
_CORE_C = os.path.join(_RUNTIME_DIR, "mapanare_core.c")
_DB_C = os.path.join(_RUNTIME_DIR, "mapanare_db.c")

# SQLite3 step return codes
SQLITE_ROW = 100
SQLITE_DONE = 101
SQLITE_OK = 0

# SQLite3 column type codes
SQLITE_INTEGER = 1
SQLITE_FLOAT = 2
SQLITE_TEXT = 3


# ---------------------------------------------------------------------------
# MnString ctypes struct — must match mapanare_core.h layout
# ---------------------------------------------------------------------------


class MnString(ctypes.Structure):
    _fields_ = [
        ("data", ctypes.c_void_p),
        ("len", ctypes.c_int64),
    ]


def _read_mnstring(s: MnString) -> str:
    """Read an MnString back to a Python string, untagging the pointer if needed."""
    if s.len <= 0 or not s.data:
        return ""
    ptr = s.data & ~1
    return ctypes.string_at(ptr, s.len).decode("utf-8", errors="replace")


def _read_mnbytes(s: MnString) -> bytes:
    """Read an MnString back to Python bytes, untagging the pointer if needed."""
    if s.len <= 0 or not s.data:
        return b""
    ptr = s.data & ~1
    return ctypes.string_at(ptr, s.len)


def _make_mnstring(text: str) -> MnString:
    """Create an MnString from a Python string using the C runtime helper."""
    encoded = text.encode("utf-8")
    return _lib.__mn_str_from_cstr(encoded)


# ---------------------------------------------------------------------------
# Library compilation fixture
# ---------------------------------------------------------------------------

_lib: ctypes.CDLL | None = None
_sqlite_available: bool = False


def _compile_db_lib(tmp_path: str) -> ctypes.CDLL:
    """Compile mapanare_db.c + mapanare_core.c into a shared library."""
    assert _CC is not None
    ext = ".dll" if _IS_WINDOWS else ".so"
    lib_path = os.path.join(tmp_path, f"libmapanare_db{ext}")

    flags = ["-shared", "-fPIC", "-O2", "-pthread"]
    libs = [] if _IS_WINDOWS else ["-ldl"]

    cmd = [_CC] + flags + [_CORE_C, _DB_C, "-o", lib_path] + libs
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        pytest.skip(f"DB library compilation failed: {result.stderr[:500]}")

    return ctypes.CDLL(lib_path)


def _setup_bindings(lib: ctypes.CDLL) -> None:
    """Configure ctypes argument/return types for all __mn_sqlite3_* and helper functions."""
    # String helpers
    lib.__mn_str_from_cstr.restype = MnString
    lib.__mn_str_from_cstr.argtypes = [ctypes.c_char_p]

    lib.__mn_str_empty.restype = MnString
    lib.__mn_str_empty.argtypes = []

    lib.__mn_str_free.restype = None
    lib.__mn_str_free.argtypes = [MnString]

    # SQLite3 API
    lib.__mn_sqlite3_open.restype = ctypes.c_int64
    lib.__mn_sqlite3_open.argtypes = [MnString]

    lib.__mn_sqlite3_close.restype = None
    lib.__mn_sqlite3_close.argtypes = [ctypes.c_int64]

    lib.__mn_sqlite3_exec.restype = ctypes.c_int64
    lib.__mn_sqlite3_exec.argtypes = [ctypes.c_int64, MnString]

    lib.__mn_sqlite3_prepare.restype = ctypes.c_int64
    lib.__mn_sqlite3_prepare.argtypes = [ctypes.c_int64, MnString]

    lib.__mn_sqlite3_bind_int.restype = ctypes.c_int64
    lib.__mn_sqlite3_bind_int.argtypes = [ctypes.c_int64, ctypes.c_int64, ctypes.c_int64]

    lib.__mn_sqlite3_bind_float.restype = ctypes.c_int64
    lib.__mn_sqlite3_bind_float.argtypes = [ctypes.c_int64, ctypes.c_int64, ctypes.c_double]

    lib.__mn_sqlite3_bind_str.restype = ctypes.c_int64
    lib.__mn_sqlite3_bind_str.argtypes = [ctypes.c_int64, ctypes.c_int64, MnString]

    lib.__mn_sqlite3_bind_null.restype = ctypes.c_int64
    lib.__mn_sqlite3_bind_null.argtypes = [ctypes.c_int64, ctypes.c_int64]

    lib.__mn_sqlite3_step.restype = ctypes.c_int64
    lib.__mn_sqlite3_step.argtypes = [ctypes.c_int64]

    lib.__mn_sqlite3_column_int.restype = ctypes.c_int64
    lib.__mn_sqlite3_column_int.argtypes = [ctypes.c_int64, ctypes.c_int64]

    lib.__mn_sqlite3_column_float.restype = ctypes.c_double
    lib.__mn_sqlite3_column_float.argtypes = [ctypes.c_int64, ctypes.c_int64]

    lib.__mn_sqlite3_column_str.restype = MnString
    lib.__mn_sqlite3_column_str.argtypes = [ctypes.c_int64, ctypes.c_int64]

    lib.__mn_sqlite3_column_type.restype = ctypes.c_int64
    lib.__mn_sqlite3_column_type.argtypes = [ctypes.c_int64, ctypes.c_int64]

    lib.__mn_sqlite3_column_count.restype = ctypes.c_int64
    lib.__mn_sqlite3_column_count.argtypes = [ctypes.c_int64]

    lib.__mn_sqlite3_column_name.restype = MnString
    lib.__mn_sqlite3_column_name.argtypes = [ctypes.c_int64, ctypes.c_int64]

    lib.__mn_sqlite3_finalize.restype = ctypes.c_int64
    lib.__mn_sqlite3_finalize.argtypes = [ctypes.c_int64]

    lib.__mn_sqlite3_errmsg.restype = MnString
    lib.__mn_sqlite3_errmsg.argtypes = [ctypes.c_int64]


def _check_sqlite_available(lib: ctypes.CDLL) -> bool:
    """Try to open an in-memory database to check if libsqlite3 is on the system."""
    path = lib.__mn_str_from_cstr(b":memory:")
    handle = lib.__mn_sqlite3_open(path)
    if handle > 0:
        lib.__mn_sqlite3_close(handle)
        return True
    return False


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------


@pytest.mark.skipif(_CC is None, reason="No C compiler available")
class TestSQLite3Bindings:
    """C-level SQLite3 binding tests via ctypes."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: object) -> None:
        """Compile the DB runtime and set up ctypes bindings."""
        global _lib, _sqlite_available  # noqa: PLW0603

        if _lib is None:
            _lib = _compile_db_lib(str(tmp_path))
            _setup_bindings(_lib)
            _sqlite_available = _check_sqlite_available(_lib)

        if not _sqlite_available:
            pytest.skip("libsqlite3 not available on this system")

        self.lib = _lib

    def _open_memory_db(self) -> int:
        """Open an in-memory SQLite3 database. Returns the handle."""
        path = getattr(self.lib, "__mn_str_from_cstr")(b":memory:")
        handle = getattr(self.lib, "__mn_sqlite3_open")(path)
        assert handle > 0, "Failed to open :memory: database"
        return handle

    def test_open_memory_returns_nonzero_handle(self) -> None:
        """__mn_sqlite3_open with :memory: returns a nonzero handle."""
        handle = self._open_memory_db()
        assert handle > 0
        getattr(self.lib, "__mn_sqlite3_close")(handle)

    def test_close(self) -> None:
        """__mn_sqlite3_close releases the handle without errors."""
        handle = self._open_memory_db()
        # Close should not crash or raise
        getattr(self.lib, "__mn_sqlite3_close")(handle)

    def test_exec_create_table(self) -> None:
        """__mn_sqlite3_exec CREATE TABLE returns 0 (SQLITE_OK)."""
        handle = self._open_memory_db()
        sql = getattr(self.lib, "__mn_str_from_cstr")(
            b"CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)"
        )
        rc = getattr(self.lib, "__mn_sqlite3_exec")(handle, sql)
        assert rc == SQLITE_OK, f"exec returned {rc}"
        getattr(self.lib, "__mn_sqlite3_close")(handle)

    def test_prepare_bind_int_step_column_int_roundtrip(self) -> None:
        """Prepare + bind_int + step + column_int roundtrip."""
        handle = self._open_memory_db()

        # Create table and insert data
        create_sql = getattr(self.lib, "__mn_str_from_cstr")(
            b"CREATE TABLE nums (id INTEGER PRIMARY KEY, val INTEGER)"
        )
        assert getattr(self.lib, "__mn_sqlite3_exec")(handle, create_sql) == SQLITE_OK

        insert_sql = getattr(self.lib, "__mn_str_from_cstr")(b"INSERT INTO nums (val) VALUES (?1)")
        stmt = getattr(self.lib, "__mn_sqlite3_prepare")(handle, insert_sql)
        assert stmt > 0, "Failed to prepare INSERT statement"

        # Bind integer value 42 at index 1
        rc = getattr(self.lib, "__mn_sqlite3_bind_int")(stmt, 1, 42)
        assert rc == SQLITE_OK

        # Step to execute INSERT
        rc = getattr(self.lib, "__mn_sqlite3_step")(stmt)
        assert rc == SQLITE_DONE, f"INSERT step returned {rc}, expected {SQLITE_DONE}"

        getattr(self.lib, "__mn_sqlite3_finalize")(stmt)

        # Query back the value
        select_sql = getattr(self.lib, "__mn_str_from_cstr")(b"SELECT val FROM nums WHERE val = 42")
        stmt = getattr(self.lib, "__mn_sqlite3_prepare")(handle, select_sql)
        assert stmt > 0

        rc = getattr(self.lib, "__mn_sqlite3_step")(stmt)
        assert rc == SQLITE_ROW, f"SELECT step returned {rc}, expected {SQLITE_ROW}"

        val = getattr(self.lib, "__mn_sqlite3_column_int")(stmt, 0)
        assert val == 42

        getattr(self.lib, "__mn_sqlite3_finalize")(stmt)
        getattr(self.lib, "__mn_sqlite3_close")(handle)

    def test_bind_str_parameterized_query(self) -> None:
        """__mn_sqlite3_bind_str parameterized query stores and retrieves text."""
        handle = self._open_memory_db()

        create_sql = getattr(self.lib, "__mn_str_from_cstr")(
            b"CREATE TABLE names (id INTEGER PRIMARY KEY, name TEXT)"
        )
        assert getattr(self.lib, "__mn_sqlite3_exec")(handle, create_sql) == SQLITE_OK

        # Insert with parameterized string
        insert_sql = getattr(self.lib, "__mn_str_from_cstr")(
            b"INSERT INTO names (name) VALUES (?1)"
        )
        stmt = getattr(self.lib, "__mn_sqlite3_prepare")(handle, insert_sql)
        assert stmt > 0

        name_val = getattr(self.lib, "__mn_str_from_cstr")(b"Mapanare")
        rc = getattr(self.lib, "__mn_sqlite3_bind_str")(stmt, 1, name_val)
        assert rc == SQLITE_OK

        rc = getattr(self.lib, "__mn_sqlite3_step")(stmt)
        assert rc == SQLITE_DONE

        getattr(self.lib, "__mn_sqlite3_finalize")(stmt)

        # Query back
        select_sql = getattr(self.lib, "__mn_str_from_cstr")(b"SELECT name FROM names LIMIT 1")
        stmt = getattr(self.lib, "__mn_sqlite3_prepare")(handle, select_sql)
        assert stmt > 0

        rc = getattr(self.lib, "__mn_sqlite3_step")(stmt)
        assert rc == SQLITE_ROW

        result = getattr(self.lib, "__mn_sqlite3_column_str")(stmt, 0)
        result_bytes = _read_mnbytes(result)
        assert result_bytes == b"Mapanare"

        getattr(self.lib, "__mn_sqlite3_finalize")(stmt)
        getattr(self.lib, "__mn_sqlite3_close")(handle)

    def test_column_count_and_column_name(self) -> None:
        """__mn_sqlite3_column_count and __mn_sqlite3_column_name return correct metadata."""
        handle = self._open_memory_db()

        create_sql = getattr(self.lib, "__mn_str_from_cstr")(
            b"CREATE TABLE meta (alpha TEXT, beta INTEGER, gamma REAL)"
        )
        assert getattr(self.lib, "__mn_sqlite3_exec")(handle, create_sql) == SQLITE_OK

        # Insert a row so SELECT has results
        insert_sql = getattr(self.lib, "__mn_str_from_cstr")(
            b"INSERT INTO meta VALUES ('a', 1, 2.5)"
        )
        assert getattr(self.lib, "__mn_sqlite3_exec")(handle, insert_sql) == SQLITE_OK

        select_sql = getattr(self.lib, "__mn_str_from_cstr")(b"SELECT alpha, beta, gamma FROM meta")
        stmt = getattr(self.lib, "__mn_sqlite3_prepare")(handle, select_sql)
        assert stmt > 0

        # Column count should be 3
        count = getattr(self.lib, "__mn_sqlite3_column_count")(stmt)
        assert count == 3

        # Step to first row so column names are available
        rc = getattr(self.lib, "__mn_sqlite3_step")(stmt)
        assert rc == SQLITE_ROW

        # Check column names
        col0 = getattr(self.lib, "__mn_sqlite3_column_name")(stmt, 0)
        col0_str = _read_mnstring(col0)
        assert col0_str == "alpha"

        col1 = getattr(self.lib, "__mn_sqlite3_column_name")(stmt, 1)
        col1_str = _read_mnstring(col1)
        assert col1_str == "beta"

        col2 = getattr(self.lib, "__mn_sqlite3_column_name")(stmt, 2)
        col2_str = _read_mnstring(col2)
        assert col2_str == "gamma"

        getattr(self.lib, "__mn_sqlite3_finalize")(stmt)
        getattr(self.lib, "__mn_sqlite3_close")(handle)

    def test_errmsg_on_invalid_sql(self) -> None:
        """__mn_sqlite3_errmsg returns a meaningful error on invalid SQL."""
        handle = self._open_memory_db()

        bad_sql = getattr(self.lib, "__mn_str_from_cstr")(b"NOT VALID SQL AT ALL ;;;")
        rc = getattr(self.lib, "__mn_sqlite3_exec")(handle, bad_sql)
        assert rc != SQLITE_OK, "Invalid SQL should not return SQLITE_OK"

        errmsg = getattr(self.lib, "__mn_sqlite3_errmsg")(handle)
        assert errmsg.len > 0, "Error message should be non-empty"
        msg_str = _read_mnstring(errmsg)
        # SQLite error messages typically contain words like "error" or "syntax"
        msg_lower = msg_str.lower()
        assert (
            "error" in msg_lower or "syntax" in msg_lower or "near" in msg_lower
        ), f"Expected error-related message, got: {msg_str}"

        getattr(self.lib, "__mn_sqlite3_close")(handle)

    def test_sql_injection_with_parameterized_query(self) -> None:
        """SQL injection attempt with parameterized query fails safely.

        The injected payload is treated as a literal string value, not executed as SQL.
        """
        handle = self._open_memory_db()

        create_sql = getattr(self.lib, "__mn_str_from_cstr")(
            b"CREATE TABLE safe (id INTEGER PRIMARY KEY, input TEXT)"
        )
        assert getattr(self.lib, "__mn_sqlite3_exec")(handle, create_sql) == SQLITE_OK

        # Attempt SQL injection via parameterized query
        insert_sql = getattr(self.lib, "__mn_str_from_cstr")(
            b"INSERT INTO safe (input) VALUES (?1)"
        )
        stmt = getattr(self.lib, "__mn_sqlite3_prepare")(handle, insert_sql)
        assert stmt > 0

        # The injection payload: this should be stored as literal text, not executed
        injection = getattr(self.lib, "__mn_str_from_cstr")(b"'; DROP TABLE safe; --")
        rc = getattr(self.lib, "__mn_sqlite3_bind_str")(stmt, 1, injection)
        assert rc == SQLITE_OK

        rc = getattr(self.lib, "__mn_sqlite3_step")(stmt)
        assert rc == SQLITE_DONE
        getattr(self.lib, "__mn_sqlite3_finalize")(stmt)

        # Verify the table still exists and the injection payload is stored as text
        select_sql = getattr(self.lib, "__mn_str_from_cstr")(b"SELECT input FROM safe LIMIT 1")
        stmt = getattr(self.lib, "__mn_sqlite3_prepare")(handle, select_sql)
        assert stmt > 0, "Table 'safe' should still exist (injection did not drop it)"

        rc = getattr(self.lib, "__mn_sqlite3_step")(stmt)
        assert rc == SQLITE_ROW

        result = getattr(self.lib, "__mn_sqlite3_column_str")(stmt, 0)
        result_bytes = _read_mnbytes(result)
        assert result_bytes == b"'; DROP TABLE safe; --"

        getattr(self.lib, "__mn_sqlite3_finalize")(stmt)
        getattr(self.lib, "__mn_sqlite3_close")(handle)

    def test_multiple_inserts_and_select_all(self) -> None:
        """Insert multiple rows and verify all are retrievable."""
        handle = self._open_memory_db()

        create_sql = getattr(self.lib, "__mn_str_from_cstr")(
            b"CREATE TABLE items (id INTEGER PRIMARY KEY, value INTEGER)"
        )
        assert getattr(self.lib, "__mn_sqlite3_exec")(handle, create_sql) == SQLITE_OK

        # Insert 10 rows
        for i in range(10):
            insert_sql = getattr(self.lib, "__mn_str_from_cstr")(
                b"INSERT INTO items (value) VALUES (?1)"
            )
            stmt = getattr(self.lib, "__mn_sqlite3_prepare")(handle, insert_sql)
            assert stmt > 0
            getattr(self.lib, "__mn_sqlite3_bind_int")(stmt, 1, (i + 1) * 100)
            rc = getattr(self.lib, "__mn_sqlite3_step")(stmt)
            assert rc == SQLITE_DONE
            getattr(self.lib, "__mn_sqlite3_finalize")(stmt)

        # Query back all rows
        select_sql = getattr(self.lib, "__mn_str_from_cstr")(b"SELECT value FROM items ORDER BY id")
        stmt = getattr(self.lib, "__mn_sqlite3_prepare")(handle, select_sql)
        assert stmt > 0

        values = []
        while True:
            rc = getattr(self.lib, "__mn_sqlite3_step")(stmt)
            if rc == SQLITE_DONE:
                break
            assert rc == SQLITE_ROW
            values.append(getattr(self.lib, "__mn_sqlite3_column_int")(stmt, 0))

        getattr(self.lib, "__mn_sqlite3_finalize")(stmt)
        getattr(self.lib, "__mn_sqlite3_close")(handle)

        assert values == [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]

    def test_column_type_detection(self) -> None:
        """__mn_sqlite3_column_type returns correct type codes."""
        handle = self._open_memory_db()

        create_sql = getattr(self.lib, "__mn_str_from_cstr")(
            b"CREATE TABLE typed (i INTEGER, f REAL, t TEXT)"
        )
        assert getattr(self.lib, "__mn_sqlite3_exec")(handle, create_sql) == SQLITE_OK

        insert_sql = getattr(self.lib, "__mn_str_from_cstr")(
            b"INSERT INTO typed VALUES (42, 3.14, 'hello')"
        )
        assert getattr(self.lib, "__mn_sqlite3_exec")(handle, insert_sql) == SQLITE_OK

        select_sql = getattr(self.lib, "__mn_str_from_cstr")(b"SELECT i, f, t FROM typed")
        stmt = getattr(self.lib, "__mn_sqlite3_prepare")(handle, select_sql)
        assert stmt > 0

        rc = getattr(self.lib, "__mn_sqlite3_step")(stmt)
        assert rc == SQLITE_ROW

        assert getattr(self.lib, "__mn_sqlite3_column_type")(stmt, 0) == SQLITE_INTEGER
        assert getattr(self.lib, "__mn_sqlite3_column_type")(stmt, 1) == SQLITE_FLOAT
        assert getattr(self.lib, "__mn_sqlite3_column_type")(stmt, 2) == SQLITE_TEXT

        getattr(self.lib, "__mn_sqlite3_finalize")(stmt)
        getattr(self.lib, "__mn_sqlite3_close")(handle)
