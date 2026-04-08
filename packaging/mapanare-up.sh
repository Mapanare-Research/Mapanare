#!/usr/bin/env bash
# mapanare-up — Mapanare version manager
# Like pyenv but for Mapanare. Manages multiple compiler versions side-by-side.
#
# Usage:
#   mapanare-up install <version|latest>   Install a version
#   mapanare-up list                       List installed versions
#   mapanare-up default <version>          Set the global default version
#   mapanare-up use <version>              Print shell command to set version
#   mapanare-up current                    Show active version
#   mapanare-up update                     Update mapanare-up itself
#   mapanare-up uninstall <version>        Remove an installed version
#   mapanare-up help                       Show this help

set -euo pipefail

VERSION="0.1.0"
REPO="Mapanare-Research/Mapanare"
MAPANARE_HOME="${MAPANARE_HOME:-$HOME/.mapanare}"
VERSIONS_DIR="$MAPANARE_HOME/versions"
BIN_DIR="$MAPANARE_HOME/bin"
DEFAULT_FILE="$MAPANARE_HOME/default"

# Ensure directories exist
mkdir -p "$VERSIONS_DIR" "$BIN_DIR"

# ---------- Helpers ----------

detect_platform() {
  local os arch
  os="$(uname -s)"
  arch="$(uname -m)"
  case "$os" in
    Linux)   os="linux" ;;
    Darwin)  os="mac"   ;;
    *)       echo "Error: Unsupported OS: $os" >&2; exit 1 ;;
  esac
  case "$arch" in
    x86_64|amd64)  arch="x64"   ;;
    aarch64|arm64) arch="arm64" ;;
    *)             echo "Error: Unsupported arch: $arch" >&2; exit 1 ;;
  esac
  echo "${os}-${arch}"
}

resolve_latest() {
  curl -fsSL "https://api.github.com/repos/${REPO}/releases/latest" \
    | grep '"tag_name"' \
    | sed -E 's/.*"tag_name":\s*"v?([^"]+)".*/\1/'
}

ensure_v_prefix() {
  case "$1" in
    v*) echo "$1" ;;
    *)  echo "v$1" ;;
  esac
}

strip_v_prefix() {
  echo "$1" | sed 's/^v//'
}

# ---------- Commands ----------

cmd_install() {
  local version="$1"

  if [ "$version" = "latest" ]; then
    echo "Resolving latest version..."
    version="$(resolve_latest)"
    if [ -z "$version" ]; then
      echo "Error: Could not determine latest version." >&2
      exit 1
    fi
    echo "Latest: $version"
  fi

  local ver_clean
  ver_clean="$(strip_v_prefix "$version")"
  local ver_tag
  ver_tag="$(ensure_v_prefix "$version")"
  local dest="$VERSIONS_DIR/$ver_clean"

  if [ -d "$dest" ] && [ -x "$dest/mapanare" -o -x "$dest/mnc" ]; then
    echo "Version $ver_clean is already installed at $dest"
    return 0
  fi

  local platform
  platform="$(detect_platform)"
  local artifact="mapanare-${platform}.tar.gz"
  local url="https://github.com/${REPO}/releases/download/${ver_tag}/${artifact}"

  echo ""
  echo "  mapanare-up install"
  echo "  Version:  $ver_clean"
  echo "  Platform: $platform"
  echo "  Source:   GitHub Releases"
  echo ""

  local tmp
  tmp="$(mktemp -d)"
  trap "rm -rf '$tmp'" EXIT

  echo "Downloading $artifact..."
  if ! curl -fSL --progress-bar -o "$tmp/$artifact" "$url"; then
    echo ""
    echo "Error: Download failed for $ver_tag ($platform)" >&2
    echo "  URL: $url" >&2
    echo "  Check: https://github.com/${REPO}/releases/tag/${ver_tag}" >&2
    exit 1
  fi

  echo "Extracting..."
  tar -xzf "$tmp/$artifact" -C "$tmp"

  mkdir -p "$dest"

  # Copy binary and support files
  if [ -f "$tmp/mapanare/mapanare" ]; then
    cp -f "$tmp/mapanare/mapanare" "$dest/mapanare"
    chmod +x "$dest/mapanare"
  fi
  if [ -d "$tmp/mapanare/_internal" ]; then
    cp -rf "$tmp/mapanare/_internal" "$dest/_internal"
  fi

  # Set as default if no default exists
  if [ ! -f "$DEFAULT_FILE" ]; then
    echo "$ver_clean" > "$DEFAULT_FILE"
    echo "Set $ver_clean as default (first install)"
  fi

  echo ""
  echo "Installed Mapanare $ver_clean to $dest"

  # Install shim if not present
  if [ ! -f "$BIN_DIR/mapanare" ]; then
    _install_shim
  fi
}

