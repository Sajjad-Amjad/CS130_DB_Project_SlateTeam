from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class MessageBase(BaseModel):
    content: str
    attachment_url: Optional[str] = None

class MessageCreate(MessageBase):
    recipient_id: int

class MessageOut(MessageBase):
    message_id: int
    conversation_id: str
    sender_id: int
    recipient_id: int
    is_read: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}

class ConversationOut(BaseModel):
    conversation_id: str
    other_user_id: int
    other_user_name: str
    last_message_content: str
    last_message_date: datetime
    unread_count: int