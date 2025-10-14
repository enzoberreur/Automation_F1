#!/usr/bin/env python3
"""
Script de test Ferrari F1 rapide et personnalisable
Usage: python3 quick_test.py [durée_secondes] [messages_par_seconde]
"""

import sys
import yaml
import tempfile
import os
from pathlib import Path

def create_custom_config(duration=30, throughput=500):
    """Créer une configuration de test personnalisée"""
    
    # Charger la config par défaut
    config_path = Path(__file__).parent / 'config.yml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Modifier les scénarios de test
    config['test_scenarios'] = [{
        'throughput': throughput,
        'duration': duration, 
        'description': f"Test personnalisé {throughput} msg/s pendant {duration}s"
    }]
    
    # Créer fichier temporaire
    temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False)
    yaml.dump(config, temp_config, default_flow_style=False)
    temp_config.close()
    
    return temp_config.name

def main():
    """Point d'entrée"""
    duration = 30  # secondes par défaut
    throughput = 500  # msg/s par défaut
    
    # Parser les arguments
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except ValueError:
            print("❌ Durée invalide. Utilisation de 30s par défaut.")
    
    if len(sys.argv) > 2:
        try:
            throughput = int(sys.argv[2])
        except ValueError:
            print("❌ Throughput invalide. Utilisation de 500 msg/s par défaut.")
    
    print(f"🏎️  Ferrari F1 Test Personnalisé")
    print(f"⏱️  Durée: {duration} secondes")
    print(f"📊 Throughput cible: {throughput} msg/s")
    print("=" * 50)
    
    # Créer config temporaire
    temp_config_path = create_custom_config(duration, throughput)
    
    try:
        # Importer et lancer le benchmark
        import run_tests
        
        benchmark = run_tests.FerrariF1Benchmark(temp_config_path)
        results = benchmark.run_all_tests()
        
        # Afficher résumé
        print("\n" + "=" * 50)
        print("🏁 Test terminé!")
        print("=" * 50)
        
        if results:
            result = results[0]  # Premier (et seul) résultat
            print(f"✅ Réussi: {'Oui' if result.passed else 'Non'}")
            print(f"📈 Throughput réel: {result.throughput_real:.1f} msg/s")
            print(f"⚡ Latence P95: {result.latency.p95:.2f} ms")
            print(f"🧠 Taux succès: {result.success_rate:.1f}%")
            print(f"💾 CPU: {result.cpu_percent:.1f}%")
            print(f"🔍 Mémoire: {result.memory_mb:.0f} MB")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    finally:
        # Nettoyer fichier temporaire
        try:
            os.unlink(temp_config_path)
        except:
            pass

if __name__ == "__main__":
    main()