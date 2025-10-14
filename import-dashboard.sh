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

import_dashboard() {
    local dashboard_file=$1
    local dashboard_name=$2
    
    log "📊 Import du $dashboard_name..."
    response=$(curl -s -X POST \
      http://localhost:3000/api/dashboards/db \
      -H 'Content-Type: application/json' \
      -u admin:admin \
      -d @$dashboard_file)
    
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
        return 1
    fi
}

# Import du dashboard ULTIMATE
log "🏆 Import du dashboard ULTIMATE Ferrari F1 Command Center"
import_dashboard "monitoring/ferrari_f1_ultimate_dashboard.json" "Ferrari F1 Ultimate Command Center"

# Import du dashboard standard comme backup
if [ -f "monitoring/grafana_dashboard.json" ]; then
    log ""
    log "📊 Import du dashboard standard (backup)"
    import_dashboard "monitoring/grafana_dashboard.json" "Ferrari F1 Standard Dashboard"
fi

log ""
if [ "$SILENT" != "--silent" ]; then
    echo "� FERRARI F1 ULTIMATE COMMAND CENTER PRÊT!"
    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│ 🏆 Ultimate Dashboard: http://localhost:3000/d/ferr... │"
    echo "│ 📊 Standard Backup:    http://localhost:3000/d/278...  │"
    echo "│ 🔐 Login:              admin / admin                   │"
    echo "│                                                         │"
    echo "│ 🎯 ULTIMATE FEATURES:                                  │"
    echo "│ • 📊 Real-time telemetry monitoring                    │"
    echo "│ • 🔮 Predictive analytics & forecasting               │"
    echo "│ • 🏁 Race strategy intelligence                        │"
    echo "│ • 🚨 Advanced alerting & SLA monitoring               │"
    echo "│ • � Performance heat analysis                         │"
    echo "│ • 💰 Business impact & ROI tracking                   │"
    echo "└─────────────────────────────────────────────────────────┘"
fi