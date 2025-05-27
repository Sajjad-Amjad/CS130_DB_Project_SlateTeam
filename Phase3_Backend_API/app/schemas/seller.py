from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

# Base SellerProfile Schema
class SellerProfileBase(BaseModel):
    professional_title: str
    description: Optional[str] = None
    portfolio_links: Optional[Dict[str, str]] = None
    education: Optional[str] = None
    certifications: Optional[str] = None
    languages: Optional[List[str]] = None
    personal_website: Optional[str] = None
    social_media_links: Optional[Dict[str, str]] = None

# Schema for creating a seller profile
class SellerProfileCreate(SellerProfileBase):
    pass

# Schema for seller profile output
class SellerProfileOut(SellerProfileBase):
    seller_id: int
    user_id: int
    response_time: Optional[int] = None
    completion_rate: Optional[int] = None
    rating_average: Optional[float] = None
    total_earnings: Optional[int] = None
    account_level: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}

# Schema for updating a seller profile
class SellerProfileUpdate(BaseModel):
    professional_title: Optional[str] = None
    description: Optional[str] = None
    portfolio_links: Optional[Dict[str, str]] = None
    education: Optional[str] = None
    certifications: Optional[str] = None
    languages: Optional[List[str]] = None
    personal_website: Optional[str] = None
    social_media_links: Optional[Dict[str, str]] = None
    
    model_config = {"from_attributes": True}