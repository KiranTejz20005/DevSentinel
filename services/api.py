from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from services.detector import check_for_incidents, detect_from_signal, get_incident
from services.repair_utils import attempt_repair

app = FastAPI(title="DevSentinel API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.post("/incidents")
def create_incident(payload: dict) -> dict:
    signal = payload.get("signal") if isinstance(payload, dict) else None
    if not signal:
        raise HTTPException(status_code=400, detail="Missing signal text")
    incident = detect_from_signal(signal)
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
