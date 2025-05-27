from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.database.session import Base

class Skill(Base):
    __tablename__ = "skills"
    
    skill_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    category = relationship("Category", back_populates="skills")
    seller_skills = relationship("SellerSkill", back_populates="skill")

class SellerSkill(Base):
    __tablename__ = "seller_skills"
    
    seller_skill_id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("seller_profiles.seller_id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.skill_id"), nullable=False)
    experience_level = Column(String(20), nullable=True)  # beginner/intermediate/expert
    
    # Relationships
    seller = relationship("SellerProfile", back_populates="seller_skills")
    skill = relationship("Skill", back_populates="seller_skills")
    
    # Table constraints
    __table_args__ = (
        # UniqueConstraint('seller_id', 'skill_id', name='uq_seller_skill'),
    )