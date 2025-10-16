# Ferrari F1 Sensor Simulator

Simulateur haute performance de capteurs IoT pour Ferrari F1.

## Caractéristiques

- 🚀 **Haute performance**: 1000-2000 messages/seconde
- 📡 **Multi-transport**: Support Kafka et HTTP
- 🔥 **Simulation d'anomalies**: Surchauffe freins, pneus, moteur
- 📊 **Métriques en temps réel**: Latence, throughput, taux d'erreur
- 🏎️ **Données réalistes**: Modèle multi-segments corrélant vitesse, freinage, pneus et météo
- 🧠 **Insights stratégie**: Calcul du temps au tour, de la santé de relais et de la fenêtre de pit-stop

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Copiez `.env.example` vers `.env` et ajustez les paramètres :

```bash
cp .env.example .env
```

Variables disponibles :
- `TELEMETRY_MODE`: Mode de transport (kafka/http)
- `TARGET_THROUGHPUT`: Messages par seconde (1000-2000)
- `CAR_ID`: Identifiant de la voiture
- `DRIVER`: Nom du pilote
- `KAFKA_BOOTSTRAP_SERVERS`: Serveurs Kafka
- `KAFKA_TOPIC`: Topic Kafka
- `HTTP_ENDPOINT`: Endpoint HTTP

## Utilisation

### Mode Kafka

```bash
# Démarrer Kafka localement (avec Docker)
docker run -d --name kafka -p 9092:9092 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  confluentinc/cp-kafka:latest

# Lancer le simulateur
export TELEMETRY_MODE=kafka
python main.py
```

### Mode HTTP

```bash
# Lancer le simulateur
export TELEMETRY_MODE=http
export HTTP_ENDPOINT=http://localhost:8001/telemetry
python main.py
```

## Format des données

Chaque message contient :

```json
{
  "timestamp": "2025-10-14T10:30:45.123456Z",
  "car_id": "Ferrari-F1-75",
  "driver": "Charles Leclerc",
  "lap": 12,
  "speed_kmh": 312.45,
  "rpm": 17500,
  "gear": 7,
  "throttle_percent": 98.5,
  "engine_temp_celsius": 115.2,
  "brake_pressure_bar": 145.0,
  "brake_temp_fl_celsius": 320.5,
  "brake_temp_fr_celsius": 315.8,
  "brake_temp_rl_celsius": 310.2,
  "brake_temp_rr_celsius": 312.1,
  "tire_compound": "soft",
  "tire_temp_fl_celsius": 102.3,
  "tire_temp_fr_celsius": 101.8,
  "tire_temp_rl_celsius": 103.5,
  "tire_temp_rr_celsius": 102.9,
  "tire_pressure_fl_psi": 21.2,
  "tire_pressure_fr_psi": 21.1,
  "tire_pressure_rl_psi": 21.3,
  "tire_pressure_rr_psi": 21.2,
  "tire_wear_percent": 35.2,
  "drs_status": "open",
  "ers_power_kw": 98.5,
  "fuel_remaining_kg": 55.3,
  "track_temp_celsius": 42.5,
  "air_temp_celsius": 29.8,
  "humidity_percent": 58.2,
  "has_anomaly": false,
  "anomaly_type": null,
  "anomaly_severity": null,
  "lap_time_seconds": 89.42,
  "stint_health_score": 78.4,
  "pit_window_probability": 0.28,
  "surface_condition": "optimal",
  "strategy_recommendation": "extend"
}
```

### Insights stratégie

Les nouveaux champs `lap_time_seconds`, `stint_health_score` et `pit_window_probability` synthétisent l'état du relais en croisant l'usure, les températures, l'humidité et le carburant. `surface_condition` indique le comportement de la piste (cool, optimal, hot, damp) tandis que `strategy_recommendation` propose une action (`extend`, `evaluate`, `pit_soon`).

Les métriques Prometheus correspondantes alimentent les dashboards Grafana améliorés :

- `ferrari_simulator_lap_time_seconds` et `ferrari_simulator_stint_health_score` pour suivre les temps au tour et la santé du relais.
- `ferrari_simulator_pit_window_probability` pour monitorer l'ouverture de la fenêtre de pit-stop (0-1).
- `ferrari_simulator_surface_condition_info{condition="…"}` expose un état binaire par condition de piste.
- `ferrari_simulator_surface_condition_state` encode la condition de piste actuelle (0 optimal → 3 humide) pour les timelines.
- `ferrari_simulator_strategy_recommendation_info{recommendation="…"}` active la recommandation courante.
- `ferrari_simulator_strategy_recommendation_state` encode la recommandation (`extend`, `evaluate`, `pit_soon`).

## Anomalies simulées

Types d'anomalies :
- `brake_overheat`: Surchauffe des freins
- `tire_overheat`: Surchauffe des pneus
- `tire_pressure_loss`: Perte de pression pneu
- `engine_overheat`: Surchauffe moteur
- `brake_fade`: Perte d'efficacité freinage

Sévérités :
- `warning`: Attention requise
- `critical`: Intervention urgente

## Performance

Le simulateur affiche des rapports toutes les 5 secondes :

```
╔══════════════════════════════════════════════════════════════╗
║ 🏎️  Ferrari F1 Telemetry Simulator - Performance Report     ║
╠══════════════════════════════════════════════════════════════╣
║ Messages envoyés:          7500 msg                          ║
║ Messages échoués:             5 msg                          ║
║ Débit (throughput):     1498.50 msg/s                        ║
║ Latence moyenne:           0.85 ms                           ║
║ Uptime:                    5.00 s                            ║
╚══════════════════════════════════════════════════════════════╝
```

## Docker

### Build

```bash
docker build -t ferrari-sensor-simulator:latest .
```

### Run

```bash
# Mode Kafka
docker run -e TELEMETRY_MODE=kafka \
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
  -e TARGET_THROUGHPUT=1500 \
  ferrari-sensor-simulator:latest

# Mode HTTP
docker run -e TELEMETRY_MODE=http \
  -e HTTP_ENDPOINT=http://stream-processor:8001/telemetry \
  ferrari-sensor-simulator:latest
```

## Kubernetes

Voir `sensor-simulator-deployment.yaml` pour le déploiement Kubernetes.

```bash
kubectl apply -f sensor-simulator-deployment.yaml
```
