from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator

class PaymentOut(BaseModel):
    payment_id: int
    order_id: int
    amount: int
    platform_fee: int
    seller_amount: int
    currency: str
    payment_method: str
    transaction_id: Optional[str] = None
    status: str
    created_at: datetime
    
    model_config = {"from_attributes": True}

class WithdrawalRequest(BaseModel):
    amount: int
    payment_method: str
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v