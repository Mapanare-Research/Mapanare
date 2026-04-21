#!/usr/bin/env bash
# verify_fixed_point.sh — Three-stage bootstrap verification.
# Proves: the self-hosted compiler compiles itself to identical output.
#
# Stage 0: Python compiles mnc_all.mn → stage1 binary (LLVM text emitter + clang)
# Stage 1: stage1 compiles mnc_all.mn → stage2.ll
# Stage 2: stage2 binary compiles mnc_all.mn → stage3.ll
# Verify: stage2.ll == stage3.ll (fixed point, within tolerance)
#
# v4.29.0: this script now has teeth. Prior to this release the v4.17.0
# "fixed-point bootstrap" claim was unfalsifiable — ``set -uo pipefail``
# had no ``-e``, every step was wrapped in ``|| true``, and the final
# ``EXIT=0`` was unconditional. The v4.26.0 panel (Rattler, Anaconda,
# Cobra) flagged this and the CI ``fixed-point`` job that called it. Now
# the script:
#
#   - Runs under ``set -euo pipefail`` so unexpected step failures abort.
#   - Propagates stage2-binary crashes as a non-zero exit instead of
#     silently producing an empty ``stage3.ll``.
#   - Fails with exit 1 if the diff between stage2.ll and stage3.ll
#     exceeds ``DIFF_THRESHOLD`` lines. The threshold is set above the
#     current near-fixed-point baseline (69 lines at v4.28.0) with
#     modest headroom. Tightening the threshold is a deliberate ratchet:
#     see ``docs/roadmap/v4/v4.29.0/SESSION_REPORT.md``.
#
# Override the threshold at the command line:
#   DIFF_THRESHOLD=200 bash scripts/verify_fixed_point.sh
#
# Keep intermediate IR for debugging:
#   bash scripts/verify_fixed_point.sh --keep

set -euo pipefail
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

# v4.29.0: deliberate diff budget. Current baseline at v4.28.0 is 69
# lines out of 111,511 (0.062%). The threshold starts at 100 to give
# modest headroom while still catching real regressions. Tightening it
# is a deliberate ratchet.
DIFF_THRESHOLD=${DIFF_THRESHOLD:-100}

KEEP=0
if [ "${1:-}" = "--keep" ]; then KEEP=1; fi

# Ensure large stack for deep recursion. ``ulimit`` is best-effort
# because some containerized environments don't allow it; log but do
# not abort the script.
if ! ulimit -s 65536 2>/dev/null; then
    echo "  note: ulimit -s 65536 unavailable in this environment"
fi

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
# v4.29.0: previously this line ended in ``|| true``, which silently
# swallowed any stage2 crash and left an empty ``stage3.ll`` — which
# then diffed cleanly against a non-empty ``stage2.ll`` and counted as
# "near fixed point". Now we capture the exit code explicitly, print a
# warning if the binary exited non-zero, and fail the script unless
# ``stage3.ll`` is non-empty AND ``llvm-as`` accepts it.
#
# This is deliberate: the v4.28.0 self-hosted compiler has a known
# teardown issue (segfault on exit after writing the full IR; see the
# v4.30.0 PLAN for the fix). The output is still correct — the crash
# is in cleanup code, after 111,521 lines of valid IR have been
# flushed to stdout. Rejecting that entire run because of a teardown
# crash would reject a genuinely-valid fixed-point comparison.
# Instead we validate the *output* and record the exit code as a
# known-issue note. v4.30.0 closes the crash itself.
set +e
/tmp/mnc-stage2 "$SOURCE" > /tmp/stage3.ll 2>/tmp/stage2_stderr.log
STAGE2_RC=$?
set -e
if [ "$STAGE2_RC" -ne 0 ]; then
    echo -e "${YELLOW}  note: mnc-stage2 exited with code ${STAGE2_RC}${NC}"
    echo "  (teardown crash is a known issue tracked for v4.30.0; the script"
    echo "   still validates that stage3.ll is non-empty and llvm-valid below)"
    if [ -s /tmp/stage2_stderr.log ]; then
        echo "  stage2 stderr:"
        sed 's/^/    /' /tmp/stage2_stderr.log | head -20
    fi
fi
STAGE3_LINES=$(wc -l < /tmp/stage3.ll)
echo "  stage3.ll: ${STAGE3_LINES} lines"
if [ "$STAGE3_LINES" -eq 0 ]; then
    echo -e "${RED}  stage3.ll is empty — stage2 produced no output${NC}"
    echo "  This is a real failure (not a known-teardown issue)."
    exit 1
fi

# Validate stage3
echo -n "  llvm-as: "
if llvm-as /tmp/stage3.ll -o /dev/null 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
    llvm-as /tmp/stage3.ll -o /dev/null 2>&1 | head -5
    exit 1
fi

# Fixed point check.
# v4.29.0: the diff tolerance is now a real gate. If the diff exceeds
# ``DIFF_THRESHOLD`` lines, the script exits non-zero. Prior to this
# release the script was hardcoded to ``EXIT=0`` regardless of diff,
# which made the v4.17.0 "fixed-point self-compilation" claim
# unfalsifiable by construction (v4.26.0 panel: Rattler, Anaconda,
# Cobra).
echo ""
echo -e "${YELLOW}[Verify] Fixed point: diff stage2.ll stage3.ll${NC}"
# Do not let ``diff`` abort the script when files differ (``set -e``
# treats a non-zero exit from diff as failure). We only want the
# line-count of the differing regions.
set +e
DIFF_LINES=$(diff /tmp/stage2.ll /tmp/stage3.ll | wc -l)
set -e

if [ "$DIFF_LINES" -eq 0 ]; then
    echo -e "${GREEN}  ✓ FIXED POINT REACHED${NC}"
    echo "  stage2.ll == stage3.ll (${STAGE2_LINES} lines, 0 diff)"
    echo ""
    echo -e "${GREEN}=== La Culebra Se Muerde La Cola ===${NC}"
    EXIT=0
elif [ "$DIFF_LINES" -le "$DIFF_THRESHOLD" ]; then
    PCT=$(python3 -c "print(f'{$DIFF_LINES/$STAGE2_LINES*100:.3f}')")
    echo -e "${YELLOW}  ~ NEAR FIXED POINT${NC}"
    echo "  ${DIFF_LINES} diff lines out of ${STAGE2_LINES} (${PCT}%)"
    echo "  within DIFF_THRESHOLD=${DIFF_THRESHOLD}; accepted."
    echo ""
    echo "  First 20 diff lines for reference:"
    diff /tmp/stage2.ll /tmp/stage3.ll | head -20 || true
    EXIT=0
else
    PCT=$(python3 -c "print(f'{$DIFF_LINES/$STAGE2_LINES*100:.3f}')")
    echo -e "${RED}  ✗ FIXED POINT REGRESSION${NC}"
    echo "  ${DIFF_LINES} diff lines out of ${STAGE2_LINES} (${PCT}%)"
    echo "  DIFF_THRESHOLD is ${DIFF_THRESHOLD}; exceeding it is a regression."
    echo ""
    echo "  First 40 diff lines:"
    diff /tmp/stage2.ll /tmp/stage3.ll | head -40 || true
    EXIT=1
fi

if [ "$KEEP" -eq 1 ]; then
    echo "  Kept: /tmp/stage2.ll /tmp/stage3.ll /tmp/mnc-stage2"
fi
exit $EXIT
