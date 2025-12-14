"""
Pydantic models for request/response handling
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class IncidentSeverity(str, Enum):
    """Incident severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    """Incident processing status"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    REPAIRING = "repairing"
    RESOLVED = "resolved"
    FAILED = "failed"


class IncidentRequest(BaseModel):
    """Request model for creating an incident"""
    title: str = Field(..., description="Incident title")
    description: str = Field(..., description="Detailed incident description")
    severity: IncidentSeverity = Field(default=IncidentSeverity.MEDIUM)
    source: str = Field(..., description="Source system/service")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "API endpoint returning 500 errors",
                "description": "The /api/users endpoint is throwing server errors",
                "severity": "high",
                "source": "monitoring-system",
                "metadata": {"error_count": 150, "affected_users": 25}
            }
        }
    }


class IncidentResponse(BaseModel):
    """Response model for incident data"""
    id: str = Field(..., description="Unique incident identifier")
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    source: str
    created_at: datetime
    updated_at: datetime
    resolution: Optional[str] = Field(default=None, description="Resolution details")
    kestra_execution_id: Optional[str] = Field(default=None, description="Kestra workflow execution ID")
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "inc_12345",
                "title": "API endpoint returning 500 errors",
                "description": "The /api/users endpoint is throwing server errors",
                "severity": "high",
                "status": "resolved",
                "source": "monitoring-system",
                "created_at": "2025-12-14T10:30:00Z",
                "updated_at": "2025-12-14T10:35:00Z",
                "resolution": "Fixed null pointer exception",
                "kestra_execution_id": "exec_67890",
                "metadata": {}
            }
        }
    }


class KesteraFlowRequest(BaseModel):
    """Request model for triggering Kestra workflows"""
    flow_id: str = Field(..., description="Kestra flow identifier")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Flow input parameters")


class KesteraFlowResponse(BaseModel):
    """Response model for Kestra workflow execution"""
    execution_id: str = Field(..., description="Execution identifier")
    status: str = Field(..., description="Execution status")
    flow_id: str
    created_at: datetime
