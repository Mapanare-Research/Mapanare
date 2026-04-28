#!/usr/bin/env python3
"""v4.127.0 — Divergence measurement harness.

Compiles each passing golden test through both the Python bootstrap and the
self-hosted ``mnc-stage1``, then reports:

  - Total line-diff count (summed across all passing goldens)
  - Function-count divergence per test
  - Classification samples across five categories:
      L (label / temp names)
      C (constants — order / formatting)
      A (attributes — different function / parameter attrs)
      S (semantic — genuinely different codegen)
      W (whitespace / formatting)
      M (module metadata — header lines only)

The fixed-point verification script ``verify_fixed_point.sh`` cannot run
end-to-end because self-hosted ``semantic.mn`` does not register ``None``
as a constructor (docket Sh.8). This script measures the meaningful
proxy: divergence between the Python reference pipeline and the
self-hosted pipeline on programs both can compile.

Usage:
    python3 scripts/measure_divergence.py [--json out.json]
"""

from __future__ import annotations

import argparse
import difflib
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOLDEN_DIR = ROOT / "tests" / "golden"
STAGE1 = ROOT / "mapanare" / "self" / "mnc-stage1"


def compile_bootstrap(mn_file: pathlib.Path) -> tuple[str, str]:
    try:
        from mapanare.cli import _compile_to_llvm_ir

        ir = _compile_to_llvm_ir(mn_file.read_text(encoding="utf-8"), str(mn_file))
        return ir, ""
    except Exception as e:  # pragma: no cover
        return "", str(e)


def compile_stage1(mn_file: pathlib.Path) -> tuple[str, str]:
    try:
        result = subprocess.run(
            [str(STAGE1), "emit-llvm", str(mn_file)], capture_output=True, timeout=30
        )
        if result.returncode != 0:
            return "", result.stderr.decode(errors="replace") or f"exit {result.returncode}"
        return result.stdout.decode(errors="replace"), ""
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT"


_DEF_RE = re.compile(r"^define\s+.*?@([\w.]+)\(", re.MULTILINE)
_DECL_RE = re.compile(r"^declare\s+.*?@([\w.]+)\(", re.MULTILINE)


def fn_set(ir: str) -> set[str]:
    return set(_DEF_RE.findall(ir))


def decl_set(ir: str) -> set[str]:
    return set(_DECL_RE.findall(ir))


# Classification heuristics. Each takes a (removed, added) pair from a diff
# block and returns either a category letter or None. Checked in order; the
# first matching category wins.

_LABEL_RE = re.compile(r"%\w+\.\d+|%\d+|^[A-Za-z_][\w.]*:$")
_RUNTIME_DECL_RE = re.compile(r"declare .*?@__mn_\w+")


def classify(removed: list[str], added: list[str]) -> str:
    """Classify a diff block into one of: L, C, A, S, W, M.

    Heuristic, not a proof. The goal is bucket sizes, not per-line precision.
    """
    blob_r = "\n".join(removed)
    blob_a = "\n".join(added)

    # Module metadata (header): ModuleID, source_filename, target datalayout/triple.
    if any(
        s in blob_r or s in blob_a
        for s in ("ModuleID =", "source_filename =", "target datalayout", "target triple")
    ):
        return "M"

    # Runtime declaration density: self-hosted emits all, bootstrap emits
    # only those used. Classify as S (semantic) since this is a codegen
    # choice, not a cosmetic formatting issue.
    if _RUNTIME_DECL_RE.search(blob_r) or _RUNTIME_DECL_RE.search(blob_a):
        return "S"

    # Attribute differences (e.g., `nounwind willreturn` vs `#0 { ... }`).
    attr_tokens = ("nounwind", "willreturn", "readonly", "noalias", "norecurse", "inlinehint")
    r_attrs = sum(tok in blob_r for tok in attr_tokens)
    a_attrs = sum(tok in blob_a for tok in attr_tokens)
    if r_attrs != a_attrs:
        return "A"

    # Whitespace-only (counting structural spaces inside braces).
    if blob_r.replace(" ", "") == blob_a.replace(" ", ""):
        return "W"

    # Constant literal order / format. Look for @.global_* or private constant.
    has_const = (
        "private constant" in blob_r
        or "private constant" in blob_a
        or "@.fmt_" in blob_r
        or "@.fmt_" in blob_a
    )
    if has_const:
        return "C"

    # Label / temp naming: if the line structure matches after replacing
    # every `%name.N` with `%X`, it's a label-only difference.
    norm_r = re.sub(r"%[\w.]+|\b[bs]b\d+\b|\bbb\d+\b|L\d+|\.\d+", "%X", blob_r)
    norm_a = re.sub(r"%[\w.]+|\b[bs]b\d+\b|\bbb\d+\b|L\d+|\.\d+", "%X", blob_a)
    if norm_r == norm_a:
        return "L"

    # Everything else is semantic.
    return "S"


