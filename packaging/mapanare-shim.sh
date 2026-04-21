#!/usr/bin/env bash
# Mapanare version shim — resolves version and dispatches to the right binary.
# Installed at ~/.mapanare/bin/mapanare
#
# Resolution order:
#   1. .mapanare-version file (walk up directories)
#   2. MAPANARE_VERSION environment variable
#   3. ~/.mapanare/default file

set -euo pipefail

MAPANARE_HOME="${MAPANARE_HOME:-$HOME/.mapanare}"

resolve_version() {
  # Walk up directories looking for .mapanare-version
  local dir="$PWD"
  while [ "$dir" != "/" ] && [ "$dir" != "." ]; do
    if [ -f "$dir/.mapanare-version" ]; then
      cat "$dir/.mapanare-version"
      return
    fi
    dir="$(dirname "$dir")"
  done
  # Fall back to env var
  if [ -n "${MAPANARE_VERSION:-}" ]; then
    echo "$MAPANARE_VERSION"
    return
  fi
  # Fall back to default
  if [ -f "$MAPANARE_HOME/default" ]; then
    cat "$MAPANARE_HOME/default"
    return
  fi
  echo ""
}

VERSION="$(resolve_version)"
if [ -z "$VERSION" ]; then
  echo "mapanare: no version set" >&2
  echo "  Run: mapanare-up install latest" >&2
  echo "  Or create .mapanare-version in your project root" >&2
  exit 1
fi

# Try the full CLI first, then the native compiler
BINARY="$MAPANARE_HOME/versions/$VERSION/mapanare"
if [ ! -x "$BINARY" ]; then
  BINARY="$MAPANARE_HOME/versions/$VERSION/mnc"
fi

if [ ! -x "$BINARY" ]; then
  echo "mapanare: version $VERSION not installed" >&2
  echo "  Run: mapanare-up install $VERSION" >&2
  exit 1
fi

exec "$BINARY" "$@"
