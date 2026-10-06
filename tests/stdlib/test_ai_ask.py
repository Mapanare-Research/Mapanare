r"""v5.40.0 Ai.\* — link-and-run regression for the `ask` runtime adapter.

Mirrors the v5.34.0 / v5.35.0 / v5.39.x concatenation harness exactly:
read `stdlib/text/string_utils.mn` + `stdlib/encoding/json.mn` +
`stdlib/ai/llm.mn` + `stdlib/ai/ask.mn` + `stdlib/ai/ask_cache.mn`,
prepend to each `.mn` test main body, compile via the Python LLVM
emitter, link against `libmapanare_rt.a`, run, assert "PASSED" appears
in stdout (and "FAIL " does NOT).

Phase 1 (Ai.5 error variants, Ai.4 env-driven config) and Phase 3
(Ai.6 cache round-trip) are deterministic and run in CI. Live
integration tests against real providers are gated on
``MAPANARE_AI_API_KEY`` and skipped by default.
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
LLM_MN = REPO_ROOT / "stdlib" / "ai" / "llm.mn"
ASK_MN = REPO_ROOT / "stdlib" / "ai" / "ask.mn"
ASK_CACHE_MN = REPO_ROOT / "stdlib" / "ai" / "ask_cache.mn"
TESTS_DIR = REPO_ROOT / "stdlib" / "ai" / "tests"
RT_ARCHIVE = REPO_ROOT / "runtime" / "native" / "libmapanare_rt.a"


# (test_file, env_overrides) — env_overrides are exported into the
# subprocess at run time. None means "clear MAPANARE_AI_* / MAPANARE_LLM_*".
TEST_FILES: list[tuple[str, dict[str, str] | None]] = [
    ("test_ask_error_variants.mn", None),
    ("test_ask_config_env.mn", None),
    (
        "test_ask_config_env_anthropic.mn",
        {
            "MAPANARE_AI_PROVIDER": "anthropic",
            "MAPANARE_AI_API_KEY": "test-key",
            "MAPANARE_AI_MODEL": "claude-sonnet-4-20250514",
        },
    ),
    ("test_ask_cache_roundtrip.mn", {"_NEEDS_CACHE_DIR": "1"}),
    ("test_ask_schema_shapes.mn", None),
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
        STRING_UTILS_MN.read_text(encoding="utf-8")
        + "\n\n"
        + JSON_MN.read_text(encoding="utf-8")
        + "\n\n"
        + LLM_MN.read_text(encoding="utf-8")
        + "\n\n"
        + ASK_MN.read_text(encoding="utf-8")
        + "\n\n"
        + ASK_CACHE_MN.read_text(encoding="utf-8")
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


def _clean_env() -> dict[str, str]:
    """Strip every MAPANARE_AI_* / MAPANARE_LLM_* var so tests run from a
    deterministic baseline. Uses os.environ as the floor so PATH / HOME
    etc. stay intact."""
    keep = {k: v for k, v in os.environ.items()}
    for k in list(keep.keys()):
        if k.startswith("MAPANARE_AI_") or k.startswith("MAPANARE_LLM_"):
            del keep[k]
    return keep


def _compile_link_run(
    combined_source: str,
    label: str,
    runtime_archive: Path,
    tmp_path: Path,
    run_env: dict[str, str] | None = None,
) -> str:
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

    env = run_env if run_env is not None else _clean_env()
    run = subprocess.run(
        [str(bin_path)],
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
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
@pytest.mark.parametrize("test_file,env_overrides", TEST_FILES)
def test_ai_ask_runtime(test_file, env_overrides, stdlib_source, runtime_archive, tmp_path):
    """Run each Ai.\\* .mn test and assert "PASSED" appears in output."""
    test_path = TESTS_DIR / test_file
    if not test_path.is_file():
        pytest.skip(f"missing {test_path}")

    main_body = test_path.read_text(encoding="utf-8")
    combined = stdlib_source + "\n\n// === harness-concatenated test ===\n\n" + main_body
    label = os.path.splitext(test_file)[0]

    env = _clean_env()
    if env_overrides is not None:
        if env_overrides.get("_NEEDS_CACHE_DIR") == "1":
            cache_dir = tmp_path / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            env["MAPANARE_AI_CACHE_DIR"] = str(cache_dir)
        else:
            for k, v in env_overrides.items():
                env[k] = v

    stdout = _compile_link_run(combined, label, runtime_archive, tmp_path, run_env=env)

    if "FAIL " in stdout:
        pytest.fail(f"{test_file} reported failures:\n{stdout}")
    assert "PASSED" in stdout, f"{test_file} did not report PASSED:\n{stdout}"


# Live integration test — gated on MAPANARE_AI_API_KEY and skipped by
# default in CI. Runs ask_with_schema against the configured provider
# end-to-end. Failures here usually mean a provider API drift, not a
# v5.40.0 regression — surface to the user.
@pytest.mark.skipif(not _have_clang(), reason="clang required to link runtime")
@pytest.mark.skipif(not _have_llvmlite(), reason="llvmlite required for MIR LLVM emit")
@pytest.mark.skipif(
    not os.environ.get("MAPANARE_AI_API_KEY"),
    reason="MAPANARE_AI_API_KEY not set; live test skipped",
)
def test_ai_ask_live(stdlib_source, runtime_archive, tmp_path):
    """End-to-end live call — bring your own API key. NOT run in CI."""
    main_body = """
struct Answer { greeting: String }

fn main() -> Int {
    pon schema: String = __struct_meta::<Answer>()
    pon r: Result<String, AskError> = ask_with_schema(
        "Reply with a short JSON greeting where greeting is set to the word hi.",
        schema
    )
    match r {
        Ok(json) => print("ASK_OK: " + json),
        Err(e) => print("ASK_ERR: " + ask_error_message(e))
    }
    print("PASSED test_ai_ask_live")
    return 0
}
"""
    combined = stdlib_source + "\n\n// === live test ===\n\n" + main_body
    env = dict(os.environ)
    stdout = _compile_link_run(combined, "test_ai_ask_live", runtime_archive, tmp_path, run_env=env)
    assert "PASSED" in stdout
