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

    Also checks for write-back stores that connect push allocas to len
    allocas — if a store copies the updated list from the push alloca to
    the len alloca, the aliasing is mitigated (downgrade to warning).
    """
    LIST_TY = r"\{i8\*, i64, i64, i64\}"
    results = []
    for fn in mod.functions.values():
        if fn.list_pushes == 0:
            continue

        # Find all allocas that are targets of list_push
        push_targets: set[str] = set()
        for m in re.finditer(
            rf"call void @__mn_list_push\({LIST_TY}\*\s+(%[\w.]+)",
            fn.body,
        ):
            push_targets.add(m.group(1))

        # Find all allocas that are sources for list_len
        len_sources: set[str] = set()
        for m in re.finditer(
            rf"call i64 @__mn_list_len\({LIST_TY}\*\s+(%[\w.]+)",
            fn.body,
        ):
            len_sources.add(m.group(1))

        # If push and len use the same allocas, no issue
        if not push_targets or not len_sources or push_targets & len_sources:
            continue

        # Check for write-back stores: after push, is there a store
        # that copies the list from a loaded-from-push-alloca to a len-alloca?
        # Pattern: %r = load LIST, LIST* %push_alloca ... store LIST %r, LIST* %len_alloca
        # Also check: store to the len alloca from ANY value loaded after a push call
        has_writeback = False
        for pt in push_targets:
            # Find values loaded from this push target
            loaded_vals: set[str] = set()
            for m in re.finditer(
                rf"(%[\w.]+)\s*=\s*load\s+{LIST_TY},\s*{LIST_TY}\*\s*{re.escape(pt)}",
                fn.body,
            ):
                loaded_vals.add(m.group(1))
            # Check if any of those loaded values are stored to a len source
            for lv in loaded_vals:
                for ls in len_sources:
                    if re.search(
                        rf"store\s+{LIST_TY}\s+{re.escape(lv)},\s*{LIST_TY}\*\s*{re.escape(ls)}",
                        fn.body,
                    ):
                        has_writeback = True
                        break
                if has_writeback:
                    break
            if has_writeback:
                break

        if has_writeback:
            results.append(
                Pathology(
                    severity="warning",
                    code="ALLOCA_ALIAS_MITIGATED",
                    function=fn.name,
                    line=fn.line_start,
                    message=f"Aliased allocas with write-back: push->{push_targets}, len->{len_sources}",
                    detail="Write-back store detected. The aliasing may be safe.",
                )
            )
        else:
            results.append(
                Pathology(
                    severity="error",
                    code="ALLOCA_ALIAS",
                    function=fn.name,
                    line=fn.line_start,
                    message=f"List push/len use different allocas: push->{push_targets}, len->{len_sources}",
                    detail=(
                        "The for-loop body pushes to one alloca but post-loop len() "
                        "reads from a stale pre-entry alloca. NO write-back found. "
                        "This function needs a recursive rewrite to avoid the bug."
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
        for m in re.finditer(r"^\s*ret\s+(.*)", fn.body, re.MULTILINE):
            rest = m.group(1).strip()
            if rest == "void":
                continue
            # Extract full type: struct types like { i1, { i64, ... } } have spaces
            if rest.startswith("{"):
                depth, end = 0, len(rest)
                for ci, ch in enumerate(rest):
                    if ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                    if depth == 0:
                        end = ci + 1
                        break
                ret_ty = rest[:end]
            else:
                ret_ty = rest.split()[0]
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


def detect_duplicate_switch_cases(mod: IRModule) -> list[Pathology]:
    """Detect switch statements with duplicate case values."""
    results = []
    for fn in mod.functions.values():
        for m in re.finditer(
            r"switch\s+i64\s+%[\w.]+,\s*label\s+%[\w.]+\s*\[([^\]]+)\]",
            fn.body,
        ):
            cases_text = m.group(1)
            case_vals = re.findall(r"i64\s+(\d+)", cases_text)
            seen: set[str] = set()
            dupes: list[str] = []
            for cv in case_vals:
                if cv in seen:
                    dupes.append(cv)
                seen.add(cv)
            if dupes:
                results.append(
                    Pathology(
                        severity="error",
                        code="DUPLICATE_CASE",
                        function=fn.name,
                        line=fn.line_start,
                        message=f"Switch has duplicate case values: {dupes}",
                        detail="Variant index resolution returned same value for different variants.",
                    )
                )
    return results


def detect_phi_undefined_refs(mod: IRModule) -> list[Pathology]:
    """Detect Phi nodes referencing values that don't exist in the function."""
    results = []
    for fn in mod.functions.values():
        if fn.phis == 0:
            continue
        # Collect all defined SSA values
        defined = set(re.findall(r"(%[\w.]+)\s*=", fn.body))
        # Also include function parameters
        sig_params = set(re.findall(r"(%[\w.]+)(?:\s*,|\s*\))", fn.signature))
        defined |= sig_params
        # Check phi incoming values
        for m in re.finditer(
            r"=\s*phi\s+\S+\s+((?:\[.*?\]\s*,?\s*)+)",
            fn.body,
        ):
            phi_text = m.group(1)
            refs = re.findall(r"\[\s*(%[\w.]+)\s*,", phi_text)
            for ref in refs:
                if ref not in defined and ref != "undef" and ref != "zeroinitializer":
                    results.append(
                        Pathology(
                            severity="error",
                            code="PHI_UNDEF_REF",
                            function=fn.name,
                            line=fn.line_start,
                            message=f"Phi references undefined value {ref}",
                            detail="Likely a void/unknown arm result added to Phi collection.",
                        )
                    )
                    break  # one per function
    return results


