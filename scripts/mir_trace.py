#!/usr/bin/env python3
"""MIR Trace — trace type flow through the MIR for a specific function.

Helps debug type inference issues by showing what types the Python lowerer
assigns to each MIR value, instruction, and return. Compares with what the
self-hosted compiler would produce.

Usage:
    # Trace a golden test function through the Python lowerer
    python scripts/mir_trace.py tests/golden/10_result.mn divide

    # Trace a function and show full instruction details
    python scripts/mir_trace.py tests/golden/10_result.mn divide -v

    # Trace all functions in a file
    python scripts/mir_trace.py tests/golden/03_function.mn

    # Compare MIR types: Python lowerer vs stage1 IR types
    python scripts/mir_trace.py tests/golden/10_result.mn divide --compare

    # Dump raw MIR as JSON for a function
    python scripts/mir_trace.py tests/golden/10_result.mn divide --json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _type_str(ty: object) -> str:
    """Format a MIRType for display."""
    if ty is None:
        return "?"
    if hasattr(ty, "kind"):
        k = ty.kind
        if hasattr(k, "value"):
            k = k.value
        k = str(k)
        name = getattr(ty, "name", "")
        # Check for generic type args via type_info
        ti = getattr(ty, "type_info", None)
        args = getattr(ti, "args", []) if ti else []
        if not args:
            args = getattr(ty, "args", [])
        if args:
            arg_strs = [_type_str(a) for a in args]
            return f"{name}<{', '.join(arg_strs)}>"
        # Use friendly names for common types
        friendly = {
            "1": "Int", "2": "Float", "3": "Bool", "4": "String",
            "5": "List", "6": "Void", "7": "Fn", "8": "Option",
            "9": "Struct", "10": "Result", "11": "Agent", "12": "Signal",
            "13": "Stream", "14": "Map", "0": "Unknown", "15": "Enum",
            "16": "Tensor", "17": "Char",
        }
        display = friendly.get(k, name or k)
        if name and name not in ("Int", "Float", "Bool", "String", "Void",
                                  "List", "Option", "Result", "Unknown"):
            return f"{name}"  # struct/enum name
        return display
    return str(ty)


def _value_str(v: object) -> str:
    """Format a MIR Value for display."""
    name = getattr(v, "name", "?")
    ty = getattr(v, "ty", None)
    if ty:
        return f"{name}: {_type_str(ty)}"
    return name


def trace_function(source: str, filename: str, fn_name: str | None, verbose: bool = False) -> list[dict]:
    """Lower a .mn file and trace MIR types for one or all functions."""
    from mapanare.parser import parse
    from mapanare.semantic import SemanticChecker
    from mapanare.lower import MIRLowerer

    ast = parse(source, filename=filename)
    checker = SemanticChecker()
    _errors = checker.check(ast)
    lowerer = MIRLowerer()
    mir = lowerer.lower(ast)

    results = []
    for fn in mir.functions:
        if fn_name and fn_name not in fn.name:
            continue

        fn_data = {
            "name": fn.name,
            "params": [],
            "return_type": _type_str(fn.return_type),
            "blocks": [],
            "values": {},
        }

        for p in fn.params:
            fn_data["params"].append({"name": p.name, "type": _type_str(p.ty)})

        for bb in fn.blocks:
            block_data = {"label": bb.label, "instructions": []}
            for inst in bb.instructions:
                inst_type = type(inst).__name__
                inst_data = {"op": inst_type}

                # Extract dest/value types
                dest = getattr(inst, "dest", None)
                if dest:
                    inst_data["dest"] = _value_str(dest)
                    fn_data["values"][getattr(dest, "name", "?")] = _type_str(getattr(dest, "ty", None))

                # Extract specific fields based on instruction type
                val = getattr(inst, "value", None)
                if val and hasattr(val, "name"):
                    inst_data["value"] = _value_str(val)

                src = getattr(inst, "src", None)
                if src and hasattr(src, "name"):
                    inst_data["src"] = _value_str(src)

                fn_name_attr = getattr(inst, "fn_name", None)
                if fn_name_attr:
                    inst_data["fn_name"] = fn_name_attr

                args = getattr(inst, "args", None)
                if args and isinstance(args, list):
                    inst_data["args"] = [_value_str(a) for a in args if hasattr(a, "name")]

                lhs = getattr(inst, "lhs", None)
                rhs = getattr(inst, "rhs", None)
                if lhs and hasattr(lhs, "name"):
                    inst_data["lhs"] = _value_str(lhs)
                if rhs and hasattr(rhs, "name"):
                    inst_data["rhs"] = _value_str(rhs)

                # WrapOk/WrapErr
                ok_val = getattr(inst, "ok_value", None) or getattr(inst, "value", None)
                if inst_type in ("WrapOk", "WrapErr") and ok_val and hasattr(ok_val, "name"):
                    inst_data["wrapped"] = _value_str(ok_val)

                # EnumPayload
                variant = getattr(inst, "variant", None)
                if variant:
                    inst_data["variant"] = variant

                # Type info
                ty = getattr(inst, "ty", None) or getattr(inst, "alloca_type", None)
                if ty:
                    inst_data["type"] = _type_str(ty)

                if verbose:
                    block_data["instructions"].append(inst_data)
                else:
                    # Compact: only show instructions that define values
                    if dest or inst_type in ("Return", "Jump", "Branch", "Switch"):
                        block_data["instructions"].append(inst_data)

            fn_data["blocks"].append(block_data)
        results.append(fn_data)

    return results


def format_trace(traces: list[dict], verbose: bool = False) -> str:
    """Format MIR trace as human-readable output."""
    lines = []
    for fn in traces:
        params = ", ".join(f"{p['name']}: {p['type']}" for p in fn["params"])
        lines.append(f"fn {fn['name']}({params}) -> {fn['return_type']} {{")

        for bb in fn["blocks"]:
            lines.append(f"  {bb['label']}:")
            for inst in bb["instructions"]:
                op = inst["op"]
                dest = inst.get("dest", "")
                parts = [f"    {dest} = {op}" if dest else f"    {op}"]

                for key in ("fn_name", "value", "src", "lhs", "rhs", "wrapped", "variant", "type"):
                    if key in inst and key != "dest":
                        parts.append(f"{key}={inst[key]}")

                if "args" in inst and inst["args"]:
                    parts.append(f"args=[{', '.join(inst['args'])}]")

                lines.append(" ".join(parts))

        lines.append("}")
        lines.append("")

        # Value type summary
        if fn["values"]:
            lines.append(f"  Value types in {fn['name']}:")
            for vname, vtype in sorted(fn["values"].items()):
                lines.append(f"    {vname:30s} {vtype}")
            lines.append("")

    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(
        prog="mir_trace",
        description="Trace MIR type flow through the Python lowerer",
    )
    p.add_argument("file", help="Path to .mn source file")
    p.add_argument("function", nargs="?", default=None, help="Function name (substring match)")
    p.add_argument("-v", "--verbose", action="store_true", help="Show all instructions")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.add_argument("--compare", action="store_true",
                   help="Compare with stage1 IR types (requires mnc-stage1)")
    p.add_argument("--stage1", default=str(ROOT / "mapanare" / "self" / "mnc-stage1"))

    args = p.parse_args()

    source = pathlib.Path(args.file).read_text(encoding="utf-8")
    traces = trace_function(source, args.file, args.function, verbose=args.verbose)

    if not traces:
        print(f"No functions found" + (f" matching '{args.function}'" if args.function else ""))
        return 1

    if args.json:
        print(json.dumps(traces, indent=2))
    else:
        print(format_trace(traces, verbose=args.verbose))

    if args.compare:
        # Also compile through stage1 and compare types
        print("--- Stage1 IR comparison ---")
        try:
            # Import ir_doctor's parse_ir and stage1_compile
            sys.path.insert(0, str(ROOT / "scripts"))
            from ir_doctor import parse_ir, stage1_compile

            ir = stage1_compile(args.file, args.stage1)
            if ir:
                mod = parse_ir(ir)
                for fn_trace in traces:
                    fn_name = fn_trace["name"]
                    ir_fn = mod.functions.get(fn_name)
                    if ir_fn:
                        print(f"\n  {fn_name}:")
                        print(f"    MIR return: {fn_trace['return_type']}")
                        # Extract return type from IR signature
                        import re
                        sig_m = re.match(r"define\s+(?:internal\s+)?(?:dso_local\s+)?(.+?)\s+@", ir_fn.signature)
                        if sig_m:
                            print(f"    IR  return: {sig_m.group(1).strip()}")
                        print(f"    IR  instrs: {ir_fn.instructions}")
                        print(f"    IR  switch: {ir_fn.switches}")
                    else:
                        print(f"\n  {fn_name}: NOT FOUND in stage1 IR")
            else:
                print("  Stage1 compilation failed")
        except Exception as e:
            print(f"  Compare failed: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
