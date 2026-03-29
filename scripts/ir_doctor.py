#!/usr/bin/env python3
"""IR Doctor — per-function diagnostic tool for the Mapanare self-hosted compiler.

Compares LLVM IR from the Python bootstrap vs mnc-stage1 at function granularity.
Detects known bug patterns, structural divergences, and generates actionable reports.

Usage:
    # Audit a single IR file for known pathologies
    python scripts/ir_doctor.py audit mapanare/self/main.ll

    # Compare bootstrap vs stage1 output for a golden test
    python scripts/ir_doctor.py diff tests/golden/07_enum_match.mn

    # Compare bootstrap vs stage1 for ALL golden tests
    python scripts/ir_doctor.py diff-all

    # Compare bootstrap vs stage1 for the full self-hosted compiler
    python scripts/ir_doctor.py diff-self

    # Dump per-function fingerprints as JSON (for external tools)
    python scripts/ir_doctor.py fingerprint mapanare/self/main.ll

    # Show function-level metrics table
    python scripts/ir_doctor.py table mapanare/self/main.ll

Options:
    --stage1 PATH    Path to mnc-stage1 binary (default: mapanare/self/mnc-stage1)
    --verbose / -v   Show per-instruction diffs for divergent functions
    --json           Output as JSON instead of human-readable
    --only NAME      Only analyze function NAME (substring match)
    --top N          Show top N largest/most complex functions (default: all)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from dataclasses import asdict, dataclass, field

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOLDEN_DIR = ROOT / "tests" / "golden"


# ---------------------------------------------------------------------------
# IR Parsing — extract individual functions from LLVM IR text
# ---------------------------------------------------------------------------

_FN_RE = re.compile(
    r"^(define\s+(?:internal\s+)?(?:dso_local\s+)?"
    r"(?:[\w{}<>*,%\s]+?)\s+"
    r'@"?([^"(\s]+)"?\s*\(.*?\))'
    r"(?:\s*#\d+)?\s*\{",
    re.MULTILINE,
)


@dataclass
class IRFunction:
    name: str
    signature: str
    body: str  # everything between { and }
    line_start: int
    line_end: int

    # structural metrics
    instructions: int = 0
    basic_blocks: int = 0
    allocas: int = 0
    stores: int = 0
    loads: int = 0
    calls: int = 0
    switches: int = 0
    phis: int = 0
    branches: int = 0
    rets: int = 0
    geps: int = 0
    list_pushes: int = 0
    list_news: int = 0
    str_eqs: int = 0
    insertvalues: int = 0
    extractvalues: int = 0
    alloca_bytes: int = 0

    # derived
    body_hash: str = ""  # structural hash (ignoring register names)


@dataclass
class IRModule:
    """Parsed LLVM IR module."""

    source: str  # original text
    functions: dict[str, IRFunction] = field(default_factory=dict)
    declares: list[str] = field(default_factory=list)
    globals: list[str] = field(default_factory=list)
    struct_types: list[str] = field(default_factory=list)


def _estimate_type_size(ty: str) -> int:
    if ty.startswith("i1"):
        return 1
    if ty.startswith("i8") and not ty.startswith("i8*"):
        return 1
    if ty.startswith("i32"):
        return 4
    if ty.startswith("i64") or ty == "double" or ty.endswith("*"):
        return 8
    if ty == "float":
        return 4
    if ty.startswith("{"):
        return (ty.count(",") + 1) * 8
    arr = re.match(r"\[(\d+)\s*x\s*(.+)\]", ty)
    if arr:
        return int(arr.group(1)) * _estimate_type_size(arr.group(2).strip())
    return 8


def _structural_hash(body: str) -> str:
    """Hash the function body ignoring register numbers.

    Normalizes %name.123 → %R, @.str.456 → @S, label names → L.
    This way two functions that do the same thing but with different
    register numbering will hash the same.
    """
    # Normalize SSA register names: %foo.123 → %R
    norm = re.sub(r"%[a-zA-Z_][\w.]*", "%R", body)
    # Normalize string globals: @.str.123 → @S
    norm = re.sub(r"@\.str\.\d+", "@S", norm)
    # Normalize labels: label %name123 → label %L
    norm = re.sub(r"label\s+%[\w.]+", "label %L", norm)
    # Normalize block labels at start of line: foo123: → L:
    norm = re.sub(r"^[\w.]+:", "L:", norm, flags=re.MULTILINE)
    # Strip whitespace variance
    norm = "\n".join(line.strip() for line in norm.splitlines() if line.strip())
    return hashlib.sha256(norm.encode()).hexdigest()[:16]


def _analyze_function(fn: IRFunction) -> None:
    """Populate structural metrics from body text."""
    body = fn.body
    fn.instructions = len([l for l in body.splitlines() if l.strip() and not l.strip().endswith(":")])
    fn.basic_blocks = len(re.findall(r"^\w[\w.]*:", body, re.MULTILINE)) + 1  # +1 for entry
    fn.allocas = body.count("= alloca ")
    fn.stores = body.count("store ")
    fn.loads = body.count("= load ")
    fn.calls = len(re.findall(r"(?:= )?call ", body))
    fn.switches = len(re.findall(r"switch\s+i64", body))
    fn.phis = body.count(" = phi ")
    fn.branches = body.count("br ")
    fn.rets = len(re.findall(r"^\s*ret\s", body, re.MULTILINE))
    fn.geps = body.count("getelementptr")
    fn.list_pushes = body.count("@__mn_list_push")
    fn.list_news = body.count("@__mn_list_new")
    fn.str_eqs = body.count("@__mn_str_eq")
    fn.insertvalues = body.count("insertvalue")
    fn.extractvalues = body.count("extractvalue")
    # alloca bytes
    fn.alloca_bytes = 0
    for m in re.finditer(r"=\s*alloca\s+(.+?)(?:\s*,|\s*$)", body, re.MULTILINE):
        fn.alloca_bytes += _estimate_type_size(m.group(1).strip())
    fn.body_hash = _structural_hash(body)


def parse_ir(text: str) -> IRModule:
    """Parse LLVM IR text into an IRModule with per-function data."""
    mod = IRModule(source=text)

    # Extract struct types
    for m in re.finditer(r"^(%[\w.]+)\s*=\s*type\s+(\{.+\})", text, re.MULTILINE):
        mod.struct_types.append(m.group(0))

    # Extract declares
    for m in re.finditer(r"^declare\s+.+", text, re.MULTILINE):
        mod.declares.append(m.group(0))

    # Extract globals
    for m in re.finditer(r"^@[\w.]+\s*=\s*(?:private|internal)?\s*(?:unnamed_addr\s+)?(?:constant|global)\s+.+", text, re.MULTILINE):
        mod.globals.append(m.group(0))

    # Extract functions — find matching braces
    for m in _FN_RE.finditer(text):
        fn_name = m.group(2)
        sig = m.group(1)
        start = m.end()  # position after the opening {
        depth = 1
        pos = start
        while pos < len(text) and depth > 0:
            if text[pos] == "{":
                depth += 1
            elif text[pos] == "}":
                depth -= 1
            pos += 1
        body = text[start : pos - 1]
        line_start = text[:m.start()].count("\n") + 1
        line_end = text[:pos].count("\n") + 1

        fn = IRFunction(
            name=fn_name,
            signature=sig,
            body=body,
            line_start=line_start,
            line_end=line_end,
        )
        _analyze_function(fn)
        mod.functions[fn_name] = fn

    return mod


# ---------------------------------------------------------------------------
# Known pathology detectors
# ---------------------------------------------------------------------------


@dataclass
class Pathology:
    severity: str  # "error", "warning", "info"
    code: str  # machine-readable code like "ALLOCA_ALIAS"
    function: str
    line: int  # approximate
    message: str
    detail: str = ""


def detect_alloca_aliasing(mod: IRModule) -> list[Pathology]:
    """Detect the for-loop alloca aliasing bug.

    Pattern: __mn_list_push writes to alloca %A, but a later
    __mn_list_len reads from a DIFFERENT alloca %B for the same variable.
    """
    results = []
    for fn in mod.functions.values():
        if fn.list_pushes == 0:
            continue

        # Find all allocas that are targets of list_push
        push_targets: set[str] = set()
        for m in re.finditer(
            r"call void @__mn_list_push\(\{i8\*, i64, i64, i64\}\*\s+(%[\w.]+)",
            fn.body,
        ):
            push_targets.add(m.group(1))

        # Find all allocas that are sources for list_len
        len_sources: set[str] = set()
        for m in re.finditer(
            r"call i64 @__mn_list_len\(\{i8\*, i64, i64, i64\}\*\s+(%[\w.]+)",
            fn.body,
        ):
            len_sources.add(m.group(1))

        # If push and len use different allocas, flag it
        if push_targets and len_sources and not push_targets & len_sources:
            results.append(
                Pathology(
                    severity="error",
                    code="ALLOCA_ALIAS",
                    function=fn.name,
                    line=fn.line_start,
                    message=f"List push/len use different allocas: push->{push_targets}, len->{len_sources}",
                    detail=(
                        "The for-loop body pushes to one alloca but post-loop len() "
                        "reads from a stale pre-entry alloca. This is the known "
                        "emit_llvm_text.py scoping bug."
                    ),
                )
            )
    return results


def detect_empty_switches(mod: IRModule) -> list[Pathology]:
    """Detect switch statements with no cases (empty match)."""
    results = []
    for fn in mod.functions.values():
        for m in re.finditer(
            r"switch\s+i64\s+%[\w.]+,\s*label\s+%[\w.]+\s*\[\s*\]",
            fn.body,
        ):
            results.append(
                Pathology(
                    severity="error",
                    code="EMPTY_SWITCH",
                    function=fn.name,
                    line=fn.line_start,
                    message="Switch with 0 cases — match arms not generated",
                    detail=(
                        "All match arms fell through to default. Likely the "
                        "alloca aliasing bug: cases.push() wrote to a loop-local "
                        "alloca, but len(cases) read from the pre-entry alloca."
                    ),
                )
            )
    return results


def detect_empty_branch_labels(mod: IRModule) -> list[Pathology]:
    """Detect br label % (empty label name) — symptom of empty switch."""
    results = []
    for fn in mod.functions.values():
        for m in re.finditer(r"br\s+label\s+%\s*$", fn.body, re.MULTILINE):
            results.append(
                Pathology(
                    severity="error",
                    code="EMPTY_LABEL",
                    function=fn.name,
                    line=fn.line_start,
                    message="Branch to empty label (br label %) — broken match",
                )
            )
    return results


def detect_type_mismatch_ret(mod: IRModule) -> list[Pathology]:
    """Detect ret type != function return type."""
    results = []
    for fn in mod.functions.values():
        # Extract declared return type from signature
        sig_match = re.match(r"define\s+(?:internal\s+)?(?:dso_local\s+)?(.+?)\s+@", fn.signature)
        if not sig_match:
            continue
        declared_ret = sig_match.group(1).strip()
        if declared_ret == "void":
            continue

        # Find ret instructions with different types
        for m in re.finditer(r"^\s*ret\s+(\S+)\s+", fn.body, re.MULTILINE):
            ret_ty = m.group(1)
            if ret_ty != declared_ret and ret_ty != "void":
                results.append(
                    Pathology(
                        severity="error",
                        code="RET_TYPE_MISMATCH",
                        function=fn.name,
                        line=fn.line_start,
                        message=f"ret {ret_ty} but function declares {declared_ret}",
                        detail=(
                            "Likely the is_comparison_op bug: all binops classified "
                            "as comparisons (returning i1) due to match fallthrough."
                        ),
                    )
                )
                break  # one per function is enough
    return results


def detect_missing_percent(mod: IRModule) -> list[Pathology]:
    """Detect SSA names without % prefix in insertvalue/store/load."""
    results = []
    for fn in mod.functions.values():
        # insertvalue with bare name: "t.f0 =insertvalue" or "t.new ="
        for m in re.finditer(r"^\s+([a-zA-Z]\w*\.\w+)\s*=\s*(?:insertvalue|call|load)", fn.body, re.MULTILINE):
            name = m.group(1)
            if not name.startswith("%"):
                results.append(
                    Pathology(
                        severity="error",
                        code="MISSING_PERCENT",
                        function=fn.name,
                        line=fn.line_start,
                        message=f"SSA name '{name}' missing % prefix",
                        detail="strip_percent() was applied to an SSA name in struct/list init.",
                    )
                )
    return results


def detect_unreachable_blocks(mod: IRModule) -> list[Pathology]:
    """Detect basic blocks that are never branched to."""
    results = []
    for fn in mod.functions.values():
        if fn.basic_blocks <= 2:
            continue
        # Find all block labels defined
        defined = set(re.findall(r"^([\w.]+):", fn.body, re.MULTILINE))
        # Find all labels branched to
        referenced = set(re.findall(r"label\s+%([\w.]+)", fn.body))
        # switch case targets
        referenced |= set(re.findall(r"label\s+%([\w.]+)", fn.body))
        unreachable = defined - referenced - {"entry", "pre_entry"}
        if len(unreachable) > 3:  # small number is normal (fallthrough)
            results.append(
                Pathology(
                    severity="warning",
                    code="UNREACHABLE_BLOCKS",
                    function=fn.name,
                    line=fn.line_start,
                    message=f"{len(unreachable)} unreachable blocks: {sorted(unreachable)[:5]}...",
                )
            )
    return results


ALL_DETECTORS = [
    detect_alloca_aliasing,
    detect_empty_switches,
    detect_empty_branch_labels,
    detect_type_mismatch_ret,
    detect_missing_percent,
    detect_unreachable_blocks,
]


def run_audit(mod: IRModule) -> list[Pathology]:
    """Run all pathology detectors on a module."""
    results = []
    for detector in ALL_DETECTORS:
        results.extend(detector(mod))
    results.sort(key=lambda p: ({"error": 0, "warning": 1, "info": 2}[p.severity], p.function))
    return results


# ---------------------------------------------------------------------------
# Function-level diff between two IR modules
# ---------------------------------------------------------------------------


@dataclass
class FnDiff:
    name: str
    status: str  # "match", "diverged", "missing_a", "missing_b"
    hash_a: str = ""
    hash_b: str = ""
    metric_diffs: dict[str, tuple[int, int]] = field(default_factory=dict)
    detail: str = ""


def diff_modules(a: IRModule, b: IRModule) -> list[FnDiff]:
    """Compare two IR modules function-by-function."""
    all_names = sorted(set(a.functions) | set(b.functions))
    diffs = []
    for name in all_names:
        fa = a.functions.get(name)
        fb = b.functions.get(name)
        if fa and not fb:
            diffs.append(FnDiff(name=name, status="missing_b", hash_a=fa.body_hash))
            continue
        if fb and not fa:
            diffs.append(FnDiff(name=name, status="missing_a", hash_b=fb.body_hash))
            continue
        assert fa and fb

        if fa.body_hash == fb.body_hash:
            diffs.append(FnDiff(name=name, status="match", hash_a=fa.body_hash, hash_b=fb.body_hash))
            continue

        # Diverged — find which metrics differ
        metrics = {}
        for attr in (
            "instructions", "basic_blocks", "allocas", "stores", "loads",
            "calls", "switches", "phis", "branches", "rets", "geps",
            "list_pushes", "list_news", "str_eqs", "insertvalues",
            "extractvalues", "alloca_bytes",
        ):
            va = getattr(fa, attr)
            vb = getattr(fb, attr)
            if va != vb:
                metrics[attr] = (va, vb)

        detail = ""
        # Highlight critical divergences
        if fa.switches != fb.switches:
            detail += f"  SWITCHES: {fa.switches} vs {fb.switches}\n"
        if fa.allocas != fb.allocas:
            detail += f"  ALLOCAS: {fa.allocas} vs {fb.allocas}\n"
        if fa.list_pushes != fb.list_pushes:
            detail += f"  LIST_PUSH: {fa.list_pushes} vs {fb.list_pushes}\n"

        diffs.append(FnDiff(
            name=name,
            status="diverged",
            hash_a=fa.body_hash,
            hash_b=fb.body_hash,
            metric_diffs=metrics,
            detail=detail,
        ))
    return diffs


# ---------------------------------------------------------------------------
# IR generation helpers
# ---------------------------------------------------------------------------


def bootstrap_compile(mn_path: str | pathlib.Path) -> str:
    """Compile a .mn file via the Python bootstrap, return LLVM IR text."""
    mn_path = pathlib.Path(mn_path)
    source = mn_path.read_text(encoding="utf-8")
    # Use the multi-module compiler for self-hosted sources
    if "import self::" in source or str(mn_path).endswith("mnc_all.mn"):
        from mapanare.multi_module import compile_multi_module_mir
        return compile_multi_module_mir(source, str(mn_path), opt_level=2, emitter_backend="text")
    else:
        # Use the CLI-level compile path which handles all wiring
        with tempfile.NamedTemporaryFile(suffix=".ll", delete=False, mode="w") as f:
            out_path = f.name
        try:
            r = subprocess.run(
                [sys.executable, "-m", "mapanare", "emit-llvm", str(mn_path),
                 "--emitter", "text", "-o", out_path],
                capture_output=True, text=True, timeout=120,
            )
            if r.returncode != 0:
                raise RuntimeError(f"Bootstrap emit-llvm failed: {r.stderr[:500]}")
            return pathlib.Path(out_path).read_text(encoding="utf-8")
        finally:
            pathlib.Path(out_path).unlink(missing_ok=True)


def stage1_compile(mn_path: str | pathlib.Path, stage1_bin: str | pathlib.Path) -> str | None:
    """Compile a .mn file via mnc-stage1, return LLVM IR text or None on failure.

    Also checks for pre-generated .ll files next to the .mn file (for cross-platform use).
    """
    mn_path = pathlib.Path(mn_path)

    # Check for pre-generated stage1 IR file: tests/golden/03_function.stage1.ll
    stage1_ll = mn_path.with_suffix(".stage1.ll")
    if stage1_ll.exists():
        return stage1_ll.read_text(encoding="utf-8")

    try:
        r = subprocess.run(
            [str(stage1_bin), str(mn_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if r.returncode != 0:
            return None
        return r.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _severity_icon(s: str) -> str:
    return {"error": "ERR", "warning": "WRN", "info": "INF"}.get(s, "???")


# Ensure stdout handles unicode on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def format_audit(pathologies: list[Pathology], mod: IRModule) -> str:
    """Human-readable audit report."""
    lines = []
    lines.append(f"IR Doctor Audit — {len(mod.functions)} functions, "
                 f"{sum(f.instructions for f in mod.functions.values())} instructions")
    lines.append("=" * 72)

    if not pathologies:
        lines.append("No pathologies detected.")
        return "\n".join(lines)

    by_code: dict[str, list[Pathology]] = defaultdict(list)
    for p in pathologies:
        by_code[p.code].append(p)

    lines.append(f"\n{len(pathologies)} issues found:\n")
    for code, ps in sorted(by_code.items()):
        sev = ps[0].severity
        lines.append(f"  [{_severity_icon(sev)}] {code} ({len(ps)}x)")
        for p in ps[:10]:
            lines.append(f"        {p.function}: {p.message}")
            if p.detail:
                lines.append(f"          ^ {p.detail}")
        if len(ps) > 10:
            lines.append(f"        ... and {len(ps) - 10} more")
    return "\n".join(lines)


def format_diff(diffs: list[FnDiff], label_a: str = "bootstrap", label_b: str = "stage1") -> str:
    """Human-readable diff report."""
    lines = []
    matched = [d for d in diffs if d.status == "match"]
    diverged = [d for d in diffs if d.status == "diverged"]
    missing_a = [d for d in diffs if d.status == "missing_a"]
    missing_b = [d for d in diffs if d.status == "missing_b"]

    total = len(diffs)
    lines.append(f"IR Doctor Diff — {label_a} vs {label_b}")
    lines.append("=" * 72)
    lines.append(f"  Functions: {total}")
    lines.append(f"  Match:     {len(matched)}/{total} ({100*len(matched)//max(total,1)}%)")
    lines.append(f"  Diverged:  {len(diverged)}")
    lines.append(f"  Only in {label_a}: {len(missing_b)}")
    lines.append(f"  Only in {label_b}: {len(missing_a)}")

    if diverged:
        lines.append(f"\nDiverged functions ({len(diverged)}):")
        lines.append("-" * 72)
        for d in diverged:
            lines.append(f"  {d.name}  [{d.hash_a} vs {d.hash_b}]")
            if d.metric_diffs:
                for metric, (va, vb) in sorted(d.metric_diffs.items()):
                    delta = vb - va
                    sign = "+" if delta > 0 else ""
                    lines.append(f"    {metric:20s}: {va:>5} -> {vb:>5} ({sign}{delta})")
            if d.detail:
                for dl in d.detail.strip().splitlines():
                    lines.append(f"    {dl}")

    if missing_b:
        lines.append(f"\nOnly in {label_a} (missing from {label_b}):")
        for d in missing_b:
            lines.append(f"  {d.name}")

    if missing_a:
        lines.append(f"\nOnly in {label_b} (missing from {label_a}):")
        for d in missing_a:
            lines.append(f"  {d.name}")

    return "\n".join(lines)


def format_table(mod: IRModule, top_n: int = 0, sort_by: str = "instructions") -> str:
    """Function-level metrics table."""
    fns = sorted(mod.functions.values(), key=lambda f: getattr(f, sort_by, 0), reverse=True)
    if top_n:
        fns = fns[:top_n]

    lines = []
    header = (
        f"{'Function':<40s} {'Instr':>6s} {'BB':>4s} {'Alloc':>5s} "
        f"{'Call':>5s} {'Sw':>3s} {'Push':>4s} {'StrEq':>5s} {'Stack':>6s} {'Hash':>16s}"
    )
    lines.append(header)
    lines.append("-" * len(header))
    for fn in fns:
        name = fn.name[:39]
        lines.append(
            f"{name:<40s} {fn.instructions:>6d} {fn.basic_blocks:>4d} {fn.allocas:>5d} "
            f"{fn.calls:>5d} {fn.switches:>3d} {fn.list_pushes:>4d} {fn.str_eqs:>5d} "
            f"{fn.alloca_bytes:>6d} {fn.body_hash:>16s}"
        )

    lines.append("-" * len(header))
    lines.append(
        f"{'TOTAL':<40s} {sum(f.instructions for f in fns):>6d} "
        f"{sum(f.basic_blocks for f in fns):>4d} {sum(f.allocas for f in fns):>5d} "
        f"{sum(f.calls for f in fns):>5d} {sum(f.switches for f in fns):>3d} "
        f"{sum(f.list_pushes for f in fns):>4d} {sum(f.str_eqs for f in fns):>5d} "
        f"{sum(f.alloca_bytes for f in fns):>6d}"
    )
    return "\n".join(lines)


def format_fingerprint_json(mod: IRModule) -> str:
    """JSON fingerprints for every function."""
    out = {}
    for fn in mod.functions.values():
        out[fn.name] = {
            "hash": fn.body_hash,
            "instructions": fn.instructions,
            "basic_blocks": fn.basic_blocks,
            "allocas": fn.allocas,
            "calls": fn.calls,
            "switches": fn.switches,
            "list_pushes": fn.list_pushes,
            "str_eqs": fn.str_eqs,
            "alloca_bytes": fn.alloca_bytes,
            "lines": (fn.line_start, fn.line_end),
        }
    return json.dumps(out, indent=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def cmd_audit(args: argparse.Namespace) -> int:
    """Audit a single IR file."""
    text = pathlib.Path(args.file).read_text(encoding="utf-8")
    mod = parse_ir(text)

    if args.only:
        mod.functions = {k: v for k, v in mod.functions.items() if args.only in k}

    pathologies = run_audit(mod)

    if args.json:
        print(json.dumps([asdict(p) for p in pathologies], indent=2))
    else:
        print(format_audit(pathologies, mod))
        if pathologies:
            # Also print the table for context
            print()
            print(format_table(mod, top_n=args.top))

    return 1 if any(p.severity == "error" for p in pathologies) else 0


def cmd_diff(args: argparse.Namespace) -> int:
    """Compare bootstrap vs stage1 for a .mn file."""
    mn_path = pathlib.Path(args.file)
    stage1 = pathlib.Path(args.stage1)

    print(f"Compiling {mn_path.name} via bootstrap...", file=sys.stderr)
    try:
        ir_a = bootstrap_compile(mn_path)
    except Exception as e:
        print(f"Bootstrap compilation failed: {e}", file=sys.stderr)
        return 1

    print(f"Compiling {mn_path.name} via stage1...", file=sys.stderr)
    ir_b = stage1_compile(mn_path, stage1)
    if ir_b is None:
        print(f"Stage1 compilation failed or timed out", file=sys.stderr)
        # Still audit the bootstrap output
        mod_a = parse_ir(ir_a)
        print(format_table(mod_a, top_n=args.top))
        return 1

    mod_a = parse_ir(ir_a)
    mod_b = parse_ir(ir_b)

    if args.only:
        mod_a.functions = {k: v for k, v in mod_a.functions.items() if args.only in k}
        mod_b.functions = {k: v for k, v in mod_b.functions.items() if args.only in k}

    diffs = diff_modules(mod_a, mod_b)

    if args.json:
        print(json.dumps([asdict(d) for d in diffs], indent=2))
    else:
        print(format_diff(diffs))
        # Audit stage1 output for known bugs
        print()
        pathologies = run_audit(mod_b)
        if pathologies:
            print(format_audit(pathologies, mod_b))

    return 0 if all(d.status == "match" for d in diffs) else 1


def cmd_diff_all(args: argparse.Namespace) -> int:
    """Compare bootstrap vs stage1 for ALL golden tests."""
    stage1 = pathlib.Path(args.stage1)
    mn_files = sorted(GOLDEN_DIR.glob("*.mn"))

    total_match = 0
    total_diverged = 0
    total_missing = 0
    results = []

    for mn_path in mn_files:
        name = mn_path.stem
        print(f"  {name}...", end=" ", file=sys.stderr, flush=True)

        try:
            ir_a = bootstrap_compile(mn_path)
        except Exception as e:
            print(f"BOOTSTRAP_FAIL ({e})", file=sys.stderr)
            results.append((name, "BOOTSTRAP_FAIL", 0, 0, 0, []))
            continue

        ir_b = stage1_compile(mn_path, stage1)
        if ir_b is None:
            print("STAGE1_FAIL", file=sys.stderr)
            results.append((name, "STAGE1_FAIL", 0, 0, 0, []))
            continue

        mod_a = parse_ir(ir_a)
        mod_b = parse_ir(ir_b)
        diffs = diff_modules(mod_a, mod_b)
        pathologies = run_audit(mod_b)

        n_match = sum(1 for d in diffs if d.status == "match")
        n_div = sum(1 for d in diffs if d.status == "diverged")
        n_miss = sum(1 for d in diffs if d.status in ("missing_a", "missing_b"))
        total_match += n_match
        total_diverged += n_div
        total_missing += n_miss

        status = "MATCH" if n_div == 0 and n_miss == 0 else "DIFF"
        print(f"{status} ({n_match}/{len(diffs)} fn)", file=sys.stderr)
        results.append((name, status, n_match, n_div, n_miss, pathologies))

    # Summary table
    print()
    print(f"{'Test':<25s} {'Status':<15s} {'Match':>5s} {'Div':>5s} {'Miss':>5s} {'Bugs':>5s}")
    print("-" * 65)
    for name, status, nm, nd, nmiss, paths in results:
        bugs = sum(1 for p in paths if p.severity == "error")
        print(f"{name:<25s} {status:<15s} {nm:>5d} {nd:>5d} {nmiss:>5d} {bugs:>5d}")
    print("-" * 65)
    total = total_match + total_diverged + total_missing
    print(f"{'TOTAL':<25s} {'':15s} {total_match:>5d} {total_diverged:>5d} {total_missing:>5d}")
    print(f"\n{total_match}/{total} functions match ({100*total_match//max(total,1)}%)")

    return 0 if total_diverged == 0 and total_missing == 0 else 1


def cmd_table(args: argparse.Namespace) -> int:
    """Show function-level metrics table."""
    text = pathlib.Path(args.file).read_text(encoding="utf-8")
    mod = parse_ir(text)
    if args.only:
        mod.functions = {k: v for k, v in mod.functions.items() if args.only in k}
    print(format_table(mod, top_n=args.top, sort_by=args.sort_by or "instructions"))
    return 0


def cmd_fingerprint(args: argparse.Namespace) -> int:
    """Dump per-function fingerprints as JSON."""
    text = pathlib.Path(args.file).read_text(encoding="utf-8")
    mod = parse_ir(text)
    if args.only:
        mod.functions = {k: v for k, v in mod.functions.items() if args.only in k}
    print(format_fingerprint_json(mod))
    return 0


def cmd_diff_ir(args: argparse.Namespace) -> int:
    """Compare two pre-generated .ll files directly."""
    ir_a = pathlib.Path(args.file_a).read_text(encoding="utf-8")
    ir_b = pathlib.Path(args.file_b).read_text(encoding="utf-8")
    label_a = pathlib.Path(args.file_a).stem
    label_b = pathlib.Path(args.file_b).stem

    mod_a = parse_ir(ir_a)
    mod_b = parse_ir(ir_b)

    if args.only:
        mod_a.functions = {k: v for k, v in mod_a.functions.items() if args.only in k}
        mod_b.functions = {k: v for k, v in mod_b.functions.items() if args.only in k}

    diffs = diff_modules(mod_a, mod_b)

    if args.json:
        print(json.dumps([asdict(d) for d in diffs], indent=2))
    else:
        print(format_diff(diffs, label_a=label_a, label_b=label_b))
        # Audit both for known bugs
        for label, mod in [(label_a, mod_a), (label_b, mod_b)]:
            pathologies = run_audit(mod)
            if pathologies:
                print(f"\n--- Pathologies in {label} ---")
                print(format_audit(pathologies, mod))

    return 0 if all(d.status == "match" for d in diffs) else 1


def cmd_snapshot(args: argparse.Namespace) -> int:
    """Generate stage1 IR snapshots for all golden tests (run this in WSL).

    Produces tests/golden/NN_name.stage1.ll files that can be used by
    diff/diff-all on Windows without needing the Linux binary.
    """
    stage1 = pathlib.Path(args.stage1)
    mn_files = sorted(GOLDEN_DIR.glob("*.mn"))
    generated = 0
    for mn_path in mn_files:
        name = mn_path.stem
        out_path = mn_path.with_suffix(".stage1.ll")
        ir = stage1_compile(mn_path, stage1)
        if ir:
            out_path.write_text(ir, encoding="utf-8")
            print(f"  {name}: {len(ir)} bytes -> {out_path.name}")
            generated += 1
        else:
            print(f"  {name}: FAILED")
    print(f"\nGenerated {generated}/{len(mn_files)} snapshots")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        prog="ir_doctor",
        description="Per-function IR diagnostics for the Mapanare compiler",
    )
    p.add_argument("--stage1", default=str(ROOT / "mapanare" / "self" / "mnc-stage1"),
                   help="Path to mnc-stage1 binary")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.add_argument("--only", default="", help="Filter functions by substring")
    p.add_argument("--top", type=int, default=0, help="Show top N functions")
    p.add_argument("-v", "--verbose", action="store_true")

    sub = p.add_subparsers(dest="command")

    # audit
    s_audit = sub.add_parser("audit", help="Audit IR file for known pathologies")
    s_audit.add_argument("file", help="Path to .ll file")

    # diff
    s_diff = sub.add_parser("diff", help="Compare bootstrap vs stage1 for a .mn file")
    s_diff.add_argument("file", help="Path to .mn file")

    # diff-ir
    s_dir = sub.add_parser("diff-ir", help="Compare two .ll files directly")
    s_dir.add_argument("file_a", help="First .ll file (e.g. bootstrap output)")
    s_dir.add_argument("file_b", help="Second .ll file (e.g. stage1 output)")

    # diff-all
    sub.add_parser("diff-all", help="Compare all golden tests")

    # snapshot
    sub.add_parser("snapshot", help="Generate stage1 IR snapshots for golden tests (WSL)")

    # table
    s_table = sub.add_parser("table", help="Show function metrics table")
    s_table.add_argument("file", help="Path to .ll file")
    s_table.add_argument("--sort-by", default="instructions",
                         help="Sort column (instructions, alloca_bytes, calls, etc.)")

    # fingerprint
    s_fp = sub.add_parser("fingerprint", help="Dump per-function fingerprints as JSON")
    s_fp.add_argument("file", help="Path to .ll file")

    args = p.parse_args()
    if not args.command:
        p.print_help()
        return 0

    handlers = {
        "audit": cmd_audit,
        "diff": cmd_diff,
        "diff-ir": cmd_diff_ir,
        "diff-all": cmd_diff_all,
        "snapshot": cmd_snapshot,
        "table": cmd_table,
        "fingerprint": cmd_fingerprint,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
