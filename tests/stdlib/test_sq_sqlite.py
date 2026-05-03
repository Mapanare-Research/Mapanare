"""v5.35.0 Sq.6 — sqlite stdlib driver tests for stdlib/sql/sqlite.mn.

Distinct from tests/stdlib/test_sql_sqlite.py, which exercises the
older stdlib/db/sqlite.mn driver (predates v5.35.0). This file tests
the new Sq.* surface in stdlib/sql/sqlite.mn (Database / Statement /
Value / SqlError) introduced at v5.35.0.

Mirrors the v5.34.0 tests/stdlib/test_time_dt.py harness exactly: read
`stdlib/sql/sqlite.mn`, prepend it to each `.mn` test main body, compile
via the MIR-based Python LLVM emitter, link against `libmapanare_rt.a`,
and run the resulting binary. Each test prints "<name> PASSED" or
"<name> FAILED" and the harness asserts the former.

Why concatenation instead of `import sql.sqlite`: cross-module function
calls have a known limitation in both backends (Python LLVM emitter
mangles defined names with the module prefix but emits unprefixed forward
declarations at call sites; native compiler stage1 does not propagate
extern_fn_def declarations across modules). v5.34.0's stdlib/time.mn
shipped under the same constraint with the same harness; v5.35.0
follows that proven pattern. See stdlib/sql/sqlite.mn's preamble for
the full PROMPT/PLAN deviations log.

Test files under stdlib/sql/sqlite/tests/:
  - test_open_close.mn       — Sq.1 lifecycle (open / close idempotent)
  - test_crud.mn             — Sq.1+2 full CREATE/INSERT/SELECT/UPDATE/DELETE
  - test_transaction.mn      — Sq.4 commit + rollback + nested SAVEPOINT
  - test_prepared_reuse.mn   — Sq.2+5 manual reuse via reset+rebind+step
  - test_error_handling.mn   — Sq.1+2+3 SqlError variant coverage
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SQLITE_MN = REPO_ROOT / "stdlib" / "sql" / "sqlite.mn"
TESTS_DIR = REPO_ROOT / "stdlib" / "sql" / "sqlite" / "tests"
RT_ARCHIVE = REPO_ROOT / "runtime" / "native" / "libmapanare_rt.a"

TEST_FILES = [
    "test_open_close.mn",
    "test_crud.mn",
    "test_transaction.mn",
    "test_prepared_reuse.mn",
    "test_error_handling.mn",
]


def _have_clang() -> bool:
    return shutil.which("clang") is not None


def _have_llvmlite() -> bool:
    try:
        import llvmlite  # noqa: F401

        return True
    except ImportError:
        return False


def _have_libsqlite3() -> bool:
    """Sq.* tests require libsqlite3 dlopen-able at runtime. Without it,
    every test would fail on database_open with LoadFail. Skip rather
    than fail noisily — most CI workers have it but we don't enforce."""
    candidates = [
        "/usr/lib/x86_64-linux-gnu/libsqlite3.so",
        "/usr/lib/x86_64-linux-gnu/libsqlite3.so.0",
        "/usr/lib/libsqlite3.so",
        "/usr/lib/libsqlite3.dylib",
    ]
    for c in candidates:
        if Path(c).is_file() or Path(c).is_symlink():
            return True
    return False


@pytest.fixture(scope="module")
def sqlite_mn_source() -> str:
    return SQLITE_MN.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def runtime_archive() -> Path:
    """Ensure libmapanare_rt.a exists with v5.35.0 Sq.7 sqlite3 exports."""
    if not RT_ARCHIVE.is_file():
        subprocess.run(
            ["make", "build-rt"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        )
    return RT_ARCHIVE


def _compile_link_run(
    combined_source: str, label: str, runtime_archive: Path, tmp_path: Path
) -> str:
    """Compile combined_source via Python LLVM emitter, link, run; return stdout."""
    from mapanare.cli import _compile_to_llvm_ir

    ir_text = _compile_to_llvm_ir(combined_source, f"{label}.mn")
    ir_path = tmp_path / f"{label}.ll"
    ir_path.write_text(ir_text)

    bin_path = tmp_path / label
    result = subprocess.run(
        [
            "clang",
            str(ir_path),
            str(runtime_archive),
            "-lm",
            "-lpthread",
            "-ldl",
            "-o",
            str(bin_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"link failed for {label}:\n{result.stderr}")

    run = subprocess.run(
        [str(bin_path)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if run.returncode != 0:
        pytest.fail(
            f"{label} exited nonzero ({run.returncode}):\n"
            f"--- stdout ---\n{run.stdout}\n"
            f"--- stderr ---\n{run.stderr}"
        )
    return run.stdout


@pytest.mark.skipif(not _have_clang(), reason="clang required to link runtime")
@pytest.mark.skipif(not _have_llvmlite(), reason="llvmlite required for MIR LLVM emit")
@pytest.mark.skipif(
    not _have_libsqlite3(),
    reason="libsqlite3.so/.dylib not found — Sq.* requires dlopen target",
)
@pytest.mark.parametrize("test_file", TEST_FILES)
def test_sq_sqlite_module(test_file, sqlite_mn_source, runtime_archive, tmp_path):
    """Run each Sq.6 .mn test file and assert "PASSED" appears in output."""
    test_path = TESTS_DIR / test_file
    if not test_path.is_file():
        pytest.skip(f"missing {test_path}")

    main_body = test_path.read_text(encoding="utf-8")
    combined = sqlite_mn_source + "\n\n// === harness-concatenated test ===\n\n" + main_body
    label = os.path.splitext(test_file)[0]
    stdout = _compile_link_run(combined, label, runtime_archive, tmp_path)

    if "FAIL" in stdout:
        pytest.fail(f"{test_file} reported failures:\n{stdout}")
    assert "PASSED" in stdout, f"{test_file} did not report PASSED:\n{stdout}"


def test_stdlib_sq_sqlite_parses_clean(sqlite_mn_source):
    """stdlib/sql/sqlite.mn parses without errors on its own."""
    from mapanare.parser import parse

    ast = parse(sqlite_mn_source)
    assert len(ast.definitions) > 0


def test_stdlib_sq_sqlite_typechecks_clean(sqlite_mn_source):
    """stdlib/sql/sqlite.mn type-checks without errors on its own."""
    from mapanare.parser import parse
    from mapanare.semantic import check

    ast = parse(sqlite_mn_source)
    errs = check(ast, filename="stdlib/sql/sqlite.mn")
    real_errors = [e for e in errs if getattr(e, "severity", "error") == "error"]
    assert len(real_errors) == 0, f"semantic errors: {real_errors}"
