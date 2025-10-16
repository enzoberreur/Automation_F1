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

SURFACE_CONDITIONS = ("optimal", "hot", "cool", "damp")
STRATEGY_ACTIONS = ("extend", "evaluate", "pit_soon")

SURFACE_CONDITION_INDEX = {
    "optimal": 0,
    "cool": 1,
    "hot": 2,
    "damp": 3,
}

STRATEGY_RECOMMENDATION_INDEX = {
    "extend": 0,
    "evaluate": 1,
    "pit_soon": 2,
}

# ============================================================================
# MÉTRIQUES PROMETHEUS - FERRARI F1 THERMAL COCKPIT
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
    
    # === MÉTRIQUES THERMAL COCKPIT DASHBOARD ===
    
    # Températures Freins (4 roues)
    brake_temp_fl = Gauge('ferrari_simulator_brake_temp_fl_celsius', 'Température frein avant gauche')
    brake_temp_fr = Gauge('ferrari_simulator_brake_temp_fr_celsius', 'Température frein avant droit')
    brake_temp_rl = Gauge('ferrari_simulator_brake_temp_rl_celsius', 'Température frein arrière gauche')
    brake_temp_rr = Gauge('ferrari_simulator_brake_temp_rr_celsius', 'Température frein arrière droit')
    
    # Températures Pneus (4 roues)
    tire_temp_fl = Gauge('ferrari_simulator_tire_temp_fl_celsius', 'Température pneu avant gauche')
    tire_temp_fr = Gauge('ferrari_simulator_tire_temp_fr_celsius', 'Température pneu avant droit')
    tire_temp_rl = Gauge('ferrari_simulator_tire_temp_rl_celsius', 'Température pneu arrière gauche')
    tire_temp_rr = Gauge('ferrari_simulator_tire_temp_rr_celsius', 'Température pneu arrière droit')
    
    # Performance & Moteur
    engine_temp = Gauge('ferrari_simulator_engine_temp_celsius', 'Température moteur')
    speed_kmh = Gauge('ferrari_simulator_speed_kmh', 'Vitesse en km/h')
    rpm = Gauge('ferrari_simulator_rpm', 'Régime moteur RPM')
    throttle_percent = Gauge('ferrari_simulator_throttle_percent', 'Position accélérateur %')
    
    # Systèmes Électroniques
    ers_power_kw = Gauge('ferrari_simulator_ers_power_kw', 'Puissance ERS en kW')
    fuel_remaining_kg = Gauge('ferrari_simulator_fuel_remaining_kg', 'Carburant restant en kg')
    
    # Pneus & Stratégie
    tire_wear_percent = Gauge('ferrari_simulator_tire_wear_percent', 'Usure pneus en %')
    lap_number = Gauge('ferrari_simulator_lap', 'Numéro de tour actuel')

    # Freinage
    brake_pressure_bar = Gauge('ferrari_simulator_brake_pressure_bar', 'Pression freinage en bar')

    # Insights stratégie
    lap_time_seconds = Gauge('ferrari_simulator_lap_time_seconds', 'Temps au tour estimé (s)')
    stint_health_score = Gauge('ferrari_simulator_stint_health_score', 'Indice de santé du relais (0-100)')
    pit_window_probability = Gauge(
        'ferrari_simulator_pit_window_probability',
        "Probabilité d'ouverture de fenêtre de stand (0-1)"
    )

    surface_condition_info = Gauge(
        'ferrari_simulator_surface_condition_info',
        'Condition de piste courante (gauge binaire par état)',
        ['condition']
    )

    strategy_recommendation_info = Gauge(
        'ferrari_simulator_strategy_recommendation_info',
        'Recommandation stratégique active (gauge binaire par action)',
        ['recommendation']
    )

    surface_condition_state = Gauge(
        'ferrari_simulator_surface_condition_state',
        'Indice numérique de condition de piste (0 optimal, 3 humide)'
    )

    strategy_recommendation_state = Gauge(
        'ferrari_simulator_strategy_recommendation_state',
        'Indice numérique de recommandation stratégique (0 extend, 2 pit)'
    )
