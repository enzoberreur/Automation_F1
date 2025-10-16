#!/bin/bash

# Script pour importer le dashboard Ferrari F1 ULTIMATE dans Grafana
# Usage: ./import-dashboard.sh [--silent]

SILENT=""

# Parse arguments
for arg in "$@"; do
    case $arg in
        --silent)
            SILENT="--silent"
            ;;
    esac
done

log() {
    if [ "$SILENT" != "--silent" ]; then
        echo "$1"
    fi
}

log "� Import du Ferrari F1 ULTIMATE Command Center Dashboard..."

# Attendre que Grafana soit prêt
log "⏳ Attente que Grafana soit prêt..."
timeout=60
while [ $timeout -gt 0 ]; do
    if curl -s -f http://localhost:3000/api/health >/dev/null 2>&1; then
        log "✅ Grafana est prêt!"
        break
    fi
    sleep 2
    timeout=$((timeout-2))
done

if [ $timeout -le 0 ]; then
    log "❌ Timeout: Grafana non accessible"
    exit 1
fi

check_dashboard_exists() {
    local dashboard_uid=$1
    local dashboard_name=$2
    
    response=$(curl -s -u admin:admin "http://localhost:3000/api/dashboards/uid/$dashboard_uid")
    
    if echo "$response" | grep -q '"dashboard"'; then
        log "✅ $dashboard_name existe déjà (pas de re-import)"
        return 0
    else
        return 1
    fi
}

import_dashboard() {
    local dashboard_file=$1
    local dashboard_name=$2
    local expected_uid=$3
    
    # Vérifier si le dashboard existe déjà
    if [ -n "$expected_uid" ] && check_dashboard_exists "$expected_uid" "$dashboard_name"; then
        if [ "$SILENT" != "--silent" ]; then
            echo "🔗 $dashboard_name: http://localhost:3000/d/$expected_uid"
        fi
        return 0
    fi
    
    log "📊 Import du $dashboard_name..."

    # Préparer le payload : Grafana accepte {"dashboard": <dashboard>, "overwrite": true}
    # Si le fichier contient déjà la clé "dashboard", on l'utilise tel quel.
    payload=$(mktemp)
    python3 - "$dashboard_file" > "$payload" <<'PY'
import json,sys
f=sys.argv[1]
obj=json.load(open(f))
if isinstance(obj, dict) and 'dashboard' in obj:
    print(json.dumps(obj))
else:
    print(json.dumps({'dashboard': obj, 'overwrite': True}))
PY

    response=$(curl -s -X POST \
      http://localhost:3000/api/dashboards/db \
      -H 'Content-Type: application/json' \
      -u admin:admin \
      -d @"$payload")
    rm -f "$payload"
    
    # Vérifier si l'import a réussi
    if echo "$response" | grep -q '"status":"success"'; then
        log "✅ $dashboard_name importé avec succès!"
        if [ "$SILENT" != "--silent" ]; then
            # Extraire l'URL du dashboard
            dashboard_uid=$(echo "$response" | grep -o '"uid":"[^"]*"' | cut -d'"' -f4)
            if [ -n "$dashboard_uid" ]; then
                echo "🔗 $dashboard_name: http://localhost:3000/d/$dashboard_uid"
            fi
        fi
        return 0
    elif echo "$response" | grep -q "already exists"; then
        log "ℹ️  $dashboard_name déjà existant"
        return 0
    else
        log "❌ Erreur lors de l'import du $dashboard_name"
        if [ "$SILENT" != "--silent" ]; then
            echo "API response: $response"
        fi
        return 1
    fi
}

# Import des dashboards multi-écuries avec vérification d'existence
log "📊 Import des dashboards multi-écuries"
import_dashboard "monitoring/grafana_dashboard_main.json" "F1 Multi-Team - Main Operations" "ferrari-main-dashboard"
import_dashboard "monitoring/grafana_dashboard_strategy.json" "F1 Multi-Team - Strategy" "ferrari-strategy-dashboard"

log ""
if [ "$SILENT" != "--silent" ]; then
    echo "🌡️ FERRARI F1 THERMAL COCKPIT DEMO PRÊT!"
    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│ 🌡️ Thermal Demo:       http://localhost:3000/d/ferr... │"
    echo "│ 🏆 Ultimate Backup:     http://localhost:3000/d/278...  │"
    echo "│ 🔐 Login:               admin / admin                   │"
    echo "│                                                         │"
    echo "│ 🔥 THERMAL COCKPIT FEATURES (DEMO):                    │"
    echo "│ • 🌡️ Thermal performance simulation                   │"
    echo "│ • ⚡ Energy flow heatmap                               │"
    echo "│ • 🏁 Performance radar (4 dimensions)                 │"
    echo "│ • 🔮 Predictive pit-stop strategy                     │"
    echo "│ • 📈 Real-time efficiency score (0-100)              │"
    echo "│ • 🚨 System thermal load monitoring                   │"
    echo "└─────────────────────────────────────────────────────────┘"
fi