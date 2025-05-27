from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class NotificationOut(BaseModel):
    notification_id: int
    user_id: int
    type: str
    content: str
    is_read: bool
    related_entity_id: Optional[int] = None
    related_entity_type: Optional[str] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}