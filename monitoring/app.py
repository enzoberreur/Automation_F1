import time
from datetime import datetime
import random
import os

class MonitoringService:
    """Service de monitoring pour Ferrari F1 IoT"""
    
    def __init__(self):
        self.service_name = "Ferrari F1 Monitoring"
        
    def collect_metrics(self):
        """Collecte les métriques des services"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "sensor_simulator": {
                    "status": "running",
                    "uptime_seconds": random.randint(1000, 10000),
                    "data_points_sent": random.randint(1000, 5000),
                },
                "stream_processor": {
                    "status": "running",
                    "uptime_seconds": random.randint(1000, 10000),
                    "events_processed": random.randint(500, 3000),
                    "avg_processing_time_ms": random.uniform(10, 50),
                },
                "airflow": {
                    "status": "running",
                    "active_dags": 1,
                    "last_run": datetime.utcnow().isoformat(),
                }
            },
            "system": {
                "cpu_usage_percent": random.uniform(20, 80),
                "memory_usage_percent": random.uniform(30, 70),
                "disk_usage_percent": random.uniform(20, 60),
            }
        }
    
    def check_health(self):
        """Vérifie la santé globale du système"""
        metrics = self.collect_metrics()
        cpu = metrics["system"]["cpu_usage_percent"]
        memory = metrics["system"]["memory_usage_percent"]
        
        status = "healthy"
        if cpu > 80 or memory > 80:
            status = "warning"
        if cpu > 90 or memory > 90:
            status = "critical"
            
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"System {status}"
        }
    
    def run(self):
        """Lance le service de monitoring"""
        print(f"📊 {self.service_name} started")
        print("🔍 Monitoring Ferrari F1 IoT Platform...")
        print("-" * 80)
        
        while True:
            health = self.check_health()
            print(f"[{health['timestamp']}] Status: {health['status'].upper()}")
            
            if health['status'] == "critical":
                print("🚨 ALERTE CRITIQUE: Ressources système critiques!")
            elif health['status'] == "warning":
                print("⚠️  ATTENTION: Utilisation élevée des ressources")
            else:
                print("✅ Système opérationnel")
            
            print("-" * 80)
            time.sleep(int(os.getenv("MONITOR_INTERVAL", "15")))

if __name__ == "__main__":
    monitor = MonitoringService()
    monitor.run()
