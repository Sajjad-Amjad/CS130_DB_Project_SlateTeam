from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, field_validator

# Gig Schemas
class GigBase(BaseModel):
    title: str
    description: str
    category_id: int
    subcategory_id: Optional[int] = None
    gig_metadata: Optional[Dict[str, Any]] = None
    search_tags: Optional[str] = None
    requirements: Optional[str] = None
    faqs: Optional[Dict[str, Any]] = None

class GigCreate(GigBase):
    pass

class GigUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    gig_metadata: Optional[Dict[str, Any]] = None
    search_tags: Optional[str] = None
    requirements: Optional[str] = None
    faqs: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class GigOut(GigBase):
    gig_id: int
    seller_id: int
    is_featured: bool
    is_active: bool
    impression_count: int
    click_count: int
    conversion_rate: Optional[float] = None
    avg_response_time: Optional[int] = None
    total_orders: int
    total_reviews: int
    ranking_score: float
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}

# Gig Package Schemas
class GigPackageBase(BaseModel):
    package_type: str
    title: str
    description: str
    price: int
    delivery_time: int
    revision_count: int
    features: Optional[Dict[str, Any]] = None

    @field_validator('package_type')
    @classmethod
    def validate_package_type(cls, v):
        if v not in ['basic', 'standard', 'premium']:
            raise ValueError('Package type must be basic, standard, or premium')
        return v

    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return v

    @field_validator('delivery_time')
    @classmethod
    def validate_delivery_time(cls, v):
        if v <= 0:
            raise ValueError('Delivery time must be greater than 0')
        return v

class GigPackageCreate(GigPackageBase):
    pass

class GigPackageUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    delivery_time: Optional[int] = None
    revision_count: Optional[int] = None
    features: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class GigPackageOut(GigPackageBase):
    package_id: int
    gig_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}

# Gig Image Schemas
class GigImageBase(BaseModel):
    image_url: str
    is_thumbnail: bool = False
    display_order: Optional[int] = None

class GigImageCreate(GigImageBase):
    pass

class GigImageOut(GigImageBase):
    image_id: int
    gig_id: int
    created_at: float
    
    model_config = {"from_attributes": True}