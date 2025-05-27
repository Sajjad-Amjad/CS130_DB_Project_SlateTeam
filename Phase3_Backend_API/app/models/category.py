from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.database.session import Base

class Category(Base):
    __tablename__ = "categories"
    
    category_id = Column(Integer, primary_key=True, index=True)
    parent_category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    icon = Column(String(255), nullable=True)
    display_order = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Self-referential relationship
    subcategories = relationship("Category", 
                                backref="parent_category",
                                remote_side=[category_id])
    
    # Relationships - only specify the primary relationship to avoid ambiguity
    gigs = relationship("Gig", foreign_keys="[Gig.category_id]", back_populates="category")
    skills = relationship("Skill", back_populates="category")