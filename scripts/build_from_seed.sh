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
    Linux-x86_64)    SEED_DIR="linux-x86_64" ;;
    Darwin-arm64)    SEED_DIR="darwin-arm64" ;;
    Darwin-x86_64)   SEED_DIR="darwin-x86_64" ;;
    *)
        echo "error: no bootstrap seed for ${OS}-${ARCH}" >&2
        echo "Available seeds: linux-x86_64, darwin-arm64, darwin-x86_64"
        echo "Use Python bootstrap instead: python scripts/build_stage1.py"
        exit 1
        ;;
esac

SEED="${ROOT}/bootstrap/seed/${SEED_DIR}/mnc"
SOURCE="${SELF_DIR}/mnc_all.mn"
MNC_MAIN="${SELF_DIR}/mnc_main.c"
CORE_C="${NATIVE_DIR}/mapanare_core.c"
RT_C="${NATIVE_DIR}/mapanare_runtime.c"
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
# v5.9.1 DX.5: explicit `emit-llvm` subcommand. Pre-v5.9.1 the seed
# treated bare ``mnc <file.mn>`` as emit-IR; v5.9.1+ seeds default to
# run-program and would attempt to execute mnc_all.mn instead. The
# v5.9.1 PLAN updated lines 95 / 122 below; this line was missed and
# only surfaced when v5.10.0's Bb.4 refreshed the seed past v5.9.1
# behavior. Both old and new seeds accept the explicit subcommand.
echo ""
echo "[1/4] Stage 1: seed compiles source → stage1 IR"
STAGE1_LL="/tmp/mapanare_stage1.ll"
"${SEED}" emit-llvm "${SOURCE}" > "${STAGE1_LL}" 2>/dev/null
echo "  IR: $(wc -l < "${STAGE1_LL}") lines"

# Remove 'internal' linkage (LLVM -O2 may strip needed functions)
sed -i 's/define internal /define /g' "${STAGE1_LL}"

echo "[2/4] Stage 1: compiling stage1 IR → stage1 binary"
STAGE1_O="/tmp/mapanare_stage1.o"
CORE_O="/tmp/mapanare_core.o"
RT_O="/tmp/mapanare_runtime.o"
MAIN_O="/tmp/mapanare_main.o"
STAGE1_BIN="/tmp/mnc-stage1"

clang -c -O2 "${STAGE1_LL}" -o "${STAGE1_O}" 2>/dev/null
gcc -c -O2 -Wall -Wextra -I "${NATIVE_DIR}" "${CORE_C}" -o "${CORE_O}"
gcc -c -O2 -Wall -Wextra -I "${NATIVE_DIR}" "${RT_C}" -o "${RT_O}"
gcc -c -O2 -Wall -Wextra "${MNC_MAIN}" -o "${MAIN_O}"
gcc "${MAIN_O}" "${STAGE1_O}" "${CORE_O}" "${RT_O}" -o "${STAGE1_BIN}" \
    -no-pie -rdynamic -lm -lpthread
echo "  Binary: ${STAGE1_BIN} ($(wc -c < "${STAGE1_BIN}") bytes)"

# --- Stage 2: stage1 → stage2 (final) ---
echo ""
echo "[3/4] Stage 2: stage1 compiles source → stage2 IR"
STAGE2_LL="/tmp/mapanare_stage2.ll"
# v5.9.1 DX.5: explicit `emit-llvm` subcommand. The stage1 binary built
# above is from v5.9.1+ source; default is now implicit-run.
"${STAGE1_BIN}" emit-llvm "${SOURCE}" > "${STAGE2_LL}" 2>/dev/null
echo "  IR: $(wc -l < "${STAGE2_LL}") lines"

# Validate IR
if command -v llvm-as >/dev/null 2>&1; then
    llvm-as "${STAGE2_LL}" -o /dev/null
    echo "  Validation: OK"
fi

