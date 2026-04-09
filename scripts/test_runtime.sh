#!/bin/bash
# test_runtime.sh — Runtime correctness tests for the self-hosted compiler.
# Compiles each golden test through mnc-stage1 → LLVM → native, runs it,
# and compares output against the Python bootstrap.

set -euo pipefail
cd "$(dirname "$0")/.."

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

STAGE1=mapanare/self/mnc-stage1
RUNTIME_C=runtime/native/mapanare_core.c
RUNTIME_INC=runtime/native

ulimit -s unlimited 2>/dev/null || true

echo -e "${YELLOW}=== Runtime Correctness Tests ===${NC}"
echo ""

pass=0
fail=0
skip=0

for test in tests/golden/*.mn; do
    name=$(basename "$test" .mn)

    # Get expected output from Python bootstrap
    expected=$(python3 -m mapanare run "$test" 2>/dev/null) || { echo "  ${name}: SKIP (Python run failed)"; skip=$((skip+1)); continue; }

    # Compile through stage1
    "$STAGE1" "$test" > "/tmp/${name}.ll" 2>/dev/null || { echo -e "  ${name}: ${RED}FAIL${NC} (stage1 compile error)"; fail=$((fail+1)); continue; }

    # LLVM assemble
    llvm-as "/tmp/${name}.ll" -o "/tmp/${name}.bc" 2>/dev/null || { echo -e "  ${name}: ${RED}FAIL${NC} (llvm-as error)"; fail=$((fail+1)); continue; }

    # Generate object
    llc "/tmp/${name}.bc" -o "/tmp/${name}.o" -filetype=obj -relocation-model=pic 2>/dev/null || { echo -e "  ${name}: ${RED}FAIL${NC} (llc error)"; fail=$((fail+1)); continue; }

    # Link
    gcc "/tmp/${name}.o" "$RUNTIME_C" -I "$RUNTIME_INC" -o "/tmp/${name}_run" -lm -lpthread 2>/dev/null || { echo -e "  ${name}: ${RED}FAIL${NC} (link error)"; fail=$((fail+1)); continue; }

    # Run and compare
    got=$(timeout 10 "/tmp/${name}_run" 2>/dev/null) || true
    if [ "$got" = "$expected" ]; then
        echo -e "  ${name}: ${GREEN}PASS${NC}"
        pass=$((pass+1))
    else
        echo -e "  ${name}: ${RED}FAIL${NC}"
        echo "    expected: $(echo "$expected" | head -1)"
        echo "    got:      $(echo "$got" | head -1)"
        fail=$((fail+1))
    fi
done

echo ""
echo -e "${pass} passed, ${fail} failed, ${skip} skipped"

if [ "$fail" -gt 0 ]; then
    exit 1
fi
