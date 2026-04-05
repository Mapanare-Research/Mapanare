"""Tests for stdlib/fs.mn -- Filesystem operations.

Tests verify that the fs stdlib module compiles to valid LLVM IR via
the MIR-based emitter. Since cross-module compilation is not yet ready,
tests inline the fs module source code within test programs.

Covers:
  - FsError enum variants
  - Path type: path(), join(), parent(), filename(), extension(), stem(),
    is_absolute(), to_string(), resolve()
  - File I/O: read_file(), write_file(), append_file() roundtrip
  - File queries: exists(), file_size(), file_mtime(), is_dir(), is_file()
  - File manipulation: remove(), rename(), copy()
  - Directory operations: mkdir(), mkdir_all(), rmdir(), list_dir(), walk()
  - Convenience: read_lines(), tmpfile()
  - Error handling (file not found, empty path)
  - Edge cases (empty path, deeply nested paths)
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

_FS_MN = (Path(__file__).resolve().parent.parent.parent / "stdlib" / "fs.mn").read_text(
    encoding="utf-8"
)


def _compile_mir(source: str) -> str:
    """Compile via MIR-based LLVM emitter."""
    return _compile_to_llvm_ir(source, "test_fs.mn", use_mir=True)


def _fs_source_with_main(main_body: str) -> str:
    """Prepend the fs module source and wrap main_body in fn main()."""
    return _FS_MN + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


# ---------------------------------------------------------------------------
# FsError enum
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestFsError:
    def test_not_found_compiles(self) -> None:
        """FsError::NotFound variant compiles."""
        src = _fs_source_with_main('let e: FsError = NotFound("missing")\nprint("ok")')
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_permission_denied_compiles(self) -> None:
        """FsError::PermissionDenied variant compiles."""
        src = _fs_source_with_main('let e: FsError = PermissionDenied("denied")\nprint("ok")')
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_io_error_compiles(self) -> None:
        """FsError::IoError variant compiles."""
        src = _fs_source_with_main('let e: FsError = IoError("disk fail")\nprint("ok")')
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_invalid_path_compiles(self) -> None:
        """FsError::InvalidPath variant compiles."""
        src = _fs_source_with_main('let e: FsError = InvalidPath("bad path")\nprint("ok")')
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Path type: join
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestPathJoin:
    def test_join_basic_compiles(self) -> None:
        """path() + join() compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("/home/user")
            let joined: Path = join(p, "docs")
            print(to_string(joined))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_join_trailing_slash_compiles(self) -> None:
        """join() with trailing slash on base compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("/home/user/")
            let joined: Path = join(p, "file.txt")
            print(to_string(joined))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_join_empty_base_compiles(self) -> None:
        """join() with empty base path compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("")
            let joined: Path = join(p, "file.txt")
            print(to_string(joined))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_join_chained_compiles(self) -> None:
        """Multiple chained join() calls compile."""
        src = _fs_source_with_main("""\
            let p: Path = path("/root")
            let p2: Path = join(p, "a")
            let p3: Path = join(p2, "b")
            let p4: Path = join(p3, "c.txt")
            print(to_string(p4))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Path type: parent
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestPathParent:
    def test_parent_basic_compiles(self) -> None:
        """parent() of /foo/bar compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("/foo/bar")
            let par: Path = parent(p)
            print(to_string(par))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parent_root_compiles(self) -> None:
        """parent() of "/" returns "/" compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("/")
            let par: Path = parent(p)
            print(to_string(par))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parent_no_slash_compiles(self) -> None:
        """parent() of "foo" returns "" compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("foo")
            let par: Path = parent(p)
            print(to_string(par))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parent_empty_compiles(self) -> None:
        """parent() of empty path returns "" compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("")
            let par: Path = parent(p)
            print(to_string(par))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parent_trailing_slash_compiles(self) -> None:
        """parent() strips trailing slash before computing parent."""
        src = _fs_source_with_main("""\
            let p: Path = path("/foo/bar/")
            let par: Path = parent(p)
            print(to_string(par))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Path type: filename
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestPathFilename:
    def test_filename_basic_compiles(self) -> None:
        """filename() of /foo/bar.txt returns "bar.txt" compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("/foo/bar.txt")
            let name: String = filename(p)
            print(name)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_filename_no_dir_compiles(self) -> None:
        """filename() of "file.txt" returns "file.txt" compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("file.txt")
            let name: String = filename(p)
            print(name)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_filename_root_compiles(self) -> None:
        """filename() of "/" returns "" compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("/")
            let name: String = filename(p)
            print(name)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_filename_empty_compiles(self) -> None:
        """filename() of empty path returns "" compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("")
            let name: String = filename(p)
            print(name)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Path type: extension
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestPathExtension:
    def test_extension_basic_compiles(self) -> None:
        """extension() of "file.txt" returns "txt" compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("/foo/file.txt")
            let ext: String = extension(p)
            print(ext)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_extension_double_compiles(self) -> None:
        """extension() of "file.tar.gz" returns "gz" compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("archive.tar.gz")
            let ext: String = extension(p)
            print(ext)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_extension_none_compiles(self) -> None:
        """extension() of "noext" returns "" compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("noext")
            let ext: String = extension(p)
            print(ext)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_extension_dotfile_compiles(self) -> None:
        """extension() of ".gitignore" returns "" (hidden file) compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path(".gitignore")
            let ext: String = extension(p)
            print(ext)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Path type: stem
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestPathStem:
    def test_stem_basic_compiles(self) -> None:
        """stem() of "file.txt" returns "file" compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("/foo/file.txt")
            let s: String = stem(p)
            print(s)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_stem_double_ext_compiles(self) -> None:
        """stem() of "file.tar.gz" returns "file.tar" compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("file.tar.gz")
            let s: String = stem(p)
            print(s)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_stem_no_ext_compiles(self) -> None:
        """stem() of "noext" returns "noext" compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("noext")
            let s: String = stem(p)
            print(s)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_stem_empty_compiles(self) -> None:
        """stem() of empty path returns "" compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("")
            let s: String = stem(p)
            print(s)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Path type: is_absolute, to_string
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestPathAbsoluteAndToString:
    def test_is_absolute_true_compiles(self) -> None:
        """is_absolute() for "/foo" returns true compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("/foo")
            let abs: Bool = is_absolute(p)
            if abs {
                print("absolute")
            } else {
                print("relative")
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_is_absolute_false_compiles(self) -> None:
        """is_absolute() for "foo" returns false compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("relative/path")
            let abs: Bool = is_absolute(p)
            if abs {
                print("absolute")
            } else {
                print("relative")
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_is_absolute_empty_compiles(self) -> None:
        """is_absolute() for empty path returns false compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("")
            let abs: Bool = is_absolute(p)
            if abs {
                print("absolute")
            } else {
                print("relative")
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_to_string_compiles(self) -> None:
        """to_string() returns the raw path string compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("/home/user/file.txt")
            let s: String = to_string(p)
            print(s)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# File I/O: read_file / write_file / append_file roundtrip
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestFileIO:
    def test_read_file_compiles(self) -> None:
        """read_file() returns Result<String, FsError> compiles."""
        src = _fs_source_with_main("""\
            let r: Result<String, FsError> = read_file("/tmp/test.txt")
            match r {
                Ok(content) => { print(content) },
                Err(e) => { print("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_file_read" in ir_out

    def test_write_file_compiles(self) -> None:
        """write_file() returns Result<Bool, FsError> compiles."""
        src = _fs_source_with_main("""\
            let r: Result<Bool, FsError> = write_file("/tmp/out.txt", "hello")
            match r {
                Ok(ok) => { print("written") },
                Err(e) => { print("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_file_write" in ir_out

    def test_append_file_compiles(self) -> None:
        """append_file() returns Result<Bool, FsError> — stubbed in native build."""
        src = _fs_source_with_main("""\
            let r: Result<Bool, FsError> = append_file("/tmp/out.txt", " world")
            match r {
                Ok(ok) => { print("appended") },
                Err(e) => { print("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_write_read_roundtrip_compiles(self) -> None:
        """write_file then read_file roundtrip compiles."""
        src = _fs_source_with_main("""\
            let wr: Result<Bool, FsError> = write_file("/tmp/rt.txt", "round trip")
            match wr {
                Ok(ok) => {
                    let rr: Result<String, FsError> = read_file("/tmp/rt.txt")
                    match rr {
                        Ok(content) => { print(content) },
                        Err(e) => { print("read error") }
                    }
                },
                Err(e) => { print("write error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_write_append_read_roundtrip_compiles(self) -> None:
        """write_file, append_file, then read_file roundtrip compiles."""
        src = _fs_source_with_main("""\
            let w: Result<Bool, FsError> = write_file("/tmp/app.txt", "hello")
            match w {
                Ok(ok) => {
                    let a: Result<Bool, FsError> = append_file("/tmp/app.txt", " world")
                    match a {
                        Ok(ok2) => {
                            let r: Result<String, FsError> = read_file("/tmp/app.txt")
                            match r {
                                Ok(content) => { print(content) },
                                Err(e) => { print("read error") }
                            }
                        },
                        Err(e) => { print("append error") }
                    }
                },
                Err(e) => { print("write error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# File queries: exists, file_size, file_mtime
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestFileQueries:
    def test_exists_compiles(self) -> None:
        """exists() returns Bool compiles."""
        src = _fs_source_with_main("""\
            let ex: Bool = exists("/tmp/test.txt")
            if ex {
                print("exists")
            } else {
                print("not found")
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_file_exists" in ir_out

    def test_file_size_compiles(self) -> None:
        """file_size() returns Result<Int, FsError> compiles."""
        src = _fs_source_with_main("""\
            let r: Result<Int, FsError> = file_size("/tmp/test.txt")
            match r {
                Ok(sz) => { print(str(sz)) },
                Err(e) => { print("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_file_size" in ir_out

    def test_file_mtime_compiles(self) -> None:
        """file_mtime() returns Result<Int, FsError> compiles."""
        src = _fs_source_with_main("""\
            let r: Result<Int, FsError> = file_mtime("/tmp/test.txt")
            match r {
                Ok(mt) => { print(str(mt)) },
                Err(e) => { print("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_file_mtime" in ir_out


# ---------------------------------------------------------------------------
# File type checks: is_dir, is_file
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestFileTypeChecks:
    def test_is_dir_compiles(self) -> None:
        """is_dir() returns Bool compiles."""
        src = _fs_source_with_main("""\
            let d: Bool = is_dir("/tmp")
            if d {
                print("is directory")
            } else {
                print("not directory")
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_is_file_compiles(self) -> None:
        """is_file() returns Bool compiles."""
        src = _fs_source_with_main("""\
            let f: Bool = is_file("/tmp/test.txt")
            if f {
                print("is file")
            } else {
                print("not file")
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_is_dir_and_is_file_together_compiles(self) -> None:
        """is_dir() and is_file() used together compile."""
        src = _fs_source_with_main("""\
            let path_str: String = "/tmp/test"
            let d: Bool = is_dir(path_str)
            let f: Bool = is_file(path_str)
            if d {
                print("directory")
            } else if f {
                print("file")
            } else {
                print("does not exist")
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# File manipulation: remove, rename, copy
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestFileManipulation:
    def test_remove_compiles(self) -> None:
        """remove() returns Result<Bool, FsError> compiles."""
        src = _fs_source_with_main("""\
            let r: Result<Bool, FsError> = remove("/tmp/to_delete.txt")
            match r {
                Ok(ok) => { print("removed") },
                Err(e) => { print("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_file_remove" in ir_out

    def test_rename_compiles(self) -> None:
        """rename() returns Result<Bool, FsError> compiles."""
        src = _fs_source_with_main("""\
            let r: Result<Bool, FsError> = rename("/tmp/old.txt", "/tmp/new.txt")
            match r {
                Ok(ok) => { print("renamed") },
                Err(e) => { print("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_file_rename" in ir_out

    def test_copy_compiles(self) -> None:
        """copy() returns Result<Bool, FsError> compiles."""
        src = _fs_source_with_main("""\
            let r: Result<Bool, FsError> = copy("/tmp/src.txt", "/tmp/dst.txt")
            match r {
                Ok(ok) => { print("copied") },
                Err(e) => { print("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_file_copy" in ir_out

    def test_write_copy_read_compiles(self) -> None:
        """write + copy + read pipeline compiles."""
        src = _fs_source_with_main("""\
            let w: Result<Bool, FsError> = write_file("/tmp/orig.txt", "content")
            match w {
                Ok(ok) => {
                    let c: Result<Bool, FsError> = copy("/tmp/orig.txt", "/tmp/copy.txt")
                    match c {
                        Ok(ok2) => {
                            let r: Result<String, FsError> = read_file("/tmp/copy.txt")
                            match r {
                                Ok(content) => { print(content) },
                                Err(e) => { print("read error") }
                            }
                        },
                        Err(e) => { print("copy error") }
                    }
                },
                Err(e) => { print("write error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Directory operations: mkdir, mkdir_all, rmdir, list_dir
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestDirectoryOperations:
    def test_mkdir_compiles(self) -> None:
        """mkdir() returns Result<Bool, FsError> compiles."""
        src = _fs_source_with_main("""\
            let r: Result<Bool, FsError> = mkdir("/tmp/testdir")
            match r {
                Ok(ok) => { print("created") },
                Err(e) => { print("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_dir_create" in ir_out

    def test_mkdir_all_compiles(self) -> None:
        """mkdir_all() with recursive flag compiles."""
        src = _fs_source_with_main("""\
            let r: Result<Bool, FsError> = mkdir_all("/tmp/a/b/c/d")
            match r {
                Ok(ok) => { print("tree created") },
                Err(e) => { print("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_dir_create" in ir_out

    def test_rmdir_compiles(self) -> None:
        """rmdir() returns Result<Bool, FsError> compiles."""
        src = _fs_source_with_main("""\
            let r: Result<Bool, FsError> = rmdir("/tmp/testdir")
            match r {
                Ok(ok) => { print("removed") },
                Err(e) => { print("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_dir_remove" in ir_out

    def test_list_dir_compiles(self) -> None:
        """list_dir() returns Result<List<DirEntry>, FsError> compiles."""
        src = _fs_source_with_main("""\
            let r: Result<List<DirEntry>, FsError> = list_dir("/tmp")
            match r {
                Ok(entries) => {
                    print(str(len(entries)))
                },
                Err(e) => { print("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_mkdir_rmdir_roundtrip_compiles(self) -> None:
        """mkdir then rmdir roundtrip compiles."""
        src = _fs_source_with_main("""\
            let mk: Result<Bool, FsError> = mkdir("/tmp/roundtrip_dir")
            match mk {
                Ok(ok) => {
                    let rm: Result<Bool, FsError> = rmdir("/tmp/roundtrip_dir")
                    match rm {
                        Ok(ok2) => { print("created and removed") },
                        Err(e) => { print("remove error") }
                    }
                },
                Err(e) => { print("create error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_mkdir_all_deeply_nested_compiles(self) -> None:
        """mkdir_all with deeply nested path compiles."""
        src = _fs_source_with_main("""\
            let r: Result<Bool, FsError> = mkdir_all("/tmp/deep/nest/a/b/c/d/e/f")
            match r {
                Ok(ok) => { print("deep tree created") },
                Err(e) => { print("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Convenience: read_lines
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestReadLines:
    def test_read_lines_compiles(self) -> None:
        """read_lines() returns Result<List<String>, FsError> compiles."""
        src = _fs_source_with_main("""\
            let r: Result<List<String>, FsError> = read_lines("/tmp/lines.txt")
            match r {
                Ok(lines) => {
                    print(str(len(lines)))
                },
                Err(e) => { print("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_write_then_read_lines_compiles(self) -> None:
        """write_file then read_lines roundtrip compiles."""
        src = _fs_source_with_main("""\
            let w: Result<Bool, FsError> = write_file("/tmp/multiline.txt", "line1\\nline2\\nline3")
            match w {
                Ok(ok) => {
                    let r: Result<List<String>, FsError> = read_lines("/tmp/multiline.txt")
                    match r {
                        Ok(lines) => { print(str(len(lines))) },
                        Err(e) => { print("read error") }
                    }
                },
                Err(e) => { print("write error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Convenience: tmpfile
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestTmpfile:
    def test_tmpfile_compiles(self) -> None:
        """tmpfile() returns Result<String, FsError> compiles."""
        src = _fs_source_with_main("""\
            let r: Result<String, FsError> = tmpfile()
            match r {
                Ok(path) => { print(path) },
                Err(e) => { print("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_tmpfile_path" in ir_out


# ---------------------------------------------------------------------------
# Path type: resolve
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestPathResolve:
    def test_resolve_compiles(self) -> None:
        """resolve() returns Result<Path, FsError> compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("/tmp")
            let r: Result<Path, FsError> = resolve(p)
            match r {
                Ok(resolved) => { print(to_string(resolved)) },
                Err(e) => { print("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_realpath" in ir_out

    def test_resolve_empty_path_compiles(self) -> None:
        """resolve() with empty path returns Err compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("")
            let r: Result<Path, FsError> = resolve(p)
            match r {
                Ok(resolved) => { print(to_string(resolved)) },
                Err(e) => { print("expected error for empty path") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Walk (recursive directory listing)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestWalk:
    def test_walk_compiles(self) -> None:
        """walk() returns List<String> compiles."""
        src = _fs_source_with_main("""\
            let files: List<String> = walk("/tmp")
            print(str(len(files)))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_walk_uses_list_dir_compiles(self) -> None:
        """walk() internally uses list_dir, both compile."""
        src = _fs_source_with_main("""\
            let entries: List<String> = walk("/tmp/testdir")
            let mut i: Int = 0
            while i < len(entries) {
                print(entries[i])
                i = i + 1
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Error handling: file not found, empty path
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestErrorHandling:
    def test_read_file_not_found_compiles(self) -> None:
        """read_file on non-existent file returns Err(NotFound) compiles."""
        src = _fs_source_with_main("""\
            let r: Result<String, FsError> = read_file("/nonexistent/file.txt")
            match r {
                Ok(content) => { print("unexpected") },
                Err(e) => { print("expected not found") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_read_file_empty_path_compiles(self) -> None:
        """read_file with empty path returns Err(InvalidPath) compiles."""
        src = _fs_source_with_main("""\
            let r: Result<String, FsError> = read_file("")
            match r {
                Ok(content) => { print("unexpected") },
                Err(e) => { print("expected invalid path") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_write_file_empty_path_compiles(self) -> None:
        """write_file with empty path returns Err(InvalidPath) compiles."""
        src = _fs_source_with_main("""\
            let r: Result<Bool, FsError> = write_file("", "data")
            match r {
                Ok(ok) => { print("unexpected") },
                Err(e) => { print("expected invalid path") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_remove_not_found_compiles(self) -> None:
        """remove on non-existent file returns Err compiles."""
        src = _fs_source_with_main("""\
            let r: Result<Bool, FsError> = remove("/nonexistent/file.txt")
            match r {
                Ok(ok) => { print("unexpected") },
                Err(e) => { print("expected error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_rename_empty_source_compiles(self) -> None:
        """rename with empty source returns Err(InvalidPath) compiles."""
        src = _fs_source_with_main("""\
            let r: Result<Bool, FsError> = rename("", "/tmp/new.txt")
            match r {
                Ok(ok) => { print("unexpected") },
                Err(e) => { print("expected invalid path") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_rename_empty_dest_compiles(self) -> None:
        """rename with empty destination returns Err(InvalidPath) compiles."""
        src = _fs_source_with_main("""\
            let r: Result<Bool, FsError> = rename("/tmp/old.txt", "")
            match r {
                Ok(ok) => { print("unexpected") },
                Err(e) => { print("expected invalid path") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_copy_empty_source_compiles(self) -> None:
        """copy with empty source returns Err(InvalidPath) compiles."""
        src = _fs_source_with_main("""\
            let r: Result<Bool, FsError> = copy("", "/tmp/dst.txt")
            match r {
                Ok(ok) => { print("unexpected") },
                Err(e) => { print("expected invalid path") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_copy_source_not_found_compiles(self) -> None:
        """copy with non-existent source returns Err(NotFound) compiles."""
        src = _fs_source_with_main("""\
            let r: Result<Bool, FsError> = copy("/nonexistent/src.txt", "/tmp/dst.txt")
            match r {
                Ok(ok) => { print("unexpected") },
                Err(e) => { print("expected not found") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_rename_source_not_found_compiles(self) -> None:
        """rename with non-existent source returns Err(NotFound) compiles."""
        src = _fs_source_with_main("""\
            let r: Result<Bool, FsError> = rename("/nonexistent/old.txt", "/tmp/new.txt")
            match r {
                Ok(ok) => { print("unexpected") },
                Err(e) => { print("expected not found") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_mkdir_empty_path_compiles(self) -> None:
        """mkdir with empty path returns Err(InvalidPath) compiles."""
        src = _fs_source_with_main("""\
            let r: Result<Bool, FsError> = mkdir("")
            match r {
                Ok(ok) => { print("unexpected") },
                Err(e) => { print("expected invalid path") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_rmdir_not_found_compiles(self) -> None:
        """rmdir on non-existent directory returns Err compiles."""
        src = _fs_source_with_main("""\
            let r: Result<Bool, FsError> = rmdir("/nonexistent/dir")
            match r {
                Ok(ok) => { print("unexpected") },
                Err(e) => { print("expected error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_list_dir_not_found_compiles(self) -> None:
        """list_dir on non-existent path returns Err compiles."""
        src = _fs_source_with_main("""\
            let r: Result<List<DirEntry>, FsError> = list_dir("/nonexistent/dir")
            match r {
                Ok(entries) => { print("unexpected") },
                Err(e) => { print("expected error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_file_size_not_found_compiles(self) -> None:
        """file_size on non-existent file returns Err compiles."""
        src = _fs_source_with_main("""\
            let r: Result<Int, FsError> = file_size("/nonexistent/file.txt")
            match r {
                Ok(sz) => { print("unexpected") },
                Err(e) => { print("expected error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_file_mtime_empty_path_compiles(self) -> None:
        """file_mtime with empty path returns Err(InvalidPath) compiles."""
        src = _fs_source_with_main("""\
            let r: Result<Int, FsError> = file_mtime("")
            match r {
                Ok(mt) => { print("unexpected") },
                Err(e) => { print("expected invalid path") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_append_file_empty_path_compiles(self) -> None:
        """append_file with empty path returns Err(InvalidPath) compiles."""
        src = _fs_source_with_main("""\
            let r: Result<Bool, FsError> = append_file("", "data")
            match r {
                Ok(ok) => { print("unexpected") },
                Err(e) => { print("expected invalid path") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Edge cases: deeply nested paths, special characters
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestEdgeCases:
    def test_deeply_nested_path_join_compiles(self) -> None:
        """Deeply nested path via repeated join() compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("/")
            let p1: Path = join(p, "a")
            let p2: Path = join(p1, "b")
            let p3: Path = join(p2, "c")
            let p4: Path = join(p3, "d")
            let p5: Path = join(p4, "e")
            let p6: Path = join(p5, "f")
            let p7: Path = join(p6, "g")
            let p8: Path = join(p7, "h")
            let p9: Path = join(p8, "file.txt")
            print(to_string(p9))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parent_of_parent_chain_compiles(self) -> None:
        """Chained parent() calls compile."""
        src = _fs_source_with_main("""\
            let p: Path = path("/a/b/c/d/e")
            let p1: Path = parent(p)
            let p2: Path = parent(p1)
            let p3: Path = parent(p2)
            print(to_string(p3))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_path_with_spaces_compiles(self) -> None:
        """Path containing spaces compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("/home/user/my documents/file name.txt")
            let name: String = filename(p)
            let ext: String = extension(p)
            let s: String = stem(p)
            print(name)
            print(ext)
            print(s)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_path_with_dots_compiles(self) -> None:
        """Path containing dots in directory names compiles."""
        src = _fs_source_with_main("""\
            let p: Path = path("/home/v1.0.0/config.d/settings.json")
            let name: String = filename(p)
            let ext: String = extension(p)
            let s: String = stem(p)
            let par: Path = parent(p)
            print(name)
            print(ext)
            print(s)
            print(to_string(par))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_all_path_methods_together_compiles(self) -> None:
        """All Path methods used together in one function compile."""
        src = _fs_source_with_main("""\
            let p: Path = path("/home/user/docs/report.pdf")
            let joined: Path = join(p, "extra")
            let par: Path = parent(p)
            let name: String = filename(p)
            let ext: String = extension(p)
            let s: String = stem(p)
            let abs: Bool = is_absolute(p)
            let raw: String = to_string(p)
            print(to_string(joined))
            print(to_string(par))
            print(name)
            print(ext)
            print(s)
            if abs {
                print("absolute")
            }
            print(raw)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_dir_entry_struct_compiles(self) -> None:
        """DirEntry struct fields (name, is_dir) accessible after list_dir compiles."""
        src = _fs_source_with_main("""\
            let r: Result<List<DirEntry>, FsError> = list_dir("/tmp")
            match r {
                Ok(entries) => {
                    let count: Int = len(entries)
                    if count > 0 {
                        let first: DirEntry = entries[0]
                        print(first.name)
                        if first.is_dir {
                            print("dir")
                        } else {
                            print("file")
                        }
                    }
                },
                Err(e) => { print("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Extern declarations
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestExternDeclarations:
    def test_all_extern_functions_declared(self) -> None:
        """All C runtime extern functions are declared in compiled IR."""
        src = _fs_source_with_main('print("ok")')
        ir_out = _compile_mir(src)
        # Core file operations (some removed: file_open/write_fd/close/dir_list
        # use raw pointer ABIs not available in native Mapanare)
        assert "__mn_file_write" in ir_out
        assert "__mn_file_exists" in ir_out
        assert "__mn_file_remove" in ir_out
        assert "__mn_dir_create" in ir_out
        assert "__mn_dir_remove" in ir_out
        assert "__mn_file_rename" in ir_out
        assert "__mn_file_copy" in ir_out
        assert "__mn_tmpfile_path" in ir_out
        assert "__mn_realpath" in ir_out
        assert "__mn_file_size" in ir_out
        assert "__mn_file_mtime" in ir_out


# ---------------------------------------------------------------------------
# Integration patterns
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestFsIntegration:
    def test_full_file_lifecycle_compiles(self) -> None:
        """write -> read -> append -> read -> remove lifecycle compiles."""
        src = _fs_source_with_main("""\
            let w: Result<Bool, FsError> = write_file("/tmp/lifecycle.txt", "initial")
            match w {
                Ok(ok) => {
                    let r1: Result<String, FsError> = read_file("/tmp/lifecycle.txt")
                    match r1 {
                        Ok(c1) => { print(c1) },
                        Err(e) => { print("read1 error") }
                    }
                    let a: Result<Bool, FsError> = append_file("/tmp/lifecycle.txt", " appended")
                    match a {
                        Ok(ok2) => {
                            let r2: Result<String, FsError> = read_file("/tmp/lifecycle.txt")
                            match r2 {
                                Ok(c2) => { print(c2) },
                                Err(e) => { print("read2 error") }
                            }
                        },
                        Err(e) => { print("append error") }
                    }
                    let rm: Result<Bool, FsError> = remove("/tmp/lifecycle.txt")
                    match rm {
                        Ok(ok3) => { print("cleaned up") },
                        Err(e) => { print("remove error") }
                    }
                },
                Err(e) => { print("write error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_dir_lifecycle_compiles(self) -> None:
        """mkdir_all -> write file inside -> list_dir -> remove -> rmdir compiles."""
        src = _fs_source_with_main("""\
            let mk: Result<Bool, FsError> = mkdir_all("/tmp/fs_test/sub")
            match mk {
                Ok(ok) => {
                    let w: Result<Bool, FsError> = write_file("/tmp/fs_test/sub/data.txt", "hello")
                    match w {
                        Ok(ok2) => {
                            let ls: Result<List<DirEntry>, FsError> = list_dir("/tmp/fs_test/sub")
                            match ls {
                                Ok(entries) => { print(str(len(entries))) },
                                Err(e) => { print("list error") }
                            }
                        },
                        Err(e) => { print("write error") }
                    }
                },
                Err(e) => { print("mkdir error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_path_and_file_ops_together_compiles(self) -> None:
        """Path manipulation combined with file operations compiles."""
        src = _fs_source_with_main("""\
            let base: Path = path("/tmp")
            let dir_path: Path = join(base, "pathtest")
            let file_path: Path = join(dir_path, "data.txt")
            let dir_str: String = to_string(dir_path)
            let file_str: String = to_string(file_path)

            let mk: Result<Bool, FsError> = mkdir(dir_str)
            match mk {
                Ok(ok) => {
                    let w: Result<Bool, FsError> = write_file(file_str, "path test")
                    match w {
                        Ok(ok2) => {
                            let ex: Bool = exists(file_str)
                            if ex {
                                print("file exists")
                            }
                            let name: String = filename(file_path)
                            print(name)
                        },
                        Err(e) => { print("write error") }
                    }
                },
                Err(e) => { print("mkdir error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_error_constructor_helpers_compiles(self) -> None:
        """Internal error constructor functions compile."""
        src = _fs_source_with_main("""\
            let e1: FsError = new_not_found("missing")
            let e2: FsError = new_permission_denied("denied")
            let e3: FsError = new_io_error("disk fail")
            let e4: FsError = new_invalid_path("bad")
            print("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
