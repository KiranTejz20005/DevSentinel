"""Kestra API client"""
import httpx
import logging
from typing import Dict, Any
from .config import settings

logger = logging.getLogger(__name__)

class KesteraClient:
    def __init__(self):
        self.headers = {"Content-Type": "application/json"}
        if settings.KESTRA_API_KEY:
            self.headers["Authorization"] = f"Bearer {settings.KESTRA_API_KEY}"
    
    async def trigger_incident_flow(self, incident_id: str, incident_data: Dict[str, Any]) -> str:
        url = f"{settings.KESTRA_URL}/api/v1/executions/{settings.KESTRA_NAMESPACE}/{settings.KESTRA_INCIDENT_FLOW_ID}"
        payload = {"inputs": {"incident_id": incident_id, "incident_data": incident_data}}
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(settings.KESTRA_TIMEOUT, connect=5.0)) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                response.raise_for_status()
                return response.json().get("id")
        except httpx.HTTPError as e:
            logger.error(f"Kestra error: {e}")
            raise
    
    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        url = f"{settings.KESTRA_URL}/api/v1/executions/{execution_id}"
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(settings.KESTRA_TIMEOUT, connect=5.0)) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Kestra status error: {e}")
            raise
    
    async def get_execution_logs(self, execution_id: str) -> str:
        url = f"{settings.KESTRA_URL}/api/v1/executions/{execution_id}/logs"
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(settings.KESTRA_TIMEOUT, connect=5.0)) as client:
                return (await client.get(url, headers=self.headers)).text
        except httpx.HTTPError as e:
            logger.error(f"Kestra logs error: {e}")
            raise
