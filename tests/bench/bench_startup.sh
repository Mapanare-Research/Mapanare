#!/usr/bin/env bash
# Repeated measurements; compilation failures always fail this check.
# --gate adds a ceiling; --baseline <json> enables a relative regression gate.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ARGS=()
if [ "${1:-}" = "--gate" ]; then
    ARGS+=(--max-ms 5000)
    shift
fi
exec python3 "${ROOT}/benchmarks/compile_time.py" "${ARGS[@]}" "$@"
