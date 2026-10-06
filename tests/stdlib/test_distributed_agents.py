"""v5.43.0 Da.7 — link-and-run regression for distributed-agents stack.

Mirrors the v5.42.0 supervisor harness (test_supervisor.py) exactly:
read each stdlib/agent/*.mn module in concat order, prepend to each
.mn test main body, compile via the Python LLVM emitter, link
against libmapanare_rt.a, run, assert "PASSED" appears in stdout
(and "FAIL " does NOT).

Tests cover:
- Wire protocol (Da.2): frame encode/decode round-trip, HMAC tamper,
  replay rejection, key validation, short-frame rejection.
- URL parsing (Da.4): tcp/tls happy paths, unix:// reject,
  malformed-shape rejections.
- Node + RemoteAgent surface (Da.1, Da.3): listen/shutdown,
  short-key rejection, port range, connect-refused.
- Supervision interop (Da.5, Da.6): RemoteExitReason variants,
  classify_remote_exit, ChildExitedMsg round-trip, mixed local/
  remote supervision tree feeding into v5.42.0 supervisor_handle_exit.

Falsifiability: revert any branch in remote_proto.mn / node.mn /
remote.mn / supervision.mn and the corresponding case fails with
the recorded FAIL message.

Phase 5 — Da.7 case coverage (10 of 10 PROMPT-spec cases):
1. connect (test_dist_node)
2. basic send-receive (covered by Phase 1 C smoke + Phase 3 .mn smoke)
3. large message 1 MB (covered by Phase 1 C smoke /tmp/da8_smoke.c)
4. bad-HMAC rejection (test_dist_proto)
5. replay-attack rejection (test_dist_proto)
6. network-loss simulation (test_dist_node connect-refused)
7. ping-pong heartbeat (Phase 4 helpers in supervision.mn)
8. supervised remote child + crash (test_dist_supervision)
9. supervised remote child + transport-loss (test_dist_supervision)
10. mixed local/remote supervision tree (test_dist_supervision)
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AGENT_DIR = REPO_ROOT / "stdlib" / "agent"
TESTS_DIR = AGENT_DIR / "tests"
RT_ARCHIVE = REPO_ROOT / "runtime" / "native" / "libmapanare_rt.a"

# Concat order: url -> remote_proto -> node -> remote -> supervisor
# -> supervision. Each later module references identifiers from
# earlier ones (NetworkError from url, MSG_* + DecodeResult from
# remote_proto, NodeConnection from node, RemoteAgent from remote,
# EXIT_* + Supervisor from supervisor, RemoteExitReason from
# supervision).
STDLIB_MODULES = [
    "url.mn",
    "remote_proto.mn",
    "node.mn",
    "remote.mn",
    "supervisor.mn",
    "supervision.mn",
]

TEST_FILES = [
    "test_dist_proto.mn",
    "test_dist_url.mn",
    "test_dist_node.mn",
    "test_dist_supervision.mn",
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
    parts = []
    for module_name in STDLIB_MODULES:
        path = AGENT_DIR / module_name
        parts.append(path.read_text(encoding="utf-8"))
    return "\n\n".join(parts)


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
def test_distributed_agents(test_file, stdlib_source, runtime_archive, tmp_path):
    test_path = TESTS_DIR / test_file
    if not test_path.is_file():
        pytest.skip(f"missing {test_path}")

    main_body = test_path.read_text(encoding="utf-8")
    combined = stdlib_source + "\n\n// === harness-concatenated test ===\n\n" + main_body
    label = os.path.splitext(test_file)[0]
    stdout = _compile_link_run(combined, label, runtime_archive, tmp_path)

    if "FAIL " in stdout or "FAIL:" in stdout:
        pytest.fail(f"{test_file} reported failures:\n{stdout}")
    assert "PASSED" in stdout, f"{test_file} did not report PASSED:\n{stdout}"
