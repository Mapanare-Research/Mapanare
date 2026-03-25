"""Tests for the extended filesystem operations in mapanare_db.c.

Compiles the database runtime as a shared library and tests the extended
filesystem API via ctypes: file_exists, file_remove, dir_create, dir_remove,
file_rename, file_copy, tmpfile_path, realpath, file_size, file_mtime.

All operations use temporary directories for isolation.
All tests are skipped if no C compiler is available.
"""

from __future__ import annotations

import ctypes
import os
import platform
import shutil
import subprocess
import time

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

_lib: ctypes.CDLL | None = None


def _compile_db_lib(tmp_path: str) -> ctypes.CDLL:
    """Compile mapanare_db.c + mapanare_core.c into a shared library."""
    global _lib  # noqa: PLW0603

    if _lib is not None:
        return _lib

    assert _CC is not None
    ext = ".dll" if _IS_WINDOWS else ".so"
    lib_path = os.path.join(tmp_path, f"libmapanare_db{ext}")

    flags = ["-shared", "-fPIC", "-O2", "-pthread"]
    libs = [] if _IS_WINDOWS else ["-ldl"]

    cmd = [_CC] + flags + [_CORE_C, _DB_C, "-o", lib_path] + libs
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        pytest.skip(f"DB library compilation failed: {result.stderr[:500]}")

    _lib = ctypes.CDLL(lib_path)
    _setup_bindings(_lib)
    return _lib


def _setup_bindings(lib: ctypes.CDLL) -> None:
    """Configure ctypes argument/return types for filesystem functions."""
    # String helpers
    lib.__mn_str_from_cstr.restype = MnString
    lib.__mn_str_from_cstr.argtypes = [ctypes.c_char_p]

    lib.__mn_str_empty.restype = MnString
    lib.__mn_str_empty.argtypes = []

    lib.__mn_str_free.restype = None
    lib.__mn_str_free.argtypes = [MnString]

    # File write/read from mapanare_core
    lib.__mn_file_write.restype = ctypes.c_int64
    lib.__mn_file_write.argtypes = [MnString, MnString]

    lib.__mn_file_read.restype = MnString
    lib.__mn_file_read.argtypes = [MnString, ctypes.POINTER(ctypes.c_int64)]

    # Extended filesystem operations from mapanare_db
    lib.__mn_file_exists.restype = ctypes.c_int64
    lib.__mn_file_exists.argtypes = [MnString]

    lib.__mn_file_remove.restype = ctypes.c_int64
    lib.__mn_file_remove.argtypes = [MnString]

    lib.__mn_dir_create.restype = ctypes.c_int64
    lib.__mn_dir_create.argtypes = [MnString, ctypes.c_int64]

    lib.__mn_dir_remove.restype = ctypes.c_int64
    lib.__mn_dir_remove.argtypes = [MnString]

    lib.__mn_file_rename.restype = ctypes.c_int64
    lib.__mn_file_rename.argtypes = [MnString, MnString]

    lib.__mn_file_copy.restype = ctypes.c_int64
    lib.__mn_file_copy.argtypes = [MnString, MnString]

    lib.__mn_tmpfile_path.restype = MnString
    lib.__mn_tmpfile_path.argtypes = []

    lib.__mn_realpath.restype = MnString
    lib.__mn_realpath.argtypes = [MnString]

    lib.__mn_file_size.restype = ctypes.c_int64
    lib.__mn_file_size.argtypes = [MnString]

    lib.__mn_file_mtime.restype = ctypes.c_int64
    lib.__mn_file_mtime.argtypes = [MnString]


def _mn_str(lib: ctypes.CDLL, text: str) -> MnString:
    """Create an MnString from a Python string."""
    return lib.__mn_str_from_cstr(text.encode("utf-8"))


def _read_mnstring(s: MnString) -> str:
    """Read an MnString back to a Python string."""
    if s.len <= 0 or not s.data:
        return ""
    return ctypes.string_at(s.data, s.len).decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------


