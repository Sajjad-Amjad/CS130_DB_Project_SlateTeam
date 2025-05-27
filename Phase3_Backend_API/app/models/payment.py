from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.session import Base

class Payment(Base):
    __tablename__ = "payments"
    
    payment_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    amount = Column(Integer, nullable=False)  # In cents
    platform_fee = Column(Integer, nullable=False)  # In cents
    seller_amount = Column(Integer, nullable=False)  # In cents
    currency = Column(String(10), default="USD", nullable=False)
    payment_method = Column(String(50), nullable=False)
    transaction_id = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False)  # pending/completed/refunded
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="payment")