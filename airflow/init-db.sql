-- ============================================================================
-- FERRARI F1 - INITIALISATION BASE DE DONNÉES
-- ============================================================================
-- Ce script initialise les bases de données nécessaires pour le projet
-- Exécuté automatiquement au démarrage de PostgreSQL
-- ============================================================================

-- Créer la base de données Ferrari F1
CREATE DATABASE ferrari_f1;

-- Créer l'utilisateur Ferrari
CREATE USER ferrari WITH PASSWORD 'ferrari';

-- Accorder les privilèges
GRANT ALL PRIVILEGES ON DATABASE ferrari_f1 TO ferrari;

-- Se connecter à la base ferrari_f1
\c ferrari_f1

-- Créer la table de télémétrie
CREATE TABLE IF NOT EXISTS telemetry_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    car_id VARCHAR(50) NOT NULL,
    driver VARCHAR(100) NOT NULL,
    lap INTEGER,
    speed_kmh FLOAT,
    rpm INTEGER,
    brake_temp_avg FLOAT,
    tire_temp_avg FLOAT,
    tire_wear_percent FLOAT,
    has_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_type VARCHAR(50),
    pitstop_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Créer les index pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_telemetry_car_id ON telemetry_data(car_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_has_anomaly ON telemetry_data(has_anomaly);
CREATE INDEX IF NOT EXISTS idx_telemetry_lap ON telemetry_data(lap);

-- Créer une table pour les statistiques agrégées
CREATE TABLE IF NOT EXISTS telemetry_statistics (
    id SERIAL PRIMARY KEY,
    execution_date TIMESTAMP NOT NULL,
    total_records INTEGER,
    avg_speed FLOAT,
    stddev_speed FLOAT,
    avg_brake_temp FLOAT,
    stddev_brake_temp FLOAT,
    avg_tire_temp FLOAT,
    stddev_tire_temp FLOAT,
    avg_tire_wear FLOAT,
    avg_pitstop_score FLOAT,
    max_pitstop_score FLOAT,
    anomaly_count INTEGER,
    anomaly_rate FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Créer une table pour les recommandations de pit-stop
CREATE TABLE IF NOT EXISTS pitstop_recommendations (
    id SERIAL PRIMARY KEY,
    execution_date TIMESTAMP NOT NULL,
    car_id VARCHAR(50) NOT NULL,
    lap INTEGER,
    score FLOAT,
    urgency VARCHAR(20),
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Accorder les privilèges à l'utilisateur ferrari
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ferrari;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ferrari;

-- Message de confirmation
DO $$
BEGIN
    RAISE NOTICE '✅ Base de données Ferrari F1 initialisée avec succès';
END $$;
