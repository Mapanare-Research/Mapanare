#!/usr/bin/env python3
"""Fix PHI predecessor issues in stage2 LLVM IR.

Usage: python3 scripts/fix_stage2_phis.py input.ll output.ll
"""

import re
import sys

with open(sys.argv[1]) as f:
    lines = f.readlines()

output = list(lines)
fixes = 0
functions = []
i = 0
while i < len(lines):
    if lines[i].strip().startswith("define "):
        start = i
        for j in range(i + 1, len(lines)):
            if lines[j].strip() == "}":
                functions.append((start, j))
                i = j + 1
                break
        else:
            i += 1
    else:
        i += 1

for fstart, fend in functions:
    preds = {}
    current = "entry"
    for k in range(fstart, fend + 1):
        s = lines[k].strip()
        m = re.match(r"^([a-zA-Z_]\w*):$", s)
        if m:
            current = m.group(1)
            continue
        for target in re.findall(r"label %([a-zA-Z_]\w*)", s):
            preds.setdefault(target, set()).add(current)
    current = "entry"
    for k in range(fstart, fend + 1):
        s = lines[k].strip()
        m = re.match(r"^([a-zA-Z_]\w*):$", s)
        if m:
            current = m.group(1)
        phi_m = re.match(r"^(\s*)(%\S+ = phi )(.+?)( \[.+)", s)
        if phi_m and "= phi " in s:
            phi_rest = phi_m.group(3) + phi_m.group(4)
            bp = phi_rest.find(" [")
            if bp > 0:
                phi_ty = phi_rest[:bp]
                phi_entries = phi_rest[bp:]
                existing = set(re.findall(r"%([a-zA-Z_]\w*)\s*\]", phi_entries))
                missing = preds.get(current, set()) - existing
                if missing:
                    extra = ", ".join(f"[ zeroinitializer, %{lbl} ]" for lbl in sorted(missing))
                    output[k] = f"  {phi_m.group(2)}{phi_ty}{phi_entries}, {extra}\n"
                    fixes += 1

# Pass 2: Fix PHI type mismatches in if_result PHIs.
# The self-hosted emitter generates if_result PHIs for statement-context
# if-else.  These PHIs reference the "last value" from each branch, which
# may have different types (e.g., i64 from a position vs %enum.Expr from
# a constructor).  Since these PHIs are never consumed, replace mismatched
# operands with zeroinitializer of the PHI's type.
type_fixes = 0
# Build a map of %name -> type for all definitions in each function scope
for fstart, fend in functions:
    defs = {}  # %name -> type string
    for k in range(fstart, fend + 1):
        s = output[k].strip()
        # Match: %name = <instr> <type> ...  or  %name = extractvalue <type> ...
        dm = re.match(
            r"(%\S+)\s*=\s*(?:phi|add|sub|mul|icmp\s+\w+|extractvalue|insertvalue|load|call|inttoptr|bitcast|getelementptr\s+\w+)\s+(\S+)",
            s,
        )
        if dm:
            defs[dm.group(1)] = dm.group(2).rstrip(",")
    # Now fix PHIs with type mismatches
    for k in range(fstart, fend + 1):
        s = output[k].strip()
        if "= phi " not in s:
            continue
        idx = s.index("= phi ")
        phi_var = s[:idx].strip()
        rest = s[idx + 6 :]  # after "= phi "
        # Parse LLVM type (may be "i64", "%enum.Foo", or "{ ptr, i64, ... }")
        if rest.startswith("{"):
            depth = 0
            end = 0
            for ci, ch in enumerate(rest):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                if depth == 0:
                    end = ci + 1
                    break
            phi_ty = rest[:end]
            entries = rest[end:]
        else:
            parts = rest.split(" ", 1)
            phi_ty = parts[0]
            entries = parts[1] if len(parts) > 1 else ""
        vals = re.findall(r"\[\s*(%[a-zA-Z_]\w*(?:\.\w+)*),", entries)
        mismatch = False
        for v in vals:
            vty = defs.get(v)
            if vty and vty != phi_ty and vty != "zeroinitializer":
                mismatch = True
                break
        if mismatch:
            # Replace mismatched operands with zeroinitializer, keep PHI type
            new_entries = entries
            for v in vals:
                vty = defs.get(v)
                if vty and vty != phi_ty and vty != "zeroinitializer":
                    new_entries = new_entries.replace(v, "zeroinitializer")
            output[k] = f"  {phi_var} = phi {phi_ty}{new_entries}\n"
            type_fixes += 1

