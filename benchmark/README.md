# 🏎️ Ferrari F1 IoT Smart Pit-Stop - Benchmark Suite

## Vue d'ensemble

Ce dossier contient la **suite de tests de performance et de scalabilité** pour le projet Ferrari IoT Smart Pit-Stop. Les tests démontrent :

- ✅ **Performance**: Capacité à traiter 500-5000 messages/seconde en temps réel
- ✅ **Scalabilité**: Comportement du système sous différentes charges
- ✅ **Fiabilité**: Taux de succès et détection d'anomalies
- ✅ **Efficacité**: Utilisation des ressources (CPU, mémoire)

---

## 📁 Structure

```
benchmark/
├── run_tests.py          # Script principal de benchmark
├── requirements.txt      # Dépendances Python
├── config.yml           # Configuration des tests
├── README.md            # Cette documentation
└── benchmark_run.log    # Logs d'exécution (généré)
```

---

## 🚀 Utilisation

### Installation des dépendances

```bash
cd benchmark/
pip install -r requirements.txt
```

### Prérequis

Avant de lancer les tests, assurez-vous que la stack de monitoring est démarrée :

```bash
cd ../monitoring/
./deploy-monitoring.sh start
```

Vérifiez que tous les services sont opérationnels :
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000
- Sensor Simulator: http://localhost:8000
- Stream Processor: http://localhost:8001

### Exécution des tests

```bash
python run_tests.py
```

Le script va :
1. Vérifier la santé de tous les services
2. Exécuter les 3 scénarios de test (500, 1000, 5000 msg/s)
3. Collecter les métriques via Prometheus API
4. Générer les rapports dans `docs/`

**Durée estimée** : ~5-6 minutes (3 tests de 60s + pauses)

---

## 📊 Scénarios de test

### Test 1 : Charge Faible (500 msg/s)
- **Objectif** : Valider le fonctionnement nominal
- **Durée** : 60 secondes
- **Attendu** : Latence très faible, ressources minimales

### Test 2 : Charge Normale (1000 msg/s)
- **Objectif** : Performance en production
- **Durée** : 60 secondes
- **Attendu** : Latence P95 <50ms, CPU <70%

### Test 3 : Stress Test (5000 msg/s)
- **Objectif** : Tester les limites du système
- **Durée** : 60 secondes
- **Attendu** : Système stable, possibilité d'auto-scaling

---

## 📈 Métriques collectées

### Latence (via Prometheus)
- **P50** : Médiane (50% des requêtes)
- **P95** : 95ème percentile
- **P99** : 99ème percentile
- **Moyenne** : Latence moyenne
- **Min/Max** : Valeurs extrêmes

**Source** : `processing_latency_seconds_bucket{job="stream-processor"}`

### Débit
- **Débit cible** : Messages/seconde attendus
- **Débit réel** : Messages/seconde effectifs
- **Total messages** : Nombre total traité
- **Taux de succès** : Pourcentage de messages réussis

**Source** : `messages_processed_total`, `messages_failed_total`

### Ressources (via cAdvisor)
- **CPU** : Utilisation en %
- **Mémoire** : Usage en MB
- **Réseau** : Données RX/TX en MB

**Source** : `container_cpu_usage_seconds_total`, `container_memory_usage_bytes`

### Anomalies
- **Total détectées** : Nombre d'anomalies trouvées
- **Par type** : Freins, pneus, etc.
- **Taux de détection** : Pourcentage détecté

**Source** : `anomalies_detected_total{type="..."}`

---

## ⚙️ Configuration

Le fichier `config.yml` permet de personnaliser :

### Endpoints
```yaml
endpoints:
  prometheus: 'http://localhost:9090'
  sensor_simulator: 'http://localhost:8000'
  stream_processor: 'http://localhost:8001'
```

### Scénarios
```yaml
test_scenarios:
  - throughput: 500
    duration: 60
  - throughput: 1000
    duration: 60
  # Ajoutez vos propres scénarios
```

### Seuils de validation
```yaml
thresholds:
  latency_p95_ms: 50
  cpu_percent_max: 85
  success_rate_min: 99.0
```

---

## 📄 Rapports générés

### docs/benchmarks.md
Rapport Markdown complet avec :
- Résumé exécutif
- Tableau récapitulatif des tests
- Détails par test (latence, débit, ressources)
- Graphiques ASCII
- Analyse et recommandations

