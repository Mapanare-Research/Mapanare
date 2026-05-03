"""v5.35.0 Sq.0 (formerly Tn.1) — link-and-run gate for all 95 goldens.

Closes the v5.28.0 RE-PANEL convergent recommendation (Cobra Cb.New1
+ Rattler Ra.Inf1, independent reviewers, same finding shape) that
had carried forward 6 releases (v5.29.0 → v5.34.0) and was named as
DEADLINE at v5.35.0 in the v5.33.0 escalation directive.

Generalizes the link-and-run pattern from test_async_link.py from 10
goldens (the async cluster 55-59 plus the 4 v5.26.1 Eu.* deferred
bug-class goldens 47/48/49/51) to all 95 goldens.

The structural test gap this closes:

  * Prior to Sq.0, the only link-and-run regression coverage on
    goldens was the 10 in test_async_link.py. The other 85 goldens
    were validated only by test_native.py, which compares Python-
    emitter IR against self-host IR.

  * That harness catches divergence between the two emitters but
    cannot catch IR shapes that are emitted identically by both
    emitters yet fail to link or run. Eu.1..Eu.4 were exactly that
    bug class: golden 47/48/49/51 IR was identical between emitters
    but produced LLVM IR that clang refused to lower or that crashed
    at runtime. Each bug hid for 3 releases (v5.23.1 → v5.26.0
    Phase-0 audit) before surfacing.

Falsifiability round-trip: revert any of the v5.26.1 Eu.* fixes (or
the v5.26.0 Mb.7 i64/i1 tag-emit fix that golden 47 also depends on)
and the corresponding parametrized case here fails with the same
shape as test_async_link.py::test_deferred_link_failures pre-v5.26.1.

Run cost: ~95 sequential emit/link/run cycles per worker. pytest
-n auto parallelizes by golden (each gets its own tmp_path), so
total wall time scales as 95 / num_workers. Module-scoped fixtures
ensure stage1 + runtime archive + clang are each resolved exactly
once per worker, not once per case.

Overlap with existing tests is intentional: test_async_link.py's
ASYNC_CLUSTER_GOLDENS (55-59) and DEFERRED_GOLDENS (47/48/49/51)
will also run here. The duplicate cost is small (~0.5s × 9 cases)
and the duplicate coverage is load-bearing — test_async_link.py
contains the v5.26.0 Mb.7 IR-invariant gate (the
test_mb7_no_zext_then_br_i1_anti_pattern test), which cannot
generalize cleanly to all 95 goldens because most don't exercise
the try-operator codepath. Keeping both files separates the
"specific bug-class IR-shape gates" (test_async_link.py) from the
"every golden links and runs" gate (this file).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_DIR = REPO_ROOT / "tests" / "golden"
STAGE1 = REPO_ROOT / "mapanare" / "self" / "mnc-stage1"
RT_ARCHIVE = REPO_ROOT / "runtime" / "native" / "libmapanare_rt.a"


def _all_goldens() -> list[Path]:
    """Discover every numbered golden in tests/golden/.

    The glob pattern `[0-9][0-9]_*.mn` matches the 95-file numbered
    corpus and excludes any non-numbered helpers (e.g. `.ref.ll`
    reference files, README, BENCHMARKS).
    """
    return sorted(GOLDEN_DIR.glob("[0-9][0-9]_*.mn"))


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
    assert emit.returncode == 0, (
        f"mnc-stage1 emit-llvm failed for {src.name}:\n" f"--- stderr ---\n{emit.stderr}"
    )
    return emit.stdout


def test_golden_corpus_count() -> None:
    """The 95-golden corpus is itself a load-bearing claim.

    The CLAUDE.md release-notes line, the BENCHMARKS.md table, and
    the v5.34.0 SESSION_REPORT all assert "Goldens 95/95". If a
    golden is added or removed without coordinating that change with
    the docs, this gate fires and forces the documentation to stay
    in sync.
    """
    goldens = _all_goldens()
    assert len(goldens) == 95, (
        f"Golden corpus drifted from 95 to {len(goldens)}. Update "
        f"this test, BENCHMARKS.md, the CLAUDE.md release-notes "
        f"entry, and the most recent SESSION_REPORT."
    )


@pytest.mark.parametrize(
    "golden",
    _all_goldens(),
    ids=lambda p: p.stem,
)
def test_link_and_run(
    golden: Path,
    stage1_binary: Path,
    runtime_archive: Path,
    clang_bin: str,
    tmp_path: Path,
) -> None:
    """Every golden must:
       (1) emit IR cleanly through mnc-stage1,
       (2) link against runtime/native/libmapanare_rt.a via clang,
       (3) run to completion with exit code 0.

    No stdout/stderr comparison — that's test_native.py's job. This
    test is exclusively about the link contract and runtime
    well-formedness.
    """
    ll_path = tmp_path / f"{golden.stem}.ll"
    bin_path = tmp_path / golden.stem

    ll_path.write_text(_emit_ir(stage1_binary, golden))

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
        f"clang link failed for {golden.name}:\n" f"--- stderr ---\n{link.stderr}"
    )

    run = subprocess.run(
        [str(bin_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert run.returncode == 0, (
        f"binary for {golden.name} exited {run.returncode}\n"
        f"stdout:\n{run.stdout}\n"
        f"stderr:\n{run.stderr}"
    )
