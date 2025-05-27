from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.session import Base
from app.models.base import TimeStampMixin

class Offer(Base, TimeStampMixin):
    __tablename__ = "offers"
    
    # ADD THIS LINE to disable implicit returning
    __table_args__ = {'implicit_returning': False}
    
    offer_id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("seller_profiles.seller_id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(2000), nullable=False)
    price = Column(Integer, nullable=False)  # In cents
    delivery_time = Column(Integer, nullable=False)  # In days
    revision_count = Column(Integer, nullable=False, default=0)
    expiry_date = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False)  # pending/accepted/rejected/expired
    
    # Relationships
    seller = relationship("SellerProfile", back_populates="offers")
    buyer = relationship("User", foreign_keys=[buyer_id])
    orders = relationship("Order", back_populates="custom_offer")