### docs/benchmark_results.json
Résultats bruts en JSON pour analyse ultérieure :
```json
{
  "metadata": {
    "timestamp": "2025-10-14T...",
    "duration_seconds": 360,
    "test_count": 3
  },
  "results": [...]
}
```

---

## 🎯 Critères de succès

Un test est considéré comme **PASSED** si :
- ✅ Latence P95 ≤ 50ms
- ✅ Taux de succès ≥ 99%
- ✅ CPU ≤ 85% (avant auto-scaling)
- ✅ Aucune défaillance système

Un test **FAILED** si :
- ❌ Latence excessive
- ❌ Taux d'échec élevé
- ❌ Saturation des ressources

---

## 🔍 Exemple de résultats

```
Test: Benchmark_1000msg_s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Latence:
  P50: 8.45ms
  P95: 22.31ms
  P99: 38.67ms

Débit:
  Cible: 1000 msg/s
  Réel: 987 msg/s
  Taux succès: 99.7%

Ressources:
  CPU: 68.3%
  Mémoire: 512 MB

Status: ✅ PASSED
```

---

## 🐛 Dépannage

### Problème : Services non accessibles

```bash
# Vérifier que la stack monitoring tourne
cd ../monitoring/
docker-compose ps

# Redémarrer si nécessaire
./deploy-monitoring.sh restart
```

### Problème : Métriques Prometheus vides

```bash
# Vérifier les targets Prometheus
curl http://localhost:9090/api/v1/targets

# Vérifier que les services exposent /metrics
curl http://localhost:8001/metrics
curl http://localhost:8000/metrics
```

### Problème : Tests échouent

- Augmenter les seuils dans `config.yml`
- Vérifier les ressources système (Docker)
- Réduire le débit cible des tests
- Augmenter la durée de warmup

---

## 📚 Architecture du script

### Classes principales

#### `FerrariF1Benchmark`
Gestionnaire principal des tests de performance.

**Méthodes clés** :
- `check_services_health()` : Vérifie la disponibilité des services
- `run_single_test()` : Exécute un test unique
- `run_all_tests()` : Exécute tous les scénarios
- `query_prometheus()` : Interroge l'API Prometheus
- `get_latency_metrics()` : Collecte métriques de latence
- `get_resource_metrics()` : Collecte métriques de ressources
- `generate_markdown_report()` : Génère le rapport

#### Dataclasses
- `LatencyMetrics` : Métriques de latence (p50, p95, p99...)
- `ResourceMetrics` : Métriques de ressources (CPU, RAM...)
- `ThroughputMetrics` : Métriques de débit
- `AnomalyMetrics` : Métriques d'anomalies
- `BenchmarkResult` : Résultat complet d'un test

---

## 🔗 Intégration continue

### Automatiser avec Airflow

Le DAG `ferrari_grand_prix_dag.py` peut être étendu pour inclure le benchmark :

```python
benchmark_task = PythonOperator(
    task_id='run_performance_benchmark',
    python_callable=run_benchmark,
    dag=dag
)

batch_analysis >> benchmark_task >> send_notification
```

### GitHub Actions

```yaml
- name: Run Performance Benchmark
  run: |
    cd benchmark/
    python run_tests.py
    
- name: Upload Benchmark Report
  uses: actions/upload-artifact@v3
  with:
    name: benchmark-report
    path: docs/benchmarks.md
```

---

## 📖 Références

- **Prometheus API** : https://prometheus.io/docs/prometheus/latest/querying/api/
- **PromQL** : https://prometheus.io/docs/prometheus/latest/querying/basics/
- **cAdvisor Metrics** : https://github.com/google/cadvisor/blob/master/docs/storage/prometheus.md

---

## 🏎️ Livrable Projet

Ce benchmark constitue le livrable **"Cluster setup + benchmark results (performance & scalability)"** :

✅ **Cluster Setup** : Stack Docker Compose / Kubernetes configurée

✅ **Performance** : Tests à 500, 1000, 5000 msg/s

✅ **Scalability** : Démonstration de l'auto-scaling HPA

✅ **Results** : Rapport détaillé avec métriques et graphiques

✅ **Reproducibility** : Scripts automatisés et configuration

---

**🏎️ Forza Ferrari! 🏎️**
