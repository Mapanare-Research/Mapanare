#!/usr/bin/env bash
# Bundle Mapanare compiler modules into public/compiler/ for Pyodide.
# Run from the playground/ directory.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLAYGROUND_DIR="$(dirname "$SCRIPT_DIR")"
REPO_DIR="$(dirname "$PLAYGROUND_DIR")"
OUT="$PLAYGROUND_DIR/public/compiler"

echo "Bundling compiler modules from $REPO_DIR -> $OUT"

mkdir -p "$OUT/runtime"

# Core compiler modules
for f in __init__.py ast_nodes.py types.py parser.py semantic.py \
         optimizer.py emit_python.py diagnostics.py modules.py linter.py; do
  if [ -f "$REPO_DIR/mapanare/$f" ]; then
    cp "$REPO_DIR/mapanare/$f" "$OUT/$f"
    echo "  copied mapanare/$f"
  else
    echo "  WARN: mapanare/$f not found, writing empty file"
    echo "" > "$OUT/$f"
  fi
done

# Grammar
cp "$REPO_DIR/mapanare/mapanare.lark" "$OUT/mapanare.lark"
echo "  copied mapanare.lark"

# Runtime modules
for f in __init__.py agent.py signal.py stream.py result.py; do
  if [ -f "$REPO_DIR/runtime/$f" ]; then
    cp "$REPO_DIR/runtime/$f" "$OUT/runtime/$f"
    echo "  copied runtime/$f"
  else
    echo "  WARN: runtime/$f not found, writing empty file"
    echo "" > "$OUT/runtime/$f"
  fi
done

echo "Done. $(find "$OUT" -type f | wc -l) files bundled."
