from datetime import datetime
from typing import Dict, List, Optional

# In-memory incident store for demo purposes.
INCIDENTS: List[Dict[str, str]] = [
    {
        "id": "placeholder-incident",
        "severity": "info",
        "detected_at": datetime.utcnow().isoformat() + "Z",
        "status": "pending",
        "summary": "Initial placeholder incident; replace with real signal ingestion.",
    }
]


def check_for_incidents() -> List[Dict[str, str]]:
    """Return the current list of incidents."""
    return INCIDENTS


def detect_from_signal(signal: str) -> Dict[str, str]:
    """Stub for signal-based detection that appends a new incident."""
    incident = {
        "id": f"signal-{hash(signal) % 10000}",
        "severity": "unknown",
        "detected_at": datetime.utcnow().isoformat() + "Z",
        "status": "pending",
        "summary": f"Detected signal: {signal[:80]}",
    }
    INCIDENTS.append(incident)
    return incident


def get_incident(incident_id: str) -> Optional[Dict[str, str]]:
    return next((i for i in INCIDENTS if i.get("id") == incident_id), None)


def mark_resolved(incident_id: str, notes: str) -> Dict[str, str]:
    incident = get_incident(incident_id)
    if not incident:
        incident = {
            "id": incident_id,
            "severity": "unknown",
            "detected_at": datetime.utcnow().isoformat() + "Z",
            "status": "pending",
            "summary": "Created during repair step.",
        }
        INCIDENTS.append(incident)

    incident.update({"status": "resolved", "resolved_at": datetime.utcnow().isoformat() + "Z", "notes": notes})
    return incident
