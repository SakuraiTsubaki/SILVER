#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MGBA_BIN="$("$ROOT_DIR/tools/bootstrap_mgba.sh")"

# AppImage FUSE is often unavailable in containers; extraction mode works there.
export APPIMAGE_EXTRACT_AND_RUN="${APPIMAGE_EXTRACT_AND_RUN:-1}"

exec "$MGBA_BIN" "$@"
