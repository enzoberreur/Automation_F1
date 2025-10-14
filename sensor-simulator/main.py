#!/usr/bin/env python3
"""
Ferrari F1 IoT Sensor Simulator - High Performance Edition
Génère 1000-2000 messages/seconde de télémétrie avec support HTTP
"""

import json
import time
import random
import logging
import asyncio
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import threading
from contextlib import nullcontext

# Import pour HTTP
try:
    import aiohttp
    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False
    print("⚠️  aiohttp non installé. Impossible de démarrer.")

# Import pour métriques Prometheus
try:
    from prometheus_client import Counter, Histogram, Gauge, start_http_server, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("⚠️  prometheus_client non installé. Pas de métriques.")


# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# MÉTRIQUES PROMETHEUS
# ============================================================================
if PROMETHEUS_AVAILABLE:
    # Compteurs
    messages_generated = Counter(
        'ferrari_simulator_messages_generated_total',
        'Nombre total de messages télémétrie générés'
    )
    
    messages_sent = Counter(
        'ferrari_simulator_messages_sent_total', 
        'Nombre total de messages envoyés avec succès'
    )
    
    send_errors = Counter(
        'ferrari_simulator_send_errors_total',
        'Nombre total d\'erreurs d\'envoi'
    )
    
    # Histogramme pour latence d'envoi
    send_latency = Histogram(
        'ferrari_simulator_send_latency_seconds',
        'Latence d\'envoi des messages télémétrie'
    )
    
    # Gauge pour throughput en temps réel
    current_throughput = Gauge(
        'ferrari_simulator_current_throughput_msg_per_sec',
        'Débit actuel en messages par seconde'
    )
else:
    # Mock objects si Prometheus n'est pas disponible
    messages_generated = None
    messages_sent = None
    send_errors = None
    send_latency = None
    current_throughput = None


@dataclass
class TelemetryData:
    """Structure de données pour la télémétrie"""
    timestamp: str
    car_id: str
    driver: str
    lap: int
    
    # Moteur
    speed_kmh: float
    rpm: int
    gear: int
    throttle_percent: float
    engine_temp_celsius: float
    
    # Freinage
    brake_pressure_bar: float
    brake_temp_fl_celsius: float
    brake_temp_fr_celsius: float
    brake_temp_rl_celsius: float
    brake_temp_rr_celsius: float
    
    # Pneus
    tire_compound: str
    tire_temp_fl_celsius: float
    tire_temp_fr_celsius: float
    tire_temp_rl_celsius: float
    tire_temp_rr_celsius: float
    tire_pressure_fl_psi: float
    tire_pressure_fr_psi: float
    tire_pressure_rl_psi: float
    tire_pressure_rr_psi: float
    tire_wear_percent: float
    
    # Aérodynamique et électronique
    drs_status: str
    ers_power_kw: float
    fuel_remaining_kg: float
    
    # Environnement
    track_temp_celsius: float
    air_temp_celsius: float
    humidity_percent: float
    
    # Flags et anomalies
    has_anomaly: bool
    anomaly_type: Optional[str]
    anomaly_severity: Optional[str]


