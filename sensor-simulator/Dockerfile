FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY main.py .

# Configuration par défaut
ENV SIMULATION_MODE=championship \
    CAR_ID=Ferrari-F1-75 \
    TEAM_NAME=Scuderia_Ferrari_HP \
    DRIVER=Charles_Leclerc \
    CAR_MODEL=SF-24 \
    CAR_NUMBER=16 \
    TARGET_THROUGHPUT_PER_CAR=250 \
    HTTP_ENDPOINT=http://stream-processor:8001/telemetry

# Point d'entrée
CMD ["python", "main.py"]
