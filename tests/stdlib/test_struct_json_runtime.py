"""v5.39.2 Js.4.B.2 — link-and-run regression for from_json::<T>.

Mirrors the v5.34.0 / v5.35.0 / v5.39.0 concatenation harness exactly:
read `stdlib/text/string_utils.mn` + `stdlib/encoding/json.mn`,
prepend to each `.mn` test main body, compile via the Python LLVM
emitter, link against `libmapanare_rt.a`, run, assert "PASSED" appears
in stdout (and "FAIL " does NOT).

Pre-fix: every test SEGV'd in `__mn_map_get` because
`stdlib/encoding/json.mn::decode_object_inner`'s
`pon mut entries: Map<String, JsonValue> = #{}` created an
empty-literal map with hardcoded `(ksz=8, vsz=8, ktag=0)` defaults
(`mapanare/emit_llvm_text.py::_do_map_init` empty branch).
String-key inserts wrote past the bucket and lookups always missed
(NULL return), then main() loaded `{i64, ptr}` from NULL → SEGV.

Post-fix: `_do_map_init` always derives sizes/tags from the declared
`MapInit.key_type` / `MapInit.val_type` regardless of pair count.

This harness is the test infrastructure that should have existed
since v5.36.0 — the existing `tests/stdlib/test_struct_json.py` is
compile-only (validates IR text, never links), which is exactly why
the SEGV stayed latent for 4 releases (v5.36.0 → v5.39.0).

Test files under stdlib/encoding/json/tests/:
- test_from_json_int.mn       — struct { x: Int }
- test_from_json_string.mn    — struct { name: String }
- test_from_json_bool.mn      — struct { active: Bool }
- test_from_json_float.mn     — struct { ratio: Float }
- test_from_json_compound.mn  — struct { name: String, age: Int }
- test_to_from_roundtrip.mn   — to_json -> from_json round-trip
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
STRING_UTILS_MN = REPO_ROOT / "stdlib" / "text" / "string_utils.mn"
JSON_MN = REPO_ROOT / "stdlib" / "encoding" / "json.mn"
TESTS_DIR = REPO_ROOT / "stdlib" / "encoding" / "json" / "tests"
RT_ARCHIVE = REPO_ROOT / "runtime" / "native" / "libmapanare_rt.a"

TEST_FILES = [
    "test_from_json_int.mn",
    "test_from_json_string.mn",
    "test_from_json_bool.mn",
    "test_from_json_float.mn",
    "test_from_json_compound.mn",
    "test_to_from_roundtrip.mn",
    # v5.39.3 Js.4.C — to_json::<T> nested struct field (was <?> pre-fix)
    "test_to_json_nested_struct.mn",
    # v5.39.4 Js.4.D.1 — to_json::<T> List-typed field (was <?> pre-fix)
    "test_to_json_list_field.mn",
    # v5.39.4 Js.4.D.2 — from_json::<T> nested struct decode (silent
    # shape mismatch pre-fix; consumer saw raw JsonValue)
    "test_from_json_nested_struct.mn",
    # v5.39.4 — full round-trip closure for nested-struct shapes
    # (strengthened at v5.39.5 with inner.ints assertions)
    "test_to_from_nested_roundtrip.mn",
    # v5.39.5 Js.4.D.3 — from_json::<T> List-typed field decode
    # (silent shape mismatch pre-fix; consumer saw raw JsonValue::Array
    # enum where List<X> was expected). Symmetric pair to v5.39.4
    # Js.4.D.1's encode-side test_to_json_list_field.mn.
    "test_from_json_list_field.mn",
]


def _have_clang() -> bool:
    return shutil.which("clang") is not None


def _have_llvmlite() -> bool:
    try:
        import llvmlite  # noqa: F401

        return True
    except ImportError:
        return False


@pytest.fixture(scope="module")
def stdlib_source() -> str:
    return (
        STRING_UTILS_MN.read_text(encoding="utf-8") + "\n\n" + JSON_MN.read_text(encoding="utf-8")
    )


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
@pytest.mark.parametrize("test_file", TEST_FILES)
def test_struct_json_runtime(test_file, stdlib_source, runtime_archive, tmp_path):
    """Run each Js.4.B.2 .mn test file and assert "PASSED" appears in output.

    Falsifiability: revert `_do_map_init`'s v5.39.2 empty-literal
    type-derivation fix, every parametrized case fails with a SEGV
    matching the GDB backtrace recorded in v5.39.2 SESSION_REPORT
    (PC at `__mn_map_get` then NULL-deref at `load {i64, ptr} from
    NULL` in main).
    """
    test_path = TESTS_DIR / test_file
    if not test_path.is_file():
        pytest.skip(f"missing {test_path}")

    main_body = test_path.read_text(encoding="utf-8")
    combined = stdlib_source + "\n\n// === harness-concatenated test ===\n\n" + main_body
    label = os.path.splitext(test_file)[0]
    stdout = _compile_link_run(combined, label, runtime_archive, tmp_path)

    if "FAIL " in stdout:
        pytest.fail(f"{test_file} reported failures:\n{stdout}")
    assert "PASSED" in stdout, f"{test_file} did not report PASSED:\n{stdout}"