class AnomalySimulator:
    """Simulateur d'anomalies pour tests"""
    
    def __init__(self, anomaly_probability: float = 0.02):
        self.anomaly_probability = anomaly_probability
        self.anomaly_types = [
            "brake_overheat",
            "tire_overheat",
            "tire_pressure_loss",
            "engine_overheat",
            "brake_fade"
        ]
    
    def should_trigger_anomaly(self) -> bool:
        """Détermine si une anomalie doit être déclenchée"""
        return random.random() < self.anomaly_probability
    
    def generate_anomaly(self) -> tuple[str, str]:
        """Génère un type et une sévérité d'anomalie"""
        anomaly_type = random.choice(self.anomaly_types)
        severity = random.choice(["warning", "critical"])
        return anomaly_type, severity
    
    def apply_anomaly(self, data: Dict, anomaly_type: str, severity: str) -> Dict:
        """Applique une anomalie aux données"""
        multiplier = 1.3 if severity == "warning" else 1.6
        
        if anomaly_type == "brake_overheat":
            data["brake_temp_fl_celsius"] *= multiplier
            data["brake_temp_fr_celsius"] *= multiplier
            data["brake_temp_rl_celsius"] *= multiplier
            data["brake_temp_rr_celsius"] *= multiplier
            
        elif anomaly_type == "tire_overheat":
            data["tire_temp_fl_celsius"] *= multiplier
            data["tire_temp_fr_celsius"] *= multiplier
            data["tire_temp_rl_celsius"] *= multiplier
            data["tire_temp_rr_celsius"] *= multiplier
            
        elif anomaly_type == "tire_pressure_loss":
            data["tire_pressure_fl_psi"] *= 0.7
            data["tire_pressure_fr_psi"] *= 0.7
            
        elif anomaly_type == "engine_overheat":
            data["engine_temp_celsius"] *= multiplier
            
        elif anomaly_type == "brake_fade":
            data["brake_pressure_bar"] *= 0.6
        
        return data


