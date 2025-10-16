# Ferrari F1 Sensor Simulator

Le simulateur reproduit un flux de télémétrie haute fréquence pour une monoplace de Formule&nbsp;1. Il alimente le `stream-processor` via HTTP et expose toutes les métriques requises par Prometheus/Grafana pour les dashboards fournis dans ce dépôt.

---

## 🚦 Pour débuter en 2 minutes

1. **Installer les dépendances** (Python 3.10+ recommandé) :
   ```bash
   pip install -r requirements.txt
   ```
2. **Lancer le simulateur** en mode HTTP :
   ```bash
   python main.py
   ```
3. **Consulter les métriques Prometheus** sur <http://localhost:8000/metrics> et vérifier que le `stream-processor` reçoit bien les échantillons sur <http://localhost:8001/health>.

Le simulateur affiche toutes les 5 secondes un rapport de performance (messages envoyés, throughput, latence moyenne). Arrêtez-le proprement avec `Ctrl+C`.

---

## 🧑‍💻 Pour les intégrateurs et ingénieurs data

- **Stack complète** : exécuter `make start` à la racine du dépôt pour démarrer les services Docker (Prometheus, Grafana, stream-processor, etc.).
- **Dashboards Grafana** : importer les JSON du dossier `monitoring/` ou lancer `./import-dashboard.sh` (les dashboards sont automatiquement importés par `make start`).
- **Observabilité** : le simulateur démarre un endpoint Prometheus (`:8000/metrics`) et pousse la télémétrie vers le `stream-processor` (`:8001/telemetry`). Les panneaux Grafana utilisent directement ces métriques.

---

## ⚙️ Configuration

Les variables d'environnement suivantes permettent d'ajuster le comportement du simulateur :

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| `CAR_ID` | Identifiant voiture | `Ferrari-F1-75` |
| `DRIVER` | Pilote associé | `Charles Leclerc` |
| `TARGET_THROUGHPUT` | Messages envoyés par seconde (doit être > 0) | `1500` |
| `HTTP_ENDPOINT` | Endpoint HTTP du `stream-processor` | `http://stream-processor:8001/telemetry` |

Le simulateur valide automatiquement `TARGET_THROUGHPUT` : une valeur invalide ou négative est ignorée et un avertissement est loggé.

---

## 🛰️ Modèle de données produit

Chaque message suit la structure suivante :

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

### Insights de stratégie

Les champs `lap_time_seconds`, `stint_health_score` et `pit_window_probability` synthétisent l'état du relais en combinant l'usure, les températures, l'humidité et le carburant. `surface_condition` décrit le grip actuel de la piste (`cool`, `optimal`, `hot`, `damp`) et `strategy_recommendation` suggère l'action à mener (`extend`, `evaluate`, `pit_soon`).

---

## 📈 Métriques Prometheus exposées

| Nom | Description |
|-----|-------------|
| `ferrari_simulator_messages_generated_total` | Messages générés par le simulateur |
| `ferrari_simulator_messages_sent_total` | Messages acceptés par le stream-processor |
| `ferrari_simulator_send_errors_total` | Erreurs de transmission HTTP |
| `ferrari_simulator_send_latency_seconds` | Histogramme de latence d'envoi |
| `ferrari_simulator_current_throughput_msg_per_sec` | Débit instantané |
| `ferrari_simulator_*` | Toutes les jauges de télémétrie (freins, pneus, moteur, carburant, stratégie) |
| `ferrari_simulator_surface_condition_state` | Condition de piste (0 = optimal … 3 = damp) |
| `ferrari_simulator_strategy_recommendation_state` | Recommandation courante (0 = extend … 2 = pit_soon) |

Ces métriques alimentent directement les dashboards `monitoring/grafana_dashboard_main.json` et `monitoring/grafana_dashboard_strategy.json`.

---

## ⚠️ Anomalies simulées

| Type | Effet |
|------|-------|
| `brake_overheat` | Augmentation température freins sur les 4 roues |
| `tire_overheat` | Augmentation température pneus sur les 4 roues |
| `tire_pressure_loss` | Perte de pression sur les 4 pneus |
| `engine_overheat` | Surchauffe moteur |
| `brake_fade` | Réduction de la pression de freinage |

Chaque anomalie est générée avec une probabilité configurable dans le code (`AnomalySimulator`) et peut être de sévérité `warning` ou `critical`.

---

## 🛠️ Dépannage

- **`ModuleNotFoundError: aiohttp`** → installer la dépendance (`pip install aiohttp`).
- **Aucun point `/metrics`** → vérifier que `prometheus_client` est installé. Sans cette librairie, l'application continue de tourner mais les métriques sont désactivées.
- **Erreurs HTTP fréquentes** → vérifier que le `stream-processor` écoute bien sur `HTTP_ENDPOINT`. Les erreurs sont comptabilisées dans `ferrari_simulator_send_errors_total`.

Pour une compréhension approfondie de l'architecture globale (Airflow, stream-processor, dashboards), consultez le README à la racine du dépôt ainsi que `ARCHITECTURE.md`.
