#!/usr/bin/env python3
"""Fix PHI predecessor issues in stage2 LLVM IR.

Usage: python3 scripts/fix_stage2_phis.py input.ll output.ll
"""
import re, sys

with open(sys.argv[1]) as f:
    lines = f.readlines()

output = list(lines)
fixes = 0
functions = []
i = 0
while i < len(lines):
    if lines[i].strip().startswith('define '):
        start = i
        for j in range(i+1, len(lines)):
            if lines[j].strip() == '}':
                functions.append((start, j)); i = j + 1; break
        else: i += 1
    else: i += 1

for fstart, fend in functions:
    preds = {}
    current = "entry"
    for k in range(fstart, fend + 1):
        s = lines[k].strip()
        m = re.match(r'^([a-zA-Z_]\w*):$', s)
        if m: current = m.group(1); continue
        for target in re.findall(r'label %([a-zA-Z_]\w*)', s):
            preds.setdefault(target, set()).add(current)
    current = "entry"
    for k in range(fstart, fend + 1):
        s = lines[k].strip()
        m = re.match(r'^([a-zA-Z_]\w*):$', s)
        if m: current = m.group(1)
        phi_m = re.match(r'^(\s*)(%\S+ = phi )(.+?)( \[.+)', s)
        if phi_m and '= phi ' in s:
            phi_rest = phi_m.group(3) + phi_m.group(4)
            bp = phi_rest.find(' [')
            if bp > 0:
                phi_ty = phi_rest[:bp]
                phi_entries = phi_rest[bp:]
                existing = set(re.findall(r'%([a-zA-Z_]\w*)\s*\]', phi_entries))
                missing = preds.get(current, set()) - existing
                if missing:
                    extra = ", ".join(f"[ zeroinitializer, %{lbl} ]" for lbl in sorted(missing))
                    output[k] = f"  {phi_m.group(2)}{phi_ty}{phi_entries}, {extra}\n"
                    fixes += 1

with open(sys.argv[2], "w") as f:
    f.writelines(output)
print(f"Fixed {fixes} PHI predecessor issues")