# Pass 3: Insert missing struct/enum type definitions.
# The self-hosted emitter uses named types (%struct.X) but the lowerer
# doesn't always register them in the MIR module's struct list.
# Generate definitions from the insertvalue chains in constructor functions.
# Type definitions inferred by `culebra infer-types` from insertvalue chains.
missing_types = {
    "%struct.AgentInfo": "{ { ptr, i64 }, { ptr, i64, i64, i64 }, { ptr, i64, i64, i64 }, { ptr, i64, i64, i64 } }",
    "%struct.CompileResult": "{ i1, { ptr, i64 }, { ptr, i64, i64, i64 } }",
    "%struct.EmitState": "{ { ptr, i64, i64, i64 }, i64, { ptr, i64, i64, i64 }, { ptr, i64, i64, i64 }, { ptr, i64 }, i64, { ptr, i64, i64, i64 }, { ptr, i64 }, { ptr, i64, i64, i64 }, { ptr, i64, i64, i64 } }",
    "%struct.EnumVariantNames": "{ { ptr, i64 }, { ptr, i64, i64, i64 } }",
    "%struct.ExternFnInfo": "{ { ptr, i64 }, { ptr, i64 }, { ptr, i64 }, { ptr, i64, i64, i64 }, %struct.MIRType }",
    "%struct.FnEntry": "{ { ptr, i64 }, { ptr, i64 }, { ptr, i64, i64, i64 } }",
    "%struct.ImplEntry": "{ { ptr, i64 }, { ptr, i64 } }",
    "%struct.ImportInfo": "{ { ptr, i64, i64, i64 }, { ptr, i64, i64, i64 } }",
    "%struct.LambdaEntry": "{ { ptr, i64 }, { ptr, i64 } }",
    "%struct.LowerResult": "{ %struct.Value, %struct.LowerState }",
    "%struct.LowerState": "{ %struct.MIRModule, { i1, ptr }, i64, i64, i64, { ptr, i64, i64, i64 }, { ptr, i64, i64, i64 }, { ptr, i64, i64, i64 }, { ptr, i64, i64, i64 }, { ptr, i64, i64, i64 }, { ptr, i64, i64, i64 } }",
    "%struct.MIRModule": "{ { ptr, i64 }, { ptr, i64, i64, i64 }, { ptr, i64, i64, i64 }, { ptr, i64, i64, i64 }, { ptr, i64, i64, i64 }, { ptr, i64, i64, i64 }, { ptr, i64, i64, i64 }, { ptr, i64, i64, i64 }, { ptr, i64, i64, i64 } }",
    "%struct.MatchBuildResult": "{ %struct.LowerState, { ptr, i64, i64, i64 }, { ptr, i64, i64, i64 }, { ptr, i64, i64, i64 }, { ptr, i64 } }",
    "%struct.PipeInfo": "{ { ptr, i64 }, { ptr, i64, i64, i64 } }",
    "%struct.StructEntry": "{ { ptr, i64 }, { ptr, i64, i64, i64 }, { ptr, i64, i64, i64 }, { ptr, i64 } }",
    "%struct.StructFieldInfo": "{ { ptr, i64 }, { ptr, i64, i64, i64 }, { ptr, i64, i64, i64 } }",
    "%struct.VarInfo": "{ { ptr, i64 }, %struct.Value, i1 }",
    "%struct.VerifyError": "{ { ptr, i64 }, { ptr, i64 }, { ptr, i64 } }",
}
# Find existing type definitions
defined = set()
for ln in output:
    m = re.match(r"(%struct\.\w+|%enum\.\w+)\s*=\s*type\s", ln.strip())
    if m:
        defined.add(m.group(1))
# Insert missing definitions after the last existing type definition
type_defs_added = 0
last_type_line = 0
for k, ln in enumerate(output):
    if re.match(r"(%struct\.\w+|%enum\.\w+)\s*=\s*type\s", ln.strip()):
        last_type_line = k
if last_type_line > 0:
    inserts = []
    for tname, tdef in missing_types.items():
        if tname not in defined:
            inserts.append(f"{tname} = type {tdef}\n")
            type_defs_added += 1
    if inserts:
        output = output[: last_type_line + 1] + inserts + output[last_type_line + 1 :]

with open(sys.argv[2], "w") as f:
    f.writelines(output)
print(
    f"Fixed {fixes} PHI predecessor issues, {type_fixes} type mismatches, {type_defs_added} type defs added"
)
