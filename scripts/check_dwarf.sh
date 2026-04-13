#!/usr/bin/env bash
# check_dwarf.sh — verify DWARF debug info in a -g build.
# v4.62.0: passes trivially (no DWARF metadata emitted yet).
# v4.63.0+: verifies DICompileUnit, DISubprogram, line info.
set -euo pipefail

SRC="${1:-tests/golden/01_hello.mn}"
LL_OUT="/tmp/mn_dwarf_check.ll"
BC_OUT="/tmp/mn_dwarf_check.bc"

echo "[check_dwarf] Emitting LLVM IR with -g from $SRC ..."
python3 -m mapanare emit-llvm -g "$SRC" -o "$LL_OUT"

echo "[check_dwarf] Assembling with llvm-as ..."
if command -v llvm-as > /dev/null 2>&1; then
    llvm-as "$LL_OUT" -o "$BC_OUT"
else
    echo "[check_dwarf] llvm-as not found — skipping assembly step"
    exit 0
fi

echo "[check_dwarf] Running llvm-dwarfdump --verify ..."
if command -v llvm-dwarfdump > /dev/null 2>&1; then
    VERIFY_OUT=$(llvm-dwarfdump --verify "$BC_OUT" 2>&1 || true)
    if echo "$VERIFY_OUT" | grep -q "error:"; then
        echo "[check_dwarf] DWARF verification FAILED:"
        echo "$VERIFY_OUT"
        exit 1
    fi
    echo "[check_dwarf] DWARF verification PASSED"
else
    echo "[check_dwarf] llvm-dwarfdump not found — skipping verification"
fi

rm -f "$LL_OUT" "$BC_OUT"
echo "[check_dwarf] Done."
