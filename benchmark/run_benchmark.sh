#!/bin/bash

# ============================================================================
# FERRARI F1 IoT - Quick Benchmark Runner
# ============================================================================
# Script rapide pour lancer le benchmark complet

set -e

echo "🏎️  Ferrari F1 IoT Smart Pit-Stop - Quick Benchmark"
echo "=================================================="
echo ""

# Vérifier que Python est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi

# Aller dans le dossier benchmark
cd "$(dirname "$0")"

# Installer les dépendances si nécessaire
if [ ! -d "venv" ]; then
    echo "📦 Installation des dépendances..."
    python3 -m pip install -r requirements.txt --quiet
fi

echo "🚀 Lancement du benchmark..."
echo ""

# Lancer le benchmark
python3 run_tests.py

echo ""
echo "✅ Benchmark terminé!"
echo ""
echo "📄 Rapports générés:"
echo "  - docs/benchmarks.md (rapport Markdown)"
echo "  - docs/benchmark_results.json (résultats JSON)"
echo ""
echo "🏎️  Forza Ferrari! 🏎️"