@pytest.mark.skipif(_CC is None, reason="No C compiler available")
class TestFileExists:
    """Tests for __mn_file_exists."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: object) -> None:
        self.lib = _compile_db_lib(str(tmp_path))
        self.tmp = str(tmp_path)

    def test_existing_file(self) -> None:
        """__mn_file_exists returns 1 for a file that exists."""
        fpath = os.path.join(self.tmp, "exists.txt")
        with open(fpath, "w") as f:
            f.write("hello")

        path_s = _mn_str(self.lib, fpath)
        assert self.lib.__mn_file_exists(path_s) == 1

    def test_nonexistent_file(self) -> None:
        """__mn_file_exists returns 0 for a file that does not exist."""
        fpath = os.path.join(self.tmp, "does_not_exist_12345.txt")
        path_s = _mn_str(self.lib, fpath)
        assert self.lib.__mn_file_exists(path_s) == 0

    def test_existing_directory(self) -> None:
        """__mn_file_exists returns 1 for a directory that exists."""
        path_s = _mn_str(self.lib, self.tmp)
        assert self.lib.__mn_file_exists(path_s) == 1


@pytest.mark.skipif(_CC is None, reason="No C compiler available")
class TestFileRemove:
    """Tests for __mn_file_remove."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: object) -> None:
        self.lib = _compile_db_lib(str(tmp_path))
        self.tmp = str(tmp_path)

    def test_remove_existing_file(self) -> None:
        """Create a file then remove it with __mn_file_remove."""
        fpath = os.path.join(self.tmp, "to_remove.txt")
        with open(fpath, "w") as f:
            f.write("temporary")

        assert os.path.exists(fpath)

        path_s = _mn_str(self.lib, fpath)
        rc = self.lib.__mn_file_remove(path_s)
        assert rc == 0
        assert not os.path.exists(fpath)

    def test_remove_nonexistent_file(self) -> None:
        """__mn_file_remove on a nonexistent file returns -1."""
        fpath = os.path.join(self.tmp, "ghost_file.txt")
        path_s = _mn_str(self.lib, fpath)
        rc = self.lib.__mn_file_remove(path_s)
        assert rc == -1


@pytest.mark.skipif(_CC is None, reason="No C compiler available")
class TestDirCreateRemove:
    """Tests for __mn_dir_create and __mn_dir_remove."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: object) -> None:
        self.lib = _compile_db_lib(str(tmp_path))
        self.tmp = str(tmp_path)

    def test_create_single_directory(self) -> None:
        """__mn_dir_create creates a single directory."""
        dpath = os.path.join(self.tmp, "newdir")
        path_s = _mn_str(self.lib, dpath)

        rc = self.lib.__mn_dir_create(path_s, 0)
        assert rc == 0
        assert os.path.isdir(dpath)

    def test_create_recursive_directory(self) -> None:
        """__mn_dir_create with recursive=1 creates nested directories."""
        dpath = os.path.join(self.tmp, "a", "b", "c")
        path_s = _mn_str(self.lib, dpath)

        rc = self.lib.__mn_dir_create(path_s, 1)
        assert rc == 0
        assert os.path.isdir(dpath)

    def test_remove_empty_directory(self) -> None:
        """__mn_dir_remove removes an empty directory."""
        dpath = os.path.join(self.tmp, "empty_dir")
        os.makedirs(dpath)
        assert os.path.isdir(dpath)

        path_s = _mn_str(self.lib, dpath)
        rc = self.lib.__mn_dir_remove(path_s)
        assert rc == 0
        assert not os.path.exists(dpath)

    def test_remove_nonexistent_directory(self) -> None:
        """__mn_dir_remove on a nonexistent directory returns -1."""
        dpath = os.path.join(self.tmp, "no_such_dir")
        path_s = _mn_str(self.lib, dpath)
        rc = self.lib.__mn_dir_remove(path_s)
        assert rc == -1


@pytest.mark.skipif(_CC is None, reason="No C compiler available")
class TestFileRename:
    """Tests for __mn_file_rename."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: object) -> None:
        self.lib = _compile_db_lib(str(tmp_path))
        self.tmp = str(tmp_path)

    def test_rename_file(self) -> None:
        """__mn_file_rename moves a file from old path to new path."""
        old = os.path.join(self.tmp, "old_name.txt")
        new = os.path.join(self.tmp, "new_name.txt")
        with open(old, "w") as f:
            f.write("rename me")

        old_s = _mn_str(self.lib, old)
        new_s = _mn_str(self.lib, new)
        rc = self.lib.__mn_file_rename(old_s, new_s)
        assert rc == 0
        assert not os.path.exists(old)
        assert os.path.exists(new)
        with open(new) as f:
            assert f.read() == "rename me"

    def test_rename_nonexistent_fails(self) -> None:
        """__mn_file_rename with a nonexistent source returns -1."""
        old = os.path.join(self.tmp, "no_such_file.txt")
        new = os.path.join(self.tmp, "target.txt")
        old_s = _mn_str(self.lib, old)
        new_s = _mn_str(self.lib, new)
        rc = self.lib.__mn_file_rename(old_s, new_s)
        assert rc == -1


