#!/usr/bin/env python3
"""Post-process stage2 LLVM IR to fix structural issues from the self-hosted compiler.

The self-hosted compiler has a known COW state threading bug that puts merge block
instructions in the entry block. This script fixes:
1. Misplaced PHI: moves instructions after switch ] to the next label block
2. Empty blocks: adds unreachable terminator
3. Dead PHIs: removes PHI nodes that reference non-predecessor blocks
"""
import sys

def fix_stage2_ir(input_path: str, output_path: str) -> int:
    lines = open(input_path).readlines()
    output = []
    fixes = 0
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Fix 1: switch ] followed by instructions → move to merge block
        if stripped == ']' and i+1 < len(lines) and not lines[i+1].strip().endswith(':'):
            output.append(line)
            i += 1
            deferred = []
            while i < len(lines):
                s = lines[i].strip()
                if s.endswith(':') and not s.startswith(';') and not s.startswith('@'):
                    break
                deferred.append(lines[i])
                i += 1
            if deferred and i < len(lines):
                output.append(lines[i])  # merge label
                for d in deferred:
                    output.append(d)
                i += 1
                fixes += 1
            else:
                for d in deferred:
                    output.append(d)
            continue
        
        # Fix 2: empty block → add unreachable
        if stripped.endswith(':') and not stripped.startswith(';') and not stripped.startswith('@'):
            if i+1 < len(lines):
                ns = lines[i+1].strip()
                if (ns.endswith(':') and not ns.startswith(';') and not ns.startswith('@')) or ns == '}':
                    output.append(line)
                    output.append('  unreachable\n')
                    i += 1
                    fixes += 1
                    continue
        
        # Fix 3: dead PHI referencing %entry after switch split
        if '= phi' in stripped and '%entry' in stripped:
            # Check if this PHI value is used
            phi_name = stripped.split('=')[0].strip()
            # Search ahead for any use of this PHI
            used = False
            for j in range(i+1, min(i+500, len(lines))):
                if phi_name in lines[j] and '= phi' not in lines[j]:
                    used = True
                    break
                if lines[j].strip() == '}':
                    break
            if not used:
                i += 1
                fixes += 1
                continue
        
        output.append(line)
        i += 1
    
    with open(output_path, 'w') as f:
        f.writelines(output)
    return fixes

if __name__ == '__main__':
    inp = sys.argv[1] if len(sys.argv) > 1 else '/tmp/stage2.ll'
    out = sys.argv[2] if len(sys.argv) > 2 else '/tmp/stage2_fixed.ll'
    n = fix_stage2_ir(inp, out)
    print(f"Fixed {n} issues in {inp} → {out}")
