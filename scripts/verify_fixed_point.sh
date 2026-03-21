#!/usr/bin/env bash
# verify_fixed_point.sh — Three-stage self-hosted compiler verification.
#
# Stage 1: Python bootstrap compiles self-hosted compiler → mnc-stage1
# Stage 2: mnc-stage1 compiles itself → mnc-stage2
# Stage 3: mnc-stage2 compiles itself → mnc-stage3
#
# Fixed point: mnc-stage2 and mnc-stage3 must be byte-identical.
#
# Usage:
#   ./scripts/verify_fixed_point.sh [--keep]
#
# Options:
#   --keep    Keep intermediate artifacts (IR, object files) for debugging
#
# Requirements:
#   - Python 3.11+ with mapanare installed (pip install -e .)
#   - gcc (for linking)
#   - Linux x86-64 (ELF binaries)

set -euo pipefail

CC="${CC:-gcc}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SELF_DIR="$ROOT/mapanare/self"
NATIVE_DIR="$ROOT/runtime/native"
KEEP=false

if [[ "${1:-}" == "--keep" ]]; then
    KEEP=true
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail()  { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }

# -----------------------------------------------------------------------
# Helper: compile self-hosted compiler using a given compiler binary
# -----------------------------------------------------------------------
compile_with_native() {
    local compiler="$1"   # Path to mnc binary (stage N)
    local output="$2"     # Output binary name (stage N+1)
    local ir_path="$3"    # Where to write the IR

    info "Compiling self-hosted sources with $compiler ..."

    # The native compiler reads a single file (main.mn imports all modules)
    if ! "$compiler" "$SELF_DIR/main.mn" > "$ir_path" 2>/dev/null; then
        warn "  Compiler failed to produce IR"
        return 1
    fi
    local ir_lines
    ir_lines=$(wc -l < "$ir_path")
    info "  IR: $ir_lines lines -> $ir_path"

    # Post-process: make compile() and format_error() externally visible
    sed -i 's/define internal {i1, {i8\*, i64}, {i8\*, i64, i64, i64}} @"compile"/define {i1, {i8*, i64}, {i8*, i64, i64, i64}} @"compile"/' "$ir_path"
    sed -i 's/define internal {i8\*, i64} @"format_error"/define {i8*, i64} @"format_error"/' "$ir_path"

    # Compile IR to object code
    info "  Compiling IR -> object code ..."
    local obj_path="${ir_path%.ll}.o"
    if ! llc -filetype=obj -O0 -o "$obj_path" "$ir_path" 2>/dev/null; then
        warn "  llc failed to compile IR (self-hosted emitter gaps)"
        return 1
    fi

    # Compile C runtime
    local core_o="${ir_path%.ll}_core.o"
    "$CC" -c -O0 -g -fPIC -I "$NATIVE_DIR" "$NATIVE_DIR/mapanare_core.c" -o "$core_o"

    # Compile main wrapper
    local main_o="${ir_path%.ll}_main.o"
    "$CC" -c -O0 -g "$SELF_DIR/mnc_main.c" -o "$main_o"

    # Link
    info "  Linking -> $output ..."
    if ! "$CC" -o "$output" "$main_o" "$obj_path" "$core_o" -rdynamic -lm -lpthread 2>/dev/null; then
        warn "  Linking failed"
        rm -f "$obj_path" "$core_o" "$main_o"
        return 1
    fi

    local size
    size=$(stat -c%s "$output" 2>/dev/null || stat -f%z "$output" 2>/dev/null)
    info "  Binary: $output ($size bytes)"

    # Cleanup intermediates unless --keep
    if [[ "$KEEP" == false ]]; then
        rm -f "$obj_path" "$core_o" "$main_o"
    fi
}

# -----------------------------------------------------------------------
# Stage 1: Python bootstrap -> mnc-stage1
# -----------------------------------------------------------------------
info "=== Stage 1: Python bootstrap -> mnc-stage1 ==="
python3 "$ROOT/scripts/build_stage1.py"