@pytest.mark.skipif(_CC is None, reason="No C compiler available")
class TestFileCopy:
    """Tests for __mn_file_copy."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: object) -> None:
        self.lib = _compile_db_lib(str(tmp_path))
        self.tmp = str(tmp_path)

    def test_copy_file(self) -> None:
        """__mn_file_copy duplicates a file to a new location."""
        src = os.path.join(self.tmp, "source.txt")
        dst = os.path.join(self.tmp, "copy.txt")
        with open(src, "w") as f:
            f.write("copy me")

        src_s = _mn_str(self.lib, src)
        dst_s = _mn_str(self.lib, dst)
        rc = self.lib.__mn_file_copy(src_s, dst_s)
        assert rc == 0

        # Both files should exist with same content
        assert os.path.exists(src)
        assert os.path.exists(dst)
        with open(dst) as f:
            assert f.read() == "copy me"

    def test_copy_nonexistent_source_fails(self) -> None:
        """__mn_file_copy with a nonexistent source returns -1."""
        src = os.path.join(self.tmp, "phantom.txt")
        dst = os.path.join(self.tmp, "dest.txt")
        src_s = _mn_str(self.lib, src)
        dst_s = _mn_str(self.lib, dst)
        rc = self.lib.__mn_file_copy(src_s, dst_s)
        assert rc == -1


@pytest.mark.skipif(_CC is None, reason="No C compiler available")
class TestTmpfilePath:
    """Tests for __mn_tmpfile_path."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: object) -> None:
        self.lib = _compile_db_lib(str(tmp_path))

    def test_returns_valid_path(self) -> None:
        """__mn_tmpfile_path returns a non-empty path string."""
        result = self.lib.__mn_tmpfile_path()
        assert result.len > 0, "tmpfile_path should return a non-empty string"
        path_str = _read_mnstring(result)
        assert len(path_str) > 0

        # The file should exist (mkstemp creates it)
        assert os.path.exists(path_str), f"Temp file should exist: {path_str}"

        # Cleanup
        if os.path.exists(path_str):
            os.unlink(path_str)

    def test_unique_paths(self) -> None:
        """__mn_tmpfile_path returns unique paths on consecutive calls."""
        paths = []
        for _ in range(5):
            result = self.lib.__mn_tmpfile_path()
            path_str = _read_mnstring(result)
            paths.append(path_str)

        # All paths should be unique
        assert len(set(paths)) == len(paths), "Temp file paths should be unique"

        # Cleanup
        for p in paths:
            if os.path.exists(p):
                os.unlink(p)


