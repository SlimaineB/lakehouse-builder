import pandas as pd
import streamlit as st
from compose_builder import build_compose, load_services
import yaml
import subprocess
import os

services_urls = {
    "superset": "http://localhost:8088",
    "clickhouse": "http://localhost:8123",
    "minio": "http://localhost:9000",
    "grafana": "http://localhost:3000",
    "prometheus": "http://localhost:9090",
    "spark": "http://localhost:4040",
    "trino": "http://localhost:8080",
    "ignite": "http://localhost:8081",
    "yarn": "http://localhost:8088",
}

def run_command_streamed(cmd):
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

def get_container_status(container_name):
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Status}}", container_name],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "absent"

def load_df(services):
    rows = []
    for svc, conf in services.items():
        status = get_container_status(svc)
        url = services_urls.get(svc, "")
        rows.append({
            "Activer": False,
            "Service": svc,
            "Version": conf["default_version"],
            "CPU": "0.5",
            "RAM": "512m",
            "Replicas": conf.get("replicas", 1),
            "Status": status,
            "URL": url,
        })
    return pd.DataFrame(rows)

st.title("🧱 Lakehouse Stack Builder")
st.markdown("Configurez votre stack analytique et voyez le status des services.")

services = load_services()

# Gestion du compteur pour refresh manuel
if "refresh_counter" not in st.session_state:
    st.session_state["refresh_counter"] = 0

# Recharge les données à chaque incrément du compteur (bouton refresh)
df = load_df(services)

edited = st.data_editor(df, use_container_width=True, num_rows="fixed")

if st.button("🔄 Rafraîchir le statut des services"):
    st.session_state["refresh_counter"] += 1
    st.experimental_rerun = None  # supprime l’appel erroné si présent

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
        missing_dependencies = []
        for svc in selected:
            declared_deps = services[svc].get("depends_on", [])
            for dep in declared_deps:
                if dep not in selected:
                    missing_dependencies.append((svc, dep))
        if missing_dependencies:
            st.error("❌ Dépendances manquantes :")
            for svc, dep in missing_dependencies:
                st.markdown(f"- `{svc}` dépend de `{dep}`, qui n'est pas activé.")
            st.stop()

        if os.path.exists("docker-compose.generated.yaml"):
            st.info("🧹 Nettoyage de l'ancienne stack...")
            run_command_streamed([
                "docker", "compose", "-f", "docker-compose.generated.yaml",
                "down", "--remove-orphans", "--volumes"
            ])

        st.info("🛠️ Génération du fichier docker-compose...")
        compose_yaml = build_compose(selected, services)
        with open("docker-compose.generated.yaml", "w") as f:
            yaml.dump(compose_yaml, f)
        st.success("✅ Fichier docker-compose.generated.yaml généré.")

        st.markdown("---")
        st.subheader("🚀 Lancement de la stack")
        code, output = run_command_streamed([
            "docker", "compose", "-f", "docker-compose.generated.yaml", "up", "-d"
        ])

        if code == 0:
            st.success("✅ Stack lancée avec succès.")
            st.balloons()

            st.markdown("### 🔗 Accès aux services")
            for svc in selected:
                url = services_urls.get(svc)
                if url:
                    st.markdown(f"- [{svc}]({url})")
        else:
            st.error("❌ Erreur lors du lancement.")
            st.code(output, language="bash")
