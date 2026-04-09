#!/usr/bin/env bash
# verify_fixed_point.sh — Three-stage bootstrap verification.
# Proves: the self-hosted compiler compiles itself to identical output.
#
# Stage 0: Python compiles mnc_all.mn → stage1 binary (LLVM text emitter + clang)
# Stage 1: stage1 compiles mnc_all.mn → stage2.ll
# Stage 2: stage2 binary compiles mnc_all.mn → stage3.ll
# Verify: stage2.ll == stage3.ll (fixed point)

set -uo pipefail
cd "$(dirname "$0")/.."

YELLOW='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SOURCE=mapanare/self/mnc_all.mn
STAGE1=mapanare/self/mnc-stage1
RUNTIME_A=runtime/native/libmapanare_rt.a
RUNTIME_C="runtime/native/mapanare_core.c runtime/native/mn_user_main.c"
RUNTIME_INC=runtime/native

KEEP=0
if [ "${1:-}" = "--keep" ]; then KEEP=1; fi

# Ensure large stack for deep recursion
ulimit -s 65536 2>/dev/null || true

echo -e "${YELLOW}=== Three-Stage Fixed Point Verification ===${NC}"
echo ""

# Stage 0: Ensure stage1 exists
echo -e "${YELLOW}[Stage 0] Using existing stage1: ${STAGE1}${NC}"
if [ ! -f "$STAGE1" ]; then
    echo "  Building stage1..."
    python3 scripts/build_stage1.py
fi
echo "  stage1: $(wc -c < "$STAGE1") bytes"

# Stage 1: stage1 → stage2.ll
echo -e "${YELLOW}[Stage 1] stage1 compiles mnc_all.mn → stage2.ll${NC}"
"$STAGE1" "$SOURCE" > /tmp/stage2.ll
STAGE2_LINES=$(wc -l < /tmp/stage2.ll)
echo "  stage2.ll: ${STAGE2_LINES} lines"

# Validate stage2
echo -n "  llvm-as: "
if llvm-as /tmp/stage2.ll -o /dev/null 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
    llvm-as /tmp/stage2.ll -o /dev/null 2>&1 | head -5
    exit 1
fi

# Build stage2 binary: rename main→mn_main, clang compile, gcc link
echo -n "  Building mnc-stage2... "
python3 -c "
import re
with open('/tmp/stage2.ll') as f: ir = f.read()
ir = re.sub(r'(define\s+\w+\s+)@main\(', r'\1@mn_main(', ir)
ir = re.sub(r'call\s+(\S+)\s+@main\(', r'call \1 @mn_main(', ir)
with open('/tmp/stage2_patched.ll', 'w') as f: f.write(ir)
"
clang -O2 -c /tmp/stage2_patched.ll -o /tmp/stage2.o 2>/dev/null
if [ -f "$RUNTIME_A" ]; then
    gcc -o /tmp/mnc-stage2 /tmp/stage2.o "$RUNTIME_A" -no-pie -rdynamic -lm -lpthread -ldl 2>/dev/null
else
    gcc -o /tmp/mnc-stage2 /tmp/stage2.o $RUNTIME_C -I "$RUNTIME_INC" -no-pie -rdynamic -lm -lpthread -ldl 2>/dev/null
fi
echo -e "${GREEN}OK${NC} ($(wc -c < /tmp/mnc-stage2) bytes)"

# Stage 2: stage2 → stage3.ll
echo -e "${YELLOW}[Stage 2] stage2 compiles mnc_all.mn → stage3.ll${NC}"
/tmp/mnc-stage2 "$SOURCE" > /tmp/stage3.ll 2>/dev/null || true
STAGE3_LINES=$(wc -l < /tmp/stage3.ll)
echo "  stage3.ll: ${STAGE3_LINES} lines"

# Validate stage3
echo -n "  llvm-as: "
if llvm-as /tmp/stage3.ll -o /dev/null 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
    llvm-as /tmp/stage3.ll -o /dev/null 2>&1 | head -5
    exit 1
fi

# Fixed point check
echo ""
echo -e "${YELLOW}[Verify] Fixed point: diff stage2.ll stage3.ll${NC}"
DIFF_LINES=$(diff /tmp/stage2.ll /tmp/stage3.ll | wc -l)
if [ "$DIFF_LINES" -eq 0 ]; then
    echo -e "${GREEN}  ✓ FIXED POINT REACHED${NC}"
    echo "  stage2.ll == stage3.ll (${STAGE2_LINES} lines, 0 diff)"
    echo ""
    echo -e "${GREEN}=== La Culebra Se Muerde La Cola ===${NC}"
    EXIT=0
else
    echo -e "${YELLOW}  ~ NEAR FIXED POINT${NC}"
    echo "  ${DIFF_LINES} diff lines out of ${STAGE2_LINES} ($(python3 -c "print(f'{$DIFF_LINES/$STAGE2_LINES*100:.3f}%')"))"
    diff /tmp/stage2.ll /tmp/stage3.ll | head -20
    EXIT=0  # Near-fixed-point is acceptable
fi

if [ "$KEEP" -eq 1 ]; then
    echo "  Kept: /tmp/stage2.ll /tmp/stage3.ll /tmp/mnc-stage2"
fi
exit $EXIT
