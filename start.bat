@echo off
echo Starting DevSentinel...
echo.
python -m uvicorn devsentinel.services.api:app --reload --port 8000
