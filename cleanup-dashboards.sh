#!/bin/bash
# Script de nettoyage des dashboards Grafana

GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASS="admin"

echo "🧹 NETTOYAGE DES DASHBOARDS GRAFANA"
echo "===================================="

# Vérifier si Grafana est accessible
if ! curl -s "$GRAFANA_URL/api/health" >/dev/null; then
    echo "❌ Grafana non accessible sur $GRAFANA_URL"
    exit 1
fi

echo "✅ Grafana accessible"

# Récupérer la liste des dashboards
DASHBOARDS=$(curl -s -u "$GRAFANA_USER:$GRAFANA_PASS" "$GRAFANA_URL/api/search?type=dash-db")

echo "📊 Dashboards trouvés:"
echo "$DASHBOARDS" | jq -r '.[] | "\(.uid) - \(.title)"' 2>/dev/null || echo "Erreur lors de la récupération"

# Dashboard à conserver (par UID ou pattern)
KEEP_PATTERN="Professional Analytics"

echo ""
echo "🎯 Dashboard à conserver: *$KEEP_PATTERN*"
echo "❌ Suppression de tous les autres dashboards..."

# Supprimer tous les dashboards sauf celui à garder
echo "$DASHBOARDS" | jq -r '.[] | select(.title | contains("'"$KEEP_PATTERN"'") | not) | .uid' 2>/dev/null | while read -r uid; do
    if [ ! -z "$uid" ]; then
        TITLE=$(echo "$DASHBOARDS" | jq -r '.[] | select(.uid == "'"$uid"'") | .title' 2>/dev/null)
        echo "🗑️  Suppression: $TITLE ($uid)"
        
        RESPONSE=$(curl -s -X DELETE \
            -u "$GRAFANA_USER:$GRAFANA_PASS" \
            "$GRAFANA_URL/api/dashboards/uid/$uid")
        
        if echo "$RESPONSE" | grep -q '"message":"Dashboard deleted"'; then
            echo "✅ Supprimé: $TITLE"
        else
            echo "⚠️  Erreur suppression: $TITLE"
        fi
    fi
done

echo ""
echo "✅ Nettoyage terminé!"
echo ""

# Vérification finale
REMAINING=$(curl -s -u "$GRAFANA_USER:$GRAFANA_PASS" "$GRAFANA_URL/api/search?type=dash-db")
COUNT=$(echo "$REMAINING" | jq '. | length' 2>/dev/null || echo "?")

echo "📊 Dashboards restants ($COUNT):"
echo "$REMAINING" | jq -r '.[] | "  • \(.title)"' 2>/dev/null || echo "Aucun ou erreur"