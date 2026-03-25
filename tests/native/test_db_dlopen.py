"""Tests for dlopen graceful fallback in mapanare_db.c.

Verifies that the shared library can be loaded, that expected function
symbols exist, and that SQLite3 functions return valid handles when
libsqlite3 is available on the system.

All tests are skipped if no C compiler is available.
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


# ---------------------------------------------------------------------------
# MnString ctypes struct
# ---------------------------------------------------------------------------


class MnString(ctypes.Structure):
    _fields_ = [
        ("data", ctypes.c_char_p),
        ("len", ctypes.c_int64),
    ]


# ---------------------------------------------------------------------------
# Module-level cached library
# ---------------------------------------------------------------------------

_compiled_lib_path: str | None = None
_compiled_lib: ctypes.CDLL | None = None


def _compile_and_load(tmp_path: str) -> ctypes.CDLL:
    """Compile the DB shared library if not already done."""
    global _compiled_lib_path, _compiled_lib  # noqa: PLW0603

    if _compiled_lib is not None:
        return _compiled_lib

    assert _CC is not None
    ext = ".dll" if _IS_WINDOWS else ".so"
    lib_path = os.path.join(tmp_path, f"libmapanare_db{ext}")

    flags = ["-shared", "-fPIC", "-O2", "-pthread"]
    libs = [] if _IS_WINDOWS else ["-ldl"]

    cmd = [_CC] + flags + [_CORE_C, _DB_C, "-o", lib_path] + libs
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        pytest.skip(f"DB library compilation failed: {result.stderr[:500]}")

    _compiled_lib_path = lib_path
    _compiled_lib = ctypes.CDLL(lib_path)
    return _compiled_lib


# ---------------------------------------------------------------------------
# Test class: shared library import and symbol verification
# ---------------------------------------------------------------------------


@pytest.mark.skipif(_CC is None, reason="No C compiler available")
class TestDlopenImport:
    """Verify the shared library can be loaded and inspected."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: object) -> None:
        self.lib = _compile_and_load(str(tmp_path))

    def test_library_loads_successfully(self) -> None:
        """The compiled shared library can be loaded via ctypes."""
        assert self.lib is not None

    def test_sqlite3_function_signatures_exist(self) -> None:
        """All __mn_sqlite3_* symbols are present in the shared library."""
        expected_symbols = [
            "__mn_sqlite3_open",
            "__mn_sqlite3_close",
            "__mn_sqlite3_exec",
            "__mn_sqlite3_prepare",
            "__mn_sqlite3_bind_int",
            "__mn_sqlite3_bind_float",
            "__mn_sqlite3_bind_str",
            "__mn_sqlite3_bind_null",
            "__mn_sqlite3_step",
            "__mn_sqlite3_column_int",
            "__mn_sqlite3_column_float",
            "__mn_sqlite3_column_str",
            "__mn_sqlite3_column_type",
            "__mn_sqlite3_column_count",
            "__mn_sqlite3_column_name",
            "__mn_sqlite3_finalize",
            "__mn_sqlite3_errmsg",
        ]

        for sym in expected_symbols:
            fn = getattr(self.lib, sym, None)
            assert fn is not None, f"Symbol {sym} not found in shared library"

    def test_pg_function_signatures_exist(self) -> None:
        """All __mn_pg_* symbols are present in the shared library."""
        expected_symbols = [
            "__mn_pg_connect",
            "__mn_pg_close",
            "__mn_pg_exec",
            "__mn_pg_exec_params",
            "__mn_pg_ntuples",
            "__mn_pg_nfields",
            "__mn_pg_getvalue",
            "__mn_pg_fname",
            "__mn_pg_status",
            "__mn_pg_errmsg",
            "__mn_pg_clear",
        ]

        for sym in expected_symbols:
            fn = getattr(self.lib, sym, None)
            assert fn is not None, f"Symbol {sym} not found in shared library"

    def test_redis_function_signatures_exist(self) -> None:
        """All __mn_redis_* symbols are present in the shared library."""
        expected_symbols = [
            "__mn_redis_connect",
            "__mn_redis_command",
            "__mn_redis_command_status",
            "__mn_redis_close",
            "__mn_redis_errmsg",
        ]

        for sym in expected_symbols:
            fn = getattr(self.lib, sym, None)
            assert fn is not None, f"Symbol {sym} not found in shared library"

    def test_filesystem_function_signatures_exist(self) -> None:
        """All extended filesystem __mn_file_* / __mn_dir_* symbols are present."""
        expected_symbols = [
            "__mn_file_exists",
            "__mn_file_remove",
            "__mn_dir_create",
            "__mn_dir_remove",
            "__mn_file_rename",
            "__mn_file_copy",
            "__mn_tmpfile_path",
            "__mn_realpath",
            "__mn_file_size",
            "__mn_file_mtime",
        ]

        for sym in expected_symbols:
            fn = getattr(self.lib, sym, None)
            assert fn is not None, f"Symbol {sym} not found in shared library"


