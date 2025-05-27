from typing import List
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.review import Review
from app.models.order import Order
from app.models.gig import Gig
from app.models.user import SellerProfile
from app.schemas.review import ReviewCreate, ReviewResponse

class ReviewService:
    @staticmethod
    def create_review(db: Session, review_data: ReviewCreate, reviewer_id: int) -> Review:
        """Create a review for a completed order."""
        # Verify order exists and is completed
        order = db.query(Order).filter(Order.order_id == review_data.order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        if order.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only review completed orders"
            )
        
        # Check if reviewer is the buyer
        if order.buyer_id != reviewer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the buyer can review this order"
            )
        
        # Check if review already exists
        existing_review = db.query(Review).filter(Review.order_id == review_data.order_id).first()
        if existing_review:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Review already exists for this order"
            )
        
        # Calculate overall rating
        overall_rating = (
            review_data.communication_rating + 
            review_data.service_rating + 
            review_data.recommendation_rating
        ) / 3.0
        
        # Create review
        review = Review(
            order_id=review_data.order_id,
            reviewer_id=reviewer_id,
            reviewee_id=order.seller_id,
            communication_rating=review_data.communication_rating,
            service_rating=review_data.service_rating,
            recommendation_rating=review_data.recommendation_rating,
            overall_rating=overall_rating,
            comment=review_data.comment
        )
        
        db.add(review)
        db.commit()
        db.refresh(review)
        
        return review

    @staticmethod
    def get_gig_reviews(db: Session, gig_id: int, skip: int = 0, limit: int = 20) -> List[Review]:
        """Get reviews for a gig."""
        reviews = db.query(Review).join(Order).filter(
            Order.gig_id == gig_id
        ).order_by(Review.created_at.desc()).offset(skip).limit(limit).all()
        
        return reviews

    @staticmethod
    def get_seller_reviews(db: Session, seller_id: int, skip: int = 0, limit: int = 20) -> List[Review]:
        """Get reviews for a seller."""
        # Get seller's user_id from seller_id
        seller = db.query(SellerProfile).filter(SellerProfile.seller_id == seller_id).first()
        if not seller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seller not found"
            )
        
        reviews = db.query(Review).filter(
            Review.reviewee_id == seller.user_id
        ).order_by(Review.created_at.desc()).offset(skip).limit(limit).all()
        
        return reviews

    @staticmethod
    def respond_to_review(db: Session, review_id: int, response_data: ReviewResponse, seller_id: int):
        """Respond to a review (seller only)."""
        review = db.query(Review).filter(Review.review_id == review_id).first()
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        # Check if the seller is the reviewee
        if review.reviewee_id != seller_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only respond to reviews about you"
            )
        
        # Check if response already exists
        if review.seller_response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Response already exists for this review"
            )
        
        # Update review with response
        review.seller_response = response_data.response
        review.seller_response_date = datetime.utcnow()
        
        db.commit()