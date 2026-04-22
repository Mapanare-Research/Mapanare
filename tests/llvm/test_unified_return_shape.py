"""v5.0.6 An.9 — regression gate for E1 unified-return optimization.

v4.145.0 E1 (`docs/roadmap/v4/v4.145.0/`) landed the unified-return-block
optimization for functions returning inline enums. It merges all return
points through a single result alloca so LLVM SROA + mem2reg can decompose
the intermediate `{i64,i64,i64}` aggregate PHI into scalar PHIs, enabling
the downstream SimplifyCFG pass to fold two dispatch switches into one
after inlining.

Until now, E1 was only integration-tested via the `enum_match` benchmark
checksum (`checksum = 52818168`). A regression that re-split the switch
would still produce the correct checksum but lose the perf win — silent
drift on the measurement that Anaconda v4.154.0 flagged as missing.

This module is the structural gate: assert the pre-optimization IR shape
that feeds E1 is still intact. Post-optimization shape would require
`opt` on PATH; when available we also verify the two-switch-to-one fold.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
ENUM_MATCH = ROOT / "benchmarks" / "system" / "enum_match.mn"


def _emit_enum_match_ir() -> str:
    """Compile enum_match.mn to LLVM IR text via the Python bootstrap emitter."""
    assert ENUM_MATCH.exists(), f"enum_match.mn missing: {ENUM_MATCH}"
    r = subprocess.run(
        [sys.executable, "-m", "mapanare", "emit-llvm", str(ENUM_MATCH)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0, f"emit-llvm failed: {r.stderr}"
    # `mapanare emit-llvm` writes to <source>.ll next to the source.
    ll_path = ENUM_MATCH.with_suffix(".ll")
    assert ll_path.exists(), f"expected {ll_path} to exist after emit"
    return ll_path.read_text(encoding="utf-8")


def _extract_function(ir: str, name: str) -> str:
    """Slice one `define ... @name(...) { ... }` body from the IR text.

    Aggregate types in the signature (e.g., `{i64, i64, i64}`) make naive
    brace-counting wrong — scan from the first `{` that starts a line,
    which by LLVM convention is the function body opener.
    """
    m = re.search(rf"^define\b[^\n]*\s@{re.escape(name)}\s*\([^\n]*$", ir, re.MULTILINE)
    assert m, f"function @{name} not found in emitted IR"
    # Advance past the signature line; the `{` at end of signature opens
    # the body. Use line-anchored `^}` to find the close.
    body_close = re.search(r"^\}\s*$", ir[m.end() :], re.MULTILINE)
    assert body_close, f"unterminated function body @{name}"
    return ir[m.start() : m.end() + body_close.end()]


def test_area_has_single_switch_pre_opt() -> None:
    """The enum-dispatch `area` function emits exactly one switch.

    This is the structural shape E1 relies on: one tag-switch feeding
    N arms, each with a single return. If a refactor reintroduces a
    secondary switch (e.g., split into "tag check" + "payload dispatch"),
    LLVM can no longer fold to one switch post-inlining and the E1 win
    is lost.
    """
    ir = _emit_enum_match_ir()
    area = _extract_function(ir, "area")
    switch_count = len(re.findall(r"^\s*switch\s+i64\s", area, re.MULTILINE))
    assert switch_count == 1, (
        f"@area should emit exactly one switch (E1 invariant), found "
        f"{switch_count}. Regression on v4.145.0 unified-return shape."
    )


def test_make_shape_uses_sret() -> None:
    """`make_shape` returns enum by sret pointer, not by value.

    E1's unification depends on `make_shape` being sret-style so the
    call site can be inlined into `area`'s caller without an intermediate
    aggregate PHI. Classified by v5.0.4 Cb.15 ABI classifier; this test
    is the user-visible gate.
    """
    ir = _emit_enum_match_ir()
    m = re.search(r"define\b[^\n]*@make_shape\s*\([^)]*\)", ir)
    assert m, "@make_shape not found in emitted IR"
    sig = m.group(0)
    assert "sret(" in sig, (
        f"@make_shape signature lost sret pointer — Rt.1/Cb.15 regression. "
        f"Signature was: {sig}"
    )


def test_post_opt_single_switch_in_hot_loop() -> None:
    """Post-`opt -O2` shape: after inlining, the hot loop contains one switch.

    Skipped when `opt` isn't on PATH (Windows dev boxes). When available,
    exercises the full E1 pipeline: structured pre-opt IR → SROA/mem2reg
    decompose aggregate PHIs → SimplifyCFG folds two switches into one.
    """
    opt = shutil.which("opt")
    if not opt:
        pytest.skip("llvm `opt` not on PATH")

    ir = _emit_enum_match_ir()
    r = subprocess.run(
        [opt, "-O2", "-S"],
        input=ir,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r.returncode == 0, f"opt failed: {r.stderr}"
    optimized = r.stdout

    # `main` is the hot loop. After inlining make_shape and area into it,
    # the body should contain a single switch (the merged dispatch).
    main_fn = _extract_function(optimized, "main")
    switch_count = len(re.findall(r"^\s*switch\s+i64\s", main_fn, re.MULTILINE))
    assert switch_count == 1, (
        f"@main hot loop has {switch_count} switches post-O2, expected 1. "
        f"E1 fold-two-switches-into-one regressed."
    )
