#!/usr/bin/env bash
# build_from_seed.sh — Build the Mapanare compiler from source, no Python.
#
# Two-stage bootstrap:
#   1. Seed binary compiles source → stage1
#   2. Stage1 compiles source → stage2 (final)
#
# Stage2 is the released binary. It has been verified to be a fixed point:
# stage2 compiling itself produces identical output (stage3 == stage4).
#
# Requirements: clang, gcc, llvm-as (for --verify). No Python.
#
# Usage:
#   bash scripts/build_from_seed.sh              # build ./mnc
#   bash scripts/build_from_seed.sh --verify     # build + verify golden tests
#   bash scripts/build_from_seed.sh --keep       # keep intermediate files
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SELF_DIR="${ROOT}/mapanare/self"
NATIVE_DIR="${ROOT}/runtime/native"
KEEP="${KEEP:-}"

# --- Platform detection ---
ARCH="$(uname -m)"
OS="$(uname -s)"
case "${OS}-${ARCH}" in
    Linux-x86_64)  SEED_DIR="linux-x86_64" ;;
    *)
        echo "error: no bootstrap seed for ${OS}-${ARCH}" >&2
        exit 1
        ;;
esac

SEED="${ROOT}/bootstrap/seed/${SEED_DIR}/mnc"
SOURCE="${SELF_DIR}/mnc_all.mn"
MNC_MAIN="${SELF_DIR}/mnc_main.c"
CORE_C="${NATIVE_DIR}/mapanare_core.c"
OUTPUT="${ROOT}/mnc"

# Self-compilation needs large stack (recursive descent parser + deep lowering)
ulimit -s unlimited 2>/dev/null || ulimit -s 262144 2>/dev/null || true

echo "=== Mapanare: Two-stage bootstrap (no Python) ==="

# --- Validate seed ---
[ -f "${SEED}" ] || { echo "error: seed not found: ${SEED}" >&2; exit 1; }
[ -f "${SOURCE}" ] || { echo "error: source not found: ${SOURCE}" >&2; exit 1; }

SHA_FILE="${ROOT}/bootstrap/seed/${SEED_DIR}/mnc.sha256"
if [ -f "${SHA_FILE}" ] && command -v sha256sum >/dev/null 2>&1; then
    if (cd "$(dirname "${SEED}")" && sha256sum -c mnc.sha256 >/dev/null 2>&1); then
        echo "  Seed checksum: OK"
    else
        echo "  WARNING: seed checksum mismatch" >&2
    fi
fi

# --- Stage 1: seed → stage1 ---
echo ""
echo "[1/4] Stage 1: seed compiles source → stage1 IR"
STAGE1_LL="/tmp/mapanare_stage1.ll"
"${SEED}" "${SOURCE}" > "${STAGE1_LL}" 2>/dev/null
echo "  IR: $(wc -l < "${STAGE1_LL}") lines"

# Remove 'internal' linkage (LLVM -O2 may strip needed functions)
sed -i 's/define internal /define /g' "${STAGE1_LL}"

echo "[2/4] Stage 1: compiling stage1 IR → stage1 binary"
STAGE1_O="/tmp/mapanare_stage1.o"
CORE_O="/tmp/mapanare_core.o"
MAIN_O="/tmp/mapanare_main.o"
STAGE1_BIN="/tmp/mnc-stage1"

clang -c -O2 "${STAGE1_LL}" -o "${STAGE1_O}" 2>/dev/null
gcc -c -O2 -I "${NATIVE_DIR}" "${CORE_C}" -o "${CORE_O}"
gcc -c -O2 "${MNC_MAIN}" -o "${MAIN_O}"
gcc "${MAIN_O}" "${STAGE1_O}" "${CORE_O}" -o "${STAGE1_BIN}" \
    -no-pie -rdynamic -lm -lpthread
echo "  Binary: ${STAGE1_BIN} ($(wc -c < "${STAGE1_BIN}") bytes)"

# --- Stage 2: stage1 → stage2 (final) ---
echo ""
echo "[3/4] Stage 2: stage1 compiles source → stage2 IR"
STAGE2_LL="/tmp/mapanare_stage2.ll"
"${STAGE1_BIN}" "${SOURCE}" > "${STAGE2_LL}" 2>/dev/null
echo "  IR: $(wc -l < "${STAGE2_LL}") lines"

# Validate IR
if command -v llvm-as >/dev/null 2>&1; then
    llvm-as "${STAGE2_LL}" -o /dev/null
    echo "  Validation: OK"
fi

echo "[4/4] Stage 2: compiling stage2 IR → final binary"
STAGE2_O="/tmp/mapanare_stage2.o"
clang -c -O2 "${STAGE2_LL}" -o "${STAGE2_O}" 2>/dev/null
gcc "${MAIN_O}" "${STAGE2_O}" "${CORE_O}" -o "${OUTPUT}" \
    -no-pie -rdynamic -lm -lpthread
echo "  Binary: ${OUTPUT} ($(wc -c < "${OUTPUT}") bytes)"

# --- Cleanup ---
if [ "${1:-}" != "--keep" ] && [ -z "${KEEP}" ]; then
    rm -f "${STAGE1_LL}" "${STAGE1_O}" "${STAGE2_LL}" "${STAGE2_O}" \
          "${CORE_O}" "${MAIN_O}" "${STAGE1_BIN}"
fi

# --- Smoke test ---
if "${OUTPUT}" "${ROOT}/tests/golden/01_hello.mn" 2>/dev/null | grep -q "define"; then
    echo "  Smoke test: OK"
else
    echo "  WARNING: smoke test failed" >&2
fi

echo ""
echo "=== Success: ${OUTPUT} ==="
echo "  Usage: ./mnc <file.mn>  (outputs LLVM IR to stdout)"

# --- Verify golden tests ---
if [ "${1:-}" = "--verify" ]; then
    echo ""
    echo "=== Verifying golden tests ==="
    if ! command -v llvm-as >/dev/null 2>&1; then
        echo "  SKIP: llvm-as not found"
        exit 0
    fi
    PASS=0; FAIL=0
    for mn in "${ROOT}"/tests/golden/*.mn; do
        if "${OUTPUT}" "$mn" 2>/dev/null | llvm-as -o /dev/null 2>/dev/null; then
            PASS=$((PASS + 1))
        else
            FAIL=$((FAIL + 1))
            echo "  FAIL: $(basename "$mn")"
        fi
    done
    echo "  ${PASS} pass, ${FAIL} fail"
    [ "${FAIL}" -eq 0 ] || exit 1
fi
