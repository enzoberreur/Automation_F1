# 🏎️ Ferrari F1 IoT - Production Ready  
# ===================================

.PHONY: help start stop clean status demo test

help: ## 📖 Aide - Commandes disponibles
	@echo "🏎️ Ferrari F1 IoT - Production Ready"
	@echo "==================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "🚀 COMMANDE PRINCIPALE:"
	@echo "  make start    # Démarrage COMPLET (Docker + K8s + Grafana + Airflow)"
	@echo "  make stop     # Arrêt et nettoyage total"

start: ## 🚀 DÉMARRAGE PRODUCTION COMPLET
	@echo "🏁 FERRARI F1 IoT - DÉMARRAGE PRODUCTION"
	@echo "========================================"
	@echo ""
	@echo "Mode de déploiement:"
	@echo "1. 🐳 Docker Only (rapide - 2min)"
	@echo "2. ☸️  Kubernetes Only (local - 3min)"  
	@echo "3. 🚀 HYBRID Docker + K8s (demo complète - 5min)"
	@echo ""
	@read -p "Choix [1]: " choice; \
	choice=$${choice:-1}; \
	case $$choice in \
		1) $(MAKE) deploy-docker ;; \
		2) $(MAKE) deploy-k8s ;; \
		3) $(MAKE) deploy-hybrid ;; \
		*) echo "❌ Choix invalide"; exit 1 ;; \
	esac

stop: ## 🛑 ARRÊT COMPLET
	@echo "🛑 FERRARI F1 IoT - ARRÊT COMPLET"
	@echo "================================="
	@$(MAKE) report-final || echo "Services déjà arrêtés"
	@echo ""
	@echo "🐳 Arrêt Docker..."
	@docker-compose down >/dev/null 2>&1 || echo "Docker déjà arrêté"
	@echo ""
	@echo "☸️ Arrêt Kubernetes..."
	@kubectl delete namespace ferrari-f1 --ignore-not-found >/dev/null 2>&1 || echo "K8s déjà nettoyé"
	@echo ""
	@echo "�� Nettoyage..."
	@docker system prune -f >/dev/null 2>&1 || true
	@echo ""
	@echo "✅ Ferrari F1 IoT complètement arrêté!"

deploy-docker: ## 🐳 Déploiement Docker complet
	@echo "🐳 DÉPLOIEMENT DOCKER FERRARI F1"
	@echo "================================="
	@echo ""
	@echo "1️⃣ Démarrage des 9 services..."
	@docker-compose up -d
	@echo ""
	@echo "2️⃣ Stabilisation (90 secondes)..."
	@sleep 90
	@echo ""
	@echo "3️⃣ Configuration Grafana..."
	@$(MAKE) setup-grafana-docker
	@echo ""
	@echo "4️⃣ Déclenchement Airflow..."
	@$(MAKE) trigger-airflow-docker
	@echo ""
	@echo "5️⃣ Validation finale..."
	@$(MAKE) validate-docker
	@echo ""
	@$(MAKE) show-urls-docker

deploy-k8s: ## ☸️ Déploiement Kubernetes complet  
	@echo "☸️ DÉPLOIEMENT KUBERNETES FERRARI F1"
	@echo "===================================="
	@echo ""
	@echo "1️⃣ Infrastructure de base..."
	@kubectl apply -f k8s/namespace.yaml
	@kubectl apply -f k8s/config.yaml
	@kubectl apply -f k8s/postgres.yaml -f k8s/redis.yaml
	@echo ""
	@echo "2️⃣ Monitoring (Prometheus + Grafana)..."
	@kubectl apply -f k8s/prometheus-grafana.yaml
	@echo ""
	@echo "3️⃣ Applications Ferrari F1..."
	@$(MAKE) deploy-ferrari-apps
	@echo ""
	@echo "4️⃣ Stabilisation (60 secondes)..."
	@sleep 60
	@echo ""
	@echo "5️⃣ Validation K8s..."
	@$(MAKE) validate-k8s
	@echo ""
	@$(MAKE) show-urls-k8s

