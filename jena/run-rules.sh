#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
CATALOG="$REPO/data/catalog.ttl"
OUT="$REPO/data/catalog-inferred.ttl"
TMP="$(mktemp)"

for rule in "$REPO"/rules/*.rq; do
  sparql --data "$CATALOG" --query "$rule" --results=ttl \
    | grep -viE '^[[:space:]]*@?prefix[[:space:]]' \
    | grep -vE '^[[:space:]]*$' \
    | grep -vE '^[[:space:]]*#' >> "$TMP"
done

{ echo "@prefix tdy: <https://tdytrading.example/parts#> ."; echo ""; sort -u "$TMP"; } > "$OUT"
rm -f "$TMP"
echo "wrote $OUT"