cmd_list() {
  local default_ver=""
  if [ -f "$DEFAULT_FILE" ]; then
    default_ver="$(cat "$DEFAULT_FILE")"
  fi

  if [ ! -d "$VERSIONS_DIR" ] || [ -z "$(ls -A "$VERSIONS_DIR" 2>/dev/null)" ]; then
    echo "No versions installed."
    echo "Run: mapanare-up install latest"
    return
  fi

  echo "Installed versions:"
  echo ""
  for dir in "$VERSIONS_DIR"/*/; do
    local ver
    ver="$(basename "$dir")"
    if [ "$ver" = "$default_ver" ]; then
      echo "  * $ver (default)"
    else
      echo "    $ver"
    fi
  done
  echo ""

  # Show active version context
  local active=""
  local project_ver=""
  local d="$PWD"
  while [ "$d" != "/" ] && [ "$d" != "." ]; do
    if [ -f "$d/.mapanare-version" ]; then
      project_ver="$(cat "$d/.mapanare-version")"
      break
    fi
    d="$(dirname "$d")"
  done

  if [ -n "$project_ver" ]; then
    echo "Active: $project_ver (from .mapanare-version)"
  elif [ -n "${MAPANARE_VERSION:-}" ]; then
    echo "Active: $MAPANARE_VERSION (from \$MAPANARE_VERSION)"
  elif [ -n "$default_ver" ]; then
    echo "Active: $default_ver (default)"
  fi
}

cmd_default() {
  local version="$1"
  local ver_clean
  ver_clean="$(strip_v_prefix "$version")"

  if [ ! -d "$VERSIONS_DIR/$ver_clean" ]; then
    echo "Error: Version $ver_clean is not installed." >&2
    echo "Run: mapanare-up install $ver_clean" >&2
    exit 1
  fi

  echo "$ver_clean" > "$DEFAULT_FILE"
  echo "Default set to $ver_clean"
}

cmd_use() {
  local version="$1"
  local ver_clean
  ver_clean="$(strip_v_prefix "$version")"

  if [ ! -d "$VERSIONS_DIR/$ver_clean" ]; then
    echo "Error: Version $ver_clean is not installed." >&2
    exit 1
  fi

  echo "Run this in your shell:"
  echo ""
  echo "  export MAPANARE_VERSION=$ver_clean"
  echo ""
  echo "Or create a .mapanare-version file in your project:"
  echo ""
  echo "  echo '$ver_clean' > .mapanare-version"
}

cmd_current() {
  # Same resolution as the shim
  local ver=""
  local source=""

  local d="$PWD"
  while [ "$d" != "/" ] && [ "$d" != "." ]; do
    if [ -f "$d/.mapanare-version" ]; then
      ver="$(cat "$d/.mapanare-version")"
      source=".mapanare-version"
      break
    fi
    d="$(dirname "$d")"
  done

  if [ -z "$ver" ] && [ -n "${MAPANARE_VERSION:-}" ]; then
    ver="$MAPANARE_VERSION"
    source="\$MAPANARE_VERSION"
  fi

  if [ -z "$ver" ] && [ -f "$DEFAULT_FILE" ]; then
    ver="$(cat "$DEFAULT_FILE")"
    source="default"
  fi

  if [ -z "$ver" ]; then
    echo "No active version. Run: mapanare-up install latest"
    exit 1
  fi

  echo "$ver (via $source)"
}

cmd_update() {
  echo "Updating mapanare-up..."
  local url="https://raw.githubusercontent.com/${REPO}/main/packaging/mapanare-up.sh"
  if curl -fsSL "$url" -o "$BIN_DIR/mapanare-up.tmp"; then
    mv "$BIN_DIR/mapanare-up.tmp" "$BIN_DIR/mapanare-up"
    chmod +x "$BIN_DIR/mapanare-up"
    echo "Updated to latest version."
  else
    echo "Error: Update failed." >&2
    rm -f "$BIN_DIR/mapanare-up.tmp"
    exit 1
  fi

  # Also update the shim
  _install_shim
  echo "Shim updated."
}

cmd_uninstall() {
  local version="$1"
  local ver_clean
  ver_clean="$(strip_v_prefix "$version")"
  local dest="$VERSIONS_DIR/$ver_clean"

  if [ ! -d "$dest" ]; then
    echo "Error: Version $ver_clean is not installed." >&2
    exit 1
  fi

  rm -rf "$dest"
  echo "Uninstalled Mapanare $ver_clean"

  # Warn if it was the default
  if [ -f "$DEFAULT_FILE" ] && [ "$(cat "$DEFAULT_FILE")" = "$ver_clean" ]; then
    rm -f "$DEFAULT_FILE"
    echo "Warning: $ver_clean was the default. Run 'mapanare-up default <version>' to set a new one."
  fi
}

cmd_help() {
  echo "mapanare-up $VERSION — Mapanare version manager"
  echo ""
  echo "Usage:"
  echo "  mapanare-up install <version|latest>   Install a version"
  echo "  mapanare-up list                       List installed versions"
  echo "  mapanare-up default <version>          Set the global default"
  echo "  mapanare-up use <version>              Print shell export command"
  echo "  mapanare-up current                    Show active version"
  echo "  mapanare-up update                     Update mapanare-up itself"
  echo "  mapanare-up uninstall <version>        Remove a version"
  echo "  mapanare-up help                       Show this help"
  echo ""
  echo "Version resolution (in order):"
  echo "  1. .mapanare-version file (walks up from current directory)"
  echo "  2. \$MAPANARE_VERSION environment variable"
  echo "  3. ~/.mapanare/default file"
  echo ""
  echo "Directories:"
  echo "  MAPANARE_HOME: $MAPANARE_HOME"
  echo "  Versions:      $VERSIONS_DIR"
  echo "  Binaries:      $BIN_DIR"
}

_install_shim() {
  local shim_url="https://raw.githubusercontent.com/${REPO}/main/packaging/mapanare-shim.sh"
  if curl -fsSL "$shim_url" -o "$BIN_DIR/mapanare"; then
    chmod +x "$BIN_DIR/mapanare"
  else
    # Fallback: create a minimal shim inline
    cat > "$BIN_DIR/mapanare" << 'SHIM'
#!/usr/bin/env bash
set -euo pipefail
H="${MAPANARE_HOME:-$HOME/.mapanare}"
V=""; d="$PWD"
while [ "$d" != "/" ]; do [ -f "$d/.mapanare-version" ] && { V=$(cat "$d/.mapanare-version"); break; }; d=$(dirname "$d"); done
[ -z "$V" ] && V="${MAPANARE_VERSION:-}"; [ -z "$V" ] && [ -f "$H/default" ] && V=$(cat "$H/default")
[ -z "$V" ] && { echo "mapanare: no version set. Run: mapanare-up install latest" >&2; exit 1; }
B="$H/versions/$V/mapanare"; [ -x "$B" ] || B="$H/versions/$V/mnc"
[ -x "$B" ] || { echo "mapanare: $V not installed. Run: mapanare-up install $V" >&2; exit 1; }
exec "$B" "$@"
SHIM
    chmod +x "$BIN_DIR/mapanare"
  fi
}

# ---------- Dispatch ----------

if [ $# -eq 0 ]; then
  cmd_help
  exit 0
fi

COMMAND="$1"
shift

case "$COMMAND" in
  install)
    if [ $# -eq 0 ]; then echo "Usage: mapanare-up install <version|latest>" >&2; exit 1; fi
    cmd_install "$1" ;;
  list|ls)
    cmd_list ;;
  default)
    if [ $# -eq 0 ]; then echo "Usage: mapanare-up default <version>" >&2; exit 1; fi
    cmd_default "$1" ;;
  use)
    if [ $# -eq 0 ]; then echo "Usage: mapanare-up use <version>" >&2; exit 1; fi
    cmd_use "$1" ;;
  current)
    cmd_current ;;
  update|self-update)
    cmd_update ;;
  uninstall|remove)
    if [ $# -eq 0 ]; then echo "Usage: mapanare-up uninstall <version>" >&2; exit 1; fi
    cmd_uninstall "$1" ;;
  help|--help|-h)
    cmd_help ;;
  --version|-v)
    echo "mapanare-up $VERSION" ;;
  *)
    echo "Unknown command: $COMMAND" >&2
    echo "Run 'mapanare-up help' for usage." >&2
    exit 1 ;;
esac
