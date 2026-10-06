"""v5.39.0 Cr.* — runtime tests for stdlib/crypto.mn additions.

Mirrors the v5.34.0 / v5.35.0 / v5.38.0 concatenation harness exactly:
read `stdlib/crypto.mn`, prepend it to each `.mn` test main body,
compile via the MIR-based Python LLVM emitter, link against
`libmapanare_rt.a`, and run the resulting binary. Each test prints
"PASSED" or "FAILED" and the harness asserts the former (and no
"FAIL " line).

Why concatenation instead of `import crypto`: cross-module function
calls have a known limitation in both backends (Python LLVM emitter
mangles defined names with the module prefix but emits unprefixed
forward declarations at call sites; native compiler stage1 does not
propagate extern_fn_def declarations across modules). v5.34.0 →
v5.38.0 all shipped under the same constraint with the same harness;
v5.39.0 follows the proven pattern.

The pre-existing `tests/stdlib/test_crypto.py` (compile-only checks)
remains untouched.

Test files under stdlib/crypto/tests/:
  - test_crypto_smoke.mn   — Cr.1 / Cr.2 / Cr.5 smoke + streaming
                              ergonomics
  - test_crypto_corpus.mn  — RFC 6234 / FIPS 202 / RFC 7693 / RFC 4231
                              known-answer vectors
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CRYPTO_MN = REPO_ROOT / "stdlib" / "crypto.mn"
TESTS_DIR = REPO_ROOT / "stdlib" / "crypto" / "tests"
RT_ARCHIVE = REPO_ROOT / "runtime" / "native" / "libmapanare_rt.a"

TEST_FILES = [
    "test_crypto_smoke.mn",
    "test_crypto_corpus.mn",
]


def _have_clang() -> bool:
    return shutil.which("clang") is not None


def _have_llvmlite() -> bool:
    try:
        import llvmlite  # noqa: F401

        return True
    except ImportError:
        return False


def _have_libcrypto() -> bool:
    """Cr.* tests require libcrypto dlopen-able at runtime. Without it,
    every digest call returns the empty string and assertions fail.
    Skip rather than fail noisily."""
    candidates = [
        "/usr/lib/x86_64-linux-gnu/libcrypto.so.3",
        "/usr/lib/x86_64-linux-gnu/libcrypto.so.1.1",
        "/usr/lib/x86_64-linux-gnu/libcrypto.so",
        "/usr/lib/libcrypto.so.3",
        "/usr/lib/libcrypto.so.1.1",
        "/usr/lib/libcrypto.so",
        "/usr/lib/libcrypto.dylib",
        "/opt/homebrew/lib/libcrypto.dylib",
    ]
    for c in candidates:
        if Path(c).is_file() or Path(c).is_symlink():
            return True
    return False


@pytest.fixture(scope="module")
def crypto_mn_source() -> str:
    return CRYPTO_MN.read_text(encoding="utf-8")


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
    not _have_libcrypto(),
    reason="libcrypto.so/.dylib not found — Cr.* requires OpenSSL libcrypto",
)
@pytest.mark.parametrize("test_file", TEST_FILES)
def test_crypto_runtime_module(test_file, crypto_mn_source, runtime_archive, tmp_path):
    """Run each Cr.* .mn test file and assert "PASSED" appears in output."""
    test_path = TESTS_DIR / test_file
    if not test_path.is_file():
        pytest.skip(f"missing {test_path}")

    main_body = test_path.read_text(encoding="utf-8")
    combined = crypto_mn_source + "\n\n// === harness-concatenated test ===\n\n" + main_body
    label = os.path.splitext(test_file)[0]
    stdout = _compile_link_run(combined, label, runtime_archive, tmp_path)

    if "FAIL " in stdout:
        pytest.fail(f"{test_file} reported failures:\n{stdout}")
    assert "PASSED" in stdout, f"{test_file} did not report PASSED:\n{stdout}"


def test_stdlib_crypto_compiles_clean(crypto_mn_source):
    """stdlib/crypto.mn (with v5.39.0 Cr.* additions) compiles via the MIR
    LLVM emitter. Proxies parser + semantic check, plus catches lowering /
    IR-emission bugs that bare parse won't surface."""
    if not _have_llvmlite():
        pytest.skip("llvmlite not installed")

    from mapanare.cli import _compile_to_llvm_ir

    src = crypto_mn_source + '\nfn main() { print("ok") }\n'
    ir_text = _compile_to_llvm_ir(src, "stdlib_crypto_compile_check.mn")
    assert "main" in ir_text
    # Sanity: the v5.39.0 additions should be referenced in the IR.
    assert "__mn_sha3_256_str" in ir_text
    assert "__mn_blake2b_str" in ir_text
    assert "__mn_hmac_sha512_str" in ir_text
    assert "__mn_constant_time_eq" in ir_text
    assert "__mn_md_ctx_new" in ir_text
    assert "__mn_hmac_ctx_new" in ir_text
