"""Tests for extended file I/O in the C I/O runtime (Phase 6, Tasks 15-20)."""

import pytest

from runtime.io_bridge import IO_AVAILABLE

pytestmark = pytest.mark.skipif(
    not IO_AVAILABLE,
    reason="I/O runtime not built — run: python runtime/native/build_io.py",
)

if IO_AVAILABLE:
    from runtime import io_bridge
    from runtime.io_bridge import MN_FILE_APPEND, MN_FILE_CREATE, MN_FILE_READ, MN_FILE_WRITE


class TestFileOpen:
    """Task 15: __mn_file_open with modes read, write, append, create."""

    def test_open_write_and_read(self, tmp_path):
        path = str(tmp_path / "test.txt")

        # Write mode: create and write
        fd = io_bridge.file_open(path, MN_FILE_WRITE)
        assert fd >= 0
        written = io_bridge.file_write_fd(fd, b"hello world")
        assert written == 11
        io_bridge.file_close(fd)

        # Read mode
        fd = io_bridge.file_open(path, MN_FILE_READ)
        assert fd >= 0
        data = io_bridge.file_read_fd(fd, 1024)
        assert data == b"hello world"
        io_bridge.file_close(fd)

    def test_open_append(self, tmp_path):
        path = str(tmp_path / "append.txt")

        # Create file
        fd = io_bridge.file_open(path, MN_FILE_WRITE)
        io_bridge.file_write_fd(fd, b"first")
        io_bridge.file_close(fd)

        # Append
        fd = io_bridge.file_open(path, MN_FILE_APPEND)
        assert fd >= 0
        io_bridge.file_write_fd(fd, b"second")
        io_bridge.file_close(fd)

        # Read back
        fd = io_bridge.file_open(path, MN_FILE_READ)
        data = io_bridge.file_read_fd(fd, 1024)
        assert data == b"firstsecond"
        io_bridge.file_close(fd)

    def test_open_create_exclusive(self, tmp_path):
        path = str(tmp_path / "exclusive.txt")

        # Create new file (should succeed)
        fd = io_bridge.file_open(path, MN_FILE_CREATE)
        assert fd >= 0
        io_bridge.file_write_fd(fd, b"data")
        io_bridge.file_close(fd)

        # Create again (should fail — file exists)
        fd2 = io_bridge.file_open(path, MN_FILE_CREATE)
        assert fd2 == -1

    def test_open_nonexistent_read(self, tmp_path):
        path = str(tmp_path / "does_not_exist.txt")
        fd = io_bridge.file_open(path, MN_FILE_READ)
        assert fd == -1


class TestFileReadWrite:
    """Tasks 16-18: read, write, close via fd."""

    def test_roundtrip_binary(self, tmp_path):
        path = str(tmp_path / "binary.bin")
        payload = bytes(range(256))

        fd = io_bridge.file_open(path, MN_FILE_WRITE)
        assert fd >= 0
        io_bridge.file_write_fd(fd, payload)
        io_bridge.file_close(fd)

        fd = io_bridge.file_open(path, MN_FILE_READ)
        assert fd >= 0
        data = io_bridge.file_read_fd(fd, 1024)
        assert data == payload
        io_bridge.file_close(fd)

    def test_read_eof(self, tmp_path):
        path = str(tmp_path / "small.txt")

        fd = io_bridge.file_open(path, MN_FILE_WRITE)
        io_bridge.file_write_fd(fd, b"hi")
        io_bridge.file_close(fd)

        fd = io_bridge.file_open(path, MN_FILE_READ)
        data1 = io_bridge.file_read_fd(fd, 1024)
        assert data1 == b"hi"
        # Second read should return empty (EOF)
        data2 = io_bridge.file_read_fd(fd, 1024)
        assert data2 == b""
        io_bridge.file_close(fd)


class TestFileStat:
    """Task 19: __mn_file_stat."""

    def test_stat_file(self, tmp_path):
        path = str(tmp_path / "stattest.txt")
        with open(path, "wb") as f:
            f.write(b"0123456789")

        st = io_bridge.file_stat(path)
        assert st is not None
        assert st.size == 10
        assert st.is_dir == 0
        assert st.mtime > 0

    def test_stat_directory(self, tmp_path):
        st = io_bridge.file_stat(str(tmp_path))
        assert st is not None
        assert st.is_dir == 1

    def test_stat_nonexistent(self, tmp_path):
        st = io_bridge.file_stat(str(tmp_path / "nope"))
        assert st is None


class TestDirList:
    """Task 20: __mn_dir_list."""

    def test_list_directory(self, tmp_path):
        # Create some files and a subdirectory
        (tmp_path / "file_a.txt").write_text("a")
        (tmp_path / "file_b.txt").write_text("b")
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        entries = io_bridge.dir_list(str(tmp_path))
        names = {e["name"] for e in entries}

        assert "file_a.txt" in names
        assert "file_b.txt" in names
        assert "subdir" in names

        # Check is_dir flag
        subdir_entry = next(e for e in entries if e["name"] == "subdir")
        assert subdir_entry["is_dir"] is True

        file_entry = next(e for e in entries if e["name"] == "file_a.txt")
        assert file_entry["is_dir"] is False

    def test_list_empty_directory(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        entries = io_bridge.dir_list(str(empty))
        assert entries == []

    def test_list_nonexistent(self, tmp_path):
        entries = io_bridge.dir_list(str(tmp_path / "nope"))
        assert entries == []
