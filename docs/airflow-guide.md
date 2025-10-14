# 🔄 Guide Airflow - Résultats d'Analyse Ferrari F1

## 🎯 **Comment voir les résultats des analyses Airflow ?**

### **1️⃣ Interface Web Airflow (Recommandé)**

```bash
# Accéder à l'interface Airflow
make airflow-ui
# OU directement : http://localhost:8080
```

**Dans l'interface Airflow vous pouvez :**

#### **📊 Vue d'ensemble des DAGs**
- 🏠 **Page d'accueil** : Liste tous les DAGs Ferrari F1
- 🏎️ **DAG `ferrari_grand_prix_dag`** : Workflow principal d'analyse
- ▶️ **État d'exécution** : Succès/Échec/En cours

#### **📈 Détails d'exécution**  
- 📅 **Grid View** : Historique des exécutions par date
- 🔍 **Graph View** : Visualisation du workflow (tâches + dépendances)
- 📊 **Task Instances** : Status détaillé de chaque tâche

#### **📋 Logs & Résultats**
- 📝 **Logs détaillés** : Cliquer sur une tâche → "Log"
- 🎯 **XCom** : Variables partagées entre tâches
- 📊 **Task Duration** : Performance de chaque analyse

---

### **2️⃣ Résultats en Base de Données**

```bash
# Voir les résultats stockés en PostgreSQL
make airflow-results
```

**Les analyses Ferrari F1 stockent :**
- **Métriques de performance** (pit-stop, temps tours)
- **Anomalies détectées** (température, pression)
- **Statistiques de course** (pilote, stratégie)
- **Rapports de performance** (comparaisons, benchmarks)

---

### **3️⃣ Logs Système**

```bash  
# Logs temps réel du scheduler Airflow
make airflow-logs

# Logs complets d'un service
docker-compose logs airflow-scheduler
docker-compose logs airflow-webserver
```

---

## 🏎️ **Workflow d'Analyse Ferrari F1**

### **DAG `ferrari_grand_prix_dag` inclut :**

#### **📥 Extraction (Extract)**
- `extract_telemetry_data` : Récupération données capteurs
- `extract_race_events` : Événements de course (pit-stops, dépassements)

#### **🔄 Transformation (Transform)**  
- `calculate_lap_times` : Calcul temps au tour optimisés
- `analyze_pit_strategy` : Analyse stratégie arrêts
- `detect_performance_anomalies` : Détection anomalies performance

#### **📊 Chargement (Load)**
- `generate_performance_report` : Rapport final performance
- `update_race_statistics` : MAJ statistiques course
- `send_team_notifications` : Notifications équipe Ferrari

---

## 📈 **Types de Résultats d'Analyse**

### **⚡ Analytics Temps Réel (Stream Processing)**
```bash
# Consulter Grafana pour métriques temps réel
open http://localhost:3000
```
- Température freins/moteur en direct
- Vitesse et position temps réel  
- Score pit-stop instantané

### **📊 Analytics Batch (Airflow)**
```bash
# Interface Airflow pour analyses historiques
open http://localhost:8080
```
- **Rapports de course** : Performance globale post-course
- **Analyses comparatives** : Pilotes, stratégies, circuits
- **Optimisations** : Recommandations pour prochaine course
- **Tendances** : Évolution performance sur saison

---

## 🎯 **Exemple d'Utilisation**

### **Scénario : Analyse Post-Course**

1. **Déclencher l'analyse**
   ```bash
   # Via Airflow UI : DAG ferrari_grand_prix_dag → "Trigger DAG"
   # OU automatique après chaque course
   ```

2. **Suivre l'exécution**
   ```bash
   make airflow-ui
   # → Cliquer sur ferrari_grand_prix_dag
   # → Voir progression temps réel
   ```

3. **Consulter résultats**
   - **Logs détaillés** : Cliquer sur tâche → "Log"
   - **Résultats stockés** : `make airflow-results`
   - **Rapports générés** : Dossier `/opt/airflow/reports/`

4. **Visualisations**
   - **Grafana** : Métriques temps réel course
   - **Airflow** : Analyses batch et rapports
   - **PostgreSQL** : Données historiques

---

## 🔧 **Commandes Utiles**

```bash
# Interface principales
make airflow-ui        # Interface web Airflow  
make airflow-results   # Résultats en base
make airflow-logs      # Logs système

# Gestion des DAGs
make exec-airflow      # Shell interactif
docker-compose restart airflow-scheduler  # Redémarrage
```

---

## 🏁 **En Résumé**

**Pour voir les résultats d'analyse Airflow Ferrari F1 :**

1. **🔄 Interface Airflow** : http://localhost:8080 (principal)
2. **📊 Base de données** : `make airflow-results` (stockage)  
3. **📝 Logs système** : `make airflow-logs` (débogage)
4. **📈 Visualisations** : Grafana pour métriques temps réel

**🏎️ Forza Ferrari ! Les analyses batch complètent parfaitement le monitoring temps réel !**