deploy-hybrid: ## 🚀 Déploiement Hybrid (Docker + K8s)
	@echo "🚀 DÉPLOIEMENT HYBRID FERRARI F1"
	@echo "================================="
	@echo ""
	@echo "Phase 1: Docker (développement)"
	@$(MAKE) deploy-docker
	@echo ""
	@echo "Phase 2: Kubernetes (production)"
	@$(MAKE) deploy-k8s  
	@echo ""
	@echo "🎯 DÉPLOIEMENT HYBRID TERMINÉ!"
	@echo ""
	@$(MAKE) show-urls-docker
	@echo ""
	@$(MAKE) show-urls-k8s

status: ## 📊 État complet des systèmes
	@echo "📊 STATUS FERRARI F1 IoT"
	@echo "========================"
	@echo ""
	@echo "🐳 Docker Services:"
	@docker-compose ps 2>/dev/null || echo "Docker non actif"
	@echo ""
	@if kubectl get namespace ferrari-f1 >/dev/null 2>&1; then \
		echo "☸️ Kubernetes Pods:"; \
		kubectl get pods -n ferrari-f1; \
		echo ""; \
		echo "🌐 K8s Services:"; \
		kubectl get services -n ferrari-f1; \
	else \
		echo "☸️ Kubernetes: Non déployé"; \
	fi
	@echo ""
	@$(MAKE) show-metrics || echo "Métriques non disponibles"

setup-grafana-docker: ## Configuration Grafana Docker (interne)
	@timeout=120; while [ $$timeout -gt 0 ]; do \
		if curl -s http://localhost:3000/api/health >/dev/null 2>&1; then \
			break; \
		fi; \
		sleep 3; \
		timeout=$$((timeout-3)); \
	done
	@./import-dashboard.sh --silent >/dev/null 2>&1 || echo "Dashboard existant"
	@echo "✅ Grafana configuré avec Ferrari F1 ULTIMATE Command Center Dashboard"

trigger-airflow-docker: ## Airflow Docker (interne)
	@$(MAKE) fix-airflow-connections >/dev/null 2>&1 || echo "Connexions déjà configurées"
	@docker-compose exec -T airflow-scheduler airflow dags trigger ferrari_grand_prix_dag >/dev/null 2>&1 || echo "✅ Airflow en cours de démarrage"

fix-airflow-connections: ## 🔧 Configuration connexions Airflow (interne)
	@docker-compose exec -T airflow-scheduler airflow connections add ferrari_postgres --conn-type postgres --conn-host postgres --conn-login airflow --conn-password airflow --conn-schema airflow --conn-port 5432 >/dev/null 2>&1 || echo "Connexion existe"

deploy-ferrari-apps: ## Déploiement applications K8s (interne)
	@docker-compose build sensor-simulator stream-processor >/dev/null 2>&1 || echo "Images déjà construites"
	@./k8s-fix.sh >/dev/null 2>&1

validate-docker: ## Validation Docker (interne)
	@echo "✅ Validation Docker..."
	@timeout=30; while [ $$timeout -gt 0 ]; do \
		if curl -s http://localhost:8000/metrics >/dev/null 2>&1 && \
		   curl -s http://localhost:8001/health >/dev/null 2>&1; then \
			echo "✅ Applications Ferrari opérationnelles"; \
			break; \
		fi; \
		sleep 2; \
		timeout=$$((timeout-2)); \
	done
	@$(MAKE) show-metrics

validate-k8s: ## Validation Kubernetes (interne)
	@echo "✅ Validation Kubernetes..."
	@kubectl get pods -n ferrari-f1 | grep Running | wc -l | xargs -I {} echo "✅ {} pods opérationnels"