def detect_for_loop_push_patterns(mod: IRModule) -> list[Pathology]:
    """Detect functions with list.push inside for-loop-like patterns.

    These are candidates for recursive rewrite to avoid alloca aliasing.
    Reports as 'info' severity — it's a work queue, not a bug.
    """
    results = []
    for fn in mod.functions.values():
        if fn.list_pushes == 0:
            continue
        # Heuristic: for-loops have "for_header" or "for_body" or "for_exit" blocks
        has_for = bool(re.search(r"for_(?:header|body|exit)\d*:", fn.body))
        if not has_for:
            continue
        # Check if push is inside a for-body block
        blocks = re.split(r"^([\w.]+):", fn.body, flags=re.MULTILINE)
        in_for_body = False
        push_in_loop = False
        for i, part in enumerate(blocks):
            if part.startswith("for_body"):
                in_for_body = True
            elif re.match(r"for_exit|for_header", part):
                in_for_body = False
            elif in_for_body and "__mn_list_push" in part:
                push_in_loop = True
                break
        if push_in_loop:
            results.append(
                Pathology(
                    severity="info",
                    code="LOOP_PUSH",
                    function=fn.name,
                    line=fn.line_start,
                    message="list.push() inside for-loop body — candidate for recursive rewrite",
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
    detect_duplicate_switch_cases,
    detect_phi_undefined_refs,
    detect_for_loop_push_patterns,
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
    """Audit a single IR file. Saves baseline for before/after comparison."""
    text = pathlib.Path(args.file).read_text(encoding="utf-8")
    mod = parse_ir(text)

    if args.only:
        mod.functions = {k: v for k, v in mod.functions.items() if args.only in k}

    pathologies = run_audit(mod)

    # Also validate with llvm-as
    valid, err = validate_ir(text)

    if args.json:
        print(json.dumps([asdict(p) for p in pathologies], indent=2))
    else:
        print(format_audit(pathologies, mod))

        if not valid:
            print(f"\nllvm-as: INVALID -- {err}")
        elif err:
            print(f"\nllvm-as: {err}")
        else:
            print(f"\nllvm-as: VALID")

        # Compare with previous baseline
        baseline_name = pathlib.Path(args.file).stem
        old_baseline = _load_baseline(baseline_name)
        if old_baseline:
            print(f"\n--- Delta from last audit ---")
            print(_format_baseline_diff(old_baseline, pathologies))

        # Save new baseline + journal
        bp = _save_baseline(baseline_name, pathologies)
        _journal_append({
            "command": "audit",
            "file": args.file,
            "functions": len(mod.functions),
            "issues": len(pathologies),
            "errors": sum(1 for p in pathologies if p.severity == "error"),
            "by_code": dict(defaultdict(int, {p.code: sum(1 for q in pathologies if q.code == p.code) for p in pathologies})),
        })
        print(f"\nBaseline saved: {bp.relative_to(ROOT)}")

        if pathologies:
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


# ---------------------------------------------------------------------------
# llvm-as validation
# ---------------------------------------------------------------------------

def _find_llvm_as() -> str | None:
    """Find llvm-as binary."""
    import shutil
    for name in ("llvm-as", "llvm-as-14", "llvm-as-15", "llvm-as-16", "llvm-as-17", "llvm-as-18"):
        p = shutil.which(name)
        if p:
            return p
    return None


def validate_ir(ir_text: str) -> tuple[bool, str]:
    """Run llvm-as on IR text. Returns (valid, error_message)."""
    llvm_as = _find_llvm_as()
    if not llvm_as:
        return True, "(llvm-as not found, skipped)"
    with tempfile.NamedTemporaryFile(suffix=".ll", mode="w", delete=False, encoding="utf-8") as f:
        f.write(ir_text)
        f.flush()
        tmp = f.name
    try:
        r = subprocess.run(
            [llvm_as, tmp, "-o", "/dev/null"],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode == 0:
            return True, ""
        # Extract first error line
        err = r.stderr.strip().splitlines()[0] if r.stderr.strip() else "unknown error"
        return False, err
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return True, "(llvm-as failed to run)"
    finally:
        pathlib.Path(tmp).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Audit baselines (before/after comparison)
# ---------------------------------------------------------------------------

BASELINE_DIR = ROOT / ".ir_doctor"
JOURNAL_FILE = BASELINE_DIR / "journal.jsonl"
SELF_DIR = ROOT / "mapanare" / "self"


def _save_baseline(name: str, pathologies: list[Pathology]) -> pathlib.Path:
    """Save audit results as a baseline for later comparison."""
    BASELINE_DIR.mkdir(exist_ok=True)
    path = BASELINE_DIR / f"{name}.json"
    data = {
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "counts": {},
        "functions": {},
    }
    by_code: dict[str, int] = defaultdict(int)
    by_fn: dict[str, list[str]] = defaultdict(list)
    for p in pathologies:
        by_code[p.code] += 1
        by_fn[p.function].append(p.code)
    data["counts"] = dict(by_code)
    data["functions"] = dict(by_fn)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def _load_baseline(name: str) -> dict | None:
    """Load a previous baseline."""
    path = BASELINE_DIR / f"{name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _format_baseline_diff(old: dict, new_pathologies: list[Pathology]) -> str:
    """Show what changed between baseline and current audit."""
    new_counts: dict[str, int] = defaultdict(int)
    new_fns: dict[str, list[str]] = defaultdict(list)
    for p in new_pathologies:
        new_counts[p.code] += 1
        new_fns[p.function].append(p.code)

    old_counts = old.get("counts", {})
    old_fns = old.get("functions", {})
    lines = []
    lines.append(f"Baseline from: {old.get('timestamp', '?')}")
    lines.append("")

    all_codes = sorted(set(old_counts) | set(new_counts))
    changed = False
    for code in all_codes:
        o = old_counts.get(code, 0)
        n = new_counts.get(code, 0)
        if o != n:
            delta = n - o
            sign = "+" if delta > 0 else ""
            lines.append(f"  {code}: {o} -> {n} ({sign}{delta})")
            changed = True

    if not changed:
        lines.append("  No changes from baseline.")
        return "\n".join(lines)

    # Show which functions were fixed or broke
    fixed_fns = set(old_fns) - set(new_fns)
    broke_fns = set(new_fns) - set(old_fns)
    if fixed_fns:
        lines.append(f"\n  Fixed ({len(fixed_fns)}):")
        for fn in sorted(fixed_fns)[:15]:
            lines.append(f"    - {fn}: {', '.join(old_fns[fn])}")
        if len(fixed_fns) > 15:
            lines.append(f"    ... and {len(fixed_fns) - 15} more")
    if broke_fns:
        lines.append(f"\n  New issues ({len(broke_fns)}):")
        for fn in sorted(broke_fns)[:15]:
            lines.append(f"    + {fn}: {', '.join(new_fns[fn])}")
        if len(broke_fns) > 15:
            lines.append(f"    ... and {len(broke_fns) - 15} more")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Struct field mapper — translate byte offsets to Mapanare field names
# ---------------------------------------------------------------------------

# LLVM type sizes (64-bit target)
_LLVM_SIZES = {
    "i1": 1, "i8": 1, "i16": 2, "i32": 4, "i64": 8,
    "double": 8, "float": 4, "i8*": 8, "ptr": 8,
}
# Common Mapanare types and their LLVM representations
_MN_TYPE_MAP = {
    "Int": ("i64", 8),
    "Float": ("double", 8),
    "Bool": ("i1", 8),  # padded to 8 in structs
    "String": ("{i8*, i64}", 16),
    "Char": ("i8", 8),  # padded
}
_LIST_SIZE = 32  # {i8*, i64, i64, i64}
_OPTION_SIZE = 16  # {i64, i8*} = {tag, payload_ptr}
_ENUM_SIZE = 16  # {i64, i8*}


def _mn_field_size(type_str: str) -> int:
    """Estimate byte size of a Mapanare type in LLVM struct layout."""
    type_str = type_str.strip()
    if type_str in _MN_TYPE_MAP:
        return _MN_TYPE_MAP[type_str][1]
    if type_str.startswith("List<"):
        return _LIST_SIZE
    if type_str.startswith("Option<"):
        return _OPTION_SIZE
    if type_str.startswith("Result<"):
        return 24  # {i1, {ptr, ptr}} padded
    # Assume struct (will be resolved later)
    return 0  # unknown


@dataclass
class StructField:
    name: str
    type_str: str
    offset: int
    size: int


@dataclass
class StructLayout:
    name: str
    fields: list[StructField]
    total_size: int


def parse_mn_structs(source: str) -> dict[str, StructLayout]:
    """Parse struct definitions from .mn source code."""
    structs: dict[str, StructLayout] = {}
    # Match: struct Name { field1: Type1, field2: Type2, ... }
    for m in re.finditer(
        r"struct\s+(\w+)\s*\{([^}]+)\}",
        source,
    ):
        name = m.group(1)
        body = m.group(2)
        fields = []
        offset = 0
        for fm in re.finditer(r"(\w+)\s*:\s*([^,}]+)", body):
            fname = fm.group(1).strip()
            ftype = fm.group(2).strip()
            size = _mn_field_size(ftype)
            if size == 0:
                # Unknown type — check if it's a known struct
                if ftype in structs:
                    size = structs[ftype].total_size
                else:
                    size = 8  # assume pointer-sized
            # Align to 8 bytes
            if offset % 8 != 0:
                offset = (offset + 7) & ~7
            fields.append(StructField(name=fname, type_str=ftype, offset=offset, size=size))
            offset += size
        if offset % 8 != 0:
            offset = (offset + 7) & ~7
        structs[name] = StructLayout(name=name, fields=fields, total_size=offset)
    return structs


def format_struct_layout(layout: StructLayout) -> str:
    """Format struct layout for display."""
    lines = [f"struct {layout.name} ({layout.total_size} bytes):"]
    for f in layout.fields:
        lines.append(f"  +{f.offset:4d}  {f.name:30s} {f.type_str:30s} ({f.size}B)")
    return "\n".join(lines)


def field_at_offset(layout: StructLayout, offset: int) -> str:
    """Find which field contains a given byte offset."""
    for f in layout.fields:
        if f.offset <= offset < f.offset + f.size:
            inner_off = offset - f.offset
            return f"{layout.name}.{f.name} (+{f.offset}, {f.type_str}, inner offset {inner_off})"
    return f"{layout.name}.??? (offset {offset} out of range, struct is {layout.total_size}B)"


# ---------------------------------------------------------------------------
# Debug journal — persistent log of what was tried and what happened
# ---------------------------------------------------------------------------

def _journal_append(entry: dict) -> None:
    """Append an entry to the debug journal."""
    BASELINE_DIR.mkdir(exist_ok=True)
    entry["timestamp"] = __import__("datetime").datetime.now().isoformat()
    with open(JOURNAL_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _journal_load(limit: int = 50) -> list[dict]:
    """Load recent journal entries."""
    if not JOURNAL_FILE.exists():
        return []
    lines = JOURNAL_FILE.read_text(encoding="utf-8").strip().splitlines()
    entries = []
    for line in lines[-limit:]:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


# ---------------------------------------------------------------------------
# Failure diagnosis — classify errors and suggest next steps
# ---------------------------------------------------------------------------

def _diagnose_compile_fail(stage1: pathlib.Path, mn_path: pathlib.Path) -> dict:
    """Run stage1 on a file and capture crash details."""
    info: dict = {"type": "compile_fail", "file": mn_path.name}
    try:
        r = subprocess.run(
            [str(stage1), str(mn_path)],
            capture_output=True, text=True, timeout=30,
        )
        info["exit_code"] = r.returncode
        info["stderr"] = r.stderr[:500] if r.stderr else ""
        info["stdout_lines"] = r.stdout.count("\n") if r.stdout else 0

        if r.returncode == 139 or "Signal 11" in r.stderr:
            info["crash"] = "SIGSEGV"
            # Extract crash location
            for line in r.stderr.splitlines():
                if "at:" in line.lower() or "+0x" in line:
                    info["crash_location"] = line.strip()
                    break
            info["suggestion"] = (
                "Segfault during compilation. Common causes:\n"
                "  1. Uninitialized list field in LowerState (lambda/recursive lowering)\n"
                "  2. Stale data pointer from shared list (COW detach missed)\n"
                "  3. Stack overflow from deep recursion\n"
                "Try: valgrind --track-origins=yes ./mapanare/self/mnc-stage1 <file>"
            )
        elif "out of memory" in r.stderr:
            info["crash"] = "OOM"
            # Extract allocation size
            m = re.search(r"requested (\d+) bytes", r.stderr)
            if m:
                info["oom_bytes"] = int(m.group(1))
            info["suggestion"] = (
                "Out of memory. Common causes:\n"
                "  1. Garbage cap/elem_size in list clone (uninitialized struct fields)\n"
                "  2. O(N^2) string concatenation in emitter\n"
                "  3. Alloca aliasing causing leaked copies\n"
                "Try: python scripts/ir_doctor.py memory"
            )
        elif r.returncode != 0:
            info["crash"] = f"exit_{r.returncode}"
            info["suggestion"] = f"Non-zero exit. Check stderr: {r.stderr[:200]}"

    except subprocess.TimeoutExpired:
        info["crash"] = "TIMEOUT"
        info["suggestion"] = "Compilation timed out (30s). Likely infinite loop or OOM."
    except OSError as e:
        info["crash"] = f"OS_ERROR: {e}"
    return info


def _diagnose_invalid_ir(ir: str, err: str) -> dict:
    """Classify an llvm-as validation error."""
    info: dict = {"type": "invalid_ir", "error": err}

    if "undefined value" in err:
        m = re.search(r"use of undefined value '(%[\w.]+)'", err)
        val = m.group(1) if m else "?"
        info["category"] = "UNDEF_VALUE"
        info["value"] = val
        info["suggestion"] = (
            f"Undefined value {val} in IR. Common causes:\n"
            "  1. Phi references a void/unknown arm result (add ty.kind != 'void' filter)\n"
            "  2. Variable defined in one block but used in another without proper SSA\n"
            "  3. Match arm body produces no value but Phi expects one\n"
            f"Try: python scripts/ir_doctor.py extract <file.ll> <function_with_{val}>"
        )
    elif "expected value token" in err:
        info["category"] = "EMPTY_LABEL"
        info["suggestion"] = (
            "Empty branch label (br label %). The match/switch produced 0 cases.\n"
            "  Root cause: alloca aliasing in the case-building loop.\n"
            "  Fix: rewrite the loop as a recursive function (see build_match_arms_rec pattern)."
        )
    elif "defined with type" in err and "but expected" in err:
        m = re.search(r"'(%[\w.]+)' defined with type '([^']+)' but expected '([^']+)'", err)
        info["category"] = "TYPE_MISMATCH"
        if m:
            info["value"] = m.group(1)
            info["actual_type"] = m.group(2)
            info["expected_type"] = m.group(3)
        info["suggestion"] = (
            "Type mismatch in IR. Common causes:\n"
            "  1. Result/Option generic args not propagated (use resolve_generic_args_rec)\n"
            "  2. WrapOk/WrapErr using fallback {ptr, ptr} instead of actual types\n"
            "  3. EnumPayload extraction type wrong (use extractvalue, not byte-offset)\n"
            "Try: python scripts/mir_trace.py <file.mn> <function> --compare"
        )
    elif "duplicate case value" in err:
        info["category"] = "DUPLICATE_CASE"
        info["suggestion"] = (
            "Duplicate case in switch. Both variants resolved to the same index.\n"
            "  Fix: check hardcoded Ok=1/Err=0/Some=1/None=0 in emit_llvm.mn"
        )
    else:
        info["category"] = "OTHER"
        info["suggestion"] = f"Unknown IR error: {err[:200]}"

    return info


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------


def cmd_valgrind(args: argparse.Namespace) -> int:
    """Run valgrind on stage1 + test file, auto-map crash offsets to field names.

    Replaces the manual: run valgrind -> copy hex offset -> structmap --offset.
    """
    stage1 = pathlib.Path(args.stage1)
    mn_path = pathlib.Path(args.test_file)
    struct_name = args.struct or "LowerState"

    if not stage1.exists():
        print(f"Stage1 not found: {stage1}", file=sys.stderr)
        return 1

    # Parse struct layouts
    all_source = ""
    for mn_file in sorted(SELF_DIR.glob("*.mn")):
        if mn_file.name != "mnc_all.mn":
            all_source += mn_file.read_text(encoding="utf-8") + "\n"
    structs = parse_mn_structs(all_source)
    layout = structs.get(struct_name)

    # Run valgrind
    print(f"Running valgrind on: {stage1.name} {mn_path.name}")
    try:
        r = subprocess.run(
            ["valgrind", "--track-origins=yes", "-q", "--error-exitcode=99",
             str(stage1), str(mn_path)],
            capture_output=True, text=True, timeout=120,
        )
    except FileNotFoundError:
        print("valgrind not found. This command requires WSL/Linux.", file=sys.stderr)
        return 1
    except subprocess.TimeoutExpired:
        print("Valgrind timed out (120s)")
        return 1

    stderr = r.stderr
    print(f"Exit code: {r.returncode}")

    # Parse valgrind output
    # Extract crash function names
    crash_fns = re.findall(r"by 0x[\dA-Fa-f]+:\s*(\w+)", stderr)
    # Extract "Invalid read/write" with addresses
    invalid_ops = re.findall(r"(Invalid (?:read|write) of size \d+)", stderr)
    # Extract hex addresses
    addrs = re.findall(r"Address (0x[\dA-Fa-f]+)", stderr)
    # Extract "Uninitialised value" origins
    uninit = re.findall(r"Uninitialised value was created by (.+)", stderr)
    # Extract function+offset patterns like func+0x1234
    fn_offsets = re.findall(r"(\w+)\+0x([\dA-Fa-f]+)", stderr)

    print(f"\n--- Valgrind Summary ---")
    if invalid_ops:
        print(f"  Errors: {', '.join(set(invalid_ops))}")
    if uninit:
        print(f"  Origin: {uninit[0]}")
    if crash_fns:
        # Show unique crash path (deduped, in order)
        seen: set[str] = set()
        path = []
        for fn in crash_fns:
            if fn not in seen:
                seen.add(fn)
                path.append(fn)
        print(f"  Call path: {' -> '.join(path[:8])}")

    # Try to map function+offset to struct field
    if layout and fn_offsets:
        print(f"\n--- Struct Field Mapping ({struct_name}) ---")
        print(format_struct_layout(layout))
        for fn_name, hex_off in fn_offsets:
            byte_off = int(hex_off, 16)
            # The offset might be into the function, not the struct.
            # Only map if it's within the struct size range.
            if byte_off <= layout.total_size:
                field_info = field_at_offset(layout, byte_off)
                print(f"\n  {fn_name}+0x{hex_off} (byte {byte_off}): {field_info}")

    # Log to journal
    _journal_append({
        "command": "valgrind",
        "test": mn_path.name,
        "exit_code": r.returncode,
        "errors": invalid_ops[:5],
        "crash_path": crash_fns[:8],
        "uninit_origin": uninit[0] if uninit else None,
    })

    # Show raw stderr if verbose
    if args.verbose:
        print(f"\n--- Raw Valgrind Output ---")
        print(stderr[:3000])

    return 0 if r.returncode == 0 else 1


def cmd_check(args: argparse.Namespace) -> int:
    """Validate IR file with llvm-as."""
    text = pathlib.Path(args.file).read_text(encoding="utf-8")
    valid, err = validate_ir(text)
    if valid:
        print(f"VALID: {args.file}")
        if err:
            print(f"  ({err})")
        return 0
    else:
        print(f"INVALID: {args.file}")
        print(f"  {err}")
        return 1


def cmd_stage2(args: argparse.Namespace) -> int:
    """Compile self-hosted modules through mnc-stage1, validate stage2 IR.

    Tests whether mnc-stage1 can compile its own source modules and produce
    valid LLVM IR.  This is the gate for Phase 4 (fixed-point verification).
    Also attempts full mnc_all.mn compilation.
    """
    stage1 = pathlib.Path(args.stage1)
    self_dir = ROOT / "mapanare" / "self"
    timeout_s = args.timeout

    modules = [
        "ast.mn", "lexer.mn", "parser.mn", "semantic.mn", "mir.mn",
        "lower_state.mn", "lower.mn", "emit_llvm_ir.mn", "emit_llvm.mn", "main.mn",
    ]

    if not stage1.exists():
        print(f"Stage1 binary not found: {stage1}", file=sys.stderr)
        return 1

    results: list[tuple[str, str, int, str]] = []
    for mod in modules:
        mn_path = self_dir / mod
        name = mod.replace(".mn", "")
        print(f"  {name}...", end=" ", flush=True)

        try:
            proc = subprocess.run(
                [str(stage1), str(mn_path)],
                capture_output=True, text=True, timeout=timeout_s,
            )
            ir = proc.stdout
            n_lines = ir.count("\n")
            if proc.returncode != 0 or n_lines == 0:
                crash = proc.stderr.strip().split("\n")[0] if proc.stderr else "no output"
                print(f"COMPILE_FAIL ({crash})")
                results.append((name, "COMPILE_FAIL", 0, crash))
                continue

            valid, err = validate_ir(ir)
            if valid:
                mod_obj = parse_ir(ir)
                pathologies = run_audit(mod_obj)
                n_errs = sum(1 for p in pathologies if p.severity == "error")
                if n_errs == 0:
                    print(f"OK  {len(mod_obj.functions)} fn  {n_lines} lines")
                    results.append((name, "OK", n_lines, ""))
                else:
                    print(f"WARN({n_errs})  {len(mod_obj.functions)} fn")
                    results.append((name, f"WARN({n_errs})", n_lines, ""))
            else:
                first_err = (err or "").split("\n")[0]
                print(f"INVALID  {n_lines} lines  {first_err}")
                results.append((name, "INVALID", n_lines, first_err))
        except subprocess.TimeoutExpired:
            print(f"TIMEOUT ({timeout_s}s)")
            results.append((name, "TIMEOUT", 0, f"killed after {timeout_s}s"))

    # Full self-compilation test
    print(f"\n  mnc_all.mn...", end=" ", flush=True)
    all_mn = self_dir / "mnc_all.mn"
    if all_mn.exists():
        try:
            proc = subprocess.run(
                [str(stage1), str(all_mn)],
                capture_output=True, text=True, timeout=timeout_s * 4,
            )
            ir = proc.stdout
            n_lines = ir.count("\n")
            if proc.returncode != 0 or n_lines == 0:
                print(f"FAIL ({proc.returncode}, {n_lines} lines)")
                results.append(("mnc_all", "FAIL", n_lines, "no output"))
            else:
                valid, err = validate_ir(ir)
                if valid:
                    print(f"OK  {n_lines} lines")
                    results.append(("mnc_all", "OK", n_lines, ""))
                else:
                    first_err = (err or "").split("\n")[0]
                    print(f"INVALID  {n_lines} lines  {first_err}")
                    results.append(("mnc_all", "INVALID", n_lines, first_err))
        except subprocess.TimeoutExpired:
            print(f"TIMEOUT ({timeout_s * 4}s)")
            results.append(("mnc_all", "TIMEOUT", 0, f"killed after {timeout_s * 4}s"))
    else:
        print("SKIP (file not found)")

    # Summary
    print(f"\n{'Module':<20s} {'Status':<15s} {'Lines':>7s}  Error")
    print("-" * 70)
    for name, status, n_lines, err in results:
        err_short = err[:40] if err else ""
        print(f"{name:<20s} {status:<15s} {n_lines:>7d}  {err_short}")
    ok = sum(1 for _, s, *_ in results if s == "OK")
    print(f"\n{ok}/{len(results)} stage2 modules valid")
    return 0 if ok == len(results) else 1


def cmd_golden(args: argparse.Namespace) -> int:
    """Fresh compile + validate + audit for all golden tests. No caching.

    This is the one command that answers: "does the self-hosted compiler
    work right now?" It compiles every golden test FRESH through stage1,
    validates with llvm-as, audits for pathologies, and shows a summary.

    Saves results to .ir_doctor/golden.json. On subsequent runs, shows
    delta: which tests were FIXED, REGRESSED, or CHANGED.
    """
    stage1 = pathlib.Path(args.stage1)
    mn_files = sorted(GOLDEN_DIR.glob("*.mn"))

    if not stage1.exists():
        print(f"Stage1 binary not found: {stage1}", file=sys.stderr)
        print("Run: python scripts/build_stage1.py", file=sys.stderr)
        return 1

    results = []
    fail_details: list[tuple[str, dict]] = []
    for mn_path in mn_files:
        name = mn_path.stem
        print(f"  {name}...", end=" ", flush=True)

        # Compile fresh through stage1
        ir = stage1_compile(mn_path, stage1)
        if ir is None:
            diag = _diagnose_compile_fail(stage1, mn_path)
            crash = diag.get("crash", "unknown")
            print(f"COMPILE_FAIL ({crash})")
            results.append((name, "COMPILE_FAIL", crash, 0, 0, 0))
            fail_details.append((name, diag))
            continue

        # Check: did it emit any functions?
        mod = parse_ir(ir)
        n_fns = len(mod.functions)
        if n_fns == 0:
            print(f"EMPTY (0 functions, {ir.count(chr(10))} lines)")
            results.append((name, "EMPTY", "", n_fns, 0, 0))
            fail_details.append((name, {
                "type": "empty", "suggestion": "Binary produced header only (no functions).\n"
                "  Check: did _clone_list_fields get disabled? Is COW lazy init breaking module lists?"
            }))
            continue

        # Validate with llvm-as
        valid, err = validate_ir(ir)
        pathologies = run_audit(mod)
        n_errs = sum(1 for p in pathologies if p.severity == "error")

        if valid and n_errs == 0:
            status = "OK"
        elif valid:
            status = f"WARN({n_errs})"
        else:
            status = "INVALID"
            diag = _diagnose_invalid_ir(ir, err)
            fail_details.append((name, diag))

        detail = err if not valid else ""
        print(f"{status}  {n_fns} fn" + (f"  {detail}" if detail else ""))
        results.append((name, status, detail, n_fns, n_errs, ir.count("\n")))

    # Summary table
    print()
    print(f"{'Test':<25s} {'Status':<15s} {'Fns':>4s} {'Errs':>5s} {'Lines':>6s}")
    print("-" * 60)
    for name, status, detail, n_fns, n_errs, n_lines in results:
        print(f"{name:<25s} {status:<15s} {n_fns:>4d} {n_errs:>5d} {n_lines:>6d}")
    print("-" * 60)

    ok = sum(1 for _, s, *_ in results if s == "OK")
    total = len(results)
    print(f"\n{ok}/{total} golden tests OK")

    if ok < total:
        print("\nFailure Details:")
        print("-" * 60)
        for name, diag in fail_details:
            status = next((s for n, s, *_ in results if n == name), "?")
            print(f"\n  {name} [{status}]")
            cat = diag.get("category", diag.get("crash", diag.get("type", "?")))
            print(f"  Category: {cat}")
            if "error" in diag:
                print(f"  Error: {diag['error'][:200]}")
            if "crash_location" in diag:
                print(f"  Crash at: {diag['crash_location']}")
            if "oom_bytes" in diag:
                oom_mb = diag["oom_bytes"] / (1024 * 1024)
                print(f"  Requested: {oom_mb:,.0f} MB")
            if "suggestion" in diag:
                for line in diag["suggestion"].splitlines():
                    print(f"  {line}")

    # Delta from previous golden run
    old_golden = _load_baseline("golden")
    if old_golden and "tests" in old_golden:
        old_tests = old_golden["tests"]
        print(f"\n--- Delta from last golden ({old_golden.get('timestamp', '?')}) ---")
        any_change = False
        for name, status, *_ in results:
            old_status = old_tests.get(name, "?")
            if old_status == status:
                continue
            any_change = True
            if status == "OK" and old_status != "OK":
                print(f"  FIXED      {name}: {old_status} -> {status}")
            elif status != "OK" and old_status == "OK":
                print(f"  REGRESSED  {name}: {old_status} -> {status}")
            else:
                print(f"  CHANGED    {name}: {old_status} -> {status}")
        if not any_change:
            print("  No changes from last run.")
        old_ok = sum(1 for s in old_tests.values() if s == "OK")
        if ok != old_ok:
            print(f"  Score: {old_ok}/{len(old_tests)} -> {ok}/{total}")

    # Save golden baseline
    BASELINE_DIR.mkdir(exist_ok=True)
    golden_data = {
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "ok": ok,
        "total": total,
        "tests": {name: status for name, status, *_ in results},
    }
    (BASELINE_DIR / "golden.json").write_text(
        json.dumps(golden_data, indent=2), encoding="utf-8"
    )

    # Log to journal
    _journal_append({
        "command": "golden",
        "score": f"{ok}/{total}",
        "tests": {name: status for name, status, *_ in results},
        "failures": {name: diag for name, diag in fail_details},
    })
    print(f"\nBaseline + journal saved to .ir_doctor/")

    return 0 if ok == total else 1


def cmd_worklist(args: argparse.Namespace) -> int:
    """Show functions that need recursive rewrite due to alloca aliasing.

    Filters to only REAL alias bugs (no write-back), sorted by severity.
    This is a direct work queue for the .mn source fixes.
    """
    text = pathlib.Path(args.file).read_text(encoding="utf-8")
    mod = parse_ir(text)

    if args.only:
        mod.functions = {k: v for k, v in mod.functions.items() if args.only in k}

    pathologies = run_audit(mod)

    # Real alias bugs (no write-back)
    real_alias = [p for p in pathologies if p.code == "ALLOCA_ALIAS"]
    mitigated = [p for p in pathologies if p.code == "ALLOCA_ALIAS_MITIGATED"]
    loop_push = [p for p in pathologies if p.code == "LOOP_PUSH"]

    print(f"Alloca Aliasing Work Queue")
    print("=" * 72)
    print(f"  Real bugs (need recursive rewrite): {len(real_alias)}")
    print(f"  Mitigated (write-back exists):      {len(mitigated)}")
    print(f"  For-loop push patterns (all):       {len(loop_push)}")

    if real_alias:
        print(f"\nFunctions needing recursive rewrite:")
        print("-" * 72)
        for p in sorted(real_alias, key=lambda p: p.function):
            fn = mod.functions.get(p.function)
            # Map to .mn module name
            parts = p.function.split("__", 1)
            mn_module = parts[0] if len(parts) > 1 else "?"
            mn_func = parts[1] if len(parts) > 1 else p.function
            size = fn.instructions if fn else 0
            pushes = fn.list_pushes if fn else 0
            print(f"  {mn_module + '/' + mn_func:<50s} {size:>5d} instr  {pushes:>2d} push")

    if mitigated:
        print(f"\nMitigated (probably safe, verify manually):")
        print("-" * 72)
        for p in sorted(mitigated, key=lambda p: p.function):
            parts = p.function.split("__", 1)
            mn_module = parts[0] if len(parts) > 1 else "?"
            mn_func = parts[1] if len(parts) > 1 else p.function
            print(f"  {mn_module + '/' + mn_func:<50s} (write-back)")

    return 1 if real_alias else 0


def cmd_extract(args: argparse.Namespace) -> int:
    """Extract and display a single function's IR from a .ll file.

    Replaces manual `sed -n '/^define.*funcname/,/^}/p' file.ll` piping.
    """
    text = pathlib.Path(args.file).read_text(encoding="utf-8")
    mod = parse_ir(text)

    name = args.func_name
    # Find by exact match or substring
    fn = mod.functions.get(name)
    if not fn:
        matches = [f for f in mod.functions.values() if name in f.name]
        if len(matches) == 1:
            fn = matches[0]
        elif len(matches) > 1:
            print(f"Ambiguous: {name} matches {len(matches)} functions:")
            for m in matches[:20]:
                print(f"  {m.name}")
            return 1
        else:
            print(f"Function not found: {name}")
            print(f"Available ({len(mod.functions)}):")
            for n in sorted(mod.functions)[:30]:
                print(f"  {n}")
            if len(mod.functions) > 30:
                print(f"  ... and {len(mod.functions) - 30} more")
            return 1

    # Print signature + body
    print(f"{fn.signature} {{")
    print(fn.body)
    print("}")

    # Print metrics summary
    print(f"\n--- {fn.name} ---")
    print(f"  Lines: {fn.line_start}-{fn.line_end}  Instr: {fn.instructions}  "
          f"BB: {fn.basic_blocks}  Alloc: {fn.allocas}  Stack: {fn.alloca_bytes}B")
    print(f"  Calls: {fn.calls}  Switch: {fn.switches}  Push: {fn.list_pushes}  "
          f"StrEq: {fn.str_eqs}  Hash: {fn.body_hash}")

    # Run detectors on just this function
    single_mod = IRModule(source="", functions={fn.name: fn})
    pathologies = run_audit(single_mod)
    if pathologies:
        print(f"\n  Issues ({len(pathologies)}):")
        for p in pathologies:
            print(f"    [{_severity_icon(p.severity)}] {p.code}: {p.message}")

    return 0


def cmd_selftest(args: argparse.Namespace) -> int:
    """Test self-compilation: compile mnc_all.mn through stage1.

    Reports: how many lines of IR were produced, how many functions
    were emitted, whether llvm-as validates, and memory usage.
    """
    stage1 = pathlib.Path(args.stage1)
    mnc_all = ROOT / "mapanare" / "self" / "mnc_all.mn"

    if not stage1.exists():
        print(f"Stage1 binary not found: {stage1}", file=sys.stderr)
        return 1
    if not mnc_all.exists():
        print(f"mnc_all.mn not found. Run: python scripts/concat_self.py", file=sys.stderr)
        return 1

    print(f"Self-compiling {mnc_all.name} ({mnc_all.stat().st_size // 1024} KB)...")

    # Compile with timeout and memory tracking
    import time as _time
    t0 = _time.monotonic()
    try:
        r = subprocess.run(
            [str(stage1), str(mnc_all)],
            capture_output=True, text=True, timeout=300,
        )
        elapsed = _time.monotonic() - t0
        ir = r.stdout
        exit_code = r.returncode
    except subprocess.TimeoutExpired:
        print("TIMEOUT (300s)")
        return 1
    except OSError as e:
        print(f"Cannot run stage1: {e}")
        return 1

    n_lines = ir.count("\n")
    mod = parse_ir(ir)
    n_fns = len(mod.functions)
    n_declares = len(mod.declares)
    n_structs = len(mod.struct_types)

    print(f"  Exit code:  {exit_code}")
    print(f"  Time:       {elapsed:.1f}s")
    print(f"  IR lines:   {n_lines}")
    print(f"  Functions:  {n_fns}")
    print(f"  Declares:   {n_declares}")
    print(f"  Structs:    {n_structs}")

    if n_fns > 0:
        valid, err = validate_ir(ir)
        print(f"  llvm-as:    {'VALID' if valid else 'INVALID: ' + err}")
        pathologies = run_audit(mod)
        n_errs = sum(1 for p in pathologies if p.severity == "error")
        n_warns = sum(1 for p in pathologies if p.severity == "warning")
        print(f"  Errors:     {n_errs}")
        print(f"  Warnings:   {n_warns}")
    else:
        print(f"  (No functions emitted — header only)")
        if r.stderr:
            print(f"  stderr: {r.stderr[:200]}")

    # Compare with bootstrap
    print(f"\n--- Bootstrap comparison ---")
    try:
        boot_ir = bootstrap_compile(mnc_all)
        boot_mod = parse_ir(boot_ir)
        print(f"  Bootstrap functions: {len(boot_mod.functions)}")
        if n_fns > 0:
            diffs = diff_modules(boot_mod, mod)
            matched = sum(1 for d in diffs if d.status == "match")
            print(f"  Matching:           {matched}/{len(diffs)}")
    except Exception as e:
        print(f"  Bootstrap failed: {e}")

    return 0 if exit_code == 0 and n_fns > 0 else 1


def cmd_memory(args: argparse.Namespace) -> int:
    """Test memory scaling: compile synthetic inputs of increasing size.

    Generates .mn files with N functions and measures peak RSS.
    Helps detect O(N^2) memory regressions.
    """
    stage1 = pathlib.Path(args.stage1)

    if not stage1.exists():
        print(f"Stage1 binary not found: {stage1}", file=sys.stderr)
        return 1

    sizes = [10, 50, 100, 200, 500]
    print(f"{'Fns':>5s} {'Lines':>6s} {'RSS MB':>7s} {'Time':>6s} {'IR Lines':>8s} {'Exit':>5s}")
    print("-" * 45)

    import time as _time
    for n_fns in sizes:
        # Generate synthetic .mn file with N functions
        lines = []
        for i in range(n_fns):
            lines.append(f"fn f{i}(x: Int) -> Int {{ return x + {i} }}")
        lines.append("fn main() { print(str(f0(42))) }")
        source = "\n".join(lines)
        n_lines = len(lines)

        with tempfile.NamedTemporaryFile(suffix=".mn", mode="w", delete=False, encoding="utf-8") as f:
            f.write(source)
            tmp = f.name

        try:
            t0 = _time.monotonic()
            # Use /usr/bin/time for RSS on Linux, fallback to no-RSS on other platforms
            try:
                r = subprocess.run(
                    ["/usr/bin/time", "-f", "%M", str(stage1), tmp],
                    capture_output=True, text=True, timeout=120,
                )
                elapsed = _time.monotonic() - t0
                # /usr/bin/time writes RSS to stderr
                rss_lines = [l for l in r.stderr.strip().splitlines() if l.strip().isdigit()]
                rss_kb = int(rss_lines[-1]) if rss_lines else 0
                rss_mb = rss_kb / 1024
            except (FileNotFoundError, OSError):
                r = subprocess.run(
                    [str(stage1), tmp],
                    capture_output=True, text=True, timeout=120,
                )
                elapsed = _time.monotonic() - t0
                rss_mb = 0

            ir_lines = r.stdout.count("\n") if r.returncode == 0 else 0
            exit_code = r.returncode
            print(f"{n_fns:>5d} {n_lines:>6d} {rss_mb:>7.1f} {elapsed:>5.1f}s {ir_lines:>8d} {exit_code:>5d}")
        except subprocess.TimeoutExpired:
            print(f"{n_fns:>5d} {n_lines:>6d}     TIMEOUT")
        finally:
            pathlib.Path(tmp).unlink(missing_ok=True)

    return 0


def cmd_journal(args: argparse.Namespace) -> int:
    """View the debug journal — history of golden/audit runs with results.

    Shows what was tried, what score was achieved, and failure details.
    Prevents repeating the same failed approaches across sessions.
    """
    entries = _journal_load(limit=args.top or 20)
    if not entries:
        print("No journal entries yet. Run 'golden' or 'audit' to start logging.")
        return 0

    search = args.only
    for e in entries:
        ts = e.get("timestamp", "?")[:19]
        cmd = e.get("command", "?")

        if search and search.lower() not in json.dumps(e).lower():
            continue

        if cmd == "golden":
            score = e.get("score", "?")
            tests = e.get("tests", {})
            fails = {k: v for k, v in tests.items() if v != "OK"}
            print(f"[{ts}] golden {score}")
            if fails:
                for name, status in fails.items():
                    # Show failure category if available
                    fd = e.get("failures", {}).get(name, {})
                    cat = fd.get("category", fd.get("crash", ""))
                    extra = f" ({cat})" if cat else ""
                    print(f"  FAIL {name}: {status}{extra}")
        elif cmd == "audit":
            f = e.get("file", "?")
            errs = e.get("errors", 0)
            n_fn = e.get("functions", 0)
            by_code = e.get("by_code", {})
            codes = ", ".join(f"{k}={v}" for k, v in sorted(by_code.items()) if v > 0)
            print(f"[{ts}] audit {f} ({n_fn} fn, {errs} errors: {codes})")
        elif cmd == "note":
            print(f"[{ts}] NOTE: {e.get('text', '?')}")
        else:
            print(f"[{ts}] {cmd}: {json.dumps(e)[:100]}")
    return 0


def cmd_note(args: argparse.Namespace) -> int:
    """Add a manual note to the debug journal.

    Use this to record what you tried, what worked, what didn't.
    Example: ir_doctor note "Tried disabling _clone_list_fields — closures still crash"
    """
    text = " ".join(args.text)
    _journal_append({"command": "note", "text": text})
    print(f"Note saved: {text}")
    return 0


def cmd_structmap(args: argparse.Namespace) -> int:
    """Map struct field offsets to Mapanare field names.

    Parses all struct definitions from mapanare/self/*.mn and shows
    byte-level layout. Optionally resolves a specific byte offset.

    Examples:
        ir_doctor structmap LowerState           # Show full layout
        ir_doctor structmap LowerState --offset 128  # What field is at byte 128?
        ir_doctor structmap                      # List all structs with sizes
    """
    # Parse all .mn source files for struct definitions
    all_source = ""
    for mn_file in sorted(SELF_DIR.glob("*.mn")):
        if mn_file.name == "mnc_all.mn":
            continue
        all_source += mn_file.read_text(encoding="utf-8") + "\n"

    structs = parse_mn_structs(all_source)
    if not structs:
        print("No struct definitions found")
        return 1

    target = args.struct_name if hasattr(args, "struct_name") and args.struct_name else None
    offset = args.offset if hasattr(args, "offset") and args.offset is not None else None

    if target:
        layout = structs.get(target)
        if not layout:
            # Try substring match
            matches = [s for s in structs if target in s]
            if len(matches) == 1:
                layout = structs[matches[0]]
            elif matches:
                print(f"Ambiguous: '{target}' matches: {', '.join(matches)}")
                return 1
            else:
                print(f"Struct '{target}' not found. Available:")
                for s in sorted(structs):
                    print(f"  {s} ({structs[s].total_size}B, {len(structs[s].fields)} fields)")
                return 1

        print(format_struct_layout(layout))
        if offset is not None:
            print(f"\n  Offset {offset}: {field_at_offset(layout, offset)}")
    else:
        # List all structs
        print(f"{'Struct':<35s} {'Size':>6s} {'Fields':>6s}  {'Field Names'}")
        print("-" * 100)
        for name in sorted(structs):
            s = structs[name]
            field_names = ", ".join(f.name for f in s.fields)
            if len(field_names) > 50:
                field_names = field_names[:47] + "..."
            print(f"{name:<35s} {s.total_size:>5d}B {len(s.fields):>6d}  {field_names}")

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
    s_audit = sub.add_parser("audit", help="Audit IR file for known pathologies + save baseline")
    s_audit.add_argument("file", help="Path to .ll file")

    # check
    s_check = sub.add_parser("check", help="Validate IR file with llvm-as")
    s_check.add_argument("file", help="Path to .ll file")

    # golden
    sub.add_parser("golden", help="Fresh compile + validate + audit ALL golden tests (WSL)")

    # worklist
    s_wl = sub.add_parser("worklist", help="Functions needing recursive rewrite (alloca alias bugs)")
    s_wl.add_argument("file", help="Path to .ll file")

    # extract
    s_ext = sub.add_parser("extract", help="Extract one function's IR from a .ll file")
    s_ext.add_argument("file", help="Path to .ll file")
    s_ext.add_argument("func_name", help="Function name (exact or substring)")

    # selftest
    sub.add_parser("selftest", help="Self-compile mnc_all.mn through stage1 (WSL)")

    # memory
    sub.add_parser("memory", help="Test memory scaling with synthetic inputs (WSL)")

    # structmap
    s_sm = sub.add_parser("structmap", help="Map struct byte offsets to field names")
    s_sm.add_argument("struct_name", nargs="?", default=None, help="Struct name (optional)")
    s_sm.add_argument("--offset", type=int, default=None, help="Byte offset to resolve")

    # journal
    sub.add_parser("journal", help="View debug journal (history of runs + notes)")

    # note
    s_note = sub.add_parser("note", help="Add a note to the debug journal")
    s_note.add_argument("text", nargs="+", help="Note text")

    # valgrind
    s_vg = sub.add_parser("valgrind", help="Run valgrind + auto-map crash to struct fields (WSL)")
    s_vg.add_argument("test_file", help="Path to .mn test file")
    s_vg.add_argument("--struct", default="LowerState", help="Struct to map offsets against")
    s_vg.add_argument("-v", "--verbose", action="store_true", help="Show raw valgrind output")

    # diff
    s_diff = sub.add_parser("diff", help="Compare bootstrap vs stage1 for a .mn file")
    s_diff.add_argument("file", help="Path to .mn file")

    # diff-ir
    s_dir = sub.add_parser("diff-ir", help="Compare two .ll files directly")
    s_dir.add_argument("file_a", help="First .ll file (e.g. bootstrap output)")
    s_dir.add_argument("file_b", help="Second .ll file (e.g. stage1 output)")

    # diff-all
    sub.add_parser("diff-all", help="Compare all golden tests")

    # stage2
    s_s2 = sub.add_parser("stage2", help="Compile self-hosted modules through mnc-stage1, validate stage2 IR")
    s_s2.add_argument("--timeout", type=int, default=30, help="Per-module timeout in seconds")

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
        "check": cmd_check,
        "golden": cmd_golden,
        "worklist": cmd_worklist,
        "extract": cmd_extract,
        "selftest": cmd_selftest,
        "memory": cmd_memory,
        "structmap": cmd_structmap,
        "journal": cmd_journal,
        "note": cmd_note,
        "valgrind": cmd_valgrind,
        "diff": cmd_diff,
        "diff-ir": cmd_diff_ir,
        "diff-all": cmd_diff_all,
        "stage2": cmd_stage2,
        "snapshot": cmd_snapshot,
        "table": cmd_table,
        "fingerprint": cmd_fingerprint,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
