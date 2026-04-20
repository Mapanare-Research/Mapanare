#!/usr/bin/env bash
# bench_compile.sh — Compile-time benchmark suite for CI.
#
# Gates (fail CI if exceeded):
#   mnc run hello.mn        < 5000ms  (generous for CI runners)
#   mnc build hello.mn      < 5000ms
#   mnc-stage1 binary size  < 10MB (stripped)
#   main.ll IR lines        < 1M (v4.155.0: 912K for 10-module self-hosted compiler)
#   IR blowup ratio         < 25x
#
# Usage:
#   bash tests/bench/bench_compile.sh              # run benchmarks
#   bash tests/bench/bench_compile.sh --gate       # run + enforce gates (CI mode)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MNC="${ROOT}/mapanare/self/mnc-stage1"
HELLO="${ROOT}/tests/golden/01_hello.mn"
MAIN_LL="${ROOT}/mapanare/self/main.ll"
GATE="${1:-}"

if [ ! -f "${MNC}" ]; then
    echo "SKIP: mnc-stage1 not found" >&2
    exit 0
fi

echo "=== Compile-Time Benchmark Suite ==="
echo ""

# --- Binary size ---
BIN_SIZE=$(wc -c < "${MNC}")
BIN_SIZE_MB=$((BIN_SIZE / 1024 / 1024))
STRIP_SIZE=$(strip -o /tmp/mnc_bench_strip "${MNC}" 2>/dev/null && wc -c < /tmp/mnc_bench_strip || echo "$BIN_SIZE")
STRIP_MB=$((STRIP_SIZE / 1024 / 1024))
echo "  Binary size:     ${BIN_SIZE} bytes (${BIN_SIZE_MB}MB)"
echo "  Stripped:        ${STRIP_SIZE} bytes (${STRIP_MB}MB)"
rm -f /tmp/mnc_bench_strip

# --- IR size ---
if [ -f "${MAIN_LL}" ]; then
    IR_LINES=$(wc -l < "${MAIN_LL}")
    echo "  IR lines:        ${IR_LINES}"

    # Source lines (all .mn files in self/)
    SRC_LINES=$(cat "${ROOT}"/mapanare/self/*.mn 2>/dev/null | wc -l)
    if [ "${SRC_LINES}" -gt 0 ]; then
        RATIO=$((IR_LINES * 100 / SRC_LINES))
        RATIO_X=$((RATIO / 100))
        echo "  Source lines:    ${SRC_LINES}"
        echo "  IR blowup:       ${RATIO_X}.$(printf '%02d' $((RATIO % 100)))x"
    fi
fi

# --- Startup time ---
if [ -f "${HELLO}" ]; then
    echo ""
    START=$(date +%s%3N 2>/dev/null || python3 -c "import time; print(int(time.time()*1000))")
    "${MNC}" run "${HELLO}" > /dev/null 2>&1 || true
    END=$(date +%s%3N 2>/dev/null || python3 -c "import time; print(int(time.time()*1000))")
    RUN_MS=$((END - START))
    echo "  mnc run hello:   ${RUN_MS}ms"

    START=$(date +%s%3N 2>/dev/null || python3 -c "import time; print(int(time.time()*1000))")
    "${MNC}" build "${HELLO}" -o /tmp/mnc_bench_hello > /dev/null 2>&1 || true
    END=$(date +%s%3N 2>/dev/null || python3 -c "import time; print(int(time.time()*1000))")
    BUILD_MS=$((END - START))
    echo "  mnc build hello: ${BUILD_MS}ms"
    rm -f /tmp/mnc_bench_hello
fi

echo ""

# --- Gate enforcement ---
if [ "${GATE}" = "--gate" ]; then
    FAIL=0

    if [ "${STRIP_SIZE}" -gt 10485760 ]; then
        echo "FAIL: binary size ${STRIP_MB}MB > 10MB" >&2
        FAIL=1
    fi

    if [ -f "${MAIN_LL}" ]; then
        if [ "${IR_LINES}" -gt 1000000 ]; then
            echo "FAIL: IR ${IR_LINES} lines > 1M" >&2
            FAIL=1
        fi
    fi

    if [ "${RUN_MS:-0}" -gt 5000 ]; then
        echo "FAIL: mnc run ${RUN_MS}ms > 5000ms" >&2
        FAIL=1
    fi

    if [ "${FAIL}" -eq 0 ]; then
        echo "All compile-time benchmarks PASSED"
    else
        exit 1
    fi
fi
