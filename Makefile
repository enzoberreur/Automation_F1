# Makefile - Ferrari F1 IoT Smart Pit-Stop

.PHONY: help build up down logs test clean benchmark production dev health

# Variables de configuration
COMPOSE_FILE = docker-compose.yml
PROJECT_NAME = ferrari-f1-iot
DOCKER_REGISTRY = ghcr.io/enzoberreur
VERSION = 1.0.0

# Aide par défaut
help: ## Afficher cette aide
	@echo "Ferrari F1 IoT Smart Pit-Stop - Commands Available:"
	@echo "================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# =======================
# DÉVELOPPEMENT LOCAL
# =======================

build: ## Construire toutes les images Docker
	@echo "🔨 Construction des images Docker Ferrari F1..."
	docker-compose -f $(COMPOSE_FILE) build --no-cache

up: ## Démarrer tous les services en arrière-plan
	@echo "🏁 Démarrage de la stack Ferrari F1 IoT..."
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "✅ Stack démarrée! Vérifiez les services:"
	@echo "   📊 Grafana: http://localhost:3000 (admin/admin)"
	@echo "   📈 Prometheus: http://localhost:9090"
	@echo "   🔄 Airflow: http://localhost:8080"
	@echo "   🏎️  Sensor Metrics: http://localhost:8000/metrics"

dev: ## Mode développement avec logs en temps réel
	@echo "🚧 Mode développement Ferrari F1..."
	docker-compose -f $(COMPOSE_FILE) up

down: ## Arrêter tous les services
	@echo "🛑 Arrêt de la stack Ferrari F1..."
	docker-compose -f $(COMPOSE_FILE) down

clean: ## Nettoyer containers, volumes et images
	@echo "🧹 Nettoyage complet de l'environnement..."
	docker-compose -f $(COMPOSE_FILE) down -v --remove-orphans
	docker system prune -f
	@echo "✅ Nettoyage terminé!"

# =======================
# MONITORING & LOGS  
# =======================

logs: ## Afficher les logs de tous les services
	docker-compose -f $(COMPOSE_FILE) logs -f

logs-sensor: ## Logs sensor-simulator uniquement  
	docker-compose -f $(COMPOSE_FILE) logs -f sensor-simulator

logs-processor: ## Logs stream-processor uniquement
	docker-compose -f $(COMPOSE_FILE) logs -f stream-processor

logs-airflow: ## Logs Airflow scheduler et webserver
	docker-compose -f $(COMPOSE_FILE) logs -f airflow-scheduler airflow-webserver

health: ## Vérifier la santé de tous les services
	@echo "🏥 Vérification santé des services Ferrari F1..."
	@echo ""
	@echo "📊 Prometheus Targets:"
	@curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, state: .health}' 2>/dev/null || echo "Prometheus non accessible"
	@echo ""
	@echo "🏎️  Sensor Simulator Health:"
	@curl -s http://localhost:8001/health 2>/dev/null || echo "Sensor Simulator non accessible"
	@echo ""
	@echo "⚡ Stream Processor Health:"  
	@curl -s http://localhost:8001/health 2>/dev/null || echo "Stream Processor non accessible"
	@echo ""
	@echo "📈 Services Docker Status:"
	@docker-compose -f $(COMPOSE_FILE) ps

# =======================
# TESTS & BENCHMARKS
# =======================

test: ## Lancer les tests unitaires
	@echo "🧪 Exécution des tests Ferrari F1..."
	docker-compose -f $(COMPOSE_FILE) exec stream-processor python -m pytest tests/ -v
	docker-compose -f $(COMPOSE_FILE) exec sensor-simulator python -m pytest tests/ -v 2>/dev/null || echo "Tests sensor-simulator non configurés"

benchmark: ## Lancer les benchmarks de performance
	@echo "🏎️  Lancement des benchmarks Ferrari F1..."
	cd benchmark && python run_tests.py --duration=60 --target-rate=500
	@echo "📊 Résultats dans benchmark/results/"

load-test: ## Test de charge intensive (5 minutes)
	@echo "🔥 Test de charge intensive Ferrari F1..."
	cd benchmark && python run_tests.py --duration=300 --target-rate=1000 --concurrent=10

# =======================
# PRODUCTION & DÉPLOIEMENT
# =======================

