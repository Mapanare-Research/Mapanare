#!/usr/bin/env bash
# Strict fixed-point validation. Build stage1 first; artifacts and a manifest
# are retained under build/fixed-point-*. No diff/crash tolerance is accepted.
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 scripts/verify_fixed_point.py "$@"