else:
    # Mock objects si Prometheus n'est pas disponible
    messages_generated = None
    messages_sent = None
    send_errors = None
    send_latency = None
    current_throughput = None
    
    # Mock objects pour métriques thermiques
    brake_temp_fl = brake_temp_fr = brake_temp_rl = brake_temp_rr = None
    tire_temp_fl = tire_temp_fr = tire_temp_rl = tire_temp_rr = None
    engine_temp = speed_kmh = rpm = throttle_percent = None
    ers_power_kw = fuel_remaining_kg = tire_wear_percent = None
    lap_number = brake_pressure_bar = None
    lap_time_seconds = stint_health_score = pit_window_probability = None
    surface_condition_info = strategy_recommendation_info = None
    surface_condition_state = strategy_recommendation_state = None


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

    # Insights stratégie
    lap_time_seconds: float
    stint_health_score: float
    pit_window_probability: float
    surface_condition: str
    strategy_recommendation: str


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
            data["tire_pressure_rl_psi"] *= 0.7
            data["tire_pressure_rr_psi"] *= 0.7
            
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

        # Modèle de piste simplifié : chaque segment représente un type de virage
        self.track_profile = [
            {"length": 0.18, "target_speed": 320, "brake_intensity": 0.15, "drs": True},  # Ligne droite
            {"length": 0.12, "target_speed": 210, "brake_intensity": 0.55, "drs": False},  # Chicane
            {"length": 0.22, "target_speed": 290, "brake_intensity": 0.25, "drs": True},
            {"length": 0.20, "target_speed": 180, "brake_intensity": 0.65, "drs": False},  # Enchaînement serré
            {"length": 0.16, "target_speed": 260, "brake_intensity": 0.35, "drs": False},
            {"length": 0.12, "target_speed": 300, "brake_intensity": 0.30, "drs": True},
        ]
        self.segment_boundaries = self._compute_segment_boundaries()
        self.lap_progress = 0.0

        # États pour lisser les séries temporelles
        self._last_speed = self.base_speed
        self._last_brake_pressure = 80.0
        self._last_brake_temps = {
            "fl": 320.0,
            "fr": 320.0,
            "rl": 300.0,
            "rr": 300.0,
        }
        self._last_tire_temps = {
            "fl": 100.0,
            "fr": 100.0,
            "rl": 98.0,
            "rr": 98.0,
        }

        # Tendances météo lentes pour éviter les oscillations brutales
        self._track_temp = 40.0 + random.uniform(-1.0, 1.0)
        self._air_temp = 28.0 + random.uniform(-1.0, 1.0)
        self._humidity = 55.0 + random.uniform(-3.0, 3.0)
        self._weather_trend = {
            "track": random.uniform(-0.02, 0.02),
            "air": random.uniform(-0.015, 0.015),
            "humidity": random.uniform(-0.08, 0.08),
        }

    def _compute_segment_boundaries(self) -> List[float]:
        """Calcule les bornes cumulées des segments de piste"""
        boundaries: List[float] = []
        cumulative = 0.0
        for segment in self.track_profile:
            cumulative += segment["length"]
            boundaries.append(cumulative)
        # Normalisation si la somme diffère légèrement de 1
        if cumulative != 1.0:
            boundaries = [b / cumulative for b in boundaries]
        return boundaries

    def _current_segment(self) -> Dict:
        """Retourne le segment de piste correspondant au progrès actuel"""
        for boundary, segment in zip(self.segment_boundaries, self.track_profile):
            if self.lap_progress <= boundary:
                return segment
        return self.track_profile[-1]

    def _advance_lap_progress(self):
        """Fait avancer la voiture sur la piste et gère le changement de tour"""
        progress_increment = random.uniform(0.018, 0.032)
        self.lap_progress += progress_increment
        if self.lap_progress >= 1.0:
            self.lap_progress -= 1.0
            self.increment_lap()

    def _compute_strategy_insights(self, data: Dict) -> Dict:
        """Calcule des insights de stratégie à partir de la télémétrie instantanée"""
        tire_wear = data["tire_wear_percent"]
        fuel = data["fuel_remaining_kg"]
        brake_temps = [
            data["brake_temp_fl_celsius"],
            data["brake_temp_fr_celsius"],
            data["brake_temp_rl_celsius"],
            data["brake_temp_rr_celsius"],
        ]
        tire_temps = [
            data["tire_temp_fl_celsius"],
            data["tire_temp_fr_celsius"],
            data["tire_temp_rl_celsius"],
            data["tire_temp_rr_celsius"],
        ]
        tire_pressures = [
            data["tire_pressure_fl_psi"],
            data["tire_pressure_fr_psi"],
            data["tire_pressure_rl_psi"],
            data["tire_pressure_rr_psi"],
        ]

        avg_brake_temp = sum(brake_temps) / 4
        avg_tire_temp = sum(tire_temps) / 4
        avg_tire_pressure = sum(tire_pressures) / 4

        track_temp = data["track_temp_celsius"]
        humidity = data["humidity_percent"]
        engine_temp = data["engine_temp_celsius"]

        # Lap time estimation influenced by wear, temps, humidity and DRS usage
        base_lap = 87.5
        wear_penalty = (tire_wear / 100) * 3.8
        fuel_penalty = (fuel / 110) * 1.6
        brake_penalty = max(0.0, avg_brake_temp - 460) * 0.018
        engine_penalty = max(0.0, engine_temp - 105) * 0.11
        humidity_penalty = max(0.0, humidity - 70) * 0.05
        drs_bonus = -1.1 if data["drs_status"] == "open" else 0.0
        lap_time = base_lap + wear_penalty + fuel_penalty + brake_penalty + engine_penalty + humidity_penalty + drs_bonus
        lap_time += random.uniform(-0.5, 0.5)
        lap_time = max(75.0, min(105.0, lap_time))

        # Stint health score (0-100)
        stint_health = 100.0
        stint_health -= tire_wear * 0.45
        stint_health -= max(0.0, engine_temp - 100) * 1.05
        stint_health -= max(0.0, avg_brake_temp - 420) * 0.22
        stint_health -= max(0.0, 22.0 - avg_tire_pressure) * 3.5
        optimal_tire_temp = track_temp + 55
        stint_health -= max(0.0, abs(avg_tire_temp - optimal_tire_temp)) * 0.12
        stint_health = max(0.0, min(100.0, stint_health))

        # Pit window probability (0-1)
        pit_pressure = 0.0
        pit_pressure += (tire_wear / 100) * 0.6
        pit_pressure += max(0.0, 32.0 - fuel) / 32.0 * 0.25
        pit_pressure += max(0.0, lap_time - 96.0) / 12.0 * 0.1
        pit_pressure += 0.15 if data["has_anomaly"] else 0.0
        pit_window_probability = max(0.0, min(1.0, pit_pressure))

        # Surface condition based on track temperature and humidity
        if humidity > 72:
            surface_condition = "damp"
        elif track_temp >= 48:
            surface_condition = "hot"
        elif track_temp <= 35:
            surface_condition = "cool"
        else:
            surface_condition = "optimal"

        if pit_window_probability > 0.65 or stint_health < 45:
            strategy_recommendation = "pit_soon"
        elif pit_window_probability > 0.4:
            strategy_recommendation = "evaluate"
        else:
            strategy_recommendation = "extend"

        return {
            "lap_time_seconds": round(lap_time, 2),
            "stint_health_score": round(stint_health, 2),
            "pit_window_probability": round(pit_window_probability, 3),
            "surface_condition": surface_condition,
            "strategy_recommendation": strategy_recommendation,
        }
        
    def generate(self) -> TelemetryData:
        """Génère un message de télémétrie"""
        # Avancer sur la piste pour connaître le segment courant
        self._advance_lap_progress()
        segment = self._current_segment()

        # Effets physiques simplifiés
        tire_wear_penalty = self.tire_wear * 0.25
        fuel_bonus = (110.0 - self.fuel) * 0.12
        segment_speed = segment["target_speed"] - tire_wear_penalty + fuel_bonus
        segment_speed += random.uniform(-5, 5)

        # Lisser la transition de vitesse
        speed = 0.65 * self._last_speed + 0.35 * max(60, min(360, segment_speed))
        self._last_speed = speed

        # RPM corrélé avec la vitesse
        rpm = int(self.base_rpm + (speed - self.base_speed) * 32)
        rpm = max(9000, min(19000, rpm))

        # Gear basé sur RPM
        if rpm < 10500:
            gear = random.randint(2, 4)
        elif rpm < 14500:
            gear = random.randint(4, 6)
        else:
            gear = random.randint(6, 8)

        # Throttle et freinage corrélés au segment
        throttle = max(0.0, min(100.0, 70 + random.uniform(-15, 10) - segment["brake_intensity"] * 80))
        brake_pressure_target = segment["brake_intensity"] * (180 + random.uniform(-10, 10))
        brake_pressure = 0.6 * self._last_brake_pressure + 0.4 * brake_pressure_target
        self._last_brake_pressure = brake_pressure

        # Température moteur dépendant du RPM et du throttle
        engine_temp = 92 + (rpm / 19000) * 32 + (throttle / 100) * 6 + random.uniform(-3, 3)

        # Températures de frein (sensibles au freinage et à la vitesse)
        base_brake_temp = 260 + segment["brake_intensity"] * 160 + (speed / 340) * 40
        for key in self._last_brake_temps:
            drift = random.uniform(-8, 8)
            self._last_brake_temps[key] = 0.6 * self._last_brake_temps[key] + 0.4 * (base_brake_temp + drift)

        brake_temp_fl = self._last_brake_temps["fl"]
        brake_temp_fr = self._last_brake_temps["fr"]
        brake_temp_rl = self._last_brake_temps["rl"]
        brake_temp_rr = self._last_brake_temps["rr"]

        # Températures pneus (dépendent du composé, du segment et de l'usure)
        compound_base = {"soft": 107, "medium": 98, "hard": 90}[self.tire_compound]
        wear_delta = self.tire_wear * 0.08
        segment_heat = segment["brake_intensity"] * 12 + (speed / 320) * 6
        for key in self._last_tire_temps:
            noise = random.uniform(-3, 3)
            target_temp = compound_base + segment_heat - wear_delta + noise
            self._last_tire_temps[key] = 0.7 * self._last_tire_temps[key] + 0.3 * target_temp

        tire_temp_fl = self._last_tire_temps["fl"]
        tire_temp_fr = self._last_tire_temps["fr"]
        tire_temp_rl = self._last_tire_temps["rl"]
        tire_temp_rr = self._last_tire_temps["rr"]

        # Pressions pneus influencées par la température
        tire_pressure_base = 21.0
        tire_pressure_fl = tire_pressure_base + (tire_temp_fl - compound_base) * 0.015 + random.uniform(-0.2, 0.2)
        tire_pressure_fr = tire_pressure_base + (tire_temp_fr - compound_base) * 0.015 + random.uniform(-0.2, 0.2)
        tire_pressure_rl = tire_pressure_base + (tire_temp_rl - compound_base) * 0.015 + random.uniform(-0.2, 0.2)
        tire_pressure_rr = tire_pressure_base + (tire_temp_rr - compound_base) * 0.015 + random.uniform(-0.2, 0.2)

        # Usure pneus basée sur l'intensité du segment et le composé
        compound_multiplier = {"soft": 0.05, "medium": 0.035, "hard": 0.025}[self.tire_compound]
        wear_increment = compound_multiplier * (0.6 + segment["brake_intensity"]) * random.uniform(0.8, 1.2)
        self.tire_wear = min(100.0, self.tire_wear + wear_increment)

        # DRS et ERS
        drs_status = "open" if segment.get("drs") and speed > 290 and throttle > 60 else "closed"
        ers_base = 80 if drs_status == "open" else 60
        ers_power = max(0.0, min(130.0, ers_base + (100 - throttle) * 0.4 + random.uniform(-10, 10)))

        # Carburant (diminue plus vite sur les segments rapides)
        fuel_usage = 0.018 + segment["brake_intensity"] * 0.01 + (throttle / 1000)
        self.fuel = max(0.0, self.fuel - fuel_usage)

        # Environnement avec tendances lentes
        self._track_temp += self._weather_trend["track"] + random.uniform(-0.15, 0.2)
        self._air_temp += self._weather_trend["air"] + random.uniform(-0.1, 0.12)
        self._humidity += self._weather_trend["humidity"] + random.uniform(-0.4, 0.4)

        track_temp = max(30.0, min(55.0, self._track_temp))
        air_temp = max(18.0, min(38.0, self._air_temp))
        humidity = max(25.0, min(85.0, self._humidity))

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

        insights = self._compute_strategy_insights(data_dict)
        data_dict.update(insights)

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
            # Mettre à jour la jauge Prometheus immédiatement
            try:
                if PROMETHEUS_AVAILABLE and current_throughput is not None:
                    elapsed = time.time() - self.start_time
                    throughput = self.messages_sent / elapsed if elapsed > 0 else 0
                    current_throughput.set(round(throughput, 2))
            except Exception:
                pass
    
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
            
            # Mettre à jour la jauge Prometheus si disponible
            try:
                if PROMETHEUS_AVAILABLE and current_throughput is not None:
                    # current_throughput attend un float en msg/s
                    current_throughput.set(round(throughput, 2))
            except Exception:
                # Ne pas faire échouer le collecteur si la mise à jour Prometheus plante
                pass

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
    
    def update_thermal_metrics(self, data: TelemetryData):
        """Met à jour toutes les métriques pour le Thermal Cockpit Dashboard"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        try:
            # Températures Freins
            if brake_temp_fl: brake_temp_fl.set(data.brake_temp_fl_celsius)
            if brake_temp_fr: brake_temp_fr.set(data.brake_temp_fr_celsius)
            if brake_temp_rl: brake_temp_rl.set(data.brake_temp_rl_celsius)
            if brake_temp_rr: brake_temp_rr.set(data.brake_temp_rr_celsius)
            
            # Températures Pneus
            if tire_temp_fl: tire_temp_fl.set(data.tire_temp_fl_celsius)
            if tire_temp_fr: tire_temp_fr.set(data.tire_temp_fr_celsius)
            if tire_temp_rl: tire_temp_rl.set(data.tire_temp_rl_celsius)
            if tire_temp_rr: tire_temp_rr.set(data.tire_temp_rr_celsius)
            
            # Performance & Moteur
            if engine_temp: engine_temp.set(data.engine_temp_celsius)
            if speed_kmh: speed_kmh.set(data.speed_kmh)
            if rpm: rpm.set(data.rpm)
            if throttle_percent: throttle_percent.set(data.throttle_percent)
            
            # Systèmes Électroniques
            if ers_power_kw: ers_power_kw.set(data.ers_power_kw)
            if fuel_remaining_kg: fuel_remaining_kg.set(data.fuel_remaining_kg)
            
            # Pneus & Stratégie
            if tire_wear_percent: tire_wear_percent.set(data.tire_wear_percent)
            if lap_number: lap_number.set(data.lap)

            # Freinage
            if brake_pressure_bar: brake_pressure_bar.set(data.brake_pressure_bar)

            # Insights stratégie
            if lap_time_seconds: lap_time_seconds.set(data.lap_time_seconds)
            if stint_health_score: stint_health_score.set(data.stint_health_score)
            if pit_window_probability: pit_window_probability.set(data.pit_window_probability)
            if surface_condition_info:
                for condition in SURFACE_CONDITIONS:
                    value = 1.0 if data.surface_condition == condition else 0.0
                    surface_condition_info.labels(condition=condition).set(value)
            if surface_condition_state:
                surface_index = SURFACE_CONDITION_INDEX.get(data.surface_condition, 0)
                surface_condition_state.set(surface_index)
            if strategy_recommendation_info:
                for action in STRATEGY_ACTIONS:
                    value = 1.0 if data.strategy_recommendation == action else 0.0
                    strategy_recommendation_info.labels(recommendation=action).set(value)
            if strategy_recommendation_state:
                recommendation_index = STRATEGY_RECOMMENDATION_INDEX.get(data.strategy_recommendation, 0)
                strategy_recommendation_state.set(recommendation_index)

        except Exception as e:
            logger.debug(f"Erreur mise à jour métriques thermiques: {e}")
    
    async def send(self, data: TelemetryData) -> float:
        """Envoie des données via HTTP POST et retourne la latence"""
        if not self.session:
            await self.initialize()
        
        start = time.time()
        data_dict = asdict(data)
        
        # Incrémenter le compteur de messages générés
        if messages_generated:
            messages_generated.inc()
        
        # Mise à jour des métriques individuelles pour Thermal Cockpit Dashboard
        self.update_thermal_metrics(data)
        
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
