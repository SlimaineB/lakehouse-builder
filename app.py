import pandas as pd
import streamlit as st
from compose_builder import build_compose, load_services
import yaml
import subprocess
import os

# Fonction pour exécuter des commandes shell avec affichage en live
def run_command(cmd):
    st.write(f"📦 Lancement de : `{ ' '.join(cmd) }`")
    output_placeholder = st.empty()
    full_output = ""

    with st.spinner("⏳ En cours..."):
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in iter(process.stdout.readline, ""):
            if line:
                full_output += line
                output_placeholder.code(full_output, language="bash")
        process.stdout.close()
        process.wait()
    return process.returncode, full_output

# Chargement des services disponibles
services = load_services()

# Préparation du tableau avec les valeurs par défaut
rows = []
for svc, conf in services.items():
    rows.append({
        "Activer": False,
        "Service": svc,
        "Version": conf["default_version"],
        "CPU": "0.5",
        "RAM": "512m",
        "Replicas": conf.get("replicas", 1)
    })

df = pd.DataFrame(rows)

st.title("🧱 Lakehouse Stack Builder")
st.markdown("Configurez votre stack analytique en sélectionnant les composants et leurs ressources.")

# Éditeur interactif
edited = st.data_editor(df, use_container_width=True, num_rows="fixed")

# Bouton de génération
if st.button("🚀 Générer et lancer la stack"):
    selected = {}
    for _, row in edited.iterrows():
        if row["Activer"]:
            selected[row["Service"]] = {
                "version": row["Version"],
                "cpu": row["CPU"],
                "mem": row["RAM"],
                "replicas": int(row["Replicas"])
            }
    
    if not selected:
        st.warning("⚠️ Aucun service sélectionné.")
    else:
        # Nettoyage de la stack précédente
        if os.path.exists("docker-compose.generated.yaml"):
            st.info("🧹 Nettoyage de l'ancienne stack...")
            run_command(["docker", "compose", "-f", "docker-compose.generated.yaml", "down", "--remove-orphans", "--volumes"])

        # Génération du fichier Compose
        st.info("🛠️ Génération du fichier docker-compose...")
        compose_yaml = build_compose(selected, services)
        with open("docker-compose.generated.yaml", "w") as f:
            yaml.dump(compose_yaml, f)
        st.success("✅ Fichier docker-compose.generated.yaml généré.")

        # Lancement de la stack
        st.markdown("---")
        st.subheader("🚀 Lancement de la stack")
        code, output = run_command(["docker", "compose", "-f", "docker-compose.generated.yaml", "up", "-d"])
        
        if code == 0:
            st.success("✅ Stack lancée avec succès.")
            st.balloons()
        else:
            st.error("❌ Une erreur est survenue lors du lancement.")
            st.code(output, language="bash")
