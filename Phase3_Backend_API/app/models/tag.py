from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database.session import Base

class Tag(Base):
    __tablename__ = "tags"
    
    tag_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    frequency = Column(Integer, default=0)
    
    # Relationships
    gig_tags = relationship("GigTag", back_populates="tag")

class GigTag(Base):
    __tablename__ = "gig_tags"
    
    gig_tag_id = Column(Integer, primary_key=True, index=True)
    gig_id = Column(Integer, ForeignKey("gigs.gig_id"), nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.tag_id"), nullable=False)
    
    # Relationships
    gig = relationship("Gig", back_populates="gig_tags")
    tag = relationship("Tag", back_populates="gig_tags")
    
    # Table constraints
    __table_args__ = (
        # UniqueConstraint('gig_id', 'tag_id', name='uq_gig_tag'),
    )