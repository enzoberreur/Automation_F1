# 🏎️ Ferrari F1 IoT Smart Pit-Stop

Plateforme de télémétrie et de monitoring inspirée d'un mur des stands de Formule 1. Le dépôt rassemble :

- un simulateur de capteurs haute fréquence (HTTP + métriques Prometheus) ;
- un service de traitement (`stream-processor`) ;
- une stack d'observabilité (Prometheus + Grafana) ;
- des orchestrations Airflow pour la donnée batch.

L'objectif : fournir un environnement réaliste pour expérimenter des pipelines IoT/streaming et des tableaux de bord stratégiques.

---

## 🚦 Démarrage rapide (tout en Docker)

Pré-requis : Docker, Docker Compose et `make`.

```bash
git clone https://github.com/enzoberreur/Automation_F1.git
cd Automation_F1
make start
```

Cette commande :
1. arrête toute exécution précédente (`docker compose down --remove-orphans`) ;
2. reconstruit et démarre les conteneurs nécessaires ;
3. importe automatiquement les dashboards Grafana.

> ℹ️ Les identifiants par défaut sont `admin / admin` pour Grafana et Airflow.

Une fois le stack prêt, accédez au poste de commande principal : <http://localhost:3000/d/ferrari-f1-dashboard>.

Pour arrêter et nettoyer :

```bash
make stop
```

Pour repartir de zéro (conteneurs arrêtés + volumes supprimés) :

```bash
make clean
```

La commande supprime également les dossiers `__pycache__` générés par Python.

----

## 🧪 Démarrage léger (simulateur seul)

Pour tester uniquement le flux de télémétrie :

```bash
cd sensor-simulator
pip install -r requirements.txt
python main.py
```

Le simulateur publie :
- la télémétrie sur `http://localhost:8001/telemetry` (attendez-vous à un message d'erreur si le `stream-processor` n'est pas démarré) ;
- les métriques Prometheus sur `http://localhost:8000/metrics`.

Consultez `sensor-simulator/README.md` pour un guide détaillé (configuration, métriques, anomalies simulées).

---

## 🔌 Services & ports

| Service | Rôle | Port local |
|---------|------|------------|
| sensor-simulator | Génère la télémétrie F1 et les métriques Prometheus | `8000` (metrics) |
| stream-processor | Reçoit la télémétrie, calcule des KPIs et expose des API | `8001` |
| prometheus | Collecte toutes les métriques | `9090` |
| grafana | Tableaux de bord temps réel | `3000` |
| airflow | Orchestration batch & maintenance de données | `8080` |
| cadvisor | Observabilité des conteneurs | `8082` |

La configuration Docker Compose se trouve dans `docker-compose.yml`. Les manifestes Kubernetes sont disponibles dans `k8s/` si vous souhaitez déployer sur un cluster.

---

## 📊 Dashboards Grafana

Les définitions JSON des dashboards résident dans `monitoring/` :

- `grafana_dashboard_main.json` — vue opérations & thermique : vitesse, freins/pneus, anomalies, stratégie.
- `grafana_dashboard_strategy.json` — suivi détaillé des recommandations pit-stop (probabilité de fenêtre, état de la piste, timeline stratégie).
- `grafana_dashboard_data.json`, `grafana_dashboard_data_quality.json` — analyses complémentaires (débit, fraîcheur, qualité de données).

Importer manuellement :

```bash
./import-dashboard.sh
```

ou passer par l’UI Grafana (`Dashboards → Import`) en collant le contenu JSON.

---

## 📈 Métriques clés

Les dashboards s'appuient principalement sur :

- **Flux** : `ferrari_simulator_messages_generated_total`, `ferrari_simulator_messages_sent_total`, `ferrari_simulator_current_throughput_msg_per_sec` (toutes taguées par `car_id`, `team`, `driver`).
- **Thermique** : `ferrari_simulator_brake_temp_*_celsius`, `ferrari_simulator_tire_temp_*_celsius`, `ferrari_simulator_engine_temp_celsius`.
- **Pneus & carburant** : `ferrari_simulator_tire_wear_percent`, `ferrari_simulator_fuel_remaining_kg`.
- **Stratégie** : `ferrari_simulator_lap_time_seconds`, `ferrari_simulator_stint_health_score`, `ferrari_simulator_pit_window_probability`, `ferrari_simulator_surface_condition_state`, `ferrari_simulator_strategy_recommendation_state`.

Toutes les métriques exposées par le simulateur sont décrites dans `sensor-simulator/README.md`. Celles du `stream-processor` sont consultables via `http://localhost:8001/metrics`.

---

## 🗺️ Architecture (aperçu)

1. **Sensor Simulator** — orchestre 20 voitures (10 équipes officielles), applique anomalies et calcule des insights de stratégie.
2. **Stream Processor** — consomme les événements HTTP, calcule des KPI temps réel et persiste l’état.
3. **Prometheus** — scrappe le simulateur, le stream-processor, cAdvisor.
4. **Grafana** — visualise la télémétrie, les insights de stratégie et la santé système.
5. **Airflow** — planifie des jobs batch (relectures, calculs périodiques, tests de qualité).

Le document `ARCHITECTURE.md` fournit une description complète (diagrammes, flux détaillés, cas d'usage).

---

## 🛠️ Développement & contributions

1. Créer une branche (`git checkout -b feature/xxx`).
2. Lancer les tests locaux si disponibles (ex. `python -m compileall sensor-simulator/main.py`).
3. Respecter le style Python (type hints, pas de `try/except` autour des imports, logs structurés).
4. Soumettre une Pull Request en décrivant clairement la modification et les tests exécutés.

Des benchmarks, guides d’usage et cas métiers supplémentaires sont disponibles dans `benchmark/` et `docs/`.

---

## ❓ Dépannage rapide

| Problème | Diagnostic | Solution |
|----------|------------|----------|
| `make start` échoue | Docker ou docker-compose manquant | Installer Docker Desktop / Compose, ou lancer les services manuellement avec `docker-compose up` |
| `http://localhost:3000` inaccessible | Grafana pas encore démarré | Patienter quelques secondes ou vérifier `docker-compose logs grafana` |
| Pas de métriques dans Prometheus | Bibliothèque `prometheus_client` non installée dans le simulateur | Installer la dépendance (`pip install prometheus-client`) puis redémarrer |
| Erreurs HTTP dans le simulateur | Stream-processor injoignable | Lancer `docker-compose up stream-processor` ou ajuster `HTTP_ENDPOINT` |

Pour aller plus loin :
- vérifier la santé des services (`docker compose ps`),
- consulter les logs (`docker compose logs -f --tail=100 <service>`),
- explorer les runbooks directement dans Grafana (panneaux texte).

---

## 📚 Ressources complémentaires

- `ARCHITECTURE.md` — détails techniques et flux.
- `sensor-simulator/README.md` — fonctionnement du générateur de télémétrie.
- `docs/` — cas d’usage métier, FAQ, notebooks exploratoires.

Bon run !
