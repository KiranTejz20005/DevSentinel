from datetime import datetime
from typing import List, Dict


def check_for_incidents() -> List[Dict[str, str]]:
    # Placeholder detection logic
    return [
        {
            "id": "placeholder-incident",
            "severity": "info",
            "detected_at": datetime.utcnow().isoformat() + "Z",
            "status": "pending",
        }
    ]


def detect_from_signal(signal: str) -> Dict[str, str]:
    # Stub for signal-based detection
    return {
        "id": f"signal-{hash(signal) % 10000}",
        "severity": "unknown",
        "detected_at": datetime.utcnow().isoformat() + "Z",
        "status": "pending",
    }
