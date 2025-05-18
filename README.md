# Lakehouse Stack Builder

## Description
Application Streamlit pour déployer une stack Lakehouse complète avec clustering, monitoring et dépendances.

## Prérequis
- Docker & Docker Compose v2
- Python 3.8+
- Streamlit

## Installation
```
pip install -r requirements.txt
streamlit run app.py
```

## Utilisation
- Sélectionner les services à activer
- Choisir la version et le nombre de nœuds (replicas)
- Cliquer sur "Générer et lancer la stack"
- Accéder aux UI des services via les ports exposés

## Monitoring
- Prometheus scrape automatiquement node-exporter et cadvisor
- Grafana accessible sur `localhost:3000`

## Configuration
- Modifier `services.yaml` pour ajouter/modifier services et dépendances
- Configs spécifiques dans le dossier `configs/`
