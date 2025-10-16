# F1 Multi-Team Sensor Simulator

Le simulateur génère en temps réel la télémétrie de **20 monoplaces (2 par écurie officielle de Formule&nbsp;1)**. Chaque voiture publie ses mesures via HTTP vers le `stream-processor` et expose toutes les métriques nécessaires pour les dashboards Prometheus/Grafana fournis dans ce dépôt. Un mode « single car » reste disponible pour des tests ciblés.

---

## 🚦 Pour débuter en 2 minutes

1. **Installer les dépendances** (Python 3.10+ recommandé) :
   ```bash
   pip install -r requirements.txt
   ```
2. **Lancer le simulateur** en mode championnat (multi-écuries) :
   ```bash
   python main.py  # SIMULATION_MODE=championship par défaut
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

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| `SIMULATION_MODE` | `championship` pour lancer les 10 équipes (20 voitures), `single` pour une voiture personnalisée | `championship` |
| `HTTP_ENDPOINT` | Endpoint HTTP du `stream-processor` | `http://stream-processor:8001/telemetry` |
| `STREAM_PROCESSOR_API_KEY` | Clé API transmise dans les requêtes HTTP | `changeme` |
| `STREAM_PROCESSOR_API_KEY_HEADER` | Nom de l'en-tête HTTP contenant la clé | `X-Api-Key` |
| `TARGET_THROUGHPUT_PER_CAR` | Messages envoyés par seconde et par voiture en mode `championship` | `250` |
| `TARGET_THROUGHPUT` | Messages envoyés par seconde en mode `single` | `1500` |
| `TEAM_NAME` | Nom de l'écurie (mode `single`) | `Scuderia Ferrari HP` |
| `CAR_MODEL` | Châssis (mode `single`) | `SF-24` |
| `CAR_NUMBER` | Numéro de course (mode `single`) | `16` |
| `CAR_ID` | Identifiant unique de la voiture (mode `single`) | `SF-24-16` |
| `DRIVER` | Pilote (mode `single`) | `Charles Leclerc` |

Les paramètres numériques (`TARGET_THROUGHPUT*`, `CAR_NUMBER`) sont validés automatiquement : en cas de valeur invalide, la valeur par défaut est réappliquée et un avertissement est loggé.

### Mode championnat (par défaut)

Le simulateur instancie automatiquement les 10 équipes officielles de la saison actuelle, avec 2 voitures par écurie. Chaque voiture dispose d'un `car_id` unique combinant le châssis et le numéro de course. Le tableau ci-dessous résume la grille générée :

| Équipe | Châssis | Pilotes | Identifiants |
|--------|---------|---------|--------------|
| Oracle Red Bull Racing | RB20 | Max Verstappen (#1), Sergio Pérez (#11) | `RB20-1`, `RB20-11` |
| Mercedes-AMG Petronas F1 | W15 | Lewis Hamilton (#44), George Russell (#63) | `W15-44`, `W15-63` |
| Scuderia Ferrari HP | SF-24 | Charles Leclerc (#16), Carlos Sainz (#55) | `SF24-16`, `SF24-55` |
| McLaren F1 Team | MCL38 | Lando Norris (#4), Oscar Piastri (#81) | `MCL38-4`, `MCL38-81` |
| Aston Martin Aramco F1 Team | AMR24 | Fernando Alonso (#14), Lance Stroll (#18) | `AMR24-14`, `AMR24-18` |
| BWT Alpine F1 Team | A524 | Esteban Ocon (#31), Pierre Gasly (#10) | `A524-31`, `A524-10` |
| Williams Racing | FW46 | Alexander Albon (#23), Logan Sargeant (#2) | `FW46-23`, `FW46-2` |
| Visa Cash App RB F1 Team | VCARB 01 | Yuki Tsunoda (#22), Daniel Ricciardo (#3) | `VCARB01-22`, `VCARB01-3` |
| Stake F1 Team Kick Sauber | C44 | Valtteri Bottas (#77), Zhou Guanyu (#24) | `C44-77`, `C44-24` |
| MoneyGram Haas F1 Team | VF-24 | Kevin Magnussen (#20), Nico Hülkenberg (#27) | `VF24-20`, `VF24-27` |

### Mode single car

Pour n'exécuter qu'une seule voiture, positionner `SIMULATION_MODE=single` et ajuster les variables `TEAM_NAME`, `CAR_MODEL`, `CAR_NUMBER`, `CAR_ID`, `DRIVER` ainsi que `TARGET_THROUGHPUT`. Exemple :

```bash
SIMULATION_MODE=single \
TEAM_NAME="McLaren F1 Team" \
CAR_MODEL=MCL38 \
CAR_NUMBER=4 \
DRIVER="Lando Norris" \
TARGET_THROUGHPUT=2000 \
python main.py
```

---

## 🛰️ Modèle de données produit

Chaque message suit la structure suivante :

```json
{
  "timestamp": "2025-10-14T10:30:45.123456Z",
  "car_id": "RB20-1",
  "team": "Oracle Red Bull Racing",
  "driver": "Max Verstappen",
  "car_number": 1,
  "car_model": "RB20",
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

Toutes les métriques sont taguées avec les labels `car_id`, `team`, `driver`, ce qui permet de comparer facilement les voitures et les écuries dans Grafana. Elles alimentent directement les dashboards `monitoring/grafana_dashboard_main.json` et `monitoring/grafana_dashboard_strategy.json`.

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
