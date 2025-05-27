from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.notification import NotificationOut
from app.services.notification import NotificationService

router = APIRouter()

@router.get("/", response_model=List[NotificationOut])
def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get notifications for current user."""
    return NotificationService.get_notifications(
        db=db, 
        user_id=current_user.user_id, 
        skip=skip, 
        limit=limit,
        unread_only=unread_only
    )

@router.put("/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Mark a notification as read."""
    NotificationService.mark_as_read(db=db, notification_id=notification_id, user_id=current_user.user_id)
    return {"message": "Notification marked as read"}

@router.put("/read-all")
def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Mark all notifications as read."""
    NotificationService.mark_all_as_read(db=db, user_id=current_user.user_id)
    return {"message": "All notifications marked as read"}

@router.get("/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get unread notification count."""
    count = NotificationService.get_unread_count(db=db, user_id=current_user.user_id)
    return {"unread_count": count}