class FerrariTelemetryGenerator:
    """Générateur de données télémétrie réalistes pour Ferrari F1"""
    
    def __init__(self, car_id: str = "Ferrari-F1-75", driver: str = "Charles Leclerc"):
        self.car_id = car_id
        self.driver = driver
        self.lap = 1
        self.tire_compound = random.choice(["soft", "medium", "hard"])
        self.fuel = 110.0  # kg
        self.tire_wear = 0.0
        self.anomaly_simulator = AnomalySimulator()
        
        # État de la voiture
        self.base_speed = 280.0
        self.base_rpm = 15000
        
    def generate(self) -> TelemetryData:
        """Génère un message de télémétrie"""
        # Simulation de variation de vitesse (circuit)
        speed_variation = random.uniform(-50, 70)
        speed = max(50, min(350, self.base_speed + speed_variation))
        
        # RPM corrélé avec la vitesse
        rpm = int(self.base_rpm + (speed - self.base_speed) * 30)
        rpm = max(8000, min(19000, rpm))
        
        # Gear basé sur RPM
        if rpm < 10000:
            gear = random.randint(1, 3)
        elif rpm < 14000:
            gear = random.randint(3, 5)
        else:
            gear = random.randint(5, 8)
        
        # Throttle et freinage
        throttle = random.uniform(0, 100) if speed > 100 else random.uniform(0, 50)
        brake_pressure = random.uniform(0, 150) if throttle < 30 else random.uniform(0, 30)
        
        # Température moteur
        engine_temp = 90 + (rpm / 19000) * 30 + random.uniform(-5, 5)
        
        # Températures de frein (élevées lors du freinage)
        brake_temp_base = 300 if brake_pressure > 100 else 200
        brake_temp_fl = brake_temp_base + random.uniform(-30, 30)
        brake_temp_fr = brake_temp_base + random.uniform(-30, 30)
        brake_temp_rl = brake_temp_base + random.uniform(-30, 30)
        brake_temp_rr = brake_temp_base + random.uniform(-30, 30)
        
        # Températures pneus (dépendent de la vitesse et du composé)
        tire_temp_base = 85 if self.tire_compound == "hard" else 95 if self.tire_compound == "medium" else 105
        tire_temp_fl = tire_temp_base + random.uniform(-8, 8)
        tire_temp_fr = tire_temp_base + random.uniform(-8, 8)
        tire_temp_rl = tire_temp_base + random.uniform(-8, 8)
        tire_temp_rr = tire_temp_base + random.uniform(-8, 8)
        
        # Pressions pneus
        tire_pressure_base = 21.0
        tire_pressure_fl = tire_pressure_base + random.uniform(-1, 1)
        tire_pressure_fr = tire_pressure_base + random.uniform(-1, 1)
        tire_pressure_rl = tire_pressure_base + random.uniform(-1, 1)
        tire_pressure_rr = tire_pressure_base + random.uniform(-1, 1)
        
        # Usure pneus (augmente avec le temps)
        self.tire_wear = min(100, self.tire_wear + random.uniform(0.01, 0.05))
        
        # DRS et ERS
        drs_status = "open" if speed > 280 and random.random() > 0.5 else "closed"
        ers_power = random.uniform(0, 120) if throttle > 50 else random.uniform(0, 50)
        
        # Carburant (diminue)
        self.fuel = max(0, self.fuel - random.uniform(0.01, 0.03))
        
        # Environnement
        track_temp = 40 + random.uniform(-5, 5)
        air_temp = 28 + random.uniform(-3, 3)
        humidity = 55 + random.uniform(-10, 10)
        
        # Création du message de base
        data_dict = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "car_id": self.car_id,
            "driver": self.driver,
            "lap": self.lap,
            "speed_kmh": round(speed, 2),
            "rpm": rpm,
            "gear": gear,
            "throttle_percent": round(throttle, 2),
            "engine_temp_celsius": round(engine_temp, 2),
            "brake_pressure_bar": round(brake_pressure, 2),
            "brake_temp_fl_celsius": round(brake_temp_fl, 2),
            "brake_temp_fr_celsius": round(brake_temp_fr, 2),
            "brake_temp_rl_celsius": round(brake_temp_rl, 2),
            "brake_temp_rr_celsius": round(brake_temp_rr, 2),
            "tire_compound": self.tire_compound,
            "tire_temp_fl_celsius": round(tire_temp_fl, 2),
            "tire_temp_fr_celsius": round(tire_temp_fr, 2),
            "tire_temp_rl_celsius": round(tire_temp_rl, 2),
            "tire_temp_rr_celsius": round(tire_temp_rr, 2),
            "tire_pressure_fl_psi": round(tire_pressure_fl, 2),
            "tire_pressure_fr_psi": round(tire_pressure_fr, 2),
            "tire_pressure_rl_psi": round(tire_pressure_rl, 2),
            "tire_pressure_rr_psi": round(tire_pressure_rr, 2),
            "tire_wear_percent": round(self.tire_wear, 2),
            "drs_status": drs_status,
            "ers_power_kw": round(ers_power, 2),
            "fuel_remaining_kg": round(self.fuel, 2),
            "track_temp_celsius": round(track_temp, 2),
            "air_temp_celsius": round(air_temp, 2),
            "humidity_percent": round(humidity, 2),
            "has_anomaly": False,
            "anomaly_type": None,
            "anomaly_severity": None
        }
        
        # Simulation d'anomalie
        if self.anomaly_simulator.should_trigger_anomaly():
            anomaly_type, severity = self.anomaly_simulator.generate_anomaly()
            data_dict = self.anomaly_simulator.apply_anomaly(data_dict, anomaly_type, severity)
            data_dict["has_anomaly"] = True
            data_dict["anomaly_type"] = anomaly_type
            data_dict["anomaly_severity"] = severity
        
        return TelemetryData(**data_dict)
    
    def increment_lap(self):
        """Incrémente le numéro de tour"""
        self.lap += 1
        # Changement de pneus tous les 15-25 tours
        if self.lap % random.randint(15, 25) == 0:
            self.tire_compound = random.choice(["soft", "medium", "hard"])
            self.tire_wear = 0.0


