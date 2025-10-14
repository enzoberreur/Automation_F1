# Ferrari F1 Stream Processor

Service de traitement en temps réel des données télémétrie avec détection d'anomalies et calcul de stratégie pit-stop.

## Caractéristiques

- 🔍 **Détection d'anomalies**: Surchauffe freins (>950°C) et pneus (>130°C) pendant 2s
- 🏁 **Stratégie pit-stop**: Score pondéré basé sur usure, performance et anomalies
- 📊 **Métriques Prometheus**: Latence, throughput, anomalies détectées
- 📡 **Multi-mode**: Support Kafka et REST
- ⚡ **Haute performance**: Traitement asynchrone optimisé

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Variables d'environnement :

```bash
# Mode de fonctionnement
PROCESSOR_MODE=rest  # rest ou kafka

# Port d'écoute
PORT=8001

# Kafka (si mode kafka)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=ferrari-telemetry

# Logging
LOG_LEVEL=INFO
```

## Utilisation

### Mode REST

```bash
# Démarrer le service
export PROCESSOR_MODE=rest
export PORT=8001
python main.py

# Le service écoute sur http://localhost:8001
```

### Mode Kafka

```bash
# Démarrer Kafka
docker run -d --name kafka -p 9092:9092 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  confluentinc/cp-kafka:latest

# Démarrer le processeur
export PROCESSOR_MODE=kafka
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
export KAFKA_TOPIC=ferrari-telemetry
python main.py
```

## Endpoints API

### `GET /`
Page d'accueil avec statistiques

```bash
curl http://localhost:8001/
```

### `POST /telemetry`
Reçoit et traite un message de télémétrie

```bash
curl -X POST http://localhost:8001/telemetry \
  -H "Content-Type: application/json" \
  -d @telemetry.json
```

### `GET /metrics`
Métriques Prometheus

```bash
curl http://localhost:8001/metrics
```

### `GET /stats`
Statistiques détaillées

```bash
curl http://localhost:8001/stats
```

### `GET /health`
Health check

```bash
curl http://localhost:8001/health
```

## Détection d'anomalies

### Seuils

- **Freins critiques**: > 950°C pendant 2 secondes
- **Pneus critiques**: > 130°C pendant 2 secondes

### Fenêtre temporelle

Le système utilise des fenêtres glissantes de 2 secondes pour détecter les anomalies persistantes.

### Types d'anomalies détectées

- `brake_overheat_fl/fr/rl/rr`: Surchauffe frein avant-gauche/droit ou arrière-gauche/droit
- `tire_overheat_fl/fr/rl/rr`: Surchauffe pneu avant-gauche/droit ou arrière-gauche/droit

## Calcul du score pit-stop

Score pondéré (0-100) basé sur :

1. **Usure des pneus** (40%): tire_wear_percent
2. **Perte de vitesse** (30%): Comparaison vitesse début vs fin
3. **Dégradation freins** (20%): Basé sur température moyenne
4. **Anomalies actives** (10%): 25 points par anomalie

### Niveaux d'urgence

- **Critical** (≥90): PIT-STOP IMMÉDIAT
- **High** (≥75): Pit-stop fortement recommandé
- **Medium** (≥50): Pit-stop dans 3-5 tours
- **Low** (<50): Surveillance normale

## Métriques Prometheus

### Compteurs

- `ferrari_messages_received_total`: Total de messages reçus
- `ferrari_anomalies_detected_total`: Anomalies détectées (par type et sévérité)
- `ferrari_pitstop_recommendations_total`: Recommandations de pit-stop

### Histogrammes

- `ferrari_processing_latency_seconds`: Latence de traitement
- `ferrari_message_size_bytes`: Taille des messages

### Jauges

- `ferrari_current_throughput_msg_per_sec`: Débit actuel
- `ferrari_avg_processing_latency_ms`: Latence moyenne
- `ferrari_active_anomalies`: Anomalies actives
- `ferrari_pitstop_score`: Score pit-stop par voiture

## Exemple de réponse

```json
{
  "status": "processed",
  "car_id": "Ferrari-F1-75",
  "lap": 15,
  "anomalies": [
    {
      "type": "brake_overheat_fl",
      "severity": "critical",
      "value": 965.3,
      "threshold": 950.0,
      "duration": 2.1,
      "message": "🔥 CRITIQUE: Frein FL en surchauffe (965.3°C > 950.0°C) pendant 2.1s"
    }
  ],
  "pitstop": {
    "score": 78.5,
    "urgency": "high",
    "recommendation": "Pit-stop fortement recommandé au prochain tour",
    "details": {
      "tire_wear": 65.2,
      "speed_loss": 15.3,
      "brake_degradation": 72.8
    }
  },
  "processing_time_ms": 2.35
}
```

