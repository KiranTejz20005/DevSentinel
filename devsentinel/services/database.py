"""
Database connection and ORM setup
"""
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import Generator
import uuid

from .config import settings
from .models import IncidentSeverity, IncidentStatus

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


class IncidentModel(Base):
    """SQLAlchemy model for incidents"""
    __tablename__ = "incidents"
    
    id = Column(String, primary_key=True, default=lambda: f"inc_{uuid.uuid4().hex[:12]}")
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    severity = Column(SQLEnum(IncidentSeverity), nullable=False)
    status = Column(SQLEnum(IncidentStatus), nullable=False, default=IncidentStatus.PENDING)
    source = Column(String, nullable=False)
    resolution = Column(String, nullable=True)
    kestra_execution_id = Column(String, nullable=True)
    incident_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables
    """
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    """
    Get a database session
    """
    return SessionLocal()
