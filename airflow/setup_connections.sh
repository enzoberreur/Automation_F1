#!/bin/bash
"""
Configuration automatique des connexions Airflow pour Ferrari F1
================================================================

Ce script configure les connexions nécessaires pour le DAG Ferrari Grand Prix :
- Connexion PostgreSQL (ferrari_postgres)
- Variables d'environnement Airflow
- Initialisation base de données

Usage:
  docker-compose exec airflow-scheduler bash /opt/airflow/setup_connections.sh
"""

echo "🔄 Configuration des connexions Airflow Ferrari F1..."
echo "======================================================"

# Attendre que Airflow soit prêt
echo "⏱️  Attente initialisation Airflow..."
sleep 5

# Créer la connexion PostgreSQL Ferrari
echo "📊 Configuration connexion PostgreSQL Ferrari..."
airflow connections add 'ferrari_postgres' \
    --conn-type 'postgres' \
    --conn-host 'postgres' \
    --conn-login 'airflow' \
    --conn-password 'airflow' \
    --conn-schema 'airflow' \
    --conn-port 5432

# Créer variables Airflow Ferrari F1
echo "⚙️  Configuration variables Ferrari F1..."
airflow variables set FERRARI_POSTGRES_HOST postgres
airflow variables set FERRARI_POSTGRES_PORT 5432
airflow variables set FERRARI_POSTGRES_USER airflow
airflow variables set FERRARI_POSTGRES_PASSWORD airflow
airflow variables set FERRARI_POSTGRES_DB airflow

# Variables URLs services
airflow variables set SENSOR_SIMULATOR_URL http://sensor-simulator:8000
airflow variables set STREAM_PROCESSOR_URL http://stream-processor:8001
airflow variables set PROMETHEUS_URL http://prometheus:9090
airflow variables set GRAFANA_URL http://grafana:3000

# Configuration télémétrie Ferrari
airflow variables set FERRARI_TEAM_ID SCU
airflow variables set FERRARI_DRIVER_1 Charles_Leclerc
airflow variables set FERRARI_DRIVER_2 Carlos_Sainz
airflow variables set FERRARI_CAR_ID_1 16
airflow variables set FERRARI_CAR_ID_2 55

echo "✅ Configuration terminée!"
echo ""
echo "🔍 Vérification des connexions créées:"
airflow connections get ferrari_postgres
echo ""
echo "🎯 Variables configurées:"
airflow variables list | grep -E "(FERRARI|SENSOR|STREAM|PROMETHEUS|GRAFANA)"
echo ""
echo "🏎️  Configuration Ferrari F1 prête! Forza Ferrari!"