@pytest.mark.skipif(_CC is None, reason="No C compiler available")
class TestRealpath:
    """Tests for __mn_realpath."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: object) -> None:
        self.lib = _compile_db_lib(str(tmp_path))
        self.tmp = str(tmp_path)

    def test_resolves_absolute_path(self) -> None:
        """__mn_realpath resolves a path to its canonical form."""
        fpath = os.path.join(self.tmp, "real.txt")
        with open(fpath, "w") as f:
            f.write("test")

        path_s = _mn_str(self.lib, fpath)
        result = self.lib.__mn_realpath(path_s)
        resolved = _read_mnstring(result)
        assert len(resolved) > 0

        # The resolved path should point to the same file
        assert os.path.exists(resolved)

    def test_resolves_relative_path(self) -> None:
        """__mn_realpath resolves '.' to an absolute path."""
        dot_s = _mn_str(self.lib, ".")
        result = self.lib.__mn_realpath(dot_s)
        resolved = _read_mnstring(result)
        assert os.path.isabs(resolved), f"Expected absolute path, got: {resolved}"

    def test_nonexistent_returns_empty(self) -> None:
        """__mn_realpath on a nonexistent path returns an empty string."""
        bad = os.path.join(self.tmp, "no", "such", "deeply", "nested", "path.txt")
        path_s = _mn_str(self.lib, bad)
        result = self.lib.__mn_realpath(path_s)
        assert result.len == 0


@pytest.mark.skipif(_CC is None, reason="No C compiler available")
class TestFileSize:
    """Tests for __mn_file_size."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: object) -> None:
        self.lib = _compile_db_lib(str(tmp_path))
        self.tmp = str(tmp_path)

    def test_correct_byte_count(self) -> None:
        """__mn_file_size returns the correct number of bytes."""
        fpath = os.path.join(self.tmp, "sized.txt")
        content = b"Hello, Mapanare!"  # 16 bytes
        with open(fpath, "wb") as f:
            f.write(content)

        path_s = _mn_str(self.lib, fpath)
        size = self.lib.__mn_file_size(path_s)
        assert size == len(content)

    def test_empty_file(self) -> None:
        """__mn_file_size returns 0 for an empty file."""
        fpath = os.path.join(self.tmp, "empty.txt")
        with open(fpath, "w") as f:
            pass

        path_s = _mn_str(self.lib, fpath)
        size = self.lib.__mn_file_size(path_s)
        assert size == 0

    def test_nonexistent_returns_negative(self) -> None:
        """__mn_file_size returns -1 for a nonexistent file."""
        fpath = os.path.join(self.tmp, "nope.txt")
        path_s = _mn_str(self.lib, fpath)
        size = self.lib.__mn_file_size(path_s)
        assert size == -1


@pytest.mark.skipif(_CC is None, reason="No C compiler available")
class TestFileMtime:
    """Tests for __mn_file_mtime."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: object) -> None:
        self.lib = _compile_db_lib(str(tmp_path))
        self.tmp = str(tmp_path)

    def test_returns_reasonable_timestamp(self) -> None:
        """__mn_file_mtime returns a Unix timestamp in a reasonable range."""
        fpath = os.path.join(self.tmp, "timestamped.txt")
        with open(fpath, "w") as f:
            f.write("mtime test")

        path_s = _mn_str(self.lib, fpath)
        mtime = self.lib.__mn_file_mtime(path_s)

        # Should be after 2020-01-01 (1577836800) and before 2040-01-01 (2208988800)
        assert mtime > 1577836800, f"mtime {mtime} is too old"
        assert mtime < 2208988800, f"mtime {mtime} is too far in the future"

        # Should be close to current time (within 60 seconds)
        now = int(time.time())
        assert abs(mtime - now) < 60, f"mtime {mtime} differs from now {now} by more than 60s"

    def test_nonexistent_returns_negative(self) -> None:
        """__mn_file_mtime returns -1 for a nonexistent file."""
        fpath = os.path.join(self.tmp, "no_file.txt")
        path_s = _mn_str(self.lib, fpath)
        mtime = self.lib.__mn_file_mtime(path_s)
        assert mtime == -1