## Performance

- **Latence**: <5ms en moyenne
- **Throughput**: >2000 messages/s par instance
- **Scalabilité**: Auto-scaling Kubernetes

## Docker

### Build

```bash
docker build -t ferrari-stream-processor:latest .
```

### Run

```bash
# Mode REST
docker run -p 8001:8001 \
  -e PROCESSOR_MODE=rest \
  ferrari-stream-processor:latest

# Mode Kafka
docker run -p 8001:8001 \
  -e PROCESSOR_MODE=kafka \
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
  ferrari-stream-processor:latest
```

## Kubernetes

Voir `stream-processor-deployment.yaml` pour le déploiement complet.

```bash
kubectl apply -f stream-processor-deployment.yaml
```

## Monitoring avec Prometheus

Le service expose automatiquement les métriques sur `/metrics`.

Configuration Prometheus :

```yaml
scrape_configs:
  - job_name: 'ferrari-stream-processor'
    static_configs:
      - targets: ['stream-processor:8001']
```

## Tests

### Test local

```bash
# Démarrer le service
python main.py &

# Envoyer un message de test
curl -X POST http://localhost:8001/telemetry \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2025-10-14T10:30:00.000000Z",
    "car_id": "Ferrari-F1-75",
    "driver": "Charles Leclerc",
    "lap": 10,
    "speed_kmh": 300,
    "rpm": 17000,
    "brake_temp_fl_celsius": 980,
    "brake_temp_fr_celsius": 975,
    "brake_temp_rl_celsius": 960,
    "brake_temp_rr_celsius": 970,
    "tire_temp_fl_celsius": 105,
    "tire_temp_fr_celsius": 103,
    "tire_temp_rl_celsius": 108,
    "tire_temp_rr_celsius": 106,
    "tire_wear_percent": 45,
    "has_anomaly": false
  }'

# Vérifier les métriques
curl http://localhost:8001/metrics | grep ferrari
```

### Test de charge

```bash
# Installer Apache Bench
brew install httpd

# Test de charge
ab -n 10000 -c 100 -p telemetry.json -T application/json \
  http://localhost:8001/telemetry
```

## Architecture

```
┌─────────────────┐
│  Sensor         │
│  Simulator      │
└────────┬────────┘
         │ (Kafka/HTTP)
         ▼
┌─────────────────┐
│  Stream         │
│  Processor      │
│  • Anomalies    │
│  • Pit-stop     │
│  • Metrics      │
└────────┬────────┘
         │
         ├─► Prometheus (métriques)
         ├─► Grafana (visualisation)
         └─► Alerting (notifications)
```

## Logs

Le service génère des logs structurés :

```
2025-10-14 10:30:45 - INFO - Message processed: Ferrari-F1-75 lap 15
2025-10-14 10:30:46 - WARNING - ⚠️  🔥 CRITIQUE: Frein FL en surchauffe...
2025-10-14 10:30:47 - INFO - 🏁 Pit-stop fortement recommandé (Score: 78.5)
```

## Troubleshooting

### Service ne démarre pas

```bash
# Vérifier les dépendances
pip list | grep -E 'fastapi|kafka|prometheus'

# Vérifier les logs
python main.py
```

### Kafka non accessible

```bash
# Vérifier la connectivité
telnet localhost 9092

# Passer en mode REST
export PROCESSOR_MODE=rest
```

### Performance insuffisante

```bash
# Augmenter les ressources
export UVICORN_WORKERS=4

# Vérifier les métriques
curl http://localhost:8001/stats
```

## Développement

### Structure du code

```python
# Classes principales
- AnomalyDetector: Détection d'anomalies
- TimeWindow: Fenêtres temporelles
- PitStopStrategyCalculator: Calcul du score
- StreamProcessor: Processeur principal
```

### Tests unitaires

```bash
pytest tests/
```

## Production Checklist

- [ ] Variables d'environnement configurées
- [ ] Prometheus configuré pour scraping
- [ ] Alertes configurées (anomalies critiques)
- [ ] Auto-scaling testé
- [ ] Logs centralisés
- [ ] Backup et recovery
- [ ] Monitoring dashboards Grafana
- [ ] Documentation à jour

## License

MIT License - Ferrari F1 Stream Processor