class MetricsCollector:
    """Collecteur de métriques de performance"""
    
    def __init__(self):
        self.messages_sent = 0
        self.messages_failed = 0
        self.total_latency = 0.0
        self.start_time = time.time()
        self.last_report_time = time.time()
        self.lock = threading.Lock()
        
    def record_success(self, latency: float):
        """Enregistre un message envoyé avec succès"""
        with self.lock:
            self.messages_sent += 1
            self.total_latency += latency
    
    def record_failure(self):
        """Enregistre un échec d'envoi"""
        with self.lock:
            self.messages_failed += 1
    
    def get_metrics(self) -> Dict:
        """Récupère les métriques actuelles"""
        with self.lock:
            elapsed = time.time() - self.start_time
            throughput = self.messages_sent / elapsed if elapsed > 0 else 0
            avg_latency = self.total_latency / self.messages_sent if self.messages_sent > 0 else 0
            
            return {
                "messages_sent": self.messages_sent,
                "messages_failed": self.messages_failed,
                "throughput_msg_per_sec": round(throughput, 2),
                "avg_latency_ms": round(avg_latency * 1000, 2),
                "uptime_seconds": round(elapsed, 2)
            }
    
    def should_report(self, interval: int = 5) -> bool:
        """Vérifie s'il faut afficher un rapport"""
        now = time.time()
        if now - self.last_report_time >= interval:
            self.last_report_time = now
            return True
        return False
    
    def print_report(self):
        """Affiche un rapport de métriques"""
        metrics = self.get_metrics()
        logger.info(f"""
╔══════════════════════════════════════════════════════════════╗
║ 🏎️  Ferrari F1 Telemetry Simulator - Performance Report     ║
╠══════════════════════════════════════════════════════════════╣
║ Messages envoyés:    {metrics['messages_sent']:>10} msg                ║
║ Messages échoués:    {metrics['messages_failed']:>10} msg                ║
║ Débit (throughput):  {metrics['throughput_msg_per_sec']:>10.2f} msg/s              ║
║ Latence moyenne:     {metrics['avg_latency_ms']:>10.2f} ms                 ║
║ Uptime:              {metrics['uptime_seconds']:>10.2f} s                  ║
╚══════════════════════════════════════════════════════════════╝
        """)


class HTTPPublisher:
    """Publisher pour endpoint HTTP"""
    
    def __init__(self, endpoint_url: str):
        if not HTTP_AVAILABLE:
            raise ImportError("aiohttp non installé")
        
        self.endpoint_url = endpoint_url
        self.session: Optional[aiohttp.ClientSession] = None
        logger.info(f"✅ HTTP Publisher initialisé: {endpoint_url}")
    
    async def initialize(self):
        """Initialise la session HTTP"""
        self.session = aiohttp.ClientSession()
    
    async def send(self, data: TelemetryData) -> float:
        """Envoie des données via HTTP POST et retourne la latence"""
        if not self.session:
            await self.initialize()
        
        start = time.time()
        data_dict = asdict(data)
        
        # Incrémenter le compteur de messages générés
        if messages_generated:
            messages_generated.inc()
        
        try:
            with send_latency.time() if send_latency else nullcontext():
                async with self.session.post(
                    self.endpoint_url,
                    json=data_dict,
                    timeout=aiohttp.ClientTimeout(total=1)
                ) as response:
                    await response.text()  # Consomme la réponse
                    latency = time.time() - start
                    
                    # Incrémenter le compteur de messages envoyés avec succès
                    if messages_sent:
                        messages_sent.inc()
                    
                    return latency
        except Exception as e:
            # Incrémenter le compteur d'erreurs
            if send_errors:
                send_errors.inc()
            logger.debug(f"HTTP error: {e}")
            return time.time() - start
    
    async def close(self):
        """Ferme la session HTTP"""
        if self.session:
            await self.session.close()


