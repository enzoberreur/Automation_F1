#!/usr/bin/env bash
set -euo pipefail

SILENT=0
if [[ "${1:-}" == "--silent" ]]; then
  SILENT=1
fi

log() {
  if [[ $SILENT -eq 0 ]]; then
    echo "$1"
  fi
}

GRAFANA_URL=${GRAFANA_URL:-http://localhost:3000}
GRAFANA_USER=${GRAFANA_USER:-admin}
GRAFANA_PASSWORD=${GRAFANA_PASSWORD:-admin}

log "Importing Grafana dashboards..."

# Wait until Grafana is reachable
for _ in {1..60}; do
  if curl -sSf "${GRAFANA_URL}/api/health" >/dev/null; then
    break
  fi
  sleep 2
done

if ! curl -sSf "${GRAFANA_URL}/api/health" >/dev/null; then
  log "Grafana is not reachable"
  exit 1
fi

import_dashboard() {
  local file=$1
  local name=$2

  tmp_payload=$(mktemp)
  python3 - "$file" >"$tmp_payload" <<'PY'
import json
import sys
path = sys.argv[1]
data = json.load(open(path))
if isinstance(data, dict) and 'dashboard' in data:
    data['overwrite'] = True
else:
    data = {'dashboard': data, 'overwrite': True}
json.dump(data, sys.stdout)
PY

  response=$(curl -sS -X POST \
    "${GRAFANA_URL}/api/dashboards/db" \
    -H 'Content-Type: application/json' \
    -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
    --data-binary "@${tmp_payload}")
  rm -f "$tmp_payload"

  if echo "$response" | grep -q '"status":"success"'; then
    if [[ $SILENT -eq 0 ]]; then
      echo "Imported ${name}"
    fi
    return 0
  fi

  if [[ $SILENT -eq 0 ]]; then
    echo "Failed to import ${name}: ${response}" >&2
  fi
  return 1
}

import_dashboard monitoring/grafana_dashboard_main.json "F1 Multi-Team - Main Operations"
import_dashboard monitoring/grafana_dashboard_strategy.json "F1 Multi-Team - Strategy"

exit 0
