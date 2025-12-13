# DevSentinel

Skeleton project for incident detection, automated repair, and RL-driven reward tuning. Folders are pre-stubbed so you can plug in your own logic.

## Structure
- `kestra/` Kestra flow definitions (AI Agent-based incident flow)
- `services/` Python services (API, detection, repair helpers)
- `cline_tasks/` Cline CLI automation tasks
- `oumi/` RL/reward configuration and functions
- `frontend/` Optional status UI (Next.js style)
- `.github/workflows/` CI/CD pipelines
- `requirements.txt` Python deps

## Quickstart
1. Create and activate a virtualenv.
2. `pip install -r requirements.txt`
3. Run the API: `uvicorn services.api:app --reload --port 8000`
4. Extend `kestra/incident_flow.yaml` with real tasks and secrets.

## Notes
- Place secrets in your runtime environment, not in repo.
- Replace placeholder logic before production use.
