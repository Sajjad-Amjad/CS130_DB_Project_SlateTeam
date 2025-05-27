from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.notification import Notification

class NotificationService:
    @staticmethod
    def get_notifications(
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 20,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a user."""
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def mark_as_read(db: Session, notification_id: int, user_id: int):
        """Mark a notification as read."""
        notification = db.query(Notification).filter(
            Notification.notification_id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        notification.is_read = True
        db.commit()

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int):
        """Mark all notifications as read for a user."""
        db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({"is_read": True})
        db.commit()

    @staticmethod
    def get_unread_count(db: Session, user_id: int) -> int:
        """Get unread notification count."""
        return db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()