echo "[4/4] Stage 2: compiling stage2 IR → final binary"
STAGE2_O="/tmp/mapanare_stage2.o"
clang -c -O2 "${STAGE2_LL}" -o "${STAGE2_O}" 2>/dev/null
gcc "${MAIN_O}" "${STAGE2_O}" "${CORE_O}" "${RT_O}" -o "${OUTPUT}" \
    -no-pie -rdynamic -lm -lpthread
echo "  Binary: ${OUTPUT} ($(wc -c < "${OUTPUT}") bytes)"

# --- Cleanup ---
if [ "${1:-}" != "--keep" ] && [ -z "${KEEP}" ]; then
    rm -f "${STAGE1_LL}" "${STAGE1_O}" "${STAGE2_LL}" "${STAGE2_O}" \
          "${CORE_O}" "${RT_O}" "${MAIN_O}" "${STAGE1_BIN}"
fi

# --- Smoke test ---
# v5.9.1 DX.5: explicit `emit-llvm` subcommand. The output binary is from
# v5.9.1+ source; default is now implicit-run (which would compile + execute
# the .mn file instead of printing IR), so the IR-emission grep needs the
# explicit subcommand.
if "${OUTPUT}" emit-llvm "${ROOT}/tests/golden/01_hello.mn" 2>/dev/null | grep -q "define"; then
    echo "  Smoke test: OK"
else
    echo "  WARNING: smoke test failed" >&2
fi

echo ""
echo "=== Success: ${OUTPUT} ==="
echo "  Usage: ./mnc <file.mn>           (compile and run, default)"
echo "         ./mnc emit-llvm <file.mn> (compile to LLVM IR)"

# --- Verify golden tests ---
if [ "${1:-}" = "--verify" ]; then
    echo ""
    echo "=== Verifying golden tests ==="
    if ! command -v llvm-as >/dev/null 2>&1; then
        echo "  SKIP: llvm-as not found"
        exit 0
    fi
    PASS=0; FAIL=0
    # v5.9.1 DX.5: explicit `emit-llvm` subcommand. Pre-DX.5 ``mnc <file.mn>``
    # printed IR; post-DX.5 it compiles + runs the program. Without the
    # explicit subcommand the per-golden invocation here would attempt to
    # execute each .mn file (most fail because they have no main, or write
    # to /tmp paths the verify step never staged), and llvm-as would parse
    # whatever bytes the run produced. The smoke check at line 128 was
    # updated for DX.5; this loop was missed and stayed latent until
    # v5.49.0 lifted the workflow_call guard so the seed-bootstrap job
    # runs on every push.
    for mn in "${ROOT}"/tests/golden/*.mn; do
        if "${OUTPUT}" emit-llvm "$mn" 2>/dev/null | llvm-as -o /dev/null 2>/dev/null; then
            PASS=$((PASS + 1))
        else
            FAIL=$((FAIL + 1))
            echo "  FAIL: $(basename "$mn")"
        fi
    done
    echo "  ${PASS} pass, ${FAIL} fail"
    # v4.155.0 / v5.24.0 Hy.4 (Cobra 3rd-panel ask): seed-built compiler
    # has known limitations — Te.5/Te.6/comprehensions/complex closures
    # postdate the v5.10.0-vintage seed. Express the expected pass count
    # as a self-evident formula instead of a magic threshold so future
    # golden additions don't silently widen the acceptance window.
    TOTAL_GOLDENS=$(ls "${ROOT}"/tests/golden/*.mn | wc -l)
    EXPECTED_SEED_FAILS=20
    EXPECTED_PASS=$((TOTAL_GOLDENS - EXPECTED_SEED_FAILS))
    if [ "${PASS}" -lt "${EXPECTED_PASS}" ]; then
        echo "  ERROR: expected >=${EXPECTED_PASS} pass (of ${TOTAL_GOLDENS} goldens, ${EXPECTED_SEED_FAILS} seed-incompatible), got ${PASS}"
        exit 1
    fi
fi