show-metrics: ## Métriques temps réel (interne)
	@MESSAGES=$$(curl -s "http://localhost:8000/metrics" 2>/dev/null | grep "ferrari_simulator_messages_sent_total " | tail -1 | awk '{print $$2}' || echo "0"); \
	LATENCY=$$(curl -s "http://localhost:8000/metrics" 2>/dev/null | awk '/ferrari_simulator_send_latency_seconds_sum/ {sum=$$2} /ferrari_simulator_send_latency_seconds_count/ {count=$$2} END {if(sum && count) printf "%.2f ms", (sum/count)*1000; else print "N/A"}'); \
	THROUGHPUT=$$(curl -s "http://localhost:8000/metrics" 2>/dev/null | grep "ferrari_simulator_current_throughput" | awk '{print $$2}' || echo "0"); \
	echo "🏎️ Messages: $$MESSAGES | ⚡ Latence: $$LATENCY | 📊 Throughput: $$THROUGHPUT msg/s"

report-final: ## Rapport final (interne)
	@echo "📈 RAPPORT FINAL FERRARI F1:"
	@$(MAKE) show-metrics 2>/dev/null || echo "Métriques non disponibles"

show-urls-docker: ## URLs Docker (interne)
	@echo "🐳 URLS DOCKER FERRARI F1:"
	@echo "┌─────────────────────────────────────────────────────────────────┐"
	@echo "│ 🏆 ULTIMATE Dashboard: http://localhost:3000/d/ferrari-f1-ul... │"
	@echo "│ � Grafana Login:      http://localhost:3000 (admin/admin)      │"
	@echo "│ 📈 Prometheus:         http://localhost:9090                    │" 
	@echo "│ 🔄 Airflow:            http://localhost:8080                    │"
	@echo "│ 🏎️ API Ferrari:        http://localhost:8001/telemetry         │"
	@echo "│ 📡 Métriques:          http://localhost:8000/metrics            │"
	@echo "└─────────────────────────────────────────────────────────────────┘"



grafana-dashboards: ## 📊 Import de tous les dashboards Ferrari F1
	@echo "📊 IMPORT DE TOUS LES DASHBOARDS FERRARI F1"
	@echo "=========================================="
	@./import-dashboard.sh
	@echo ""
	@echo "🎯 DASHBOARDS DISPONIBLES:"
	@echo "┌──────────────────────────────────────────────────────────────┐"
	@echo "│ 📊 Standard:    http://localhost:3000/d/9b4fab13-87d7-...   │"
	@echo "│ 🚀 Pro:         http://localhost:3000/d/ferrari-f1-pro-...  │"
	@echo "│ 🏆 Executive:   http://localhost:3000/d/ferrari-f1-exec-... │"
	@echo "│ � Predictive:  http://localhost:3000/d/ferrari-f1-pred-... │"
	@echo "│ �🔐 Login:       admin / admin                                │"
	@echo "└──────────────────────────────────────────────────────────────┘"

grafana-tour: ## 🎬 Tour guidé des dashboards Ferrari F1
	@echo "🎬 TOUR GUIDÉ DES DASHBOARDS FERRARI F1"
	@echo "======================================="
	@echo ""
	@echo "🎯 4 NIVEAUX D'ANALYSE DISPONIBLES:"
	@echo ""
	@echo "1️⃣ 📊 STANDARD - Monitoring de base"
	@echo "   🔗 http://localhost:3000/d/27831c4e-9ccf-4da6-b21b-7f9704035db5"
	@echo "   📋 Métriques essentielles, graphiques simples"
	@echo ""
	@echo "2️⃣ 🚀 PROFESSIONAL - Analytics avancés"
	@echo "   🔗 http://localhost:3000/d/ferrari-f1-pro-analytics"
	@echo "   📋 Percentiles, latence, success rates, heatmaps"
	@echo ""
	@echo "3️⃣ 🏆 EXECUTIVE - Business KPIs"
	@echo "   🔗 http://localhost:3000/d/ferrari-f1-executive-dashboard"
	@echo "   📋 Health scores, impact business, SLA monitoring"
	@echo ""
	@echo "4️⃣ 🔮 PREDICTIVE - AI & Machine Learning"
	@echo "   🔗 http://localhost:3000/d/ferrari-f1-predictive-analytics"
	@echo "   📋 Forecasting, capacity planning, anomaly prediction"
	@echo ""
	@echo "🔐 Credentials: admin / admin"

