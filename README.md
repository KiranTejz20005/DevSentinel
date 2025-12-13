# DevSentinel

DevSentinel is an AI-driven incident management prototype that detects issues, summarizes impact, and can auto-apply fixes. It wires together Kestra (orchestration), Cline CLI (autonomous code edits), CodeRabbit (PR review), Oumi (RL training), and Vercel (deployment) to satisfy hackathon requirements.

## Structure
- `kestra/` Kestra flow definitions (AI Agent-based incident flow)
- `services/` Python services (API, detection, repair helpers)
- `cline_tasks/` Cline CLI automation tasks
- `oumi/` RL/reward configuration and functions
- `frontend/` Optional status UI (Next.js style)
- `.github/workflows/` CI/CD pipelines
- `requirements.txt` Python deps

## System architecture
- Monitoring & ingestion: logs/metrics feed incidents into Kestra (can be a dummy log generator while prototyping).
- Orchestration (Kestra): Kestra AI Agent summarizes incidents and decides next steps, optionally branching to sub-flows or scripts.
- Automated repair: If a code/config bug is detected, Cline CLI is invoked to modify the repo automatically (can be triggered by Kestra or run separately).
- Code review (CodeRabbit): Changes are pushed to GitHub; CodeRabbit reviews PRs and can propose one-click fixes.
- Model improvement (Oumi): Oumi trains an assistant via RL; custom reward functions score successful repairs, and `oumi train` runs experiments.
- UI & deploy (Vercel): A simple FastAPI/Next.js status surface is deployed to Vercel for the demo.

High-level flow: `Logs -> Kestra AI summary -> decision -> Cline code fix -> GitHub commit -> CodeRabbit review -> (optional Oumi RL retrain) -> redeploy on Vercel`.

## Quickstart
1. Create and activate a virtualenv.
2. `pip install -r requirements.txt`
3. Run the API: `uvicorn services.api:app --reload --port 8000`
4. Extend `kestra/incident_flow.yaml` with real tasks and secrets.

## Demo endpoints (mocked)
- `GET /health` basic check
- `GET /incidents` list mocked incidents (in-memory)
- `GET /actions` recent mock repair actions
- `POST /repair` with `{ "id": "incident-id" }` simulates a repair and returns a mock diff

## Devcontainer
- Open in GitHub Codespaces or VS Code Dev Containers; we ship `.devcontainer/devcontainer.json` with Python 3.11 and Node 18.

## Notes
- Place secrets in your runtime environment, not in repo.
- Replace placeholder logic before production use.
