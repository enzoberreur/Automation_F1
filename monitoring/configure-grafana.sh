#!/bin/bash

# ============================================================================
# FERRARI F1 IoT - Configuration Grafana Dashboard
# ============================================================================
# Script pour configurer Grafana après le démarrage
# - Importer le dashboard Ferrari F1
# - Configurer les alertes
# - Vérifier les métriques

set -e

echo "🏎️  Ferrari F1 IoT - Configuration Dashboard Grafana"
echo "=================================================="

GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASS="admin"

# Fonction d'attente avec timeout
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_wait=60
    local count=0
    
    echo "⏳ Attente de $service_name..."
    while [ $count -lt $max_wait ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            echo "✅ $service_name est disponible"
            return 0
        fi
        echo "   Tentative $((count+1))/$max_wait..."
        sleep 2
        count=$((count+1))
    done
    
    echo "❌ Timeout: $service_name n'est pas disponible"
    return 1
}

# Attendre Grafana
wait_for_service "$GRAFANA_URL/api/health" "Grafana"

# Attendre Prometheus  
wait_for_service "http://localhost:9090/-/healthy" "Prometheus"

echo ""
echo "📊 Vérification des métriques disponibles..."

# Vérifier les métriques Ferrari
METRICS=$(curl -s "http://localhost:9090/api/v1/label/__name__/values" | jq -r '.data[]' | grep ferrari || true)

if [ -n "$METRICS" ]; then
    echo "✅ Métriques Ferrari détectées:"
    echo "$METRICS" | while read metric; do
        echo "   📈 $metric"
    done
else
    echo "⚠️  Aucune métrique Ferrari détectée (normal au premier démarrage)"
fi

echo ""
echo "🎯 Configuration du dashboard..."

# Note: Dashboard automatique supprimé - utiliser le dashboard principal via provisioning

echo ""
echo "🎯 Configuration terminée !"
echo ""
echo "📱 Accès aux interfaces:"
echo "   🔗 Grafana: http://localhost:3000"
echo "   🔑 Login: admin / admin"
echo "   📊 Prometheus: http://localhost:9090"
echo ""
echo "📈 Métriques temps réel disponibles:"
echo "   • ferrari_messages_received_total"
echo "   • ferrari_pitstop_score" 
echo "   • ferrari_active_anomalies"
echo "   • ferrari_processing_latency_seconds"
echo ""
echo "🏎️  Prêt pour la démonstration ! Forza Ferrari! 🏎️"