from sqlalchemy import Column, DateTime, func
from datetime import datetime

from app.database.session import Base

class TimeStampMixin:
    """Timestamp mixin for SQLAlchemy models"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)