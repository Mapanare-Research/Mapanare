"""v5.38.0 Re.* — runtime tests for stdlib/text/regex.mn.

Mirrors the v5.34.0 / v5.35.0 concatenation harness exactly: read
`stdlib/text/regex.mn`, prepend it to each `.mn` test main body,
compile via the MIR-based Python LLVM emitter, link against
`libmapanare_rt.a`, and run the resulting binary. Each test prints
"<name> PASSED" or "<name> FAILED" and the harness asserts the former.

Why concatenation instead of `import text.regex`: cross-module
function calls have a known limitation in both backends (Python LLVM
emitter mangles defined names with the module prefix but emits
unprefixed forward declarations at call sites; native compiler
stage1 does not propagate extern_fn_def declarations across
modules). v5.34.0 / v5.35.0 / v5.36.0 / v5.37.0 all shipped under
the same constraint with the same harness; v5.38.0 follows the
proven pattern. See stdlib/text/regex.mn's preamble for the
v5.38.0 PROMPT/PLAN deviations log.

Test files under stdlib/text/tests/:
  - test_regex_smoke.mn   — Re.1+Re.2+Re.3 smoke (compile / captures
                            / named groups / backref replace / find)
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REGEX_MN = REPO_ROOT / "stdlib" / "text" / "regex.mn"
TESTS_DIR = REPO_ROOT / "stdlib" / "text" / "tests"
RT_ARCHIVE = REPO_ROOT / "runtime" / "native" / "libmapanare_rt.a"

TEST_FILES = [
    "test_regex_smoke.mn",
    "test_regex_corpus.mn",
]


def _have_clang() -> bool:
    return shutil.which("clang") is not None


def _have_llvmlite() -> bool:
    try:
        import llvmlite  # noqa: F401

        return True
    except ImportError:
        return False


def _have_libpcre2() -> bool:
    """Re.* tests require libpcre2-8 dlopen-able at runtime. Without it,
    every test would fail on compile / exec with "PCRE2 not available".
    Skip rather than fail noisily."""
    candidates = [
        "/usr/lib/x86_64-linux-gnu/libpcre2-8.so.0",
        "/usr/lib/x86_64-linux-gnu/libpcre2-8.so",
        "/usr/lib/libpcre2-8.so.0",
        "/usr/lib/libpcre2-8.so",
        "/usr/lib/libpcre2-8.dylib",
        "/opt/homebrew/lib/libpcre2-8.dylib",
    ]
    for c in candidates:
        if Path(c).is_file() or Path(c).is_symlink():
            return True
    return False


@pytest.fixture(scope="module")
def regex_mn_source() -> str:
    return REGEX_MN.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def runtime_archive() -> Path:
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
    not _have_libpcre2(),
    reason="libpcre2-8.so/.dylib not found — Re.* requires PCRE2 dlopen target",
)
@pytest.mark.parametrize("test_file", TEST_FILES)
def test_text_regex_module(test_file, regex_mn_source, runtime_archive, tmp_path):
    """Run each Re.* .mn test file and assert "PASSED" appears in output."""
    test_path = TESTS_DIR / test_file
    if not test_path.is_file():
        pytest.skip(f"missing {test_path}")

    main_body = test_path.read_text(encoding="utf-8")
    combined = regex_mn_source + "\n\n// === harness-concatenated test ===\n\n" + main_body
    label = os.path.splitext(test_file)[0]
    stdout = _compile_link_run(combined, label, runtime_archive, tmp_path)

    if "FAIL" in stdout:
        pytest.fail(f"{test_file} reported failures:\n{stdout}")
    assert "PASSED" in stdout, f"{test_file} did not report PASSED:\n{stdout}"


def test_stdlib_text_regex_compiles_clean(regex_mn_source):
    """stdlib/text/regex.mn compiles via the MIR LLVM emitter (proxies the
    parser+semantic check, and also catches lowering / IR-emission bugs
    that bare parse won't surface)."""
    if not _have_llvmlite():
        pytest.skip("llvmlite not installed")

    from mapanare.cli import _compile_to_llvm_ir

    src = regex_mn_source + '\nfn main() { print("ok") }\n'
    ir_text = _compile_to_llvm_ir(src, "stdlib_text_regex_compile_check.mn")
    assert "main" in ir_text
    assert "__mn_regex_compile_str" in ir_text
