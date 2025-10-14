#!/bin/bash
# Script de déploiement pour stream-processor

set -e

echo "🏎️  Ferrari F1 Stream Processor - Déploiement Kubernetes"
echo "=========================================================="

# Variables
NAMESPACE=${NAMESPACE:-default}
IMAGE_NAME="ferrari-stream-processor:latest"
MODE=${MODE:-minikube}

# Vérifications
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 n'est pas installé"
        exit 1
    fi
    echo "✅ $1 trouvé"
}

echo ""
echo "📋 Vérification des prérequis..."
check_command docker
check_command kubectl

if [ "$MODE" = "minikube" ]; then
    check_command minikube
    
    if ! minikube status &> /dev/null; then
        echo "⚠️  Minikube n'est pas démarré"
        echo "🚀 Démarrage de Minikube..."
        minikube start --cpus=4 --memory=8192 --driver=docker
    else
        echo "✅ Minikube actif"
    fi
fi

# Build
echo ""
echo "🔨 Construction de l'image Docker..."
if [ "$MODE" = "minikube" ]; then
    eval $(minikube docker-env)
fi

cd "$(dirname "$0")/.."
docker build -t $IMAGE_NAME ./stream-processor

echo "✅ Image construite: $IMAGE_NAME"

# Déploiement
echo ""
echo "🚀 Déploiement sur Kubernetes (namespace: $NAMESPACE)..."
kubectl apply -f k8s/stream-processor.yaml -n $NAMESPACE

# Attente
echo ""
echo "⏳ Attente du déploiement..."
kubectl rollout status deployment/stream-processor -n $NAMESPACE

# État
echo ""
echo "📊 État du déploiement:"
kubectl get pods -l app=stream-processor -n $NAMESPACE
kubectl get svc stream-processor -n $NAMESPACE
kubectl get hpa stream-processor-hpa -n $NAMESPACE

# Port-forward pour accès local
echo ""
echo "🌐 Configuration du port-forward..."
kubectl port-forward -n $NAMESPACE svc/stream-processor 8001:8001 &
PF_PID=$!

sleep 2

echo ""
echo "✅ Déploiement terminé!"
echo ""
echo "📡 Service accessible sur: http://localhost:8001"
echo "📊 Métriques Prometheus: http://localhost:8001/metrics"
echo "💊 Health check: http://localhost:8001/health"
echo ""
echo "Commandes utiles:"
echo "  kubectl get pods -l app=stream-processor"
echo "  kubectl logs -f deployment/stream-processor"
echo "  kubectl top pods -l app=stream-processor"
echo "  curl http://localhost:8001/stats"
echo ""
echo "Pour arrêter le port-forward: kill $PF_PID"
