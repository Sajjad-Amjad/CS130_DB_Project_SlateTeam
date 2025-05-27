from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator
import enum
import json

from app.database.session import Base
from app.models.base import TimeStampMixin

class JSONType(TypeDecorator):
    """Custom JSON type for SQL Server compatibility."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value

class UserRole(str, enum.Enum):
    BUYER = "buyer"
    SELLER = "seller"
    BOTH = "both"
    ADMIN = "admin"

class User(Base, TimeStampMixin):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    user_role = Column(String(20), nullable=False)
    full_name = Column(String(255), nullable=False)
    profile_picture = Column(String(1000), nullable=True)
    country = Column(String(100), nullable=True)
    language = Column(String(50), nullable=True)
    registration_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    seller_profile = relationship("SellerProfile", back_populates="user", uselist=False)
    orders_as_buyer = relationship("Order", foreign_keys="[Order.buyer_id]", back_populates="buyer")
    orders_as_seller = relationship("Order", foreign_keys="[Order.seller_id]", back_populates="seller")
    messages_sent = relationship("Message", foreign_keys="[Message.sender_id]", back_populates="sender")
    messages_received = relationship("Message", foreign_keys="[Message.recipient_id]", back_populates="recipient")
    reviews_given = relationship("Review", foreign_keys="[Review.reviewer_id]", back_populates="reviewer")
    reviews_received = relationship("Review", foreign_keys="[Review.reviewee_id]", back_populates="reviewee")
    notifications = relationship("Notification", back_populates="user")
    favorites = relationship("Favorite", back_populates="user")

class SellerProfile(Base, TimeStampMixin):
    __tablename__ = "seller_profiles"

    seller_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), unique=True, nullable=False)
    professional_title = Column(String(255), nullable=False)
    description = Column(String(4000), nullable=True)
    portfolio_links = Column(JSONType, nullable=True)  # Fixed: Use JSONType
    education = Column(String(1000), nullable=True)
    certifications = Column(String(1000), nullable=True)
    languages = Column(JSONType, nullable=True)  # Fixed: Use JSONType
    response_time = Column(Integer, nullable=True)  # Average in minutes
    completion_rate = Column(Integer, nullable=True)  # Percentage
    rating_average = Column(Integer, nullable=True)  # Derived from reviews
    total_earnings = Column(Integer, nullable=True)
    account_level = Column(String(20), nullable=False, default="new")  # new/level_1/level_2/top_rated
    personal_website = Column(String(255), nullable=True)
    social_media_links = Column(JSONType, nullable=True)  # Fixed: Use JSONType

    # Relationships
    user = relationship("User", back_populates="seller_profile")
    gigs = relationship("Gig", back_populates="seller")
    offers = relationship("Offer", back_populates="seller")
    seller_skills = relationship("SellerSkill", back_populates="seller")