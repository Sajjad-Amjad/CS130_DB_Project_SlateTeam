from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.session import Base

class Favorite(Base):
    __tablename__ = "favorites"
    
    favorite_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    gig_id = Column(Integer, ForeignKey("gigs.gig_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="favorites")
    gig = relationship("Gig", back_populates="favorites")
    
    # Table constraints
    __table_args__ = (
        # UniqueConstraint('user_id', 'gig_id', name='uq_user_gig_favorite'),
    )