#!/usr/bin/env bash
# Mapanare Language Installer
# Usage:
#   curl -fsSL https://mapanare.dev/install | bash
#   curl -fsSL https://mapanare.dev/install | bash -s -- --version 4.0.0
#   curl -fsSL https://mapanare.dev/install | bash -s -- --install-dir ~/.local/bin
set -euo pipefail

REPO="Mapanare-Research/Mapanare"
INSTALL_DIR="${MAPANARE_INSTALL_DIR:-/usr/local/bin}"
REQUESTED_VERSION=""

# ---------- Parse arguments ----------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)    REQUESTED_VERSION="$2"; shift 2 ;;
    --install-dir) INSTALL_DIR="$2"; shift 2 ;;
    --help|-h)
      echo "Usage: curl -fsSL https://mapanare.dev/install | bash -s -- [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --version VERSION    Install a specific version (e.g. 4.0.0)"
      echo "  --install-dir DIR    Install to DIR (default: /usr/local/bin)"
      echo "  --help               Show this help"
      exit 0 ;;
    *) echo "Unknown option: $1. Use --help for usage."; exit 1 ;;
  esac
done

TMP_DIR="$(mktemp -d)"

cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

# ---------- Detect platform ----------
OS="$(uname -s)"
ARCH="$(uname -m)"

case "$OS" in
  Linux)   PLATFORM="linux" ;;
  Darwin)  PLATFORM="mac"   ;;
  *)       echo "Error: Unsupported OS: $OS"; exit 1 ;;
esac

case "$ARCH" in
  x86_64|amd64)   ARCH_TAG="x64"   ;;
  aarch64|arm64)   ARCH_TAG="arm64" ;;
  *)               echo "Error: Unsupported architecture: $ARCH"; exit 1 ;;
esac

ARTIFACT="mapanare-${PLATFORM}-${ARCH_TAG}.tar.gz"

# ---------- Resolve version ----------
if [ -n "$REQUESTED_VERSION" ]; then
  # Ensure v prefix
  case "$REQUESTED_VERSION" in
    v*) VERSION="$REQUESTED_VERSION" ;;
    *)  VERSION="v${REQUESTED_VERSION}" ;;
  esac
else
  VERSION="${MAPANARE_VERSION:-latest}"
fi

if [ "$VERSION" = "latest" ]; then
  echo "Fetching latest release..."
  VERSION="$(curl -fsSL "https://api.github.com/repos/${REPO}/releases/latest" | grep '"tag_name"' | sed -E 's/.*"tag_name":\s*"([^"]+)".*/\1/')"
fi

if [ -z "$VERSION" ]; then
  echo "Error: Could not determine latest version."
  echo "Set MAPANARE_VERSION=vX.Y.Z or use --version to install a specific version."
  exit 1
fi

DOWNLOAD_URL="https://github.com/${REPO}/releases/download/${VERSION}/${ARTIFACT}"

# ---------- Download & install ----------
echo ""
echo "  Mapanare Language Installer"
echo "  Version:  ${VERSION}"
echo "  Platform: ${PLATFORM}-${ARCH_TAG}"
echo "  Target:   ${INSTALL_DIR}"
echo ""

echo "Downloading ${ARTIFACT}..."
if ! curl -fSL --progress-bar -o "${TMP_DIR}/${ARTIFACT}" "$DOWNLOAD_URL"; then
  echo ""
  echo "Error: Download failed."
  echo "  URL: ${DOWNLOAD_URL}"
  echo ""
  echo "Possible causes:"
  echo "  - Version ${VERSION} may not exist"
  echo "  - No binary available for ${PLATFORM}-${ARCH_TAG}"
  echo "  - Check releases: https://github.com/${REPO}/releases"
  exit 1
fi

echo "Extracting..."
tar -xzf "${TMP_DIR}/${ARTIFACT}" -C "$TMP_DIR"

# Install binary
NEEDS_SUDO=false
if [ ! -w "$INSTALL_DIR" ]; then
  NEEDS_SUDO=true
fi

