from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator
from datetime import datetime
import json

from app.database.session import Base
from app.models.base import TimeStampMixin

class JSONType(TypeDecorator):
    """Custom JSON type for SQL Server compatibility."""
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value

class Order(Base, TimeStampMixin):
    __tablename__ = "orders"
    
    order_id = Column(Integer, primary_key=True, index=True)
    gig_id = Column(Integer, ForeignKey("gigs.gig_id"), nullable=False)
    package_id = Column(Integer, ForeignKey("gig_packages.package_id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    custom_offer_id = Column(Integer, ForeignKey("offers.offer_id"), nullable=True)
    requirements = Column(String(2000), nullable=True)
    price = Column(Integer, nullable=False)  # In cents
    delivery_time = Column(Integer, nullable=False)  # In days
    expected_delivery_date = Column(DateTime, nullable=False)
    actual_delivery_date = Column(DateTime, nullable=True)
    revision_count = Column(Integer, nullable=False)  # Total allowed
    revisions_used = Column(Integer, default=0)
    status = Column(String(20), nullable=False)  # pending/in_progress/delivered/completed/cancelled/disputed
    is_late = Column(Boolean, default=False)
    
    # Relationships
    gig = relationship("Gig", back_populates="orders")
    package = relationship("GigPackage", back_populates="orders")
    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="orders_as_buyer")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="orders_as_seller")
    custom_offer = relationship("Offer", back_populates="orders")
    deliveries = relationship("OrderDelivery", back_populates="order")
    revisions = relationship("OrderRevision", back_populates="order")
    review = relationship("Review", back_populates="order", uselist=False)
    payment = relationship("Payment", back_populates="order", uselist=False)

class OrderDelivery(Base):
    __tablename__ = "order_deliveries"
    
    delivery_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    message = Column(String(2000), nullable=True)
    files = Column(JSONType, nullable=True)  # Fixed: Use JSONType instead of String
    delivered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_final_delivery = Column(Boolean, default=False)
    
    # Relationships
    order = relationship("Order", back_populates="deliveries")

class OrderRevision(Base):
    __tablename__ = "order_revisions"
    
    revision_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    requested_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    request_message = Column(String(2000), nullable=False)
    request_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    response_message = Column(String(2000), nullable=True)
    response_date = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False)  # pending/accepted/rejected
    
    # Relationships
    order = relationship("Order", back_populates="revisions")
    requester = relationship("User", foreign_keys=[requested_by])