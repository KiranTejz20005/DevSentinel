from datetime import datetime
from typing import Dict

from services.detector import mark_resolved


def attempt_repair(incident_id: str) -> Dict[str, str]:
    """Simulate a repair step and return a mock diff for demo purposes."""
    notes = "Applied mock fix via Cline stub"
    resolved = mark_resolved(incident_id, notes)

    mock_diff = """diff --git a/services/example.py b/services/example.py
--- a/services/example.py
+++ b/services/example.py
@@
-# TODO: handle retry
+# Fixed retry logic to avoid dropping incidents
"""

    return {
        "incident_id": incident_id,
        "action": "mock_cline_fix",
        "status": "resolved",
        "resolved_at": resolved.get("resolved_at", datetime.utcnow().isoformat() + "Z"),
        "notes": notes,
        "diff": mock_diff,
    }