echo "Installing to ${INSTALL_DIR}..."
if [ "$NEEDS_SUDO" = true ]; then
  sudo cp -f "${TMP_DIR}/mapanare/mapanare" "${INSTALL_DIR}/mapanare"
  sudo chmod +x "${INSTALL_DIR}/mapanare"
else
  cp -f "${TMP_DIR}/mapanare/mapanare" "${INSTALL_DIR}/mapanare"
  chmod +x "${INSTALL_DIR}/mapanare"
fi

# Copy supporting files (shared libs, etc.) if the dist has them
if [ -d "${TMP_DIR}/mapanare/_internal" ]; then
  MAPANARE_LIB_DIR="${INSTALL_DIR}/../lib/mapanare"
  if [ "$NEEDS_SUDO" = true ]; then
    sudo mkdir -p "$MAPANARE_LIB_DIR"
    sudo cp -rf "${TMP_DIR}/mapanare/_internal" "$MAPANARE_LIB_DIR/"
  else
    mkdir -p "$MAPANARE_LIB_DIR"
    cp -rf "${TMP_DIR}/mapanare/_internal" "$MAPANARE_LIB_DIR/"
  fi
fi

# ---------- Install mapanare-up (version manager) ----------
MAPANARE_HOME="${MAPANARE_HOME:-$HOME/.mapanare}"
UP_DIR="$MAPANARE_HOME/bin"
mkdir -p "$UP_DIR"

echo "Installing version manager (mapanare-up)..."
UP_URL="https://raw.githubusercontent.com/${REPO}/main/packaging/mapanare-up.sh"
SHIM_URL="https://raw.githubusercontent.com/${REPO}/main/packaging/mapanare-shim.sh"

curl -fsSL "$UP_URL" -o "$UP_DIR/mapanare-up" 2>/dev/null && chmod +x "$UP_DIR/mapanare-up" || true
curl -fsSL "$SHIM_URL" -o "$UP_DIR/mapanare-shim" 2>/dev/null && chmod +x "$UP_DIR/mapanare-shim" || true

# Store this version for mapanare-up tracking
VER_CLEAN="$(echo "$VERSION" | sed 's/^v//')"
DEST_DIR="$MAPANARE_HOME/versions/$VER_CLEAN"
mkdir -p "$DEST_DIR"
if [ -f "${INSTALL_DIR}/mapanare" ]; then
  ln -sf "${INSTALL_DIR}/mapanare" "$DEST_DIR/mapanare" 2>/dev/null || true
fi
echo "$VER_CLEAN" > "$MAPANARE_HOME/default"

# Add ~/.mapanare/bin to PATH if not already there
SHELL_RC=""
if [ -f "$HOME/.zshrc" ]; then
  SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
  SHELL_RC="$HOME/.bashrc"
fi

if [ -n "$SHELL_RC" ] && ! grep -q 'mapanare/bin' "$SHELL_RC" 2>/dev/null; then
  echo "" >> "$SHELL_RC"
  echo '# Mapanare version manager' >> "$SHELL_RC"
  echo 'export PATH="$HOME/.mapanare/bin:$PATH"' >> "$SHELL_RC"
fi

# ---------- Verify ----------
echo ""
if command -v mapanare &>/dev/null; then
  echo "Installed successfully!"
  echo ""
  mapanare --version
  echo ""
  echo "Get started:"
  echo "  mapanare init myproject"
  echo "  cd myproject"
  echo "  mapanare run main.mn       # compile & run"
  echo "  mapanare check main.mn     # type-check only"
  echo "  mapanare build main.mn     # native binary (requires LLVM)"
  echo ""
  echo "Version manager:"
  echo "  mapanare-up list           # show installed versions"
  echo "  mapanare-up install 4.0.0  # install a specific version"
  echo "  mapanare-up default 4.0.0  # set global default"
else
  echo "Installed to ${INSTALL_DIR}/mapanare"
  echo ""
  echo "Make sure ${INSTALL_DIR} is in your PATH:"
  echo "  export PATH=\"${INSTALL_DIR}:\$PATH\""
fi
