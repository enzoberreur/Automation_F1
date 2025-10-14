#!/bin/bash

# Script de fix rapide pour K8s - utilise les images Docker locales
echo "🔧 Fix rapide Kubernetes Ferrari F1..."

# 1. Construire et charger les images dans le cluster local
echo "📦 Construction et chargement des images..."

# Construire les images
docker-compose build sensor-simulator stream-processor

# Pour Docker Desktop K8s, les images sont déjà disponibles
# Pour minikube, il faudrait faire : minikube image load

echo "🏎️ Redéploiement simplifié Ferrari F1..."

# 2. Créer des déploiements simplifiés sans les features avancées
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stream-processor-simple
  namespace: ferrari-f1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: stream-processor
  template:
    metadata:
      labels:
        app: stream-processor
    spec:
      containers:
      - name: stream-processor
        image: automation_f1-stream-processor:latest
        imagePullPolicy: Never
        ports:
        - containerPort: 8001
        env:
        - name: TELEMETRY_MODE
          value: "http"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: stream-processor-simple
  namespace: ferrari-f1
spec:
  selector:
    app: stream-processor
  ports:
  - port: 8001
    targetPort: 8001
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sensor-simulator-simple
  namespace: ferrari-f1
spec:
  replicas: 1
  selector:
    matchLabels:
      app: sensor-simulator
  template:
    metadata:
      labels:
        app: sensor-simulator
    spec:
      containers:
      - name: sensor-simulator
        image: automation_f1-sensor-simulator:latest
        imagePullPolicy: Never
        ports:
        - containerPort: 8000
        env:
        - name: TELEMETRY_MODE
          value: "http"
        - name: STREAM_PROCESSOR_URL
          value: "http://stream-processor-simple:8001"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: sensor-simulator-simple
  namespace: ferrari-f1
spec:
  selector:
    app: sensor-simulator
  ports:
  - port: 8000
    targetPort: 8000
EOF

echo "✅ Déploiement simplifié terminé!"

# 3. Attendre et afficher le statut
echo "⏳ Attente que les pods soient prêts..."
sleep 10

kubectl get pods -n ferrari-f1

echo ""
echo "🎯 Pour accéder aux services:"
echo "kubectl port-forward -n ferrari-f1 svc/grafana 3000:3000"
echo "kubectl port-forward -n ferrari-f1 svc/prometheus 9090:9090"