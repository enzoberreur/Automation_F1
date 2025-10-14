#!/bin/bash
# Script de déploiement rapide pour le sensor-simulator

set -e

echo "🏎️  Ferrari F1 Sensor Simulator - Déploiement Kubernetes"
echo "=========================================================="

# Variables
NAMESPACE=${NAMESPACE:-default}
IMAGE_NAME="ferrari-sensor-simulator:latest"
MODE=${MODE:-minikube}

# Fonction de vérification
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 n'est pas installé"
        exit 1
    fi
    echo "✅ $1 trouvé"
}

# Vérifications préliminaires
echo ""
echo "📋 Vérification des prérequis..."
check_command docker
check_command kubectl

if [ "$MODE" = "minikube" ]; then
    check_command minikube
    
    # Vérifier que Minikube est démarré
    if ! minikube status &> /dev/null; then
        echo "⚠️  Minikube n'est pas démarré"
        echo "🚀 Démarrage de Minikube..."
        minikube start --cpus=4 --memory=8192 --driver=docker
    else
        echo "✅ Minikube actif"
    fi
fi

# Build de l'image Docker
echo ""
echo "🔨 Construction de l'image Docker..."
if [ "$MODE" = "minikube" ]; then
    echo "📦 Configuration de Docker pour Minikube..."
    eval $(minikube docker-env)
fi

cd "$(dirname "$0")/.."
docker build -t $IMAGE_NAME ./sensor-simulator

echo "✅ Image construite: $IMAGE_NAME"

# Déploiement sur Kubernetes
echo ""
echo "🚀 Déploiement sur Kubernetes (namespace: $NAMESPACE)..."
kubectl apply -f k8s/sensor-simulator.yaml -n $NAMESPACE

# Attente du déploiement
echo ""
echo "⏳ Attente du déploiement..."
kubectl rollout status deployment/sensor-simulator -n $NAMESPACE

# Affichage de l'état
echo ""
echo "📊 État du déploiement:"
kubectl get pods -l app=sensor-simulator -n $NAMESPACE
kubectl get svc sensor-simulator -n $NAMESPACE
kubectl get hpa sensor-simulator-hpa -n $NAMESPACE

# Logs
echo ""
echo "📜 Logs des premiers pods (Ctrl+C pour arrêter):"
sleep 2
kubectl logs -f -l app=sensor-simulator -n $NAMESPACE --all-containers=true --max-log-requests=5

echo ""
echo "✅ Déploiement terminé!"
echo ""
echo "Commandes utiles:"
echo "  kubectl get pods -l app=sensor-simulator"
echo "  kubectl logs -f deployment/sensor-simulator"
echo "  kubectl top pods -l app=sensor-simulator"
echo "  kubectl get hpa sensor-simulator-hpa --watch"