class FerrariSensorSimulator:
    """Simulateur principal haute performance"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.generator = FerrariTelemetryGenerator(
            car_id=config.get("car_id", "Ferrari-F1-75"),
            driver=config.get("driver", "Charles Leclerc")
        )
        self.metrics = MetricsCollector()
        self.running = False
        self.publisher = None
        
        # Configuration du mode de transport
        self.mode = config.get("mode", "http").lower()
        self.target_throughput = config.get("target_throughput", 1500)  # msg/s
        
        # Démarrer serveur métriques Prometheus
        self.start_metrics_server()
        
    def setup_publisher(self):
        """Configure le publisher HTTP"""
        if self.mode != "http":
            logger.warning(f"⚠️  Mode '{self.mode}' non supporté, passage en mode HTTP")
            self.mode = "http"
            
        self.publisher = HTTPPublisher(
            endpoint_url=self.config.get("http_endpoint", "http://localhost:8001/telemetry")
        )
    
    def start_metrics_server(self):
        """Démarre le serveur HTTP pour les métriques Prometheus"""
        if PROMETHEUS_AVAILABLE:
            try:
                # Démarre sur le port 8000 pour les métriques
                start_http_server(8000)
                logger.info("🔍 Serveur de métriques Prometheus démarré sur :8000/metrics")
            except Exception as e:
                logger.warning(f"⚠️  Impossible de démarrer le serveur de métriques: {e}")
    
    async def run_async(self):
        """Exécution asynchrone (pour HTTP)"""
        logger.info(f"🏁 Démarrage du simulateur en mode {self.mode.upper()}")
        logger.info(f"🎯 Objectif: {self.target_throughput} messages/s")
        
        self.setup_publisher()
        
        if self.mode == "http":
            await self.publisher.initialize()
        
        self.running = True
        
        # Calcul du délai entre messages pour atteindre le throughput cible
        delay = 1.0 / self.target_throughput
        
        try:
            while self.running:
                # Génération du message
                telemetry = self.generator.generate()
                
                # Envoi HTTP
                try:
                    latency = await self.publisher.send(telemetry)
                    self.metrics.record_success(latency)
                except Exception as e:
                    logger.error(f"Erreur d'envoi: {e}")
                    self.metrics.record_failure()
                
                # Rapport périodique
                if self.metrics.should_report(interval=5):
                    self.metrics.print_report()
                
                # Délai pour contrôler le throughput
                await asyncio.sleep(delay)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Arrêt du simulateur...")
        finally:
            if self.mode == "http":
                await self.publisher.close()
            # Rapport final
            self.metrics.print_report()
    
    def run_sync(self):
        """Exécution synchrone (mode de compatibilité)"""
        logger.info(f"🏁 Démarrage du simulateur en mode {self.mode.upper()}")
        logger.info(f"🎯 Objectif: {self.target_throughput} messages/s")
        
        self.setup_publisher()
        self.running = True
        
        # Calcul du délai entre messages
        delay = 1.0 / self.target_throughput
        
        try:
            while self.running:
                # Génération du message
                telemetry = self.generator.generate()
                
                # Envoi
                try:
                    latency = self.publisher.send(telemetry)
                    self.metrics.record_success(latency)
                except Exception as e:
                    logger.error(f"Erreur d'envoi: {e}")
                    self.metrics.record_failure()
                
                # Rapport périodique
                if self.metrics.should_report(interval=5):
                    self.metrics.print_report()
                
                # Délai pour contrôler le throughput
                time.sleep(delay)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Arrêt du simulateur...")
        finally:
            if self.mode == "kafka":
                self.publisher.close()
            
            # Rapport final
            self.metrics.print_report()
    
    def run(self):
        """Point d'entrée principal"""
        asyncio.run(self.run_async())


def load_config() -> Dict:
    """Charge la configuration depuis les variables d'environnement"""
    config = {
        "mode": os.getenv("TELEMETRY_MODE", "http"),  # http uniquement
        "car_id": os.getenv("CAR_ID", "Ferrari-F1-75"),
        "driver": os.getenv("DRIVER", "Charles Leclerc"),
        "target_throughput": int(os.getenv("TARGET_THROUGHPUT", "1500")),
        

        
        # HTTP
        "http_endpoint": os.getenv("HTTP_ENDPOINT", "http://stream-processor:8001/telemetry"),
    }
    
    return config


def main():
    """Point d'entrée principal"""
    logger.info("=" * 80)
    logger.info("🏎️  Ferrari F1 IoT Sensor Simulator - High Performance Edition")
    logger.info("=" * 80)
    
    config = load_config()
    
    logger.info(f"Configuration:")
    for key, value in config.items():
        if "password" not in key.lower():
            logger.info(f"  {key}: {value}")
    
    simulator = FerrariSensorSimulator(config)
    simulator.run()


if __name__ == "__main__":
    main()
