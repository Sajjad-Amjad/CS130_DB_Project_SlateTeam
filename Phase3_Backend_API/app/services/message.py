from typing import List
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models.message import Message
from app.models.user import User
from app.models.notification import Notification
from app.schemas.message import MessageCreate, ConversationOut

class MessageService:
    @staticmethod
    def generate_conversation_id(user_id1: int, user_id2: int) -> str:
        """Generate conversation ID from two user IDs."""
        return f"{min(user_id1, user_id2)}-{max(user_id1, user_id2)}"

    @staticmethod
    def send_message(db: Session, message_data: MessageCreate, sender_id: int) -> Message:
        """Send a message."""
        # Verify recipient exists
        recipient = db.query(User).filter(User.user_id == message_data.recipient_id).first()
        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipient not found"
            )
        
        # Generate conversation ID
        conversation_id = MessageService.generate_conversation_id(sender_id, message_data.recipient_id)
        
        # Create message
        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            recipient_id=message_data.recipient_id,
            content=message_data.content,
            attachment_url=message_data.attachment_url,
            is_read=False
        )
        
        db.add(message)
        
        # Create notification for recipient
        notification = Notification(
            user_id=message_data.recipient_id,
            type="new_message",
            content="You have received a new message",
            related_entity_id=message.message_id,
            related_entity_type="message"
        )
        
        db.add(notification)
        db.commit()
        db.refresh(message)
        
        return message

    @staticmethod
    def get_conversations(db: Session, user_id: int) -> List[ConversationOut]:
        """Get all conversations for a user."""
        # Get all unique conversation IDs for the user
        conversations = db.query(Message.conversation_id).filter(
            or_(Message.sender_id == user_id, Message.recipient_id == user_id)
        ).distinct().all()
        
        conversation_list = []
        
        for (conversation_id,) in conversations:
            # Get the last message in this conversation
            last_message = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.desc()).first()
            
            if last_message:
                # Determine the other user in the conversation
                other_user_id = (
                    last_message.recipient_id if last_message.sender_id == user_id 
                    else last_message.sender_id
                )
                
                other_user = db.query(User).filter(User.user_id == other_user_id).first()
                
                # Count unread messages
                unread_count = db.query(Message).filter(
                    and_(
                        Message.conversation_id == conversation_id,
                        Message.recipient_id == user_id,
                        Message.is_read == False
                    )
                ).count()
                
                conversation_list.append(ConversationOut(
                    conversation_id=conversation_id,
                    other_user_id=other_user_id,
                    other_user_name=other_user.full_name if other_user else "Unknown",
                    last_message_content=last_message.content,
                    last_message_date=last_message.created_at,
                    unread_count=unread_count
                ))
        
        # Sort by last message date
        conversation_list.sort(key=lambda x: x.last_message_date, reverse=True)
        
        return conversation_list

    @staticmethod
    def get_conversation_messages(
        db: Session, 
        conversation_id: str, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 50
    ) -> List[Message]:
        """Get messages in a conversation."""
        # Verify user is part of this conversation
        user_ids = conversation_id.split('-')
        if str(user_id) not in user_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this conversation"
            )
        
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
        
        # Mark messages as read for the current user
        unread_messages = db.query(Message).filter(
            and_(
                Message.conversation_id == conversation_id,
                Message.recipient_id == user_id,
                Message.is_read == False
            )
        ).all()
        
        for message in unread_messages:
            message.is_read = True
        
        db.commit()
        
        return list(reversed(messages))  # Return in chronological order

    @staticmethod
    def mark_as_read(db: Session, message_id: int, user_id: int):
        """Mark a message as read."""
        message = db.query(Message).filter(
            Message.message_id == message_id,
            Message.recipient_id == user_id
        ).first()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or you don't have permission"
            )
        
        message.is_read = True
        db.commit()