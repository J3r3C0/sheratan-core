# backend/sheratan_core_adapter/mission_service.py

from __future__ import annotations

from typing import Any

from .client import core_get, core_post


def create_mission_for_user(
    user_id: str,
    title: str,
    description: str,
    max_iterations: int = 10,
) -> dict[str, Any]:
    payload = {
        "title": title,
        "description": description,
        "metadata": {
            "created_by": user_id,
            "max_iterations": max_iterations,
        },
        "tags": ["workspace", f"user:{user_id}"],
    }
    return core_post("/api/missions", payload)


def list_missions() -> list[dict[str, Any]]:
    return core_get("/api/missions", {})


def dispatch_job(job_id: str) -> dict[str, Any]:
    """
    Kleiner Helper, um einen Job im Core zu dispatchen.
    """
    return core_post(f"/api/jobs/{job_id}/dispatch", {})


def start_discovery_task(mission_id: str, project_root: str) -> dict[str, Any]:
    """
    Erzeugt einen einfachen list_files-Task als initiale "Discovery".
    """
    task_payload = {
        "name": "project_discovery",
        "description": f"Project discovery for {project_root}",
        "kind": "list_files",
        "params": {
            "root": project_root,
            "patterns": ["*.py"],
        },
    }

    task = core_post(f"/api/missions/{mission_id}/tasks", task_payload)

    job_payload = {
        "payload": {
            "trigger": "initial",
        }
    }
    job = core_post(f"/api/tasks/{task['id']}/jobs", job_payload)

    dispatch_job(job["id"])

    return {
        "task": task,
        "job": job,
    }


def sync_mission_jobs(mission_status: dict[str, Any]) -> None:
    """
    Optionale Hilfe: alle Jobs der Mission einmal syncen,
    damit neue Resultate vom Worker reingezogen werden.
    """
    jobs = mission_status.get("jobs") or []
    for job in jobs:
        job_id = job.get("id")
        if not job_id:
            continue
        try:
            core_post(f"/api/jobs/{job_id}/sync", {})
        except Exception:
            # Sync-Fehler sind hier nicht kritisch
            continue


def get_mission_status(mission_id: str) -> dict[str, Any]:
    """
    Aggregierte Sicht: Mission + Tasks + Jobs.
    Vorher wird ein Sync versucht.
    """
    status = core_get(f"/api/missions/{mission_id}/status", {})
    # optional: einmal Jobs syncen und dann Status nochmal holen
    sync_mission_jobs(status)
    status = core_get(f"/api/missions/{mission_id}/status", {})
    return status


def sync_job(job_id: str) -> dict[str, Any]:
    """
    Synchronisiert ein Job-Result vom Worker (webrelay_in).
    Ruft den Core-Endpunkt /api/jobs/{job_id}/sync auf.
    """
    return core_post(f"/api/jobs/{job_id}/sync", {})


def apply_agent_plan(mission_id: str, job_id: str) -> dict[str, Any]:
    """
    Liest das Result eines agent_plan-Jobs (create_followup_jobs)
    und erzeugt daraus:
      - neue Tasks
      - neue Jobs
      - dispatcht Jobs mit auto_dispatch = true
      
    Erwartet LCP Format mit 'kind' statt 'task'.
    """
    sync_job(job_id)
    job = core_get(f"/api/jobs/{job_id}", {})

    result = job.get("result") or {}
    if result.get("action") != "create_followup_jobs":
        return {
            "ok": False,
            "error": f"job {job_id} has no create_followup_jobs result",
            "action": result.get("action"),
        }

    new_jobs_spec = result.get("new_jobs", [])
    created: list[dict] = []

    for spec in new_jobs_spec:
        # LCP Definition Format: {"name": "...", "kind": "...", "params": {...}, "auto_dispatch": bool}
        kind = spec.get("kind")
        if not kind:
            continue

        task_payload = {
            "name": spec.get("name") or f"Agent job: {kind}",
            "description": spec.get("description") or "",
            "kind": kind,
            "params": spec.get("params") or {},
        }

        # Task anlegen
        task = core_post(f"/api/missions/{mission_id}/tasks", task_payload)

        # Job anlegen
        job_payload = {"payload": spec.get("params") or {}}
        job2 = core_post(f"/api/tasks/{task['id']}/jobs", job_payload)

        # auto_dispatch beachten (default: false laut LCP Definition)
        auto = spec.get("auto_dispatch", False)
        if auto:
            dispatch_job(job2["id"])

        created.append(
            {
                "task": task,
                "job": job2,
                "auto_dispatched": auto,
            }
        )

    return {
        "ok": True,
        "commentary": result.get("commentary"),
        "created": created,
    }


# ------------------------------------------------------------------ #
# Boss Directive 4.1: Standard Playground Mission
# ------------------------------------------------------------------ #
def create_standard_code_analysis_mission(user_id: str = "local") -> dict[str, Any]:
    """Create a standard code analysis mission for /workspace/project.
    
    Boss Directive 4.1: Developer playground mission that can be started
    with one click from the dashboard.
    
    Args:
        user_id: User identifier
        
    Returns:
        Mission + Task creation response
    """
    title = "Analyze /workspace/project and propose refactors"
    description = (
        "List all Python files in /workspace/project, summarize their purpose, "
        "and propose 3 concrete refactor tasks."
    )

    # Create mission
    mission = create_mission_for_user(
        user_id=user_id,
        title=title,
        description=description,
        max_iterations=6,
    )

    mission_id = mission["id"]

    # Create initial agent_plan task
    task_payload = {
        "name": "Initial codebase analysis",
        "description": "Let the agent inspect the codebase and plan followup jobs.",
        "kind": "agent_plan",
        "params": {
            "user_prompt": "Analyze /workspace/project and create a plan",
            "project_root": "/workspace/project"
        },
    }

    task = core_post(f"/api/missions/{mission_id}/tasks", task_payload)

    # Create job for the task - MUST include task structure for worker!
    job_payload = {
        "payload": {
            "task": {
                "kind": "agent_plan",
                "params": task_payload["params"]
            },
            "params": task_payload["params"]
        }
    }
    job = core_post(f"/api/tasks/{task['id']}/jobs", job_payload)

    # Auto-dispatch
    dispatch_job(job["id"])

    return {
        "mission": mission,
        "task": task,
        "job": job,
    }
