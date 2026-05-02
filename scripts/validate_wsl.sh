#!/usr/bin/env bash
# v5.25.0 Pv.4 — Linux pytest signal from a Windows host.
#
# Closes the gap that produced the v5.13.0 → v5.24.1 "fresh-checkout
# CI surprise" class: the Pv.1/Pv.2 regressions were both caught by
# Linux pytest jobs after a stale local Windows artifact masked them
# on the developer machine. This script gives the dev one command
# to run the Linux pytest path before push, without leaving the
# Windows dev loop.
#
# Designed to be invoked two ways:
#   1. Direct on Linux/WSL:  ``bash scripts/validate_wsl.sh``
#   2. From Windows pwsh:    ``.\dev.ps1 validate-wsl``
#                            (which shells out to wsl -d Ubuntu).
#
# The pre-push hook at ``scripts/hooks/pre-push.sample`` is the
# opt-in third entry-point.
#
# Strict mode: fail on any error, undefined var, or pipe break.
# The script must be safe to invoke from any CWD — the first thing
# it does is ``cd`` to the repo root (resolved relative to itself).

set -euo pipefail

# Resolve the repo root from this script's location so ``cd``
# survives ``wsl -d Ubuntu bash -c "..."`` (runs in $HOME, not
# the project dir, per dev.ps1 prompt note).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

echo "[validate-wsl] repo root: $REPO_ROOT"

# Step 1: rebuild the runtime archive. Required so the Pv.3
# clean-build-test gate has something to link against and so any
# ``mapanare test`` invocation in the test suite succeeds.
echo "[validate-wsl] make build-rt"
make -s build-rt

# Step 2: rebuild the bootstrap stage1 binary. Bootstrap-side
# tests (tests/bootstrap/*) skip if mnc-stage1 is absent — but a
# stale stage1 against new C-runtime exports produces wrong-answer
# greens, not skips. Always rebuild.
echo "[validate-wsl] python3 scripts/build_stage1.py"
python3 scripts/build_stage1.py >/dev/null

# Step 3: full pytest. ``-x`` short-circuits on the first failure
# so the dev sees the real signal fast; ``-n auto`` parallelizes
# across cores. ``--tb=short`` keeps tracebacks tight when a
# failure does fire.
echo "[validate-wsl] pytest tests/"
exec pytest tests/ -x -n auto --tb=short
