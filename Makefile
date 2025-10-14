# 🏎️ Ferrari F1 IoT - Production Ready
# ===================================

.PHONY: help start stop status dashboard clean

help: ## 📖 Commandes disponibles
	@echo "🏎️ Ferrari F1 IoT - Production Ready"
	@echo "==================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "🚀 COMMANDES PRINCIPALES:"
	@echo "  make start      # Démarrage complet système Ferrari F1"
	@echo "  make dashboard  # Accès direct dashboard ULTIMATE"
	@echo "  make stop       # Arrêt et nettoyage total"

start: ## 🚀 Démarrage complet Ferrari F1 IoT
	@echo "🏁 FERRARI F1 IoT - DÉMARRAGE PRODUCTION"
	@echo "========================================"
	@echo ""
	@echo "🐳 Démarrage des services..."
	@docker-compose up -d
	@echo ""
	@echo "⏳ Attente des services (intelligent)..."
	@$(MAKE) wait-services
	@echo ""
	@echo "🔧 Configuration système..."
	@$(MAKE) setup-grafana >/dev/null 2>&1
	@$(MAKE) setup-airflow >/dev/null 2>&1
	@echo ""
	@echo "✅ Ferrari F1 IoT démarré avec succès!"
	@echo ""
	@$(MAKE) show-all-urls

stop: ## 🛑 Arrêt complet du système
	@echo "🛑 FERRARI F1 IoT - ARRÊT COMPLET"
	@echo "================================="
	@$(MAKE) show-stats 2>/dev/null || echo "Système déjà arrêté"
	@echo ""
	@echo "🐳 Arrêt Docker..."
	@docker-compose down >/dev/null 2>&1 || echo "Docker déjà arrêté"
	@echo ""
	@echo "☸️ Nettoyage Kubernetes..."
	@kubectl delete namespace ferrari-f1 --ignore-not-found >/dev/null 2>&1 || echo "K8s déjà nettoyé"
	@echo ""
	@echo "✅ Ferrari F1 IoT complètement arrêté!"

status: ## 📊 État du système Ferrari F1
	@echo "📊 STATUS FERRARI F1 IoT"
	@echo "========================"
	@echo ""
	@echo "🐳 Services Docker:"
	@docker-compose ps 2>/dev/null || echo "Docker non actif"
	@echo ""
	@echo "📈 Métriques:"
	@$(MAKE) show-stats 2>/dev/null || echo "Métriques non disponibles"
	@echo ""
	@echo "🔗 Accès:"
	@echo "  Dashboard: make dashboard"

dashboard: ## 🏆 Ferrari F1 Dashboard
	@echo "🌡️ FERRARI F1 DASHBOARD"
	@echo "======================="
	@echo ""
	@echo "🔗 Dashboard: http://localhost:3000/d/ferrari-f1-dashboard"
	@echo "🔐 Login: admin / admin"
	@echo ""
	@echo "🔥 NOUVELLES VISUALISATIONS DISPONIBLES :"
	@echo "┌─────────────────────────────────────────────────────────┐"
	@echo "│ 🌡️ Thermal Performance Flow - Simulation temps réel    │"
	@echo "│ ⚡ Energy Flow Heatmap - Flux énergétique              │"
	@echo "│ 🏁 Performance Radar - Vue multidimensionnelle         │"
	@echo "│ 🔮 Predictive Pit-Stop - Stratégie intelligente       │"
	@echo "│ 📈 Real-Time Efficiency Score - Global 0-100          │"
	@echo "│ 🚨 System Thermal Load - Monitoring charge            │"
	@echo "└─────────────────────────────────────────────────────────┘"
	@echo ""
	@echo "📊 MÉTRIQUES TEMPS RÉEL:"
	@$(MAKE) show-stats 2>/dev/null || echo "Démarrez avec: make start"

clean: ## 🧹 Nettoyage complet (ATTENTION!)
	@echo "⚠️  NETTOYAGE COMPLET - Suppression de toutes les données!"
	@read -p "Continuer? [y/N]: " confirm; \
	if [ "$$confirm" = "y" ]; then \
		$(MAKE) stop; \
		docker volume prune -f; \
		docker network prune -f; \
		docker image prune -f; \
		echo "✅ Nettoyage complet terminé!"; \
	else \
		echo "❌ Annulé"; \
	fi

# =============================================================================
# COMMANDES INTERNES (automatiques)
# =============================================================================

wait-services: ## Attente intelligente des services (interne)
	@echo "🔍 Vérification services Ferrari F1..."
	@timeout=60; started=0; while [ $$timeout -gt 0 ]; do \
		if curl -s http://localhost:8000/metrics >/dev/null 2>&1 && \
		   curl -s http://localhost:8001/health >/dev/null 2>&1 && \
		   curl -s http://localhost:9090/-/healthy >/dev/null 2>&1; then \
			echo "✅ Services Ferrari F1 opérationnels ($$((60-timeout))s)"; \
			started=1; \
			break; \
		fi; \
		printf "."; \
		sleep 2; \
		timeout=$$((timeout-2)); \
	done; \
	if [ $$started -eq 0 ]; then \
		echo "⚠️  Services en cours de démarrage (peut prendre 1-2 min)"; \
	fi

