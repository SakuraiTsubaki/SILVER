#!/usr/bin/env bash
set -euo pipefail

VERSION="${MGBA_VERSION:-0.10.5}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MACHINE="$(uname -m)"

case "$MACHINE" in
  x86_64|amd64)
    ARCH="x64"
    ;;
  aarch64|arm64)
    ARCH="arm64"
    ;;
  *)
    echo "Unsupported architecture for official mGBA AppImage: $MACHINE" >&2
    exit 2
    ;;
esac

CACHE_ROOT="${MGBA_CACHE_DIR:-$ROOT_DIR/.tools/mgba}"
INSTALL_DIR="$CACHE_ROOT/$VERSION/$ARCH"
BIN="$INSTALL_DIR/mgba.AppImage"
ASSET="mGBA-$VERSION-appimage-$ARCH.appimage"
URL="${MGBA_RELEASE_BASE:-https://github.com/mgba-emu/mgba/releases/download}/$VERSION/$ASSET"

mkdir -p "$INSTALL_DIR"

if [[ ! -x "$BIN" ]]; then
  TMP="$BIN.part"
  rm -f "$TMP"

  echo "Downloading official mGBA $VERSION ($ARCH) from GitHub..." >&2
  if command -v curl >/dev/null 2>&1; then
    curl --fail --location --retry 3 --retry-delay 2 --output "$TMP" "$URL"
  elif command -v wget >/dev/null 2>&1; then
    wget --tries=3 --output-document="$TMP" "$URL"
  else
    echo "curl or wget is required to bootstrap mGBA." >&2
    exit 3
  fi

  if [[ ! -s "$TMP" ]]; then
    echo "mGBA download produced an empty file." >&2
    rm -f "$TMP"
    exit 4
  fi

  # AppImage is an ELF executable. Reject HTML/error payloads before caching.
  if [[ "$(LC_ALL=C head -c 4 "$TMP" | od -An -t x1 | tr -d ' \n')" != "7f454c46" ]]; then
    echo "Downloaded file is not an ELF/AppImage payload." >&2
    rm -f "$TMP"
    exit 5
  fi

  chmod 0755 "$TMP"
  mv "$TMP" "$BIN"
fi

printf '%s\n' "$BIN"
