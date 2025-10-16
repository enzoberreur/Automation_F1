# Sécurité & Conformité - Ferrari F1 Data Platform

Ce guide résume les contrôles de sécurité ajoutés à la plateforme pour couvrir le pilier "Security & Compliance" du barème.

## Authentification des flux télémétrie
- **API Key obligatoire** : le service `stream-processor` refuse tout message qui n'est pas accompagné d'une clé transmise dans l'en-tête `X-Api-Key`.
- **Configuration centralisée** : la clé et le nom d'en-tête sont fournis via les variables d'environnement `STREAM_PROCESSOR_API_KEY` et `STREAM_PROCESSOR_API_KEY_HEADER` partagées entre les conteneurs.
- **Protection par défaut** : un secret de développement est défini dans `docker-compose.yml` ; il doit être remplacé via l'environnement (`export STREAM_PROCESSOR_API_KEY=...`).

## Cloisonnement réseau Kubernetes
- **NetworkPolicy** : `k8s/networkpolicy.yaml` limite les flux entrants du stream processor aux seuls pods du simulateur, d'Airflow et des outils d'exploitation.
- **Egress minimal** : seuls PostgreSQL, Prometheus et Internet (443) restent accessibles pour l'émission de métriques et la résolution de dépendances.

## Observabilité des rejets de sécurité
- Chaque rejet d'authentification est tracé dans les logs du stream processor avec le nom de l'en-tête incriminé.
- Les dashboards Grafana peuvent être enrichis avec un panneau `rate` sur la métrique `ferrari_messages_received_total` pour corréler les drops.

## Bonnes pratiques recommandées
- **Rotation de secrets** : utilisez un gestionnaire de secrets (Vault, SSM) pour injecter la clé à chaud en production.
- **Transport chiffré** : placez Traefik ou Nginx Ingress Controller avec TLS devant le stream processor pour protéger les flux réseau.
- **Audit** : combinez les logs avec Loki ou Elastic afin de conserver la trace des requêtes refusées.

Ces mesures apportent un socle concret de conformité tout en restant simples à déployer dans un environnement pédagogique.
