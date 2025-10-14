# Makefile - Ferrari F1 IoT Smart Pit-Stop

.PHONY: help build up dev down clean logs health benchmark airflow-trigger ps reset

# Aide par défaut
help: ## Afficher cette aide
	@echo "Ferrari F1 IoT Smart Pit-Stop - Commandes Disponibles:"
	@echo "======================================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# =======================
# DÉVELOPPEMENT LOCAL
# =======================

build: ## Construire toutes les images Docker
	@echo "🔨 Construction des images Docker Ferrari F1..."
	docker-compose build --no-cache

up: ## Démarrer tous les services
	@echo "🏁 Démarrage de la stack Ferrari F1 IoT..."
	docker-compose up -d
	@echo "✅ Stack démarrée! Interfaces disponibles:"
	@echo "   📊 Grafana: http://localhost:3000 (admin/admin)"
	@echo "   📈 Prometheus: http://localhost:9090"
	@echo "   🔄 Airflow: http://localhost:8080"
	@echo "   🏎️  Sensor Metrics: http://localhost:8000/metrics"

dev: ## Mode développement avec logs en temps réel
	@echo "🚧 Mode développement Ferrari F1..."
	docker-compose up

down: ## Arrêter tous les services
	@echo "🛑 Arrêt de la stack Ferrari F1..."
	docker-compose down

clean: ## Nettoyer containers, volumes et images
	@echo "🧹 Nettoyage complet..."
	docker-compose down -v --remove-orphans
	docker system prune -f
	@echo "✅ Nettoyage terminé!"

# =======================
# MONITORING & LOGS  
# =======================

logs: ## Afficher les logs de tous les services
	docker-compose logs -f

health: ## Vérifier la santé de tous les services
	@echo "🏥 Santé des services Ferrari F1..."
	@echo ""
	@echo "📊 Services Docker:"
	@docker-compose ps
	@echo ""
	@echo "📈 Prometheus Targets:"
	@curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, state: .health}' 2>/dev/null || echo "Prometheus non accessible"

# =======================
# BENCHMARKS & AIRFLOW
# =======================

benchmark: ## Métriques temps réel du système Ferrari F1
	@echo "🏎️  Ferrari F1 - Métriques Temps Réel"
	@echo "======================================"
	@echo ""
	@MESSAGES=$$(curl -s "http://localhost:8000/metrics" | grep "ferrari_simulator_messages_sent_total " | tail -1 | awk '{print $$2}'); echo "📈 Messages totaux: $$MESSAGES"
	@LATENCY=$$(curl -s "http://localhost:8000/metrics" | awk '/ferrari_simulator_send_latency_seconds_sum/ {sum=$$2} /ferrari_simulator_send_latency_seconds_count/ {count=$$2} END {if(sum && count) printf "%.2f ms", (sum/count)*1000; else print "N/A"}'); echo "⚡ Latence moyenne: $$LATENCY"
	@ERRORS=$$(curl -s "http://localhost:8000/metrics" | grep "ferrari_simulator_send_errors_total " | tail -1 | awk '{print $$2}' 2>/dev/null || echo "0"); echo "❌ Erreurs: $$ERRORS"
	@echo ""
	@echo "🎯 Dashboards Ferrari F1:"
	@echo "   📊 Grafana: http://localhost:3000 (admin/admin)"
	@echo "   📈 Prometheus: http://localhost:9090"
	@echo "   🔄 Airflow: http://localhost:8080"
	@echo "   🏎️  Métriques: http://localhost:8000/metrics"

airflow-trigger: ## Déclencher manuellement le DAG Ferrari Grand Prix
	@echo "🏎️  Déclenchement DAG Ferrari Grand Prix..."
	@docker-compose exec -T airflow-scheduler airflow dags trigger ferrari_grand_prix_dag
	@echo "✅ DAG déclenché! Interface: http://localhost:8080"

# =======================
# UTILITAIRES
# =======================

ps: ## Status des conteneurs
	docker-compose ps

reset: ## Reset complet (ATTENTION: perte de données!)
	@echo "⚠️  ATTENTION: Reset complet de l'environnement Ferrari F1"
	@echo "Toutes les données seront perdues. Continuer? [y/N]"
	@read confirm && [ "$$confirm" = "y" ] || exit 1
	$(MAKE) down
	docker volume prune -f
	docker network prune -f
	$(MAKE) build
	$(MAKE) up

# Valeur par défaut
.DEFAULT_GOAL := help