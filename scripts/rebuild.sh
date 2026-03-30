#!/usr/bin/env bash
# rebuild.sh — One-command edit-compile-test cycle for the self-hosted compiler.
#
# Usage:
#   bash scripts/rebuild.sh              # concat + build + golden (default)
#   bash scripts/rebuild.sh golden       # same as above
#   bash scripts/rebuild.sh quick        # concat + build only (skip golden)
#   bash scripts/rebuild.sh full         # concat + build + golden + selftest + memory
#   bash scripts/rebuild.sh test         # pytest only (no rebuild)
#   bash scripts/rebuild.sh audit        # rebuild + audit main.ll
#   bash scripts/rebuild.sh worklist     # rebuild + worklist
#
# Timings (typical):
#   concat:  <1s
#   build:   5-15s
#   golden:  2-5s
#   selftest: 5-60s
#   memory:  10-30s

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MODE="${1:-golden}"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

step() { echo -e "${CYAN}=== $1 ===${NC}"; }
ok()   { echo -e "${GREEN}OK${NC}: $1"; }
fail() { echo -e "${RED}FAIL${NC}: $1"; }
warn() { echo -e "${YELLOW}WARN${NC}: $1"; }

# Track total time
SECONDS=0

do_concat() {
    step "Concatenating self-hosted modules"
    python3 scripts/concat_self.py 2>&1
}

do_build() {
    step "Building mnc-stage1"
    python3 scripts/build_stage1.py 2>&1 | tail -2
    if [ $? -ne 0 ]; then
        fail "build_stage1.py failed"
        exit 1
    fi
}

do_pytest() {
    step "Running pytest (self-hosted + llvm + mir)"
    python3 -m pytest tests/self_hosted/ tests/llvm/ tests/mir/ -q --tb=short 2>&1 | tail -3
}

do_golden() {
    step "Golden tests (fresh, no cache)"
    python3 scripts/ir_doctor.py golden 2>&1
}

do_audit() {
    step "Auditing main.ll"
    python3 scripts/ir_doctor.py audit mapanare/self/main.ll 2>&1
}

do_worklist() {
    step "Alloca aliasing worklist"
    python3 scripts/ir_doctor.py worklist mapanare/self/main.ll 2>&1
}

do_selftest() {
    step "Self-compilation test"
    python3 scripts/ir_doctor.py selftest 2>&1
}

do_memory() {
    step "Memory scaling test"
    python3 scripts/ir_doctor.py memory 2>&1
}

case "$MODE" in
    quick)
        do_concat
        do_build
        ;;
    golden)
        do_concat
        do_build
        do_golden
        ;;
    full)
        do_concat
        do_build
        do_golden
        do_selftest
        do_memory
        ;;
    test)
        do_pytest
        ;;
    audit)
        do_concat
        do_build
        do_audit
        ;;
    worklist)
        do_concat
        do_build
        do_worklist
        ;;
    *)
        echo "Usage: bash scripts/rebuild.sh [golden|quick|full|test|audit|worklist]"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Done in ${SECONDS}s${NC}"
