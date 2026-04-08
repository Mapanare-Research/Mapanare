#!/bin/bash
# ============================================================
#  Mapanare Transpile-to-Native Benchmark
#
#  Shows the full pipeline:
#    1. mapanare transpile  (Python → Mapanare)
#    2. mapanare emit-llvm  (Mapanare → LLVM IR)
#    3. clang -O2           (LLVM IR → native binary)
#    4. Run and compare
#
#  Usage: bash examples/transpile/run_demo.sh
# ============================================================
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
TMP="/tmp/mn_bench_$$"
mkdir -p "$TMP"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${BOLD}========================================================${NC}"
echo -e "${BOLD}  Mapanare: Python → Native Benchmark${NC}"
echo -e "${BOLD}  Pipeline: .py → transpile → .mn → LLVM IR → binary${NC}"
echo -e "${BOLD}========================================================${NC}"
echo ""

run_bench() {
    local NAME="$1"
    local PY_FILE="$2"
    local DESC="$3"

    echo -e "${CYAN}--- $NAME ---${NC}"
    echo -e "${YELLOW}$DESC${NC}"
    echo ""

    # Step 1: Show Python source
    local PY_LINES
    PY_LINES=$(wc -l < "$PY_FILE")
    echo -e "  [1/5] Python source: $PY_FILE ($PY_LINES lines)"

    # Step 2: Transpile
    local MN_FILE="$TMP/$(basename "${PY_FILE%.py}.mn")"
    python3 -m mapanare transpile "$PY_FILE" -o "$MN_FILE" 2>/dev/null
    local MN_LINES
    MN_LINES=$(wc -l < "$MN_FILE")
    echo -e "  [2/5] Transpiled:    $MN_FILE ($MN_LINES lines)"

    # Step 3: Emit LLVM IR
    local LL_FILE="$TMP/$(basename "${PY_FILE%.py}.ll")"
    python3 -m mapanare emit-llvm "$MN_FILE" -o "$LL_FILE" 2>/dev/null
    echo "  [3/5] LLVM IR:       $LL_FILE"

    # Step 4: Compile to native
    local BIN_FILE="$TMP/$(basename "${PY_FILE%.py}")"
    clang -O2 "$LL_FILE" -o "$BIN_FILE" -lm 2>/dev/null
    echo "  [4/5] Native binary: $BIN_FILE"
    echo ""

    # Step 5: Run both and compare
    echo "  [5/5] Running..."
    echo ""

    local PY_START PY_END PY_MS PY_OUT
    PY_START=$(date +%s%N)
    PY_OUT=$(python3 "$PY_FILE" 2>&1)
    PY_END=$(date +%s%N)
    PY_MS=$(( (PY_END - PY_START) / 1000000 ))
    echo "  Python output: $PY_OUT"
    echo -e "  Python time:   ${PY_MS}ms"

    local MN_START MN_END MN_MS MN_OUT
    MN_START=$(date +%s%N)
    MN_OUT=$("$BIN_FILE" 2>&1)
    MN_END=$(date +%s%N)
    MN_MS=$(( (MN_END - MN_START) / 1000000 ))
    echo "  Native output: $MN_OUT"
    echo -e "  Native time:   ${MN_MS}ms"

    if [ "$MN_MS" -gt 0 ]; then
        local SPEEDUP=$(( PY_MS / MN_MS ))
        echo -e "  ${GREEN}>>> Speedup: ~${SPEEDUP}x faster${NC}"
    else
        echo -e "  ${GREEN}>>> Native completed in <1ms${NC}"
    fi
    echo ""

    # Store for summary
    eval "BENCH_${BENCH_N}_NAME='$NAME'"
    eval "BENCH_${BENCH_N}_PY=$PY_MS"
    eval "BENCH_${BENCH_N}_MN=$MN_MS"
    BENCH_N=$((BENCH_N + 1))
}

BENCH_N=0

run_bench "Recursive Fibonacci fib(40)" \
          "fibonacci_bench.py" \
          "Pure function-call overhead. ~2^40 recursive calls."

run_bench "Count Primes below 500,000" \
          "primes.py" \
          "Trial division with nested loops + early return."

run_bench "Longest Collatz Chain below 1,000,000" \
          "collatz.py" \
          "1M iterations, each with variable-length inner loop."

# Summary
echo -e "${BOLD}========================================================${NC}"
echo -e "${BOLD}  Summary${NC}"
echo -e "${BOLD}========================================================${NC}"
echo ""
printf "  %-38s %9s %9s %9s\n" "Benchmark" "Python" "Native" "Speedup"
printf "  %-38s %9s %9s %9s\n" "──────────────────────────────────────" "─────────" "─────────" "─────────"
for ((j=0; j<BENCH_N; j++)); do
    eval "N=\$BENCH_${j}_NAME"
    eval "P=\$BENCH_${j}_PY"
    eval "M=\$BENCH_${j}_MN"
    if [ "$M" -gt 0 ]; then
        S="~$(( P / M ))x"
    else
        S="<1ms"
    fi
    printf "  %-38s %7dms %7dms %9s\n" "$N" "$P" "$M" "$S"
done
echo ""
echo "  Pipeline: .py → mapanare transpile → mapanare emit-llvm → clang -O2"
echo "  Zero manual edits. Types inferred from Python annotations."
echo ""

rm -rf "$TMP"
