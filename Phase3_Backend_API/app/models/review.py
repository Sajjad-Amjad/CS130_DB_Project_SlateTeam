from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.session import Base

class Review(Base):
    __tablename__ = "reviews"
    
    # ADD THIS LINE to disable implicit returning
    __table_args__ = {'implicit_returning': False}
    
    review_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), unique=True, nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    reviewee_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    communication_rating = Column(Integer, nullable=False)
    service_rating = Column(Integer, nullable=False)
    recommendation_rating = Column(Integer, nullable=False)
    overall_rating = Column(Float, nullable=False)  # Calculated average
    comment = Column(String(2000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    seller_response = Column(String(2000), nullable=True)
    seller_response_date = Column(DateTime, nullable=True)
    
    # Relationships
    order = relationship("Order", back_populates="review")
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="reviews_given")
    reviewee = relationship("User", foreign_keys=[reviewee_id], back_populates="reviews_received")