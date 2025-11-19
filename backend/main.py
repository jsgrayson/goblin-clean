from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ---- Backend Core Application ----
# Import backend service logic (if needed)
from backend.app.main import app as core_app

# ---- UI Routers ----
from backend.ui.router import router as ui_router
from backend.ui.actions_router import router as actions_router
from backend.ui.status_api import router as status_router
from backend.ui.logs_router import router as logs_router
from backend.ui.config_router import router as config_router

# ---- Agent Import (Vertical Slice Feature) ----
try:
    from agents import tsm_brain_agent
except ImportError:
    tsm_brain_agent = None

# -------------------------------------------------
# Create FastAPI App
# -------------------------------------------------
app = FastAPI(title="Goblin Backend")

# -------------------------------------------------
# CORS (allow UI requests safely)
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # You may lock this down later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Mount Core Backend (agents / ML / tasks)
# -------------------------------------------------
app.mount("/backend", core_app)

# -------------------------------------------------
# Mount UI Routers
# -------------------------------------------------
app.include_router(ui_router)          # HTML pages + static files
app.include_router(actions_router)     # Start/stop/restart agents
app.include_router(status_router)      # CPU/mem/disk + container status
app.include_router(logs_router)        # Log viewer (Step 5)
app.include_router(config_router)

# -------------------------------------------------
# Root endpoint
# -------------------------------------------------
@app.get("/")
async def root():
    return {"status": "ok", "message": "Goblin backend running"}

# -------------------------------------------------
# NEW: TSM Brain Agent Endpoint (Vertical Slice)
# -------------------------------------------------
@app.post("/run_tsm_brain")
async def run_tsm_brain():
    if tsm_brain_agent:
        result = tsm_brain_agent.run()
        return {"result": result}
    else:
        return {"result": "TSM Brain agent module not found"}

# -------------------------------------------------
# Optional: Uvicorn Runtime (only used if run directly)
# -------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
