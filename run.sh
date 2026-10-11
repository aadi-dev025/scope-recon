#!/usr/bin/env bash
# convenience wrapper so I don't have to remember flags at 2am.
# usage: ./run.sh example.com scope.json
set -euo pipefail

DOMAIN="${1:-}"
SCOPE="${2:-scope.json}"

if [ -z "$DOMAIN" ]; then
  echo "usage: ./run.sh <domain> [scope.json]" >&2
  exit 1
fi

if [ ! -f "$SCOPE" ]; then
  echo "no scope file at $SCOPE -- make one (see scope.example.json)" >&2
  exit 1
fi

mkdir -p out
STAMP=$(date +%Y%m%d-%H%M%S)

python3 recon.py "$DOMAIN" --scope "$SCOPE" --json \
  | tee "out/${DOMAIN}-${STAMP}.json"

echo "saved to out/${DOMAIN}-${STAMP}.json" >&2
