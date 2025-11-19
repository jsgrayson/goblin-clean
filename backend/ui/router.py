from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import psutil
import docker
import time

router = APIRouter()

templates = Jinja2Templates(directory="backend/ui/templates")
docker_client = docker.from_env()

@router.get("/ui", response_class=HTMLResponse)
async def ui_dashboard(request: Request):
    # ------------------------------
    # System Metrics
    # ------------------------------
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    # ------------------------------
    # Docker Container Status
    # ------------------------------
    containers = docker_client.containers.list(all=True)
    container_status = []
    for c in containers:
        container_status.append({
            "name": c.name,
            "status": c.status,
            "id": c.short_id
        })

    # ------------------------------
    # Agent Heartbeats
    # (from Prometheus / backend metrics system)
    # ------------------------------
    # This is placeholder — Phase 2 will read real metrics.
    agent_status = {
        "warden": "unknown",
        "tsm_brain": "unknown",
        "ah_runner": "unknown",
        "bank_runner": "unknown",
        "ml_worker": "unknown"
    }

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "cpu": cpu,
        "mem": mem,
        "disk": disk,
        "containers": container_status,
        "agent_status": agent_status,
        "timestamp": int(time.time())
    })

