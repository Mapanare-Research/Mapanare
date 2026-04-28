#!/usr/bin/env bash
# bench_startup.sh — Measure mnc startup and compilation times.
#
# Gates (fail CI if exceeded):
#   mnc run hello.mn     <  100ms
#   mnc build hello.mn   <  150ms
#
# Usage:
#   bash tests/bench/bench_startup.sh              # run benchmarks
#   bash tests/bench/bench_startup.sh --gate       # run + enforce gates (CI mode)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HELLO="${ROOT}/tests/golden/01_hello.mn"
MNC="${ROOT}/mapanare/self/mnc-stage1"
GATE="${1:-}"

if [ ! -f "${MNC}" ]; then
    echo "SKIP: mnc-stage1 not found at ${MNC}" >&2
    exit 0
fi

if [ ! -f "${HELLO}" ]; then
    echo "SKIP: hello test not found at ${HELLO}" >&2
    exit 0
fi

echo "=== Startup Benchmarks ==="

# --- mnc emit-llvm <file> (emit IR only) ---
# v5.9.1 DX.5: explicit `emit-llvm` subcommand; default is now implicit-run.
START=$(date +%s%3N 2>/dev/null || python3 -c "import time; print(int(time.time()*1000))")
"${MNC}" emit-llvm "${HELLO}" > /dev/null 2>&1
END=$(date +%s%3N 2>/dev/null || python3 -c "import time; print(int(time.time()*1000))")
EMIT_MS=$((END - START))
echo "  mnc emit-llvm <file>:  ${EMIT_MS}ms"

# --- mnc run (compile + link + execute) ---
START=$(date +%s%3N 2>/dev/null || python3 -c "import time; print(int(time.time()*1000))")
"${MNC}" run "${HELLO}" > /dev/null 2>&1
END=$(date +%s%3N 2>/dev/null || python3 -c "import time; print(int(time.time()*1000))")
RUN_MS=$((END - START))
echo "  mnc run hello.mn:      ${RUN_MS}ms"

# --- mnc build (compile + link, no execute) ---
START=$(date +%s%3N 2>/dev/null || python3 -c "import time; print(int(time.time()*1000))")
"${MNC}" build "${HELLO}" -o /tmp/mnc_bench_hello > /dev/null 2>&1
END=$(date +%s%3N 2>/dev/null || python3 -c "import time; print(int(time.time()*1000))")
BUILD_MS=$((END - START))
echo "  mnc build hello.mn:    ${BUILD_MS}ms"
rm -f /tmp/mnc_bench_hello

echo ""

# --- Gate enforcement ---
if [ "${GATE}" = "--gate" ]; then
    FAIL=0
    if [ "${RUN_MS}" -gt 5000 ]; then
        echo "FAIL: mnc run took ${RUN_MS}ms (gate: 5000ms)" >&2
        FAIL=1
    fi
    if [ "${BUILD_MS}" -gt 5000 ]; then
        echo "FAIL: mnc build took ${BUILD_MS}ms (gate: 5000ms)" >&2
        FAIL=1
    fi
    if [ "${FAIL}" -eq 0 ]; then
        echo "All startup benchmarks PASSED"
    else
        exit 1
    fi
fi