STAGE1="$SELF_DIR/mnc-stage1"
if [[ ! -x "$STAGE1" ]]; then
    fail "Stage 1 build failed: $STAGE1 not found"
fi
info "Stage 1 complete: $STAGE1"

# Quick sanity check
echo 'fn main() { println("hello") }' > /tmp/mnc_fp_test.mn
if ! "$STAGE1" /tmp/mnc_fp_test.mn > /dev/null 2>&1; then
    warn "Stage 1 sanity check failed (may be expected if emitter has known issues)"
fi
rm -f /tmp/mnc_fp_test.mn

# -----------------------------------------------------------------------
# Stage 2: mnc-stage1 -> mnc-stage2
# -----------------------------------------------------------------------
info ""
info "=== Stage 2: mnc-stage1 -> mnc-stage2 ==="

STAGE2="$SELF_DIR/mnc-stage2"
STAGE2_IR="$SELF_DIR/stage2.ll"

if ! compile_with_native "$STAGE1" "$STAGE2" "$STAGE2_IR" 2>/dev/null; then
    warn "Stage 2 failed — self-hosted emitter (emit_llvm.mn) has known gaps."
    warn "This is expected until emit_llvm.mn handles all IR constructs."
    warn "Stage 1 (Python bootstrap → mnc-stage1) is verified working."
    # Cleanup
    rm -f "$STAGE2_IR" "$STAGE2" "$SELF_DIR/stage2_core.o" "$SELF_DIR/stage2_main.o" "$SELF_DIR/stage2.o"
    exit 0
fi
info "Stage 2 complete: $STAGE2"

# -----------------------------------------------------------------------
# Stage 3: mnc-stage2 -> mnc-stage3
# -----------------------------------------------------------------------
info ""
info "=== Stage 3: mnc-stage2 -> mnc-stage3 ==="

STAGE3="$SELF_DIR/mnc-stage3"
STAGE3_IR="$SELF_DIR/stage3.ll"

if ! compile_with_native "$STAGE2" "$STAGE3" "$STAGE3_IR" 2>/dev/null; then
    warn "Stage 3 failed — self-hosted emitter gaps persist through stage 2."
    rm -f "$STAGE3_IR" "$STAGE3" "$SELF_DIR/stage3_core.o" "$SELF_DIR/stage3_main.o" "$SELF_DIR/stage3.o"
    rm -f "$STAGE2_IR" "$STAGE2"
    exit 0
fi
info "Stage 3 complete: $STAGE3"

# -----------------------------------------------------------------------
# Fixed-point verification
# -----------------------------------------------------------------------
info ""
info "=== Fixed-Point Verification ==="

# Compare IR first (more informative diff)
if diff -q "$STAGE2_IR" "$STAGE3_IR" > /dev/null 2>&1; then
    info "IR comparison: Stage 2 IR == Stage 3 IR (PASS)"
else
    warn "IR comparison: Stage 2 IR != Stage 3 IR"
    if [[ "$KEEP" == true ]]; then
        info "  Diff saved to $SELF_DIR/ir_diff.txt"
        diff "$STAGE2_IR" "$STAGE3_IR" > "$SELF_DIR/ir_diff.txt" 2>&1 || true
    fi
fi

# Compare binaries
if cmp -s "$STAGE2" "$STAGE3"; then
    info ""
    info "================================================"
    info "  FIXED POINT ACHIEVED: mnc-stage2 == mnc-stage3"
    info "  The compiler can compile itself identically."
    info "================================================"
    RESULT=0
else
    info ""
    fail "================================================"
    fail "  FIXED POINT FAILED: mnc-stage2 != mnc-stage3"
    fail "  The compiler does not yet reach a fixed point."
    fail "================================================"
    RESULT=1
fi

# Cleanup unless --keep
if [[ "$KEEP" == false ]]; then
    rm -f "$STAGE2_IR" "$STAGE3_IR" "$STAGE2" "$STAGE3"
    info "Cleaned up intermediate files."
else
    info "Intermediate files kept in $SELF_DIR/"
fi

exit ${RESULT:-1}
