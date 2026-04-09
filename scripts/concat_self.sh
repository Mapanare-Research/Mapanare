#!/usr/bin/env bash
# concat_self.sh — Concatenate self-hosted compiler modules (no Python).
#
# Equivalent to: python scripts/concat_self.py
# Strips "import self::*" lines and concatenates in dependency order.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SELF_DIR="${ROOT}/mapanare/self"
OUT="${1:-${SELF_DIR}/mnc_all.mn}"

# Dependency order — leaves first, driver last
MODULES=(
    ast.mn
    lexer.mn
    parser.mn
    semantic.mn
    mir.mn
    lower_state.mn
    lower.mn
    emit_llvm_ir.mn
    emit_llvm.mn
    main.mn
)

{
    echo "// Auto-generated: all self-hosted compiler modules concatenated."
    echo "// Do not edit — regenerate with: bash scripts/concat_self.sh"
    echo ""
    for mod in "${MODULES[@]}"; do
        echo "// ===== ${mod} ====="
        # Strip import self:: lines and normalize line endings
        sed 's/\r$//' "${SELF_DIR}/${mod}" | grep -v '^\s*import self::'
        echo ""
    done
} > "${OUT}"

echo "Wrote $(wc -c < "${OUT}") bytes → ${OUT}"
