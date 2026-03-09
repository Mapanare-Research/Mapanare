#!/usr/bin/env bash
# Mapanare Language Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/Mapanare-Research/Mapanare/main/install.sh | bash
set -euo pipefail

REPO="Mapanare-Research/Mapanare"
INSTALL_DIR="${MAPANARE_INSTALL_DIR:-/usr/local/bin}"
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
VERSION="${MAPANARE_VERSION:-latest}"
if [ "$VERSION" = "latest" ]; then
  echo "Fetching latest release..."
  VERSION="$(curl -fsSL "https://api.github.com/repos/${REPO}/releases/latest" | grep '"tag_name"' | sed -E 's/.*"tag_name":\s*"([^"]+)".*/\1/')"
fi

if [ -z "$VERSION" ]; then
  echo "Error: Could not determine latest version."
  echo "Set MAPANARE_VERSION=vX.Y.Z to install a specific version."
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
  echo "  mapanare run main.mn"
else
  echo "Installed to ${INSTALL_DIR}/mapanare"
  echo ""
  echo "Make sure ${INSTALL_DIR} is in your PATH:"
  echo "  export PATH=\"${INSTALL_DIR}:\$PATH\""
fi
