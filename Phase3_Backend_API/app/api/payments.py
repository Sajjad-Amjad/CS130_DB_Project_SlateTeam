from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, get_current_seller
from app.database.session import get_db
from app.models.user import User, SellerProfile
from app.schemas.payment import PaymentOut, WithdrawalRequest
from app.services.payment import PaymentService

router = APIRouter()

@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment_by_id(
    payment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get payment by ID."""
    return PaymentService.get_payment_by_id(db=db, payment_id=payment_id, user_id=current_user.user_id)

@router.get("/earnings/summary")
def get_earnings_summary(
    current_seller: SellerProfile = Depends(get_current_seller),
    db: Session = Depends(get_db)
) -> Any:
    """Get earnings summary for current seller."""
    return PaymentService.get_earnings_summary(db=db, seller_id=current_seller.user_id)

@router.get("/earnings/history", response_model=List[PaymentOut])
def get_earnings_history(
    current_seller: SellerProfile = Depends(get_current_seller),
    db: Session = Depends(get_db)
) -> Any:
    """Get earnings history for current seller."""
    return PaymentService.get_earnings_history(db=db, seller_id=current_seller.user_id)

@router.post("/withdraw")
def request_withdrawal(
    withdrawal_data: WithdrawalRequest,
    current_seller: SellerProfile = Depends(get_current_seller),
    db: Session = Depends(get_db)
) -> Any:
    """Request withdrawal of earnings."""
    PaymentService.request_withdrawal(
        db=db, 
        seller_id=current_seller.user_id, 
        withdrawal_data=withdrawal_data
    )
    return {"message": "Withdrawal request submitted successfully"}