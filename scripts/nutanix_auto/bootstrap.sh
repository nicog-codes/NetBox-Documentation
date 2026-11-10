#!/usr/bin/env bash
set -euo pipefail
APP_DIR="/opt/netbox-import/nutanix-auto"
ENV_FILE="/opt/netbox-import/netbox-library-import/.env"
BASE="https://raw.githubusercontent.com/nicog-codes/NetBox-Documentation/main"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERREUR: NETBOX_URL et NETBOX_TOKEN attendus dans $ENV_FILE" >&2
  exit 2
fi
mkdir -p "$APP_DIR/data"
cd "$APP_DIR"
curl -fsSL "$BASE/scripts/nutanix_auto/pipeline.py" -o pipeline.py
curl -fsSL "$BASE/scripts/nutanix_auto/Dockerfile" -o Dockerfile
curl -fsSL "$BASE/scripts/import_nutanix_elevation_images.py" -o import_nutanix_elevation_images.py
docker build -t nutanix-auto-elevations:local .
echo
if [[ "$#" -gt 0 && "$1" == "--apply" ]]; then
  echo "MODE: IMPORT REEL"
else
  echo "MODE: SIMULATION"
fi
echo "Images / controle : $APP_DIR/data"
docker run --rm \
  --env-file "$ENV_FILE" \
  -e NETBOX_TLS_VERIFY=false \
  -v "$APP_DIR/data:/data" \
  nutanix-auto-elevations:local "$@"
