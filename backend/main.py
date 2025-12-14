from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sheratan_core_adapter.mission_service import (
    create_mission_for_user,
    start_discovery_task,
    list_missions,
    get_mission_status,
    apply_agent_plan,
    create_standard_code_analysis_mission,  # Boss directive 4.1
)
from metrics_stream import router as metrics_router

app = FastAPI(title="Sheratan Backend PoC")

# CORS für WebSocket-Verbindungen vom Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:3000", 
        "http://localhost:3001",  # Sheratan React Dashboard
        "http://localhost:3002",  # Sheratan Dashboard alt
        "http://localhost:8000", 
        "http://localhost:8001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics Router registrieren
app.include_router(metrics_router)


class MissionCreate(BaseModel):
    user_id: str
    title: str
    description: str
    project_root: str | None = None

@app.get("/")
def root():
    return {"backend": "running"}

@app.get("/missions")
def get_missions():
    return list_missions()

@app.post("/missions/start")
def start_mission(data: MissionCreate):
    mission = create_mission_for_user(
        user_id=data.user_id,
        title=data.title,
        description=data.description,
    )

    if data.project_root:
        task_job = start_discovery_task(
            mission_id=mission["id"],
            project_root=data.project_root,
        )
    else:
        task_job = None

    return {
        "mission": mission,
        "task_job": task_job,
    }

@app.get("/missions/{mission_id}/status")
def mission_status(mission_id: str):
    """
    Aggregierte Sicht: Mission + Tasks + Jobs (inkl. Sync-Versuch).
    """
    return get_mission_status(mission_id)

@app.post("/missions/{mission_id}/apply_plan/{job_id}")
def apply_plan(mission_id: str, job_id: str):
    """
    Nimmt das Ergebnis eines agent_plan-Jobs und
    erzeugt daraus die definierten Followup-Tasks/Jobs.
    """
    return apply_agent_plan(mission_id, job_id)


# Boss Directive 4.1: Standard Code Analysis Mission
@app.post("/api/missions/standard-code-analysis")
def create_code_analysis():
    """
    One-click playground mission:
    Analyzes /workspace/project and proposes refactors.
    """
    return create_standard_code_analysis_mission(user_id="dashboard")
