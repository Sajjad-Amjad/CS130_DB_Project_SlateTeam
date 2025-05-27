from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator

class OfferBase(BaseModel):
    buyer_id: int
    title: str
    description: str
    price: int
    delivery_time: int
    revision_count: int = 0
    expiry_days: Optional[int] = 7
    
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

class OfferCreate(OfferBase):
    pass

class OfferUpdate(BaseModel):
    status: str
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ['pending', 'accepted', 'rejected', 'expired']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v

class OfferOut(OfferBase):
    offer_id: int
    seller_id: int
    expiry_date: datetime
    status: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}