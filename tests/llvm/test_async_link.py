"""v5.26.0 Mb.7.D — IR invariant + link contract for the
try-operator / async surface.

Phase 0 audit (`docs/roadmap/v5/v5.26.0/AUDIT.md`) discovered
that the v5.23.1-era claim "9 LINK_FAIL goldens trip the i64/i1
tag-emit bug" was based on test_native.py harness output, which
compares Python-emitter IR against self-host IR rather than
running an actual link cycle. Re-running the link contract
showed:

  * **Goldens 55–59 (the async cluster)** never had the i64/i1
    bug — they don't use try-operator and don't take the
    `emit_enum_tag → Branch` codepath. They link cleanly both
    pre- and post-Mb.7.

  * **Golden 47** (`?` on Result) had the i64/i1 bug at
    `emit_enum_tag`'s output AND a separate bug in `emit_unwrap`
    that makes the linker reject the IR for an unrelated reason.
    Mb.7 closes the i64/i1 site (the bug pattern moves from line
    229 to line 235); full link still requires the v5.26.1 Unwrap
    fix.

  * **Goldens 48/49/51** have distinct bug classes (Result-literal
    insertvalue type mismatch / match-on-Int / or-pattern duplicate
    cases). Each needs its own Phase 0 investigation.

This module's regression contract therefore has three layers:

  1. **IR invariant** (the load-bearing test) — for golden 47, the
     emitted IR must not contain the
     `%X = zext i1 ... to i64` followed by `br i1 %X` anti-pattern
     in any function. This directly tests Mb.7's fix.

  2. **Async cluster link** — sanity guard that nothing in the
     async lowering path regresses; runs the full clang link/run
     cycle on goldens 55–59.

  3. **Deferred LINK_FAIL goldens** — 47/48/49/51 marked `xfail`
     with documented bug classes. A future fix flips them to
     `XPASS` (pytest fails the suite), forcing the author to
     remove the marker and update this doc.

Falsifiability round-trip (documented in v5.26.0 SESSION_REPORT):

  * Revert the fix in `mapanare/self/emit_llvm.mn::emit_enum_tag`
    → IR-invariant test on golden 47 FAILs (anti-pattern present
    twice — `do_work` and `do_work_fail`).
  * Re-apply the fix → IR-invariant test PASSes.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_DIR = REPO_ROOT / "tests" / "golden"
STAGE1 = REPO_ROOT / "mapanare" / "self" / "mnc-stage1"
RT_ARCHIVE = REPO_ROOT / "runtime" / "native" / "libmapanare_rt.a"

ASYNC_CLUSTER_GOLDENS = [55, 56, 57, 58, 59]

DEFERRED_GOLDENS = {
    47: "v5.26.1 Eu.1: closed — emit_unwrap on Result extracts inner "
    "aggregate then Ok payload (Python + self-host).",
    48: "v5.26.1 Eu.2: closed — Ok()/Err() lowerer defaults missing "
    "Result type args so wrap_ok/wrap_err's outer + inner widths agree.",
    49: "v5.26.1 Eu.3: closed — primitive subjects bypass EnumTag and "
    "use a sequential test cascade with literal re-checks at arm entry.",
    51: "v5.26.1 Eu.4: closed — switch cases dedup by tag, and or-pattern "
    "arms with literal-bearing alts emit a per-alt entry switch.",
}


def _resolve_golden(num: int) -> Path:
    matches = sorted(GOLDEN_DIR.glob(f"{num:02d}_*.mn"))
    preferred_keywords = ("async", "match", "try", "guards")
    for m in matches:
        if any(kw in m.name for kw in preferred_keywords):
            return m
    if matches:
        return matches[0]
    raise FileNotFoundError(f"no golden found for prefix {num:02d}_*.mn")


@pytest.fixture(scope="module")
def stage1_binary() -> Path:
    if not STAGE1.exists():
        pytest.skip(f"{STAGE1} not built; run `python3 scripts/build_stage1.py` first")
    return STAGE1


@pytest.fixture(scope="module")
def runtime_archive() -> Path:
    if not RT_ARCHIVE.exists():
        pytest.skip(f"{RT_ARCHIVE} not built; run `make build-rt` first")
    return RT_ARCHIVE


@pytest.fixture(scope="module")
def clang_bin() -> str:
    path = shutil.which("clang")
    if path is None:
        pytest.skip("clang not on PATH")
    return path


def _emit_ir(stage1_binary: Path, src: Path) -> str:
    emit = subprocess.run(
        [str(stage1_binary), "emit-llvm", str(src)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert emit.returncode == 0, f"mnc-stage1 emit-llvm failed: {emit.stderr}"
    return emit.stdout


def test_mb7_no_zext_then_br_i1_anti_pattern(stage1_binary: Path) -> None:
    """Mb.7 IR invariant — `emit_enum_tag` for try-operator on
    Result/Option must NOT emit the bug pattern:

        %X = zext i1 ... to i64
        br i1 %X, label %A, label %B

    Pre-fix this fired in `do_work` and `do_work_fail` of golden
    47. Post-fix the SSA value used by `br i1` is the i1
    extractvalue result directly, with no intervening zext.

    This is the load-bearing falsifiability gate for the Mb.7 fix.
    Reverting `mapanare/self/emit_llvm.mn::emit_enum_tag` to the
    pre-Mb.7 version makes this test fail.
    """
    src = _resolve_golden(47)
    ir = _emit_ir(stage1_binary, src)
    lines = ir.splitlines()
    # Build a map from SSA name to the line index where it's defined
    # via `zext i1 ... to i64`. Each consumer site that does
    # `br i1 %name` against such a name is a hit.
    zext_def = re.compile(r"^\s*(%\S+)\s*=\s*zext i1 \S+ to i64\s*$")
    br_use = re.compile(r"^\s*br i1 (%\S+)\s*,")
    zexted: set[str] = set()
    hits: list[tuple[int, str]] = []
    for ln, line in enumerate(lines, start=1):
        m_def = zext_def.match(line)
        if m_def:
            zexted.add(m_def.group(1))
            continue
        m_use = br_use.match(line)
        if m_use and m_use.group(1) in zexted:
            hits.append((ln, line.strip()))
    assert not hits, (
        "Mb.7 anti-pattern resurfaced — `br i1 %X` where %X was "
        "defined via `zext i1 ... to i64`. Sites:\n"
        + "\n".join(f"  line {ln}: {body}" for ln, body in hits)
        + "\n\nThe self-host `emit_enum_tag` is supposed to honor "
        "`dest.ty.kind == TK_BOOL` and emit the i1 extractvalue "
        "directly without zext for the try-op consumer."
    )


@pytest.mark.parametrize("golden_num", ASYNC_CLUSTER_GOLDENS)
def test_async_cluster_links_and_runs(
    golden_num: int,
    stage1_binary: Path,
    runtime_archive: Path,
    clang_bin: str,
    tmp_path: Path,
) -> None:
    """Sanity guard for the async lowering path. Goldens 55–59
    didn't have Mb.7's i64/i1 bug — they don't go through the
    `emit_enum_tag → Branch` codepath — but the v5.23.1-era
    SESSION_REPORT mistakenly grouped them with the LINK_FAIL
    cluster. Lock in the link contract so any future regression
    in async or coroutine codegen surfaces here, not in the
    publish job.
    """
    src = _resolve_golden(golden_num)
    ll_path = tmp_path / f"{golden_num}.ll"
    bin_path = tmp_path / f"{golden_num}"

    ll_path.write_text(_emit_ir(stage1_binary, src))

    link = subprocess.run(
        [
            clang_bin,
            str(ll_path),
            str(runtime_archive),
            "-lm",
            "-lpthread",
            "-ldl",
            "-o",
            str(bin_path),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert link.returncode == 0, (
        f"clang link failed for golden {golden_num} ({src.name}):\n"
        f"--- stderr ---\n{link.stderr}"
    )

    run = subprocess.run(
        [str(bin_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert run.returncode == 0, (
        f"binary for golden {golden_num} ({src.name}) exited "
        f"{run.returncode}\nstdout:\n{run.stdout}\nstderr:\n{run.stderr}"
    )


@pytest.mark.parametrize(
    "golden_num,reason",
    sorted(DEFERRED_GOLDENS.items()),
)
def test_deferred_link_failures(
    golden_num: int,
    reason: str,
    stage1_binary: Path,
    runtime_archive: Path,
    clang_bin: str,
    tmp_path: Path,
) -> None:
    """v5.26.1 Eu.* — formerly xfail link contracts for the four
    distinct bug classes surfaced by v5.26.0 Phase 0 audit. All four
    closed at v5.26.1 HEAD (Eu.1 emit_unwrap, Eu.2 Result-literal
    args, Eu.3 match-on-Int, Eu.4 or-pattern + guards). Now a regular
    link contract — these golden programs must compile, link cleanly
    against the runtime archive, and exit 0.
    """
    src = _resolve_golden(golden_num)
    ll_path = tmp_path / f"{golden_num}.ll"
    bin_path = tmp_path / f"{golden_num}"
    ll_path.write_text(_emit_ir(stage1_binary, src))
    link = subprocess.run(
        [
            clang_bin,
            str(ll_path),
            str(runtime_archive),
            "-lm",
            "-lpthread",
            "-ldl",
            "-o",
            str(bin_path),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert link.returncode == 0, (
        f"clang link failed for golden {golden_num} ({src.name}):\n"
        f"--- stderr ---\n{link.stderr}\n"
        f"reason context: {reason}"
    )
    run = subprocess.run(
        [str(bin_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert run.returncode == 0, (
        f"binary for golden {golden_num} ({src.name}) exited "
        f"{run.returncode}\nstdout:\n{run.stdout}\nstderr:\n{run.stderr}"
    )
