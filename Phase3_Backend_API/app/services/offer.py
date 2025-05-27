from typing import List
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.offer import Offer
from app.models.user import User, SellerProfile
from app.models.notification import Notification
from app.schemas.offer import OfferCreate

class OfferService:
    @staticmethod
    def create_offer(db: Session, offer_data: OfferCreate, seller_id: int) -> Offer:
        """Create a custom offer."""
        # Verify buyer exists
        buyer = db.query(User).filter(User.user_id == offer_data.buyer_id).first()
        if not buyer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Buyer not found"
            )
        
        # Check if seller is trying to create offer for themselves
        seller_profile = db.query(SellerProfile).filter(SellerProfile.seller_id == seller_id).first()
        if seller_profile and seller_profile.user_id == offer_data.buyer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create offer for yourself"
            )
        
        # Calculate expiry date
        expiry_date = datetime.utcnow() + timedelta(days=offer_data.expiry_days or 7)
        
        # Create offer
        offer = Offer(
            seller_id=seller_id,
            buyer_id=offer_data.buyer_id,
            title=offer_data.title,
            description=offer_data.description,
            price=offer_data.price,
            delivery_time=offer_data.delivery_time,
            revision_count=offer_data.revision_count,
            expiry_date=expiry_date,
            status="pending"
        )
        
        db.add(offer)
        
        # Create notification for buyer
        notification = Notification(
            user_id=offer_data.buyer_id,
            type="new_offer",
            content="You have received a custom offer",
            related_entity_id=offer.offer_id,
            related_entity_type="offer"
        )
        
        db.add(notification)
        db.commit()
        db.refresh(offer)
        
        return offer

    @staticmethod
    def get_offer_by_id(db: Session, offer_id: int, user_id: int) -> Offer:
        """Get offer by ID with permission check."""
        offer = db.query(Offer).filter(Offer.offer_id == offer_id).first()
        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offer not found"
            )
        
        # Check permission
        seller_profile = db.query(SellerProfile).filter(SellerProfile.seller_id == offer.seller_id).first()
        seller_user_id = seller_profile.user_id if seller_profile else None
        
        if offer.buyer_id != user_id and seller_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this offer"
            )
        
        return offer

    @staticmethod
    def get_sent_offers(db: Session, seller_id: int) -> List[Offer]:
        """Get offers sent by a seller."""
        return db.query(Offer).filter(Offer.seller_id == seller_id).order_by(Offer.created_at.desc()).all()

    @staticmethod
    def get_received_offers(db: Session, buyer_id: int) -> List[Offer]:
        """Get offers received by a buyer."""
        return db.query(Offer).filter(Offer.buyer_id == buyer_id).order_by(Offer.created_at.desc()).all()

    @staticmethod
    def accept_offer(db: Session, offer_id: int, buyer_id: int):
        """Accept an offer."""
        offer = db.query(Offer).filter(
            Offer.offer_id == offer_id,
            Offer.buyer_id == buyer_id
        ).first()
        
        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offer not found or you don't have permission"
            )
        
        if offer.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Offer is no longer available"
            )
        
        if offer.expiry_date < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Offer has expired"
            )
        
        # Update offer status
        offer.status = "accepted"
        
        # Create notification for seller
        seller_profile = db.query(SellerProfile).filter(SellerProfile.seller_id == offer.seller_id).first()
        if seller_profile:
            notification = Notification(
                user_id=seller_profile.user_id,
                type="offer_accepted",
                content="Your offer has been accepted",
                related_entity_id=offer_id,
                related_entity_type="offer"
            )
            db.add(notification)
        
        db.commit()

    @staticmethod
    def reject_offer(db: Session, offer_id: int, buyer_id: int):
        """Reject an offer."""
        offer = db.query(Offer).filter(
            Offer.offer_id == offer_id,
            Offer.buyer_id == buyer_id
        ).first()
        
        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offer not found or you don't have permission"
            )
        
        if offer.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Offer is no longer available"
            )
        
        # Update offer status
        offer.status = "rejected"
        
        # Create notification for seller
        seller_profile = db.query(SellerProfile).filter(SellerProfile.seller_id == offer.seller_id).first()
        if seller_profile:
            notification = Notification(
                user_id=seller_profile.user_id,
                type="offer_rejected",
                content="Your offer has been rejected",
                related_entity_id=offer_id,
                related_entity_type="offer"
            )
            db.add(notification)
        
        db.commit()