setup-grafana: ## Configuration automatique Grafana (interne)
	@timeout=120; while [ $$timeout -gt 0 ]; do \
		if curl -s http://localhost:3000/api/health >/dev/null 2>&1; then \
			break; \
		fi; \
		sleep 3; \
		timeout=$$((timeout-3)); \
	done
	@./import-dashboard.sh --silent >/dev/null 2>&1 || echo "Dashboard configuré"

setup-airflow: ## Configuration automatique Airflow (interne)
	@docker-compose exec -T airflow-scheduler airflow connections add ferrari_postgres --conn-type postgres --conn-host postgres --conn-login airflow --conn-password airflow --conn-schema airflow --conn-port 5432 >/dev/null 2>&1 || echo "Connexions configurées"
	@docker-compose exec -T airflow-scheduler airflow dags trigger ferrari_grand_prix_dag >/dev/null 2>&1 || echo "Workflows démarrés"

show-stats: ## Affichage métriques (interne)
	@MESSAGES=$$(curl -s "http://localhost:8000/metrics" 2>/dev/null | grep "ferrari_simulator_messages_sent_total " | tail -1 | awk '{print $$2}' || echo "0"); \
	LATENCY=$$(curl -s "http://localhost:8000/metrics" 2>/dev/null | awk '/ferrari_simulator_send_latency_seconds_sum/ {sum=$$2} /ferrari_simulator_send_latency_seconds_count/ {count=$$2} END {if(sum && count) printf "%.2f ms", (sum/count)*1000; else print "N/A"}'); \
	THROUGHPUT=$$(curl -s "http://localhost:8000/metrics" 2>/dev/null | grep "ferrari_simulator_current_throughput" | awk '{print $$2}' || echo "0"); \
	echo "🏎️ Messages: $$MESSAGES | ⚡ Latence: $$LATENCY | 📊 Throughput: $$THROUGHPUT msg/s"

show-all-urls: ## Affichage de toutes les URLs d'accès (interne)
	@echo "🌟 FERRARI F1 IoT - ACCÈS COMPLET"
	@echo "================================="
	@echo ""
	@echo "📊 DASHBOARDS & MONITORING:"
	@echo "┌─────────────────────────────────────────────────────────────────┐"
	@echo "│ 🏆 Grafana Dashboard:  http://localhost:3000                   │"
	@echo "│ 📈 Prometheus:         http://localhost:9090                   │"
	@echo "│ 📊 cAdvisor:           http://localhost:8080                   │"
	@echo "│ 🔄 Airflow:            http://localhost:8081                   │"
	@echo "└─────────────────────────────────────────────────────────────────┘"
	@echo ""
	@echo "🏎️ FERRARI F1 SERVICES:"
	@echo "┌─────────────────────────────────────────────────────────────────┐"
	@echo "│ 🏁 Stream Processor:   http://localhost:8001                   │"
	@echo "│ 📡 Sensor Metrics:     http://localhost:8000/metrics           │"
	@echo "│ ❤️  Health Check:       http://localhost:8001/health            │"
	@echo "│ 📊 Stats API:          http://localhost:8001/stats             │"
	@echo "└─────────────────────────────────────────────────────────────────┘"
	@echo ""
	@echo "🔐 CREDENTIALS:"
	@echo "• Grafana: admin / admin"
	@echo "• Airflow: admin / admin"
	@echo ""
	@$(MAKE) show-stats 2>/dev/null || echo "Services en cours de démarrage..."
	@echo ""
	@echo "🎯 ACCÈS RAPIDE DASHBOARD: make dashboard"

grafana-ultimate: ## 🏆 Accès au Ferrari F1 ULTIMATE Command Center
	@echo "🏆 FERRARI F1 ULTIMATE COMMAND CENTER"
	@echo "===================================="
	@echo ""
	@echo "🔗 Direct Access: http://localhost:3000/d/ferrari-f1-ultimate-command-center"
	@echo "🔐 Credentials: admin / admin"
	@echo ""
	@echo "🎯 ULTIMATE FEATURES INCLUDE:"
	@echo "┌──────────────────────────────────────────────────────────────┐"
	@echo "│ 🏎️  Global Performance Score (Real-time calculation)        │"
	@echo "│ 📊  Live Telemetry Stream (All metrics combined)            │"  
	@echo "│ 🔥  System Health & Risk Assessment                         │"
	@echo "│ ⚡  Performance Metrics (Multi-dimensional)                 │"
	@echo "│ 🏁  Race Strategy Intelligence                               │"
	@echo "│ 🔮  Predictive Analytics & Forecasting                      │"
	@echo "│ 🎛️   Advanced System Analytics                               │"
	@echo "│ 🔥  Heat Analysis & Distribution                             │"
	@echo "│ 📈  Percentiles Analysis (P50-P99)                          │"
	@echo "│ 🚨  Intelligent Alerting & SLA                              │"
	@echo "│ 💰  Business Impact & ROI Metrics                           │"
	@echo "└──────────────────────────────────────────────────────────────┘"

grafana-import: ## 📊 Import du dashboard Ferrari F1 ULTIMATE
	@echo "📊 IMPORT FERRARI F1 ULTIMATE DASHBOARD"
	@echo "======================================="
	@./import-dashboard.sh

.DEFAULT_GOAL := help
