"""
Ferrari Grand Prix DAG - Workflow d'Automation Principal
========================================================

Ce DAG représente le workflow d'automation exigé par le projet Ferrari IoT Smart Pit-Stop.
Il orchestre l'ensemble de la chaîne de traitement des données télémétrie F1 :

1. Démarrage du simulateur de capteurs (sensor-simulator)
2. Démarrage du processeur de flux (stream-processor)
3. Collecte et sauvegarde des données dans PostgreSQL
4. Analyse batch (statistiques et scoring)
5. Notification et logging des résultats

Auteur: Ferrari F1 Team
Date: 14 octobre 2025
Version: 1.0.0
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import logging
import time

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.dummy import DummyOperator
from airflow.utils.task_group import TaskGroup

# Configuration du logger
logger = logging.getLogger(__name__)

TEAM_GRID: List[Dict[str, str]] = [
    {"team": "Scuderia Ferrari", "driver": "Charles Leclerc", "car_id": "Ferrari-SF-24-16"},
    {"team": "Scuderia Ferrari", "driver": "Carlos Sainz", "car_id": "Ferrari-SF-24-55"},
    {"team": "Oracle Red Bull Racing", "driver": "Max Verstappen", "car_id": "RedBull-RB20-1"},
    {"team": "Oracle Red Bull Racing", "driver": "Sergio Pérez", "car_id": "RedBull-RB20-11"},
    {"team": "Mercedes-AMG Petronas", "driver": "Lewis Hamilton", "car_id": "Mercedes-W15-44"},
    {"team": "Mercedes-AMG Petronas", "driver": "George Russell", "car_id": "Mercedes-W15-63"},
    {"team": "McLaren F1 Team", "driver": "Lando Norris", "car_id": "McLaren-MCL38-4"},
    {"team": "McLaren F1 Team", "driver": "Oscar Piastri", "car_id": "McLaren-MCL38-81"},
    {"team": "Aston Martin Aramco", "driver": "Fernando Alonso", "car_id": "AstonMartin-AMR24-14"},
    {"team": "Aston Martin Aramco", "driver": "Lance Stroll", "car_id": "AstonMartin-AMR24-18"},
    {"team": "Alpine F1 Team", "driver": "Esteban Ocon", "car_id": "Alpine-A524-31"},
    {"team": "Alpine F1 Team", "driver": "Pierre Gasly", "car_id": "Alpine-A524-10"},
    {"team": "Visa Cash App RB", "driver": "Yuki Tsunoda", "car_id": "RB-VCARB01-22"},
    {"team": "Visa Cash App RB", "driver": "Daniel Ricciardo", "car_id": "RB-VCARB01-3"},
    {"team": "Stake F1 Team Kick", "driver": "Valtteri Bottas", "car_id": "Kick-Sauber-C44-77"},
    {"team": "Stake F1 Team Kick", "driver": "Guanyu Zhou", "car_id": "Kick-Sauber-C44-24"},
    {"team": "Williams Racing", "driver": "Alex Albon", "car_id": "Williams-FW46-23"},
    {"team": "Williams Racing", "driver": "Logan Sargeant", "car_id": "Williams-FW46-2"},
    {"team": "Haas F1 Team", "driver": "Kevin Magnussen", "car_id": "Haas-VF24-20"},
    {"team": "Haas F1 Team", "driver": "Nico Hülkenberg", "car_id": "Haas-VF24-27"},
]

EXPECTED_TEAMS = sorted({entry["team"] for entry in TEAM_GRID})

# ============================================================================
# CONFIGURATION DU DAG
# ============================================================================

default_args = {
    'owner': 'ferrari-f1-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 10, 14),
    'email': ['f1-automation@ferrari.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
    'execution_timeout': timedelta(hours=1),
}

# ============================================================================
# OPÉRATEURS PERSONNALISÉS
# ============================================================================

class ServiceManager:
    """Gestionnaire de services pour sensor-simulator et stream-processor"""
    
    @staticmethod
    def start_sensor_simulator(**context) -> Dict:
        """Démarre le simulateur de capteurs"""
        logger.info("🏎️  Démarrage du Sensor Simulator...")
        
        # Récupération des paramètres
        config = context['dag_run'].conf or {}
        target_throughput = config.get('target_throughput', 1000)
        duration_seconds = config.get('duration_seconds', 60)
        
        logger.info(f"Configuration: {target_throughput} msg/s pendant {duration_seconds}s")
        
        # En production, on démarrerait le service via Kubernetes API ou Docker
        # Ici on simule le démarrage
        simulator_config = {
            'service': 'sensor-simulator',
            'status': 'started',
            'timestamp': datetime.utcnow().isoformat(),
            'config': {
                'mode': 'http',
                'target_throughput': target_throughput,
                'duration': duration_seconds,
                'car_id': 'Ferrari-F1-75',
                'driver': 'Charles_Leclerc'
            }
        }
        
        # Pousser la config dans XCom pour les tâches suivantes
        context['task_instance'].xcom_push(key='simulator_config', value=simulator_config)
        
        logger.info("✅ Sensor Simulator démarré avec succès")
        return simulator_config
    
    @staticmethod
    def start_stream_processor(**context) -> Dict:
        """Démarre le processeur de flux"""
        logger.info("🔄 Démarrage du Stream Processor...")
        
        # Récupérer la config du simulateur avec le bon task_id (TaskGroup)
        simulator_config = context['task_instance'].xcom_pull(
            task_ids='start_services.start_sensor_simulator',
            key='simulator_config'
        )
        
        processor_config = {
            'service': 'stream-processor',
            'status': 'started',
            'timestamp': datetime.utcnow().isoformat(),
            'config': {
                'mode': 'rest',
                'port': 8001
            }
        }
        
        context['task_instance'].xcom_push(key='processor_config', value=processor_config)
        
        logger.info("✅ Stream Processor démarré avec succès")
        return processor_config
    
    @staticmethod
    def wait_for_data_collection(**context) -> Dict:
        """Attend la collecte des données pendant la durée configurée"""
        simulator_config = context['task_instance'].xcom_pull(
            task_ids='start_services.start_sensor_simulator',
            key='simulator_config'
        )
        
        duration = simulator_config['config']['duration']
        logger.info(f"⏳ Collecte des données pendant {duration} secondes...")
        
        # En production, on surveillerait les métriques réelles
        # Ici on simule avec un sleep court
        time.sleep(5)  # Simulation
        
        collection_stats = {
            'duration_seconds': duration,
            'estimated_messages': duration * simulator_config['config']['target_throughput'],
            'collection_end': datetime.utcnow().isoformat()
        }
        
        context['task_instance'].xcom_push(key='collection_stats', value=collection_stats)
        
        logger.info(f"✅ Collecte terminée: ~{collection_stats['estimated_messages']} messages")
        return collection_stats
    
    @staticmethod
    def stop_services(**context) -> Dict:
        """Arrête tous les services"""
        logger.info("🛑 Arrêt des services...")
        
        # Arrêt du simulateur et du processeur
        # En production: API Kubernetes ou commandes Docker
        
        stop_info = {
            'simulator_stopped': True,
            'processor_stopped': True,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info("✅ Tous les services arrêtés")
        return stop_info


class DataPersistence:
    """Gestionnaire de persistance des données"""
    
    @staticmethod
    def save_telemetry_data(**context) -> Dict:
        """Sauvegarde les données de télémétrie dans PostgreSQL"""
        logger.info("💾 Sauvegarde des données dans PostgreSQL...")
        
        # Récupérer les stats de collecte
        collection_stats = context['task_instance'].xcom_pull(
            task_ids='wait_for_data_collection',
            key='collection_stats'
        )
        
        # Connexion PostgreSQL
        pg_hook = PostgresHook(postgres_conn_id='ferrari_postgres')
        
        # Générer des données de démonstration
        # En production, on lirait depuis l'API du stream-processor
        sample_data = DataPersistence._generate_sample_data(
            count=min(100, collection_stats['estimated_messages'])
        )
        
        # Insertion batch
        insert_query = """
        INSERT INTO telemetry_data (
            timestamp, car_id, team, driver, lap, speed_kmh, rpm,
            brake_temp_avg, tire_temp_avg, tire_wear_percent,
            has_anomaly, anomaly_type, pitstop_score
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        records_inserted = 0
        teams_streamed = set()
        for data in sample_data:
            try:
                pg_hook.run(
                    insert_query,
                    parameters=(
                        data["timestamp"],
                        data["car_id"],
                        data["team"],
                        data["driver"],
                        data["lap"],
                        data["speed_kmh"],
                        data["rpm"],
                        data["brake_temp_avg"],
                        data["tire_temp_avg"],
                        data["tire_wear_percent"],
                        data["has_anomaly"],
                        data["anomaly_type"],
                        data["pitstop_score"],
                    ),
                )
                records_inserted += 1
                teams_streamed.add(data["team"])
            except Exception as e:
                logger.error(f"Erreur insertion: {e}")

        save_stats = {
            'records_inserted': records_inserted,
            'table': 'telemetry_data',
            'timestamp': datetime.utcnow().isoformat(),
            'teams_streamed': sorted(teams_streamed),
        }
        
        context['task_instance'].xcom_push(key='save_stats', value=save_stats)
        
        logger.info(f"✅ {records_inserted} enregistrements sauvegardés")
        return save_stats
    
    @staticmethod
    def _generate_sample_data(count: int) -> List[Dict[str, Any]]:
        """Génère des données de démonstration multi-équipes."""
        import random

        data: List[Dict[str, Any]] = []
        base_time = datetime.utcnow()

        roster_sequence = TEAM_GRID.copy()
        random.shuffle(roster_sequence)

        idx = 0
        for roster in roster_sequence[:min(count, len(roster_sequence))]:
            timestamp = base_time + timedelta(seconds=idx)
            data.append(DataPersistence._build_record(timestamp, roster))
            idx += 1

        for i in range(idx, count):
            timestamp = base_time + timedelta(seconds=i)
            roster = random.choice(TEAM_GRID)
            data.append(DataPersistence._build_record(timestamp, roster))

        return data

    @staticmethod
    def _build_record(timestamp: datetime, roster: Dict[str, str]) -> Dict[str, Any]:
        import random

        return {
            "timestamp": timestamp,
            "car_id": roster["car_id"],
            "team": roster["team"],
            "driver": roster["driver"],
            "lap": random.randint(1, 58),
            "speed_kmh": random.uniform(210, 345),
            "rpm": random.randint(10500, 19000),
            "brake_temp_avg": random.uniform(300, 950),
            "tire_temp_avg": random.uniform(75, 130),
            "tire_wear_percent": random.uniform(0, 95),
            "has_anomaly": random.choice([True, False]),
            "anomaly_type": random.choice([None, 'brake_overheat', 'tire_overheat', 'ers_drop', 'fuel_pressure']),
            "pitstop_score": random.uniform(0, 100),
        }


class BatchAnalytics:
    """Analyse batch des données collectées"""
    
    @staticmethod
    def compute_statistics(**context) -> Dict:
        """Calcule les statistiques globales"""
        logger.info("📊 Calcul des statistiques...")
        
        pg_hook = PostgresHook(postgres_conn_id='ferrari_postgres')
        
        # Requête pour les statistiques
        stats_query = """
        SELECT 
            COUNT(*) as total_records,
            AVG(speed_kmh) as avg_speed,
            STDDEV(speed_kmh) as stddev_speed,
            AVG(brake_temp_avg) as avg_brake_temp,
            STDDEV(brake_temp_avg) as stddev_brake_temp,
            AVG(tire_temp_avg) as avg_tire_temp,
            STDDEV(tire_temp_avg) as stddev_tire_temp,
            AVG(tire_wear_percent) as avg_tire_wear,
            AVG(pitstop_score) as avg_pitstop_score,
            COUNT(CASE WHEN has_anomaly THEN 1 END) as anomaly_count,
            MAX(pitstop_score) as max_pitstop_score
        FROM telemetry_data
        WHERE timestamp >= NOW() - INTERVAL '1 hour'
        """
        
        result = pg_hook.get_first(stats_query)

        if result:
            statistics = {
                'total_records': result[0],
                'speed': {
                    'mean': round(float(result[1]), 2) if result[1] else 0,
                    'stddev': round(float(result[2]), 2) if result[2] else 0
                },
                'brake_temperature': {
                    'mean': round(float(result[3]), 2) if result[3] else 0,
                    'stddev': round(float(result[4]), 2) if result[4] else 0
                },
                'tire_temperature': {
                    'mean': round(float(result[5]), 2) if result[5] else 0,
                    'stddev': round(float(result[6]), 2) if result[6] else 0
                },
                'tire_wear': {
                    'mean': round(float(result[7]), 2) if result[7] else 0
                },
                'pitstop_score': {
                    'mean': round(float(result[8]), 2) if result[8] else 0,
                    'max': round(float(result[10]), 2) if result[10] else 0
                },
                'anomalies': {
                    'count': result[9] or 0,
                    'rate': round((result[9] / result[0] * 100), 2) if result[0] > 0 else 0
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        else:
            statistics = {'error': 'No data available'}

        team_stats_query = """
        SELECT
            team,
            COUNT(*) as events,
            AVG(speed_kmh) as avg_speed,
            AVG(tire_wear_percent) as avg_tire_wear,
            AVG(pitstop_score) as avg_pitstop_score,
            COUNT(CASE WHEN has_anomaly THEN 1 END) as anomaly_count
        FROM telemetry_data
        WHERE timestamp >= NOW() - INTERVAL '1 hour'
        GROUP BY team
        ORDER BY team
        """

        team_records = pg_hook.get_records(team_stats_query)
        team_statistics = []
        for team, events, avg_speed, avg_wear, avg_pit, anomaly_count in team_records:
            anomaly_rate = round((anomaly_count / events * 100), 2) if events else 0
            team_statistics.append({
                'team': team,
                'events': events,
                'avg_speed': round(float(avg_speed), 2) if avg_speed else 0,
                'avg_tire_wear': round(float(avg_wear), 2) if avg_wear else 0,
                'avg_pitstop_score': round(float(avg_pit), 2) if avg_pit else 0,
                'anomaly_rate': anomaly_rate,
            })

        if team_statistics:
            statistics['team_breakdown'] = team_statistics
            BatchAnalytics.persist_team_statistics(pg_hook, team_statistics)

        context['task_instance'].xcom_push(key='statistics', value=statistics)

        logger.info(f"✅ Statistiques calculées: {json.dumps(statistics, indent=2)}")
        return statistics
    
    @staticmethod
    def analyze_pitstop_recommendations(**context) -> Dict:
        """Analyse les recommandations de pit-stop"""
        logger.info("🏁 Analyse des stratégies pit-stop...")
        
        statistics = context['task_instance'].xcom_pull(
            task_ids='batch_analysis.compute_statistics',
            key='statistics'
        )
        
        pg_hook = PostgresHook(postgres_conn_id='ferrari_postgres')
        
        # Analyse des scores par tour
        pitstop_query = """
        SELECT 
            lap,
            AVG(pitstop_score) as avg_score,
            MAX(pitstop_score) as max_score,
            COUNT(CASE WHEN pitstop_score > 75 THEN 1 END) as critical_count
        FROM telemetry_data
        WHERE timestamp >= NOW() - INTERVAL '1 hour'
        GROUP BY lap
        ORDER BY lap
        """
        
        lap_analysis = pg_hook.get_records(pitstop_query)
        
        recommendations = {
            'avg_pitstop_score': statistics.get('pitstop_score', {}).get('mean', 0),
            'max_pitstop_score': statistics.get('pitstop_score', {}).get('max', 0),
            'recommendation': 'Continue' if statistics.get('pitstop_score', {}).get('mean', 0) < 50 else 'Pit-stop recommended',
            'critical_laps': [lap[0] for lap in lap_analysis if lap[3] > 0] if lap_analysis else [],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        context['task_instance'].xcom_push(key='recommendations', value=recommendations)
        
        logger.info(f"✅ Analyse pit-stop: {json.dumps(recommendations, indent=2)}")
        return recommendations

    @staticmethod
    def persist_team_statistics(pg_hook: PostgresHook, team_statistics: List[Dict[str, Any]]):
        """Persiste les statistiques par équipe dans la table dédiée."""

        if not team_statistics:
            return

        insert_query = """
        INSERT INTO telemetry_team_summary (
            execution_date,
            team,
            events,
            avg_speed,
            avg_tire_wear,
            avg_pitstop_score,
            anomaly_rate
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        execution_date = datetime.utcnow()
        for stat in team_statistics:
            pg_hook.run(
                insert_query,
                parameters=(
                    execution_date,
                    stat['team'],
                    stat['events'],
                    stat['avg_speed'],
                    stat['avg_tire_wear'],
                    stat['avg_pitstop_score'],
                    stat['anomaly_rate'],
                ),
            )


class NotificationManager:
    """Gestionnaire de notifications et logs"""
    
    @staticmethod
    def send_success_notification(**context) -> Dict:
        """Envoie une notification de succès"""
        logger.info("📧 Envoi des notifications...")
        
        # Récupérer toutes les données des tâches précédentes
        statistics = context['task_instance'].xcom_pull(
            task_ids='batch_analysis.compute_statistics',
            key='statistics'
        )
        
        recommendations = context['task_instance'].xcom_pull(
            task_ids='batch_analysis.analyze_pitstop_recommendations',
            key='recommendations'
        )

        save_stats = context['task_instance'].xcom_pull(
            task_ids='save_telemetry_data',
            key='save_stats'
        )

        dq_recent = context['task_instance'].xcom_pull(
            task_ids='data_quality.assert_recent_data',
            key='dq_recent_events'
        )

        dq_missing = context['task_instance'].xcom_pull(
            task_ids='data_quality.validate_team_coverage',
            key='dq_missing_teams'
        )
        
        # Construction du rapport
        report = {
            'status': 'SUCCESS',
            'execution_date': context['execution_date'].isoformat(),
            'dag_run_id': context['dag_run'].run_id,
            'summary': {
                'records_collected': save_stats.get('records_inserted', 0),
                'anomalies_detected': statistics.get('anomalies', {}).get('count', 0),
                'avg_speed': statistics.get('speed', {}).get('mean', 0),
                'avg_pitstop_score': recommendations.get('avg_pitstop_score', 0),
                'recommendation': recommendations.get('recommendation', 'Unknown'),
                'recent_events_window': dq_recent or 0,
                'teams_streamed': save_stats.get('teams_streamed', [])
            },
            'details': {
                'statistics': statistics,
                'pitstop_analysis': recommendations,
                'data_quality': {
                    'recent_events': dq_recent,
                    'missing_teams': dq_missing,
                }
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Log du rapport complet
        logger.info("=" * 80)
        logger.info("🏁 FERRARI F1 GRAND PRIX - RAPPORT D'EXÉCUTION")
        logger.info("=" * 80)
        logger.info(json.dumps(report, indent=2))
        logger.info("=" * 80)
        
        # En production: envoyer à Grafana, Slack, email, etc.
        NotificationManager._send_to_grafana(report)
        
        context['task_instance'].xcom_push(key='final_report', value=report)
        
        logger.info("✅ Notifications envoyées avec succès")
        return report
    
    @staticmethod
    def _send_to_grafana(report: Dict):
        """Envoie les données à Grafana (simulation)"""
        # En production: POST vers Grafana API ou Prometheus Pushgateway
        logger.info(f"📊 Envoi des métriques à Grafana...")
        logger.info(f"   - Records: {report['summary']['records_collected']}")
        logger.info(f"   - Anomalies: {report['summary']['anomalies_detected']}")
        logger.info(f"   - Avg Speed: {report['summary']['avg_speed']} km/h")
        logger.info(f"   - Pit-stop Score: {report['summary']['avg_pitstop_score']}")


class DataQuality:
    """Contrôles de qualité des données ingérées."""

    @staticmethod
    def assert_recent_data(**context) -> Dict[str, Any]:
        pg_hook = PostgresHook(postgres_conn_id='ferrari_postgres')
        recent_count = pg_hook.get_first(
            """
            SELECT COUNT(*)
            FROM telemetry_data
            WHERE timestamp >= NOW() - INTERVAL '5 minutes'
            """
        )

        total = recent_count[0] if recent_count else 0
        if total == 0:
            raise ValueError("Aucune télémétrie récente détectée dans les 5 dernières minutes")

        context['task_instance'].xcom_push(key='dq_recent_events', value=total)
        logger.info("✅ Data Quality - %s événements récents", total)
        return {"recent_events": total}

    @staticmethod
    def validate_team_coverage(**context) -> Dict[str, Any]:
        pg_hook = PostgresHook(postgres_conn_id='ferrari_postgres')
        team_rows = pg_hook.get_records(
            """
            SELECT DISTINCT team
            FROM telemetry_data
            WHERE timestamp >= NOW() - INTERVAL '1 hour'
            """
        )

        observed = sorted(row[0] for row in team_rows)
        missing = sorted(set(EXPECTED_TEAMS) - set(observed))

        context['task_instance'].xcom_push(key='dq_missing_teams', value=missing)

        if missing:
            raise ValueError(f"Les équipes suivantes sont absentes de la fenêtre d'analyse: {', '.join(missing)}")

        logger.info("✅ Data Quality - Couverture complète des %d équipes", len(EXPECTED_TEAMS))
        return {"teams": observed}

# ============================================================================
# DÉFINITION DU DAG
# ============================================================================

with DAG(
    dag_id='ferrari_grand_prix_dag',
    default_args=default_args,
    description='🏎️ Workflow d\'automation Ferrari F1 IoT Smart Pit-Stop - Orchestration complète',
    schedule_interval='@hourly',  # Exécution toutes les heures
    catchup=False,
    max_active_runs=1,
    tags=['ferrari', 'f1', 'telemetry', 'automation', 'iot'],
    doc_md=__doc__,
) as dag:
    
    # ========================================================================
    # ÉTAPE 0: INITIALISATION
    # ========================================================================
    
    start = DummyOperator(
        task_id='start',
        doc_md="Point de départ du workflow Ferrari Grand Prix"
    )
    
    # ========================================================================
    # ÉTAPE 1: PRÉPARATION DE L'INFRASTRUCTURE
    # ========================================================================
    
    with TaskGroup('prepare_infrastructure', tooltip='Préparation de l\'infrastructure') as prepare_infra:
        
        create_telemetry_table = PostgresOperator(
            task_id='create_telemetry_table',
            postgres_conn_id='ferrari_postgres',
            sql="""
            CREATE TABLE IF NOT EXISTS telemetry_data (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                car_id VARCHAR(50) NOT NULL,
                team VARCHAR(100) NOT NULL,
                driver VARCHAR(100) NOT NULL,
                lap INTEGER,
                speed_kmh FLOAT,
                rpm INTEGER,
                brake_temp_avg FLOAT,
                tire_temp_avg FLOAT,
                tire_wear_percent FLOAT,
                has_anomaly BOOLEAN,
                anomaly_type VARCHAR(50),
                pitstop_score FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry_data(timestamp);
            CREATE INDEX IF NOT EXISTS idx_telemetry_car_id ON telemetry_data(car_id);
            CREATE INDEX IF NOT EXISTS idx_telemetry_team ON telemetry_data(team);
            CREATE INDEX IF NOT EXISTS idx_telemetry_has_anomaly ON telemetry_data(has_anomaly);
            """,
            doc_md="Crée la table telemetry_data avec les index nécessaires"
        )

        create_team_summary_table = PostgresOperator(
            task_id='create_team_summary_table',
            postgres_conn_id='ferrari_postgres',
            sql="""
            CREATE TABLE IF NOT EXISTS telemetry_team_summary (
                id SERIAL PRIMARY KEY,
                execution_date TIMESTAMP NOT NULL,
                team VARCHAR(100) NOT NULL,
                events INTEGER,
                avg_speed FLOAT,
                avg_tire_wear FLOAT,
                avg_pitstop_score FLOAT,
                anomaly_rate FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            doc_md="Crée la table d'agrégation par équipe"
        )

        create_telemetry_table >> create_team_summary_table
        
        create_telemetry_table
    
    # ========================================================================
    # ÉTAPE 2: DÉMARRAGE DES SERVICES
    # ========================================================================
    
    with TaskGroup('start_services', tooltip='Démarrage des services') as start_services_group:
        
        start_sensor_simulator = PythonOperator(
            task_id='start_sensor_simulator',
            python_callable=ServiceManager.start_sensor_simulator,
            doc_md="Démarre le simulateur de capteurs Ferrari F1"
        )
        
        start_stream_processor = PythonOperator(
            task_id='start_stream_processor',
            python_callable=ServiceManager.start_stream_processor,
            doc_md="Démarre le processeur de flux en temps réel"
        )
        
        start_sensor_simulator >> start_stream_processor
    
    # ========================================================================
    # ÉTAPE 3: COLLECTE DES DONNÉES
    # ========================================================================
    
    wait_for_data_collection = PythonOperator(
        task_id='wait_for_data_collection',
        python_callable=ServiceManager.wait_for_data_collection,
        doc_md="Attend la fin de la collecte des données télémétrie"
    )
    
    # ========================================================================
    # ÉTAPE 4: SAUVEGARDE DES DONNÉES
    # ========================================================================
    
    save_telemetry_data = PythonOperator(
        task_id='save_telemetry_data',
        python_callable=DataPersistence.save_telemetry_data,
        doc_md="Sauvegarde les données dans PostgreSQL"
    )
    
    # ========================================================================
    # ÉTAPE 5: CONTRÔLES QUALITÉ
    # ========================================================================

    with TaskGroup('data_quality', tooltip='Vérifications de fraîcheur et de couverture') as data_quality_group:

        assert_recent_data = PythonOperator(
            task_id='assert_recent_data',
            python_callable=DataQuality.assert_recent_data,
            doc_md="Valide la présence d'événements dans les 5 dernières minutes"
        )

        validate_team_coverage = PythonOperator(
            task_id='validate_team_coverage',
            python_callable=DataQuality.validate_team_coverage,
            doc_md="Contrôle que les 10 équipes sont représentées"
        )

        assert_recent_data >> validate_team_coverage

    # ========================================================================
    # ÉTAPE 6: ARRÊT DES SERVICES
    # ========================================================================

    stop_services = PythonOperator(
        task_id='stop_services',
        python_callable=ServiceManager.stop_services,
        doc_md="Arrête tous les services après la collecte"
    )

    # ========================================================================
    # ÉTAPE 7: ANALYSE BATCH
    # ========================================================================
    
    with TaskGroup('batch_analysis', tooltip='Analyse batch des données') as batch_analysis_group:
        
        compute_statistics = PythonOperator(
            task_id='compute_statistics',
            python_callable=BatchAnalytics.compute_statistics,
            doc_md="Calcule les statistiques (moyenne, variance, etc.)"
        )
        
        analyze_pitstop_recommendations = PythonOperator(
            task_id='analyze_pitstop_recommendations',
            python_callable=BatchAnalytics.analyze_pitstop_recommendations,
            doc_md="Analyse les recommandations de pit-stop"
        )
        
        compute_statistics >> analyze_pitstop_recommendations
    
    # ========================================================================
    # ÉTAPE 8: NOTIFICATIONS
    # ========================================================================
    
    send_success_notification = PythonOperator(
        task_id='send_success_notification',
        python_callable=NotificationManager.send_success_notification,
        doc_md="Envoie les notifications de succès et le rapport"
    )
    
    # ========================================================================
    # ÉTAPE 9: FIN
    # ========================================================================
    
    end = DummyOperator(
        task_id='end',
        doc_md="Fin du workflow Ferrari Grand Prix"
    )
    
    # ========================================================================
    # DÉFINITION DU FLUX D'EXÉCUTION
    # ========================================================================
    
    start >> prepare_infra >> start_services_group >> wait_for_data_collection
    wait_for_data_collection >> save_telemetry_data >> data_quality_group >> stop_services
    stop_services >> batch_analysis_group >> send_success_notification >> end


# ============================================================================
# DOCUMENTATION DU WORKFLOW
# ============================================================================

"""
WORKFLOW D'AUTOMATION FERRARI F1 - ARCHITECTURE
================================================

Ce DAG implémente le workflow d'automation complet exigé par le projet:

┌─────────────────────────────────────────────────────────────────────┐
│                         FERRARI GRAND PRIX DAG                      │
│                    Workflow d'Automation Principal                  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  1. START        │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────────────┐
                    │  2. PREPARE INFRASTRUCTURE│
                    │  • Create DB Tables      │
                    │  • Check Database        │
                    └────────┬─────────────────┘
                             │
                             ▼
                    ┌──────────────────────────┐
                    │  3. START SERVICES       │
                    │  • Sensor Simulator      │
                    │  • Stream Processor      │
                    └────────┬─────────────────┘
                             │
                             ▼
                    ┌──────────────────────────┐
                    │  4. COLLECT DATA         │
                    │  • Wait for duration     │
                    │  • Monitor progress      │
                    └────────┬─────────────────┘
                             │
                             ▼
                    ┌──────────────────────────┐
                    │  5. SAVE TO DATABASE     │
                    │  • PostgreSQL insertion  │
                    │  • CSV export (optional) │
                    └────────┬─────────────────┘
                             │
                             ▼
                    ┌──────────────────────────┐
                    │  6. STOP SERVICES        │
                    │  • Graceful shutdown     │
                    └────────┬─────────────────┘
                             │
                             ▼
                    ┌──────────────────────────┐
                    │  7. BATCH ANALYSIS       │
                    │  • Compute statistics    │
                    │  • Analyze pit-stop      │
                    └────────┬─────────────────┘
                             │
                             ▼
                    ┌──────────────────────────┐
                    │  8. NOTIFICATIONS        │
                    │  • Grafana               │
                    │  • Logging               │
                    └────────┬─────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  9. END          │
                    └──────────────────┘

PARAMÈTRES DE CONFIGURATION:
============================

Via dag_run.conf:
{
    "target_throughput": 1000,    # Messages par seconde
    "duration_seconds": 60        # Durée de collecte
}

MÉTRIQUES CALCULÉES:
===================

• Moyenne et variance de vitesse
• Moyenne et variance de température (freins, pneus)
• Score pit-stop moyen
• Taux d'anomalies
• Recommandations de stratégie

NOTIFICATIONS:
==============

• Logs Airflow détaillés
• Métriques Grafana/Prometheus
• Rapport JSON complet
• Alertes en cas d'anomalies critiques

"""
