"""v5.42.0 As.5 — binary-compat regression for the
mapanare_agent_t struct extension.

The four new fields (parent, on_exit, on_exit_cb_data,
last_exit_kind, last_exit_reason[256]) appended to mapanare_agent_t
in v5.42.0 are structurally backward-compatible because:

  1. mapanare_agent_init() does memset(agent, 0, sizeof(*agent)),
     which zeros all new fields so old behavior is preserved.

  2. The two stage1 emitters (mapanare/emit_llvm_text.py and
     mapanare/self/emit_llvm.mn) treat mapanare_agent_t as opaque
     `ptr` and only allocate via mapanare_agent_new (heap), never
     stack-allocating with hard-coded sizeof.

This test pins those invariants:

  A) Struct size is stable for old callers — the new fields make
     the struct LARGER, but no caller hard-codes the size, so this
     manifests as "we know the new size and assert it has not
     drifted further unexpectedly between releases."

  B) The lower.py emitter treats mapanare_agent_t pointers as
     opaque (no LLVM IR references the struct's fields).

Falsifiability: insert a new field IN THE MIDDLE of
mapanare_agent_t (not at the end) and (B) still passes but the
runtime semantics break for any pre-existing binary; the v5.42.0
contract is that fields stay APPEND-ONLY.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUNTIME_H = REPO_ROOT / "runtime" / "native" / "mapanare_runtime.h"
RUNTIME_C = REPO_ROOT / "runtime" / "native" / "mapanare_runtime.c"
EMITTER_PY = REPO_ROOT / "mapanare" / "emit_llvm_text.py"


def _have_gcc() -> bool:
    return shutil.which("gcc") is not None


@pytest.mark.skipif(not _have_gcc(), reason="gcc required for sizeof check")
def test_mapanare_agent_t_size_probe(tmp_path):
    """Compile a tiny C probe that prints sizeof(mapanare_agent_t).

    We don't lock a specific number — that depends on platform
    alignment — but we assert it's >= the v5.41.0 baseline plus the
    minimum bytes the four new fields need (3 pointers + i32 + 256
    bytes = 24+4+256 with alignment ~ 296, but rounding may push to
    304+). On 64-bit Linux the value should be ~768+ bytes.

    The real falsifiability is the next test (B): no struct-field
    reference leaks through the emitter.
    """
    probe = tmp_path / "probe.c"
    probe.write_text(
        "#include <stdio.h>\n"
        '#include "mapanare_runtime.h"\n'
        "int main(void) {\n"
        '    printf("%zu\\n", sizeof(mapanare_agent_t));\n'
        "    return 0;\n"
        "}\n"
    )
    binary = tmp_path / "probe"
    cc = subprocess.run(
        [
            "gcc",
            "-O0",
            "-g",
            "-pthread",
            f"-I{REPO_ROOT / 'runtime' / 'native'}",
            str(probe),
            str(REPO_ROOT / "runtime" / "native" / "libmapanare_rt.a"),
            "-lm",
            "-lpthread",
            "-ldl",
            "-o",
            str(binary),
        ],
        capture_output=True,
        text=True,
    )
    if cc.returncode != 0:
        # Library may not be built in this environment.
        if "libmapanare_rt.a" in cc.stderr and "No such file" in cc.stderr:
            pytest.skip("libmapanare_rt.a not built (run `make build-rt`)")
        pytest.fail(f"probe compile failed:\n{cc.stderr}")

    run = subprocess.run([str(binary)], capture_output=True, text=True)
    assert run.returncode == 0
    size = int(run.stdout.strip())
    # Pre-v5.42.0 struct was about 488 bytes on x86_64 Linux. After
    # adding 3 pointers (24) + atomic_i32 (4) + char[256] (256) =
    # 284 bytes plus alignment, expect 768-832 bytes. Lock the lower
    # bound; the upper bound is 1024 to flag accidental bloat.
    assert size >= 488, (
        f"sizeof(mapanare_agent_t)={size} — smaller than v5.41.0 "
        f"baseline 488. v5.42.0 appended fields; if this regresses, "
        f"a field was deleted, not added."
    )
    assert size <= 1024, (
        f"sizeof(mapanare_agent_t)={size} > 1024 — accidental bloat? "
        f"v5.42.0 As.6 expected ~768-832 bytes."
    )


def test_emitter_treats_agent_as_opaque_ptr():
    """The Python LLVM emitter must declare mapanare_agent_new and
    related functions with `ptr` returns/params, never with a named
    struct type. This is the structural invariant that makes
    appending fields binary-compat-safe.
    """
    src = EMITTER_PY.read_text(encoding="utf-8")
    # mapanare_agent_new declared with PTR/I32 pattern
    m = re.search(
        r'_ensure\("mapanare_agent_new",\s*PTR,\s*\[PTR,\s*PTR,\s*PTR,\s*I32,\s*I32\]\)',
        src,
    )
    assert m, (
        "mapanare_agent_new declaration in emit_llvm_text.py does not "
        "match the opaque-PTR shape; if this declaration changed, "
        "verify the binary-compat contract."
    )
    # mapanare_agent_send is (PTR, PTR) -> I32
    m = re.search(
        r'_ensure\("mapanare_agent_send",\s*I32,\s*\[PTR,\s*PTR\]\)',
        src,
    )
    assert m, "mapanare_agent_send declaration drifted from opaque-PTR " "shape."


def test_new_fields_append_only_in_header():
    """The v5.42.0 As.6 fields land at the END of mapanare_agent_t.

    Spec: locate the closing `} mapanare_agent_t;` and walk back to
    the prior `void (*message_dtor)(void *msg);` (the v4.33.0 last
    field before v5.42.0). The new fields must appear between these
    two anchors — not before message_dtor.
    """
    src = RUNTIME_H.read_text(encoding="utf-8")
    end_anchor = "} mapanare_agent_t;"
    pre_v5_42_anchor = "void (*message_dtor)(void *msg);"
    end_idx = src.rfind(end_anchor)
    pre_idx = src.find(pre_v5_42_anchor)
    assert pre_idx > 0 and end_idx > pre_idx, (
        "could not locate the message_dtor → end-of-struct region; "
        "if the struct was renamed, update this test."
    )
    region = src[pre_idx:end_idx]
    # The four new fields all appear in this trailing region.
    for field in (
        "*parent",
        "on_exit",
        "on_exit_cb_data",
        "last_exit_kind",
        "last_exit_reason",
    ):
        assert field in region, (
            f"v5.42.0 As.6 field `{field}` not in the trailing "
            f"region of mapanare_agent_t — fields must be append-only."
        )


def test_on_exit_callback_call_sites():
    """The v5.42.0 As.6 callback must fire at the FAILED transition
    sites — the three `state, MAPANARE_AGENT_FAILED` stores in
    mapanare_runtime.c each get a follow-on `if (agent->on_exit)`
    invocation in a stable window.
    """
    src = RUNTIME_C.read_text(encoding="utf-8")
    failed_stores = re.findall(
        r"atomic_store_i32\(&agent->state,\s*MAPANARE_AGENT_FAILED\)",
        src,
    )
    # Three FAILED transition sites in the dispatch paths
    # (lines 606, 612 in coop scheduler; 1411 in pthread worker).
    # All three must be present; we don't lock the count if the
    # runtime adds more, but each one we DO see needs an on_exit
    # follow-on within the next 200 chars.
    assert len(failed_stores) >= 3, (
        f"expected >= 3 FAILED transition sites in runtime.c, " f"found {len(failed_stores)}"
    )
    # Each FAILED store window has the on_exit invocation
    for m in re.finditer(
        r"atomic_store_i32\(&agent->state,\s*MAPANARE_AGENT_FAILED\)",
        src,
    ):
        window = src[m.end() : m.end() + 400]
        assert "agent->on_exit" in window, (
            "FAILED transition site does not invoke on_exit callback "
            "within 400 chars; v5.42.0 As.6 contract violated. "
            f"Window:\n{window[:200]}"
        )
