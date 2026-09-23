#!/usr/bin/env bash
set -euo pipefail

REF="${POKEEMERALD_EXPANSION_REF:-75b806a3ab57a81ff1eb6179288981f0b3cc3050}"
REPOSITORY="${POKEEMERALD_EXPANSION_REPOSITORY:-https://github.com/rh-hideout/pokeemerald-expansion.git}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE_ROOT="${POKEEMERALD_EXPANSION_CACHE_DIR:-$ROOT_DIR/.tools/pokeemerald-expansion}"
CHECKOUT="$CACHE_ROOT/$REF"

mkdir -p "$CACHE_ROOT"

if [[ ! -d "$CHECKOUT/.git" ]]; then
  rm -rf "$CHECKOUT"
  git clone --filter=blob:none --no-checkout "$REPOSITORY" "$CHECKOUT"
fi

git -C "$CHECKOUT" fetch --depth=1 origin "$REF"
git -C "$CHECKOUT" checkout --detach --force "$REF"

ACTUAL="$(git -C "$CHECKOUT" rev-parse HEAD)"
if [[ "$ACTUAL" != "$REF" ]]; then
  echo "Pinned core mismatch: expected $REF, got $ACTUAL" >&2
  exit 2
fi

printf '%s\n' "$CHECKOUT"
