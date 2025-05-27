from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewOut, ReviewResponse
from app.services.review import ReviewService

router = APIRouter()

@router.post("/", response_model=ReviewOut)
def create_review(
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create a review for a completed order."""
    return ReviewService.create_review(db=db, review_data=review_data, reviewer_id=current_user.user_id)

@router.get("/gig/{gig_id}", response_model=List[ReviewOut])
def get_gig_reviews(
    gig_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Any:
    """Get reviews for a gig."""
    return ReviewService.get_gig_reviews(db=db, gig_id=gig_id, skip=skip, limit=limit)

@router.get("/seller/{seller_id}", response_model=List[ReviewOut])
def get_seller_reviews(
    seller_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Any:
    """Get reviews for a seller."""
    return ReviewService.get_seller_reviews(db=db, seller_id=seller_id, skip=skip, limit=limit)

@router.post("/{review_id}/response")
def respond_to_review(
    review_id: int,
    response_data: ReviewResponse,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Respond to a review (seller only)."""
    ReviewService.respond_to_review(
        db=db, 
        review_id=review_id, 
        response_data=response_data, 
        seller_id=current_user.user_id
    )
    return {"message": "Review response added successfully"}