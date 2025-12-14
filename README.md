# DevSentinel

AI-powered incident detection and automated code repair system using Google Gemini API.

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Add your GEMINI_API_KEY to .env
```

3. Run the server:
```bash
uvicorn devsentinel.services.api:app --reload --port 8000
```

4. Access:
- Backend API: http://localhost:8000
- Frontend Dashboard: http://localhost:3000 (run `python frontend/server.py`)
- API Docs: http://localhost:8000/docs

## Key Features

- 🤖 AI-powered incident analysis with Google Gemini
- 🔧 Automated code repair via Cline integration
- 📊 Real-time dashboard for incident tracking
- 🔄 Kestra workflow orchestration
- 🚀 Vercel deployment ready

## Environment Variables

Required in `.env`:
- `GEMINI_API_KEY` - Get from https://makersuite.google.com/app/apikey
- `GEMINI_MODEL` - Default: gemini-pro
- `GEMINI_TEMPERATURE` - Default: 0.7

Optional:
- `KESTRA_BASE_URL`, `KESTRA_API_TOKEN` - For workflow orchestration
- `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` - For deployment
