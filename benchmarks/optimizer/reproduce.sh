#!/usr/bin/env bash
# reproduce.sh — Re-run the v4.90.0 cumulative benchmark
#
# Usage:
#   bash benchmarks/optimizer/reproduce.sh              # Full run (5 runs + cross-language)
#   bash benchmarks/optimizer/reproduce.sh --quick      # Quick run (3 runs, no cross-language)
#
# Requirements: llvm-as, opt, llc, clang, python3, rustc (optional: go)
# Output: benchmarks/optimizer/v4.90.0-current.json
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

RUNS=5
CROSS="--cross-language"

if [[ "${1:-}" == "--quick" ]]; then
    RUNS=3
    CROSS=""
fi

echo "=== v4.90.0 Benchmark Reproduction ==="
echo "Runs per benchmark: $RUNS"
echo "Cross-language: ${CROSS:-disabled}"
echo ""

# Check prerequisites
for tool in llvm-as opt llc clang python3; do
    if ! command -v "$tool" &>/dev/null; then
        echo "ERROR: $tool not found in PATH"
        exit 1
    fi
done

if [ ! -f "$ROOT/runtime/native/libmapanare_rt.a" ]; then
    echo "ERROR: libmapanare_rt.a not found. Build with: make -C runtime/native"
    exit 1
fi

# Run benchmarks
python3 "$SCRIPT_DIR/run_baseline.py" \
    --runs "$RUNS" \
    $CROSS \
    --output "$SCRIPT_DIR/v4.90.0-current.json"

echo ""
echo "Results saved to benchmarks/optimizer/v4.90.0-current.json"
echo "Compare against v4.82.0-baseline.json for cumulative delta."
