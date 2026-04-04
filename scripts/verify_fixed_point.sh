#!/usr/bin/env bash
# verify_fixed_point.sh — Three-stage bootstrap verification.
# Proves: the self-hosted compiler compiles itself to identical output.
#
# Stage 0: Python compiles mnc_all.mn → stage1 binary (C backend + gcc)
# Stage 1: stage1 compiles mnc_all.mn → stage2.ll
# Stage 2: stage2 binary compiles mnc_all.mn → stage3.ll
# Verify: stage2.ll == stage3.ll (fixed point)

set -euo pipefail
cd "$(dirname "$0")/.."

YELLOW='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SOURCE=mapanare/self/mnc_all.mn
RUNTIME_C=runtime/native/mapanare_core.c
DRIVER_C=runtime/native/mnc_driver.c
RUNTIME_INC=runtime/native

KEEP=0
if [ "${1:-}" = "--keep" ]; then KEEP=1; fi

echo -e "${YELLOW}=== Three-Stage Fixed Point Verification ===${NC}"
echo ""

# Stage 0: Python → stage1
echo -e "${YELLOW}[Stage 0] Python compiles self-hosted source → stage1 binary${NC}"
python3 scripts/concat_self.py
python3 -m mapanare emit-c "$SOURCE" -o /tmp/stage1.c
gcc -O0 -I "$RUNTIME_INC" /tmp/stage1.c "$RUNTIME_C" -o /tmp/mnc-stage1 -lm -lpthread
echo "  stage1: $(wc -c < /tmp/mnc-stage1) bytes"

# Stage 1: stage1 → stage2.ll
echo -e "${YELLOW}[Stage 1] stage1 compiles self-hosted source → stage2.ll${NC}"
ulimit -s unlimited
/tmp/mnc-stage1 "$SOURCE" > /tmp/stage2.ll
STAGE2_LINES=$(wc -l < /tmp/stage2.ll)
echo "  stage2.ll: ${STAGE2_LINES} lines"

# Validate stage2
echo -n "  llvm-as: "
if llvm-as /tmp/stage2.ll -o /tmp/stage2.bc 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
    llvm-as /tmp/stage2.ll -o /dev/null 2>&1 | head -5
    exit 1
fi

# Build stage2 binary
echo -n "  llc+gcc: "
llc /tmp/stage2.bc -o /tmp/stage2.o -filetype=obj -relocation-model=pic
gcc /tmp/stage2.o "$DRIVER_C" "$RUNTIME_C" -I "$RUNTIME_INC" -o /tmp/mnc-stage2 -lm -lpthread
echo -e "${GREEN}OK${NC} ($(wc -c < /tmp/mnc-stage2) bytes)"

# Stage 2: stage2 → stage3.ll
echo -e "${YELLOW}[Stage 2] stage2 compiles self-hosted source → stage3.ll${NC}"
/tmp/mnc-stage2 "$SOURCE" > /tmp/stage3.ll
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
    if [ "$KEEP" -eq 1 ]; then
        echo "  Kept: /tmp/stage2.ll /tmp/stage3.ll /tmp/mnc-stage1 /tmp/mnc-stage2"
    fi
    exit 0
else
    echo -e "${RED}  ✗ NOT AT FIXED POINT${NC}"
    echo "  ${DIFF_LINES} lines differ"
    diff /tmp/stage2.ll /tmp/stage3.ll | head -20
    exit 1
fi
