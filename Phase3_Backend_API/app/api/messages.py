from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.message import MessageCreate, MessageOut, ConversationOut
from app.services.message import MessageService

router = APIRouter()

@router.get("/conversations", response_model=List[ConversationOut])
def get_conversations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get all conversations for current user."""
    return MessageService.get_conversations(db=db, user_id=current_user.user_id)

@router.get("/conversations/{conversation_id}", response_model=List[MessageOut])
def get_conversation_messages(
    conversation_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get messages in a conversation."""
    return MessageService.get_conversation_messages(
        db=db, 
        conversation_id=conversation_id, 
        user_id=current_user.user_id,
        skip=skip,
        limit=limit
    )

@router.post("/send", response_model=MessageOut)
def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Send a message."""
    return MessageService.send_message(
        db=db, 
        message_data=message_data, 
        sender_id=current_user.user_id
    )

@router.put("/{message_id}/read")
def mark_message_as_read(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Mark a message as read."""
    MessageService.mark_as_read(db=db, message_id=message_id, user_id=current_user.user_id)
    return {"message": "Message marked as read"}