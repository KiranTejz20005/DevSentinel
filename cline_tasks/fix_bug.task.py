"""Cline task: stub for auto bug fixing."""

MOCK_DIFF = """diff --git a/services/api.py b/services/api.py
--- a/services/api.py
+++ b/services/api.py
@@
-# TODO: add retry logic
+# Added retry logic to avoid missing incidents during transient failures
"""


def run(context: dict | None = None) -> dict:
    """Return a mock diff as if Cline applied a fix."""
    incident_id = (context or {}).get("incident_id", "placeholder-incident")
    return {
        "status": "completed",
        "message": "Applied mock fix via Cline stub",
        "incident_id": incident_id,
        "diff": MOCK_DIFF,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run(), indent=2))
