"""
Main FastAPI application for DevSentinel
"""
from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from .models import IncidentRequest, IncidentResponse, IncidentStatus, IncidentSeverity
from .incident_handler import IncidentHandler
from .gemini_client import gemini_client
from .config import settings
from .database import get_session, IncidentModel

app = FastAPI(
    title="DevSentinel API",
    description="AI-powered incident detection and resolution system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

incident_handler = IncidentHandler()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "DevSentinel"}


@app.get("/api/stats")
async def get_stats():
    """Get incident statistics"""
    try:
        session = get_session()
        try:
            total = session.query(IncidentModel).count()
            resolved = session.query(IncidentModel).filter(
                IncidentModel.status == IncidentStatus.RESOLVED
            ).count()
            pending = session.query(IncidentModel).filter(
                IncidentModel.status == IncidentStatus.PENDING
            ).count()
            analyzing = session.query(IncidentModel).filter(
                IncidentModel.status == IncidentStatus.ANALYZING
            ).count()
            repairing = session.query(IncidentModel).filter(
                IncidentModel.status == IncidentStatus.REPAIRING
            ).count()
            failed = session.query(IncidentModel).filter(
                IncidentModel.status == IncidentStatus.FAILED
            ).count()
            actions = session.query(IncidentModel).filter(
                IncidentModel.status.in_([IncidentStatus.REPAIRING, IncidentStatus.RESOLVED])
            ).count()
            
            return {
                "total": total,
                "resolved": resolved,
                "pending": pending,
                "analyzing": analyzing,
                "repairing": repairing,
                "failed": failed,
                "active": pending + analyzing + repairing,
                "actions": actions
            }
        finally:
            session.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/incidents")
async def get_incidents_list(skip: int = 0, limit: int = 100):
    """List all incidents with pagination (frontend format)"""
    try:
        results = await incident_handler.list_incidents(skip=skip, limit=limit)
        return {
            "incidents": [
                {
                    "id": inc.id,
                    "severity": inc.severity.value,
                    "status": inc.status.value,
                    "summary": inc.title,
                    "description": inc.description,
                    "source": inc.source,
                    "detected_at": inc.created_at.isoformat() if inc.created_at else None,
                    "resolved_at": inc.updated_at.isoformat() if inc.status == IncidentStatus.RESOLVED and inc.updated_at else None,
                    "resolution": inc.resolution,
                    "kestra_execution_id": inc.kestra_execution_id
                }
                for inc in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/actions")
async def get_actions():
    """Get list of repair actions"""
    try:
        session = get_session()
        try:
            incidents = session.query(IncidentModel).filter(
                IncidentModel.status.in_([IncidentStatus.REPAIRING, IncidentStatus.RESOLVED])
            ).all()
            
            actions = []
            for inc in incidents:
                if inc.resolution:
                    actions.append({
                        "incident_id": inc.id,
                        "action": "auto-repair",
                        "status": "completed" if inc.status == IncidentStatus.RESOLVED else "in_progress",
                        "notes": inc.resolution,
                        "diff": None
                    })
            
            return {"actions": actions}
        finally:
            session.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/incidents")
async def create_incident_api(incident: IncidentRequest):
    """Create and process a new incident (frontend format)"""
    try:
        result = await incident_handler.process_incident(incident)
        return {
            "id": result.id,
            "severity": result.severity.value,
            "status": result.status.value,
            "summary": result.title,
            "detected_at": result.created_at.isoformat() if result.created_at else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/repair")
async def trigger_repair(data: Dict[str, Any] = Body(...)):
    """Trigger manual repair for an incident"""
    try:
        incident_id = data.get("incident_id")
        if not incident_id:
            raise HTTPException(status_code=400, detail="incident_id is required")
        
        incident = await incident_handler.get_incident(incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        # Trigger repair through incident handler
        session = get_session()
        try:
            db_incident = session.query(IncidentModel).filter(
                IncidentModel.id == incident_id
            ).first()
            
            if db_incident:
                await incident_handler._attempt_auto_repair(db_incident)
                return {"status": "repair_triggered", "incident_id": incident_id}
        finally:
            session.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/incidents/{incident_id}")
async def delete_incident(incident_id: str):
    """Delete an incident"""
    try:
        session = get_session()
        try:
            incident = session.query(IncidentModel).filter(
                IncidentModel.id == incident_id
            ).first()
            
            if not incident:
                raise HTTPException(status_code=404, detail="Incident not found")
            
            session.delete(incident)
            session.commit()
            return {"status": "deleted", "incident_id": incident_id}
        finally:
            session.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cline/fix-bug")
async def cline_fix_bug(data: Dict[str, Any] = Body(...)):
    """Trigger Cline to fix a bug"""
    try:
        description = data.get("description", "")
        files = data.get("files", [])
        
        # Create an incident for this bug fix
        incident = IncidentRequest(
            title="Manual Bug Fix Request",
            description=description,
            severity=IncidentSeverity.MEDIUM,
            source="manual_cline",
            metadata={"files": files}
        )
        
        result = await incident_handler.process_incident(incident)
        return {
            "status": "success",
            "incident_id": result.id,
            "message": "Bug fix initiated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rewards/test")
async def test_rewards():
    """Test endpoint for reward functions"""
    return {
        "status": "ok",
        "message": "Rewards system operational",
        "test_results": {
            "baseline_score": 0.75,
            "optimized_score": 0.92
        }
    }


@app.post("/incidents", response_model=IncidentResponse)
async def create_incident(incident: IncidentRequest):
    """
    Create and process a new incident
    """
    try:
        result = await incident_handler.process_incident(incident)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: str):
    """
    Retrieve incident details by ID
    """
    try:
        result = await incident_handler.get_incident(incident_id)
        if not result:
            raise HTTPException(status_code=404, detail="Incident not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/incidents", response_model=List[IncidentResponse])
async def list_incidents(skip: int = 0, limit: int = 100):
    """
    List all incidents with pagination
    """
    try:
        results = await incident_handler.list_incidents(skip=skip, limit=limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Gemini AI endpoints
class AnalyzeCodeRequest(BaseModel):
    """Request model for code analysis"""
    code: str
    language: str = "python"
    context: Optional[str] = None


class AIAnalysisResponse(BaseModel):
    """Response model for AI analysis"""
    analysis: Optional[str]
    available: bool


@app.post("/api/ai/analyze-code", response_model=AIAnalysisResponse)
async def analyze_code(request: AnalyzeCodeRequest):
    """
    Analyze code snippet using Gemini AI
    """
    try:
        if not gemini_client.is_available():
            return AIAnalysisResponse(
                analysis=None,
                available=False
            )
        
        analysis = await gemini_client.analyze_code_snippet(
            code=request.code,
            language=request.language,
            context=request.context
        )
        
        return AIAnalysisResponse(
            analysis=analysis,
            available=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai/status")
async def get_ai_status():
    """
    Check Gemini AI availability and configuration
    """
    try:
        is_available = gemini_client.is_available()
        return {
            "available": is_available,
            "model": settings.GEMINI_MODEL if is_available else None,
            "provider": "Google Gemini",
            "configured": bool(settings.GEMINI_API_KEY)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))