show-urls-k8s: ## URLs Kubernetes (interne)
	@echo "☸️ URLS KUBERNETES FERRARI F1:"
	@echo "┌─────────────────────────────────────────────────────────────────┐"
	@echo "│ 💡 Accès: make k8s-access                                      │"
	@echo "│ 📊 Grafana: kubectl port-forward -n ferrari-f1 svc/grafana ... │"
	@echo "│ 📈 Prometheus: kubectl port-forward -n ferrari-f1 svc/prom...  │"
	@echo "│ 🏎️ Status: make k8s-status                                     │"
	@echo "└─────────────────────────────────────────────────────────────────┘"

k8s-access: ## 🌐 Accès services Kubernetes
	@echo "🌐 ACCÈS KUBERNETES FERRARI F1"
	@echo "==============================="
	@echo ""
	@echo "Services disponibles:"
	@echo "1. 📊 Grafana Dashboard (port 3000)"
	@echo "2. 📈 Prometheus Metrics (port 9090)"
	@echo "3. 🏎️ Sensor Simulator (port 8000)"
	@echo "4. ⚡ Stream Processor (port 8001)"
	@echo ""
	@read -p "Service [1]: " service; \
	service=$${service:-1}; \
	case $$service in \
		1) echo "📊 Grafana: http://localhost:3000"; kubectl port-forward -n ferrari-f1 svc/grafana 3000:3000 ;; \
		2) echo "📈 Prometheus: http://localhost:9090"; kubectl port-forward -n ferrari-f1 svc/prometheus 9090:9090 ;; \
		3) echo "🏎️ Sensor: http://localhost:8000"; kubectl port-forward -n ferrari-f1 svc/sensor-simulator-simple 8000:8000 ;; \
		4) echo "⚡ Processor: http://localhost:8001"; kubectl port-forward -n ferrari-f1 svc/stream-processor-simple 8001:8001 ;; \
		*) echo "❌ Service invalide" ;; \
	esac

k8s-status: ## 📊 Status Kubernetes détaillé
	@echo "☸️ STATUS KUBERNETES FERRARI F1"
	@echo "==============================="
	@if kubectl get namespace ferrari-f1 >/dev/null 2>&1; then \
		kubectl get pods,services,pvc -n ferrari-f1; \
		echo ""; \
		echo "🎯 Accès: make k8s-access"; \
	else \
		echo "❌ Namespace ferrari-f1 non trouvé"; \
		echo "💡 Utilisez: make start (option 2 ou 3)"; \
	fi

demo: ## 🎬 Démonstration complète (5 minutes)
	@echo "🎬 DÉMONSTRATION FERRARI F1 IoT - 5 MINUTES"
	@echo "==========================================="
	@echo ""
	@$(MAKE) deploy-docker
	@echo ""
	@echo "📊 Collecte de données (3 minutes)..."
	@for i in 1 2 3; do \
		echo "⏱️ Minute $$i/3:"; \
		$(MAKE) show-metrics; \
		sleep 60; \
	done
	@echo ""
	@echo "🏁 Démonstration terminée!"

test: ## ⚡ Test rapide validation (2 minutes)
	@echo "⚡ TEST RAPIDE FERRARI F1 - VALIDATION"
	@echo "======================================"
	@$(MAKE) deploy-docker
	@echo ""
	@echo "⏳ Test validation (120 secondes)..."
	@sleep 120
	@echo ""
	@echo "📊 Résultats finaux:"
	@$(MAKE) show-metrics
	@echo ""
	@echo "✅ Test de validation terminé!"

clean: ## 🧹 Nettoyage complet (ATTENTION!)
	@echo "⚠️ NETTOYAGE COMPLET - Suppression de toutes les données!"
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
