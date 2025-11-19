from fastapi import APIRouter
from prometheus_client.parser import text_string_to_metric_families
import requests
import psutil
import docker

router = APIRouter()
docker_client = docker.from_env()

PROM_URL = "http://localhost:8000/status/metrics"

def get_prom_metrics():
    metrics = {}
    try:
        raw = requests.get(PROM_URL, timeout=1).text
        for family in text_string_to_metric_families(raw):
            for sample in family.samples:
                metrics[sample.name] = sample.value
    except:
        pass
    return metrics

@router.get("/ui/status")
async def ui_status():
    prom = get_prom_metrics()

    # Grab agent heartbeat timestamps
    agent_heartbeats = {
        "warden":     prom.get("goblin_agent_heartbeat_warden", None),
        "tsm_brain":  prom.get("goblin_agent_heartbeat_tsm_brain", None),
        "ah_runner":  prom.get("goblin_agent_heartbeat_ah_runner", None),
        "bank_runner":prom.get("goblin_agent_heartbeat_bank_runner", None),
        "ml_worker":  prom.get("goblin_agent_heartbeat_ml_worker", None),
    }

    # Convert timestamps into status colors
    now = psutil.boot_time() + (psutil.boot_time() - psutil.boot_time())  # hack for monotonic

    agent_status = {}
    for agent, ts in agent_heartbeats.items():
        if ts is None:
            agent_status[agent] = "red"
        else:
            diff = time.time() - ts
            if diff < 30:
                agent_status[agent] = "green"
            elif diff < 60:
                agent_status[agent] = "yellow"
            else:
                agent_status[agent] = "red"

    # System metrics
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    # Docker containers
    try:
        containers = docker_client.containers.list(all=True)
        c_stats = [
            {"name": c.name, "status": c.status}
            for c in containers
        ]
    except:
        c_stats = []

    return {
        "cpu": cpu,
        "mem": mem,
        "disk": disk,
        "agents": agent_status,
        "containers": c_stats
    }