def bucket_diff(bootstrap_ir: str, stage1_ir: str) -> dict[str, int]:
    """Run unified diff and classify each hunk."""
    buckets = {"L": 0, "C": 0, "A": 0, "S": 0, "W": 0, "M": 0}
    b_lines = bootstrap_ir.splitlines()
    s_lines = stage1_ir.splitlines()

    matcher = difflib.SequenceMatcher(None, b_lines, s_lines, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        removed = b_lines[i1:i2]
        added = s_lines[j1:j2]
        cat = classify(removed, added)
        buckets[cat] += max(len(removed), len(added))
    return buckets


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=pathlib.Path, default=None)
    args = ap.parse_args()

    if not STAGE1.exists():
        print(f"ERR: {STAGE1} not found; run `python3 scripts/build_stage1.py`", file=sys.stderr)
        return 1

    results = []
    golden_files = sorted(GOLDEN_DIR.glob("*.mn"))
    total_buckets = {"L": 0, "C": 0, "A": 0, "S": 0, "W": 0, "M": 0}
    total_lines_diff = 0
    total_bootstrap_lines = 0
    total_stage1_lines = 0
    passing_goldens = 0
    fn_divergent = 0

    for mn in golden_files:
        b_ir, b_err = compile_bootstrap(mn)
        if b_err:
            continue
        s_ir, s_err = compile_stage1(mn)
        if s_err or not s_ir.strip():
            continue

        passing_goldens += 1
        b_lines = b_ir.count("\n") + 1
        s_lines = s_ir.count("\n") + 1
        total_bootstrap_lines += b_lines
        total_stage1_lines += s_lines

        b_fns = fn_set(b_ir)
        s_fns = fn_set(s_ir)
        if b_fns != s_fns:
            fn_divergent += 1

        diff_lines = sum(
            1 for _ in difflib.unified_diff(b_ir.splitlines(), s_ir.splitlines(), lineterm="")
        )
        total_lines_diff += diff_lines

        buckets = bucket_diff(b_ir, s_ir)
        for k, v in buckets.items():
            total_buckets[k] += v

        results.append(
            {
                "name": mn.stem,
                "bootstrap_lines": b_lines,
                "stage1_lines": s_lines,
                "bootstrap_fns": len(b_fns),
                "stage1_fns": len(s_fns),
                "bootstrap_decls": len(decl_set(b_ir)),
                "stage1_decls": len(decl_set(s_ir)),
                "diff_lines": diff_lines,
                "missing_fns": sorted(b_fns - s_fns),
                "extra_fns": sorted(s_fns - b_fns),
                "buckets": buckets,
            }
        )

    summary = {
        "passing_goldens": passing_goldens,
        "total_bootstrap_lines": total_bootstrap_lines,
        "total_stage1_lines": total_stage1_lines,
        "total_diff_lines": total_lines_diff,
        "fn_divergent_count": fn_divergent,
        "category_totals": total_buckets,
        "per_test": results,
    }

    print(f"passing goldens:          {passing_goldens}")
    print(f"total bootstrap lines:    {total_bootstrap_lines:,}")
    print(f"total stage1 lines:       {total_stage1_lines:,}")
    print(f"total diff lines:         {total_lines_diff:,}")
    print(f"fn-set divergent tests:   {fn_divergent}")
    print("category totals (diff lines assigned):")
    for k in ("S", "M", "C", "A", "W", "L"):
        print(f"  {k}: {total_buckets[k]:,}")
    ordered = sorted(total_buckets.items(), key=lambda kv: -kv[1])
    print(f"top 3 categories: {', '.join(k for k, _ in ordered[:3])}")

    if args.json:
        args.json.write_text(json.dumps(summary, indent=2))
        print(f"wrote {args.json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