production: ## Configuration optimisée production
	@echo "🏭 Configuration production Ferrari F1..."
	@cp docker-compose.yml docker-compose.prod.yml
	@sed -i.bak 's/restart: "no"/restart: always/g' docker-compose.prod.yml
	@sed -i.bak 's/127.0.0.1://g' docker-compose.prod.yml
	@echo "✅ docker-compose.prod.yml créé pour production"
	docker-compose -f docker-compose.prod.yml up -d

k8s-deploy: ## Déployer sur Kubernetes  
	@echo "☸️  Déploiement Kubernetes Ferrari F1..."
	kubectl apply -f k8s/
	@echo "✅ Déployé! Vérifiez avec: kubectl get pods"

k8s-status: ## Status du déploiement Kubernetes
	@echo "☸️  Status Kubernetes Ferrari F1:"
	kubectl get pods,services -l app.kubernetes.io/name=ferrari-f1

k8s-clean: ## Nettoyer le déploiement Kubernetes
	kubectl delete -f k8s/

# =======================
# REGISTRY & IMAGES
# =======================

push: ## Pousser les images vers le registry
	@echo "📦 Publication des images Ferrari F1..."
	docker tag $(PROJECT_NAME)_sensor-simulator $(DOCKER_REGISTRY)/$(PROJECT_NAME)-sensor-simulator:$(VERSION)
	docker tag $(PROJECT_NAME)_stream-processor $(DOCKER_REGISTRY)/$(PROJECT_NAME)-stream-processor:$(VERSION)
	docker tag $(PROJECT_NAME)_monitoring $(DOCKER_REGISTRY)/$(PROJECT_NAME)-monitoring:$(VERSION)
	docker push $(DOCKER_REGISTRY)/$(PROJECT_NAME)-sensor-simulator:$(VERSION)
	docker push $(DOCKER_REGISTRY)/$(PROJECT_NAME)-stream-processor:$(VERSION) 
	docker push $(DOCKER_REGISTRY)/$(PROJECT_NAME)-monitoring:$(VERSION)

pull: ## Récupérer les images du registry
	docker pull $(DOCKER_REGISTRY)/$(PROJECT_NAME)-sensor-simulator:$(VERSION)
	docker pull $(DOCKER_REGISTRY)/$(PROJECT_NAME)-stream-processor:$(VERSION)
	docker pull $(DOCKER_REGISTRY)/$(PROJECT_NAME)-monitoring:$(VERSION)

# =======================
# UTILITAIRES
# =======================

ps: ## Lister tous les conteneurs du projet
	docker-compose -f $(COMPOSE_FILE) ps

exec-sensor: ## Shell interactif sensor-simulator
	docker-compose -f $(COMPOSE_FILE) exec sensor-simulator /bin/bash

exec-processor: ## Shell interactif stream-processor  
	docker-compose -f $(COMPOSE_FILE) exec stream-processor /bin/bash

exec-airflow: ## Shell interactif Airflow scheduler
	docker-compose -f $(COMPOSE_FILE) exec airflow-scheduler /bin/bash

reset: ## Reset complet (DANGER: perte de données!)
	@echo "⚠️  ATTENTION: Reset complet de l'environnement Ferrari F1"
	@echo "Toutes les données seront perdues. Continuer? [y/N]"
	@read confirm && [ "$$confirm" = "y" ] || exit 1
	$(MAKE) down
	docker volume prune -f
	docker network prune -f
	$(MAKE) build
	$(MAKE) up

# =======================
# MAINTENANCE
# =======================

backup: ## Sauvegarde des données importantes
	@echo "💾 Sauvegarde Ferrari F1..."
	@mkdir -p backups/$(shell date +%Y%m%d_%H%M%S)
	docker-compose -f $(COMPOSE_FILE) exec -T postgres pg_dump -U airflow airflow > backups/$(shell date +%Y%m%d_%H%M%S)/postgres_backup.sql
	@echo "✅ Sauvegarde dans backups/"

update: ## Mise à jour des images Docker
	@echo "⬆️  Mise à jour Ferrari F1..."
	docker-compose -f $(COMPOSE_FILE) pull
	$(MAKE) down
	$(MAKE) up
	@echo "✅ Mise à jour terminée!"

# Valeurs par défaut
.DEFAULT_GOAL := help