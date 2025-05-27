from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator
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

class Gig(Base, TimeStampMixin):
    __tablename__ = "gigs"
    
    # ADD THIS LINE to disable implicit returning
    __table_args__ = {'implicit_returning': False}
    
    gig_id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("seller_profiles.seller_id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    subcategory_id = Column(Integer, ForeignKey("categories.category_id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(String(4000), nullable=False)
    gig_metadata = Column(JSONType, nullable=True)
    search_tags = Column(String(500), nullable=True)
    requirements = Column(String(2000), nullable=True)
    faqs = Column(JSONType, nullable=True)
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    impression_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)
    conversion_rate = Column(Float, nullable=True)
    avg_response_time = Column(Integer, nullable=True)
    total_orders = Column(Integer, default=0)
    total_reviews = Column(Integer, default=0)
    ranking_score = Column(Float, default=0)
    
    # Relationships
    seller = relationship("SellerProfile", back_populates="gigs")
    category = relationship("Category", foreign_keys=[category_id], back_populates="gigs")
    subcategory = relationship("Category", foreign_keys=[subcategory_id])
    packages = relationship("GigPackage", back_populates="gig")
    images = relationship("GigImage", back_populates="gig")
    orders = relationship("Order", back_populates="gig")
    gig_tags = relationship("GigTag", back_populates="gig")
    favorites = relationship("Favorite", back_populates="gig")


class GigPackage(Base, TimeStampMixin):
    __tablename__ = "gig_packages"
    
    package_id = Column(Integer, primary_key=True, index=True)
    gig_id = Column(Integer, ForeignKey("gigs.gig_id"), nullable=False)
    package_type = Column(String(20), nullable=False)  # basic/standard/premium
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=False)
    price = Column(Integer, nullable=False)  # In cents
    delivery_time = Column(Integer, nullable=False)  # In days
    revision_count = Column(Integer, nullable=False, default=0)
    features = Column(JSONType, nullable=True)  # Fixed: Use JSONType
    is_active = Column(Boolean, default=True)
    
    # Relationships
    gig = relationship("Gig", back_populates="packages")
    orders = relationship("Order", back_populates="package")

class GigImage(Base):
    __tablename__ = "gig_images"
    
    image_id = Column(Integer, primary_key=True, index=True)
    gig_id = Column(Integer, ForeignKey("gigs.gig_id"), nullable=False)
    image_url = Column(String(1000), nullable=False)
    is_thumbnail = Column(Boolean, default=False)
    display_order = Column(Integer, nullable=True)
    created_at = Column(Float, nullable=False)
    
    # Relationships
    gig = relationship("Gig", back_populates="images")