#!/usr/bin/env bash
# build_from_seed.sh — Install the Mapanare compiler from the bootstrap seed.
#
# The seed binary is a pre-built, verified compiler. This script validates it
# and installs it as ./mnc. The compiler source is in mapanare/self/ for
# transparency and development (use Python bootstrap for development builds).
#
# Requirements: llvm (for --verify). No Python.
#
# Usage:
#   bash scripts/build_from_seed.sh          # install ./mnc
#   bash scripts/build_from_seed.sh --verify  # install + verify golden tests
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# --- Platform detection ---
ARCH="$(uname -m)"
OS="$(uname -s)"

case "${OS}-${ARCH}" in
    Linux-x86_64)  SEED_DIR="linux-x86_64" ;;
    *)
        echo "error: no bootstrap seed for ${OS}-${ARCH}" >&2
        echo "  Available: linux-x86_64" >&2
        exit 1
        ;;
esac

SEED="${ROOT}/bootstrap/seed/${SEED_DIR}/mnc"
OUTPUT="${ROOT}/mnc"

echo "=== Mapanare: Install from seed ==="

[ -f "${SEED}" ] || { echo "error: seed not found: ${SEED}" >&2; exit 1; }

# Verify checksum
SHA_FILE="${ROOT}/bootstrap/seed/${SEED_DIR}/mnc.sha256"
if [ -f "${SHA_FILE}" ] && command -v sha256sum >/dev/null 2>&1; then
    if (cd "$(dirname "${SEED}")" && sha256sum -c mnc.sha256 >/dev/null 2>&1); then
        echo "  Seed checksum: OK"
    else
        echo "  WARNING: seed checksum mismatch" >&2
    fi
fi

# Install
cp "${SEED}" "${OUTPUT}"
chmod +x "${OUTPUT}"
SIZE=$(wc -c < "${OUTPUT}")
echo "  Installed: ${OUTPUT} (${SIZE} bytes)"

# Quick smoke test
if "${OUTPUT}" "${ROOT}/tests/golden/01_hello.mn" >/dev/null 2>&1; then
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
        echo "  SKIP: llvm-as not found (install llvm for verification)"
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