@pytest.mark.skipif(_CC is None, reason="No C compiler available")
class TestDlopenSQLiteAvailability:
    """Test SQLite3 functions when libsqlite3 is available."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: object) -> None:
        self.lib = _compile_and_load(str(tmp_path))
        # Set up minimal bindings
        self.lib.__mn_str_from_cstr.restype = MnString
        self.lib.__mn_str_from_cstr.argtypes = [ctypes.c_char_p]

        self.lib.__mn_sqlite3_open.restype = ctypes.c_int64
        self.lib.__mn_sqlite3_open.argtypes = [MnString]

        self.lib.__mn_sqlite3_close.restype = None
        self.lib.__mn_sqlite3_close.argtypes = [ctypes.c_int64]

    def test_sqlite3_open_returns_valid_handle_when_available(self) -> None:
        """If libsqlite3 is installed, __mn_sqlite3_open returns a valid handle.

        If libsqlite3 is not installed, __mn_sqlite3_open returns 0 (graceful fallback).
        """
        path = self.lib.__mn_str_from_cstr(b":memory:")
        handle = self.lib.__mn_sqlite3_open(path)

        if handle > 0:
            # libsqlite3 is available — handle should be valid
            self.lib.__mn_sqlite3_close(handle)
        else:
            # libsqlite3 is not available — 0 is the expected graceful fallback
            assert handle == 0

    def test_sqlite3_close_on_invalid_handle_does_not_crash(self) -> None:
        """Calling close with handle 0 or invalid handle does not crash."""
        # Should be a no-op
        self.lib.__mn_sqlite3_close(0)
        self.lib.__mn_sqlite3_close(-1)
        self.lib.__mn_sqlite3_close(999)


@pytest.mark.skipif(_CC is None, reason="No C compiler available")
class TestDlopenGracefulFallback:
    """Test that functions return graceful errors when libraries are unavailable."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: object) -> None:
        self.lib = _compile_and_load(str(tmp_path))

        self.lib.__mn_str_from_cstr.restype = MnString
        self.lib.__mn_str_from_cstr.argtypes = [ctypes.c_char_p]

        self.lib.__mn_pg_connect.restype = ctypes.c_int64
        self.lib.__mn_pg_connect.argtypes = [MnString]

        self.lib.__mn_redis_connect.restype = ctypes.c_int64
        self.lib.__mn_redis_connect.argtypes = [MnString, ctypes.c_int64]

        self.lib.__mn_pg_errmsg.restype = MnString
        self.lib.__mn_pg_errmsg.argtypes = [ctypes.c_int64]

        self.lib.__mn_redis_errmsg.restype = MnString
        self.lib.__mn_redis_errmsg.argtypes = [ctypes.c_int64]

    def test_pg_connect_returns_zero_without_libpq(self) -> None:
        """If libpq is not available, __mn_pg_connect returns 0 without crashing."""
        conninfo = self.lib.__mn_str_from_cstr(b"host=localhost dbname=test")
        handle = self.lib.__mn_pg_connect(conninfo)
        # Returns 0 if libpq not installed, or a valid handle if it is
        assert handle >= 0

    def test_pg_errmsg_on_invalid_handle(self) -> None:
        """__mn_pg_errmsg on invalid handle returns a fallback message."""
        msg = self.lib.__mn_pg_errmsg(0)
        assert msg.len > 0, "Should return a non-empty fallback error message"

    def test_redis_connect_returns_zero_without_hiredis(self) -> None:
        """If hiredis is not available, __mn_redis_connect returns 0 without crashing."""
        host = self.lib.__mn_str_from_cstr(b"localhost")
        handle = self.lib.__mn_redis_connect(host, 6379)
        # Returns 0 if hiredis not installed or no Redis server running
        assert handle >= 0

    def test_redis_errmsg_on_invalid_handle(self) -> None:
        """__mn_redis_errmsg on invalid handle returns a fallback message."""
        msg = self.lib.__mn_redis_errmsg(0)
        assert msg.len > 0, "Should return a non-empty fallback error message"
