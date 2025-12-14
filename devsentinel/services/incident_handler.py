"""
Business logic for incident processing
"""
from typing import List, Optional
from datetime import datetime
import logging

from .models import IncidentRequest, IncidentResponse, IncidentStatus
from .database import get_session, IncidentModel
from .kestra_client import KesteraClient
from .cline_runner import ClineRunner
from .gemini_client import gemini_client
from .config import settings

logger = logging.getLogger(__name__)


class IncidentHandler:
    """
    Handles incident lifecycle and coordination with external systems
    """
    
    def __init__(self):
        self.kestra_client = KesteraClient()
        self.cline_runner = ClineRunner()
    
    async def process_incident(self, incident: IncidentRequest) -> IncidentResponse:
        """
        Process a new incident through the resolution pipeline
        
        Args:
            incident: Incident request data
            
        Returns:
            IncidentResponse with processing details
        """
        logger.info(f"Processing new incident: {incident.title}")
        
        # Create incident record in database
        db_incident = await self._create_incident_record(incident)
        
        try:
            # Update status to analyzing
            db_incident = await self._update_incident_status(
                db_incident.id, 
                IncidentStatus.ANALYZING
            )
            
            # Generate AI analysis using Gemini
            try:
                analysis = await gemini_client.generate_incident_analysis(
                    title=incident.title,
                    description=incident.description,
                    severity=incident.severity.value,
                    context=incident.metadata
                )
                if analysis:
                    logger.info(f"Generated AI analysis for incident {db_incident.id}")
                    if db_incident.incident_metadata is None:
                        db_incident.incident_metadata = {}
                    db_incident.incident_metadata['ai_analysis'] = analysis
                    await self._save_incident(db_incident)
            except Exception as gemini_error:
                logger.warning(f"Gemini analysis unavailable: {str(gemini_error)}")
            
            # Try to trigger Kestra workflow for analysis
            try:
                execution_id = await self.kestra_client.trigger_incident_flow(
                    incident_id=db_incident.id,
                    incident_data=incident.model_dump()
                )
                db_incident.kestra_execution_id = execution_id
                await self._save_incident(db_incident)
            except Exception as kestra_error:
                logger.warning(f"Kestra integration unavailable: {str(kestra_error)}")
                # Continue processing even if Kestra is unavailable
            
            # Run Cline for automated repair (if configured)
            if settings.ENABLE_AUTO_REPAIR:
                await self._attempt_auto_repair(db_incident)
            else:
                # Mark as pending if auto-repair is disabled
                db_incident = await self._update_incident_status(
                    db_incident.id,
                    IncidentStatus.PENDING
                )
            
            return self._to_response(db_incident)
            
        except Exception as e:
            logger.error(f"Error processing incident {db_incident.id}: {str(e)}")
            db_incident = await self._update_incident_status(
                db_incident.id,
                IncidentStatus.FAILED
            )
            db_incident.resolution = f"Processing failed: {str(e)}"
            await self._save_incident(db_incident)
            raise
    
    async def get_incident(self, incident_id: str) -> Optional[IncidentResponse]:
        """
        Retrieve incident by ID
        
        Args:
            incident_id: Unique incident identifier
            
        Returns:
            IncidentResponse if found, None otherwise
        """
        session = get_session()
        try:
            incident = session.query(IncidentModel).filter(
                IncidentModel.id == incident_id
            ).first()
            
            if incident:
                return self._to_response(incident)
            return None
        finally:
            session.close()
    
    async def list_incidents(self, skip: int = 0, limit: int = 100) -> List[IncidentResponse]:
        """
        List incidents with pagination
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of IncidentResponse objects
        """
        session = get_session()
        try:
            incidents = session.query(IncidentModel).order_by(
                IncidentModel.created_at.desc()
            ).offset(skip).limit(limit).all()
            
            return [self._to_response(inc) for inc in incidents]
        finally:
            session.close()
    
    async def _create_incident_record(self, incident: IncidentRequest) -> IncidentModel:
        """Create incident record in database"""
        session = get_session()
        try:
            db_incident = IncidentModel(
                title=incident.title,
                description=incident.description,
                severity=incident.severity,
                status=IncidentStatus.PENDING,
                source=incident.source,
                incident_metadata=incident.metadata
            )
            session.add(db_incident)
            session.commit()
            session.refresh(db_incident)
            return db_incident
        finally:
            session.close()
    
    async def _update_incident_status(
        self, 
        incident_id: str, 
        status: IncidentStatus
    ) -> IncidentModel:
        """Update incident status"""
        session = get_session()
        try:
            incident = session.query(IncidentModel).filter(
                IncidentModel.id == incident_id
            ).first()
            
            if incident:
                incident.status = status
                incident.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(incident)
            return incident
        finally:
            session.close()
    
    async def _save_incident(self, incident: IncidentModel):
        """Save incident changes to database"""
        session = get_session()
        try:
            session.merge(incident)
            session.commit()
        finally:
            session.close()
    
    async def _attempt_auto_repair(self, incident: IncidentModel):
        """
        Attempt automated repair using Cline with Gemini AI suggestions
        """
        try:
            logger.info(f"Attempting auto-repair for incident {incident.id}")
            
            incident = await self._update_incident_status(
                incident.id,
                IncidentStatus.REPAIRING
            )
            
            # Get AI-powered resolution suggestions first
            resolution_suggestions = None
            try:
                resolution_suggestions = await gemini_client.suggest_resolution_steps(
                    title=incident.title,
                    description=incident.description,
                    error_details=incident.incident_metadata.get('error_details') if incident.incident_metadata else None
                )
                if resolution_suggestions:
                    logger.info(f"Generated resolution suggestions for incident {incident.id}")
                    if incident.incident_metadata is None:
                        incident.incident_metadata = {}
                    incident.incident_metadata['resolution_suggestions'] = resolution_suggestions
                    await self._save_incident(incident)
            except Exception as gemini_error:
                logger.warning(f"Failed to generate resolution suggestions: {str(gemini_error)}")
            
            repair_result = await self.cline_runner.execute_repair(
                incident_id=incident.id,
                description=incident.description,
                ai_suggestions=resolution_suggestions
            )
            
            if repair_result.get("success"):
                incident.status = IncidentStatus.RESOLVED
                incident.resolution = repair_result.get("resolution", "Auto-repaired successfully")
            else:
                incident.status = IncidentStatus.FAILED
                incident.resolution = f"Auto-repair failed: {repair_result.get('error')}"
            
            await self._save_incident(incident)
            
        except Exception as e:
            logger.error(f"Auto-repair failed for incident {incident.id}: {str(e)}")
    
    def _to_response(self, incident: IncidentModel) -> IncidentResponse:
        """Convert database model to response model"""
        return IncidentResponse(
            id=incident.id,
            title=incident.title,
            description=incident.description,
            severity=incident.severity,
            status=incident.status,
            source=incident.source,
            created_at=incident.created_at,
            updated_at=incident.updated_at,
            resolution=incident.resolution,
            kestra_execution_id=incident.kestra_execution_id,
            metadata=incident.incident_metadata
        )
