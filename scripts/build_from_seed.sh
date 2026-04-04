#!/usr/bin/env bash
# build_from_seed.sh — Build the Mapanare compiler from the bootstrap seed.
#
# Requirements: gcc, llvm (llvm-as, llc) OR clang. No Python.
#
# Usage:
#   bash scripts/build_from_seed.sh          # build ./mnc
#   bash scripts/build_from_seed.sh --verify  # build + verify fixed point
#
# The seed binary compiles the self-hosted source to LLVM IR, which is then
# compiled to a native binary via the standard LLVM toolchain + gcc linker.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# --- Platform detection ---
ARCH="$(uname -m)"
OS="$(uname -s)"

case "${OS}-${ARCH}" in
    Linux-x86_64)  SEED_DIR="linux-x86_64" ;;
    # Future:
    # Darwin-arm64)  SEED_DIR="darwin-arm64" ;;
    # MINGW*|MSYS*)  SEED_DIR="windows-x64" ;;
    *)
        echo "error: no bootstrap seed for ${OS}-${ARCH}" >&2
        echo "  Available: linux-x86_64" >&2
        echo "  Use Python bootstrap instead: python scripts/build_stage1.py" >&2
        exit 1
        ;;
esac

SEED="${ROOT}/bootstrap/seed/${SEED_DIR}/mnc"
SOURCE="${ROOT}/mapanare/self/mnc_all.mn"
RUNTIME="${ROOT}/runtime/native/mapanare_core.c"
DRIVER="${ROOT}/mapanare/self/mnc_main.c"
RUNTIME_DIR="${ROOT}/runtime/native"
OUTPUT="${ROOT}/mnc"

CC="${CC:-gcc}"
TMPDIR="${TMPDIR:-/tmp}"

# --- Verify prerequisites ---
echo "=== Mapanare: Build from seed ==="

if [ ! -x "${SEED}" ]; then
    echo "error: seed binary not found or not executable: ${SEED}" >&2
    echo "  Run: chmod +x ${SEED}" >&2
    exit 1
fi

if [ ! -f "${SOURCE}" ]; then
    echo "error: source not found: ${SOURCE}" >&2
    echo "  Run: python scripts/concat_self.py  (or check mapanare/self/)" >&2
    exit 1
fi

# Check for clang (preferred) or llvm-as + llc
USE_CLANG=0
if command -v clang >/dev/null 2>&1; then
    USE_CLANG=1
    echo "  Toolchain: clang + ${CC} (linker)"
elif command -v llvm-as >/dev/null 2>&1 && command -v llc >/dev/null 2>&1; then
    echo "  Toolchain: llvm-as + llc + ${CC}"
else
    echo "error: need clang OR (llvm-as + llc). Install llvm." >&2
    exit 1
fi

command -v "${CC}" >/dev/null 2>&1 || {
    echo "error: ${CC} not found. Install gcc." >&2
    exit 1
}

# --- Verify seed checksum (optional, warn-only) ---
SHA_FILE="${ROOT}/bootstrap/seed/${SEED_DIR}/mnc.sha256"
if [ -f "${SHA_FILE}" ] && command -v sha256sum >/dev/null 2>&1; then
    if (cd "$(dirname "${SEED}")" && sha256sum -c mnc.sha256 >/dev/null 2>&1); then
        echo "  Seed checksum: OK"
    else
        echo "  WARNING: seed checksum mismatch — binary may be modified" >&2
    fi
fi

# --- Stage 1: Seed compiles source → LLVM IR ---
echo "[1/4] Compiling source → LLVM IR (via seed) ..."
IR_FILE="${TMPDIR}/mapanare_stage1.ll"
# Self-compilation needs deep recursion; ensure large stack
ulimit -s unlimited 2>/dev/null || true
"${SEED}" "${SOURCE}" > "${IR_FILE}"
IR_LINES=$(wc -l < "${IR_FILE}")
echo "  IR: ${IR_LINES} lines → ${IR_FILE}"

# --- Stage 2: LLVM IR → object code ---
echo "[2/4] Compiling LLVM IR → object code ..."
OBJ_FILE="${TMPDIR}/mapanare_stage1.o"

if [ "${USE_CLANG}" -eq 1 ]; then
    clang -c -O2 "${IR_FILE}" -o "${OBJ_FILE}"
else
    BC_FILE="${TMPDIR}/mapanare_stage1.bc"
    llvm-as "${IR_FILE}" -o "${BC_FILE}"
    llc "${BC_FILE}" -o "${OBJ_FILE}" -filetype=obj -relocation-model=pic
    rm -f "${BC_FILE}"
fi
echo "  Object: $(wc -c < "${OBJ_FILE}") bytes → ${OBJ_FILE}"

# --- Stage 3: Compile C runtime + driver ---
echo "[3/4] Compiling C runtime + driver ..."
CORE_OBJ="${TMPDIR}/mapanare_core.o"
MAIN_OBJ="${TMPDIR}/mnc_main.o"
"${CC}" -c -O2 -fPIC -I "${RUNTIME_DIR}" "${RUNTIME}" -o "${CORE_OBJ}"
"${CC}" -c -O2 "${DRIVER}" -o "${MAIN_OBJ}"

# --- Stage 4: Link ---
echo "[4/4] Linking ..."
"${CC}" -o "${OUTPUT}" \
    "${MAIN_OBJ}" "${OBJ_FILE}" "${CORE_OBJ}" \
    -no-pie -rdynamic -lm -lpthread \
    -Wl,-z,stacksize=67108864

# Cleanup (keep IR if --verify requested)
rm -f "${OBJ_FILE}" "${CORE_OBJ}" "${MAIN_OBJ}"

SIZE=$(wc -c < "${OUTPUT}")
echo ""
echo "=== Success: ${OUTPUT} (${SIZE} bytes) ==="

# --- Optional: verify fixed point ---
if [ "${1:-}" = "--verify" ]; then
    echo ""
    echo "=== Verifying fixed point ==="
    STAGE2_IR="${TMPDIR}/mapanare_stage2.ll"
    "${OUTPUT}" "${SOURCE}" > "${STAGE2_IR}"

    if diff -q "${IR_FILE}" "${STAGE2_IR}" >/dev/null 2>&1; then
        echo "  Fixed point: PASS (stage1 == stage2)"
    else
        STAGE1_LINES=$(wc -l < "${IR_FILE}")
        STAGE2_LINES=$(wc -l < "${STAGE2_IR}")
        echo "  Fixed point: stage1=${STAGE1_LINES} lines, stage2=${STAGE2_LINES} lines"
        echo "  (Run scripts/verify_fixed_point.sh for full 3-stage check)"
    fi
    rm -f "${STAGE2_IR}"
fi

rm -f "${IR_FILE}"
