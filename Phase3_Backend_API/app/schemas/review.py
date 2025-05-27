from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator

class ReviewBase(BaseModel):
    communication_rating: int
    service_rating: int
    recommendation_rating: int
    comment: Optional[str] = None
    
    @field_validator('communication_rating', 'service_rating', 'recommendation_rating')
    @classmethod
    def validate_ratings(cls, v):
        if not 1 <= v <= 5:
            raise ValueError('Rating must be between 1 and 5')
        return v

class ReviewCreate(ReviewBase):
    order_id: int

class ReviewOut(ReviewBase):
    review_id: int
    order_id: int
    reviewer_id: int
    reviewee_id: int
    overall_rating: float
    created_at: datetime
    seller_response: Optional[str] = None
    seller_response_date: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

class ReviewResponse(BaseModel):
    response: str
    
    @field_validator('response')
    @classmethod
    def validate_response(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('Response cannot be empty')
        return v