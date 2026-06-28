#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "==> validating CSVs"
python3 src/validate_csv.py

echo "==> generating catalog.ttl from CSVs"
python3 src/intake.py

echo "==> running compatibility rules"
./jena/run-rules.sh

echo "==> done. catalog.ttl and catalog-inferred.ttl regenerated."
echo "    rebuild the container with: docker compose build --no-cache"
