#!/usr/bin/env bash
# mnc-watch.sh — Watch for .mn file changes and rebuild incrementally.
#
# Usage:
#   bash scripts/mnc-watch.sh <dir> [-o output]
#   bash scripts/mnc-watch.sh mapanare/self/ -o mnc
#
# Requires: inotifywait (from inotify-tools package)
set -euo pipefail

DIR="${1:-.}"
shift || true

if ! command -v inotifywait >/dev/null 2>&1; then
    echo "error: inotifywait not found. Install: sudo apt-get install inotify-tools" >&2
    exit 1
fi

echo "Watching ${DIR} for .mn changes... (Ctrl+C to stop)"

# Initial build
bash scripts/mnc-build.sh "${DIR}" --timing "$@" 2>&1 || true

# Watch for changes
while inotifywait -q -e modify -e create -e delete --include '\.mn$' "${DIR}" >/dev/null 2>&1; do
    echo ""
    echo "--- Change detected, rebuilding... ---"
    bash scripts/mnc-build.sh "${DIR}" --timing "$@" 2>&1 || true
done
