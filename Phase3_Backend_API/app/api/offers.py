from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, get_current_seller
from app.database.session import get_db
from app.models.user import User, SellerProfile
from app.schemas.offer import OfferCreate, OfferOut, OfferUpdate
from app.services.offer import OfferService

router = APIRouter()

@router.post("/", response_model=OfferOut)
def create_offer(
    offer_data: OfferCreate,
    current_seller: SellerProfile = Depends(get_current_seller),
    db: Session = Depends(get_db)
) -> Any:
    """Create a custom offer."""
    return OfferService.create_offer(db=db, offer_data=offer_data, seller_id=current_seller.seller_id)

@router.get("/sent", response_model=List[OfferOut])
def get_sent_offers(
    current_seller: SellerProfile = Depends(get_current_seller),
    db: Session = Depends(get_db)
) -> Any:
    """Get offers sent by current seller."""
    return OfferService.get_sent_offers(db=db, seller_id=current_seller.seller_id)

@router.get("/received", response_model=List[OfferOut])
def get_received_offers(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get offers received by current user."""
    return OfferService.get_received_offers(db=db, buyer_id=current_user.user_id)

@router.get("/{offer_id}", response_model=OfferOut)
def get_offer_by_id(
    offer_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get offer by ID."""
    return OfferService.get_offer_by_id(db=db, offer_id=offer_id, user_id=current_user.user_id)

@router.put("/{offer_id}/accept")
def accept_offer(
    offer_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Accept an offer."""
    OfferService.accept_offer(db=db, offer_id=offer_id, buyer_id=current_user.user_id)
    return {"message": "Offer accepted successfully"}

@router.put("/{offer_id}/reject")
def reject_offer(
    offer_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Reject an offer."""
    OfferService.reject_offer(db=db, offer_id=offer_id, buyer_id=current_user.user_id)
    return {"message": "Offer rejected successfully"}