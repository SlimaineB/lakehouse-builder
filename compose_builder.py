import yaml

def build_compose(selected, all_services):
    services = {}
    volumes = {}
    networks = {"lakehouse-net": {}}

    for svc_name, opts in selected.items():
        base = all_services[svc_name]
        image = f"{base['image']}:{opts['version']}"
        replicas = opts.get("replicas", base.get("replicas", 1))
        cluster = base.get("cluster", False)
        deps = base.get("dependencies", [])

        for i in range(replicas):
            name = f"{svc_name}-{i+1}" if cluster else svc_name
            resources = {
                "limits": {
                    "cpus": opts.get("cpu", "0.5"),
                    "memory": opts.get("mem", "512m")
                }
            }

            svc = {
                "image": image,
                "networks": ["lakehouse-net"],
                "environment": base.get("environment", {}),
                "deploy": {
                    "replicas": 1,
                    "resources": resources
                },
                "ports": base.get("ports", []) if (not cluster or i == 0) else []
            }
            if i == 0 and deps:
                svc["depends_on"] = deps
            services[name] = svc

        if svc_name == "minio":
            volumes["minio-data"] = {}
            services["minio"]["volumes"] = ["minio-data:/data"]

    compose = {
        "services": services,
        "volumes": volumes,
        "networks": networks
    }
    return compose

def load_services():
    with open("services.yaml") as f:
        return yaml.safe_load(f)
