# Simplified automation entry points

COMPOSE ?= docker compose

.PHONY: help start stop clean import-dashboards

help: ## Show available commands
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sed 's/:.*##/: /'

start: ## Rebuild and start the full stack
	$(COMPOSE) down --remove-orphans
	$(COMPOSE) up --build -d
	./import-dashboard.sh --silent

stop: ## Stop all services
	$(COMPOSE) down --remove-orphans

clean: ## Remove containers, volumes and Python caches
	$(COMPOSE) down --volumes --remove-orphans
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +

import-dashboards: ## Reload Grafana dashboards
	./import-dashboard.sh

.DEFAULT_GOAL := help
