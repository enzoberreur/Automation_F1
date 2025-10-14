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
ENV TELEMETRY_MODE=http \
    CAR_ID=Ferrari-F1-75 \
    DRIVER=Charles_Leclerc \
    TARGET_THROUGHPUT=1500 \
    HTTP_ENDPOINT=http://stream-processor:8001/telemetry

# Point d'entrée
CMD ["python", "main.py"]
