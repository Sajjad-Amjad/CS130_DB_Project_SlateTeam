from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, field_validator

# Order Schemas
class OrderBase(BaseModel):
    gig_id: int
    package_id: int
    requirements: Optional[str] = None

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    status: str
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ['pending', 'in_progress', 'delivered', 'completed', 'cancelled', 'disputed']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v

class OrderOut(OrderBase):
    order_id: int
    buyer_id: int
    seller_id: int
    custom_offer_id: Optional[int] = None
    price: int
    delivery_time: int
    expected_delivery_date: datetime
    actual_delivery_date: Optional[datetime] = None
    revision_count: int
    revisions_used: int
    status: str
    is_late: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}

# Order Delivery Schemas
class OrderDeliveryBase(BaseModel):
    message: Optional[str] = None
    files: Optional[Dict[str, Any]] = None
    is_final_delivery: bool = True

class OrderDeliveryCreate(OrderDeliveryBase):
    pass

class OrderDeliveryOut(OrderDeliveryBase):
    delivery_id: int
    order_id: int
    delivered_at: datetime
    
    model_config = {"from_attributes": True}

# Order Revision Schemas
class OrderRevisionBase(BaseModel):
    request_message: str

class OrderRevisionCreate(OrderRevisionBase):
    pass

class OrderRevisionOut(OrderRevisionBase):
    revision_id: int
    order_id: int
    requested_by: int
    request_date: datetime
    response_message: Optional[str] = None
    response_date: Optional[datetime] = None
    status: str
    
    model_config = {"from_attributes": True}