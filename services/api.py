from typing import Dict, List

from fastapi import FastAPI, HTTPException

from services.detector import check_for_incidents, get_incident
from services.repair_utils import attempt_repair

app = FastAPI(title="DevSentinel API", version="0.1.0")

# In-memory list of recent actions for demo observability.
ACTIONS: List[Dict[str, str]] = []


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/incidents")
def incidents() -> dict:
    return {"incidents": check_for_incidents()}


@app.get("/incidents/{incident_id}")
def incident_detail(incident_id: str) -> dict:
    incident = get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"incident": incident}


@app.get("/actions")
def actions() -> dict:
    return {"actions": ACTIONS[-10:][::-1]}  # return last 10, newest first


@app.post("/repair")
def repair(incident: dict) -> dict:
    incident_id = incident.get("id") if isinstance(incident, dict) else None
    if not incident_id:
        raise HTTPException(status_code=400, detail="Missing incident id")

    result = attempt_repair(incident_id)
    ACTIONS.append({
        "incident_id": incident_id,
        "action": result.get("action", "repair"),
        "status": result.get("status", "unknown"),
        "diff": result.get("diff", ""),
        "notes": result.get("notes", ""),
    })
    return {"result": result}
