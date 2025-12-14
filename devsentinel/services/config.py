"""
Configuration settings for DevSentinel services
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # Application settings
    APP_NAME: str = "DevSentinel"
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./devsentinel.db"
    
    # Kestra settings
    KESTRA_URL: str = "http://localhost:8080"
    KESTRA_BASE_URL: str = "http://localhost:8080"
    KESTRA_API_KEY: str = ""
    KESTRA_API_TOKEN: str = ""
    KESTRA_NAMESPACE: str = "devsentinel"
    KESTRA_INCIDENT_FLOW_ID: str = "incident_flow"
    KESTRA_TIMEOUT: float = 30.0
    
    # Cline settings
    CLINE_CLI_PATH: str = "cline"
    CLINE_TIMEOUT: float = 300.0
    ENABLE_AUTO_REPAIR: bool = False
    CLINE_RUNTIME_DIR: Optional[str] = None
    
    # Workspace settings
    WORKSPACE_PATH: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    
    # Google Gemini API settings
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-pro-latest"
    GEMINI_TEMPERATURE: float = 0.7
    
    # Vercel settings (optional)
    VERCEL_TOKEN: str = ""
    VERCEL_ORG_ID: str = ""
    VERCEL_PROJECT_ID: str = ""
    
    # API settings
    UVICORN_WORKERS: int = 1
    API_BASE_URL: str = "http://localhost:8000"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }


# Create global settings instance
settings = Settings()
