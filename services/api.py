from fastapi import FastAPI

from services.detector import check_for_incidents
from services.repair_utils import attempt_repair

app = FastAPI(title="DevSentinel API", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/incidents")
def incidents() -> dict:
    # Replace with real detection pipeline (metrics, logs, events)
    return {"incidents": check_for_incidents()}


@app.post("/repair")
def repair(incident: dict) -> dict:
    incident_id = incident.get("id") if isinstance(incident, dict) else None
    return {"result": attempt_repair(incident_id or "unknown")}
