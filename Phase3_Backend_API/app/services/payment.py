from typing import List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.payment import Payment
from app.models.order import Order
from app.models.user import SellerProfile
from app.schemas.payment import WithdrawalRequest

class PaymentService:
    @staticmethod
    def get_payment_by_id(db: Session, payment_id: int, user_id: int) -> Payment:
        """Get payment by ID with permission check."""
        payment = db.query(Payment).join(Order).filter(
            Payment.payment_id == payment_id,
            and_(
                Payment.order_id == Order.order_id,
                (Order.buyer_id == user_id) | (Order.seller_id == user_id)
            )
        ).first()
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found or access denied"
            )
        
        return payment

    @staticmethod
    def get_earnings_summary(db: Session, seller_id: int) -> Dict[str, Any]:
        """Get earnings summary for a seller."""
        # Total earnings
        total_earnings = db.query(func.sum(Payment.seller_amount)).join(Order).filter(
            Order.seller_id == seller_id,
            Payment.status == "completed"
        ).scalar() or 0
        
        # Available for withdrawal (completed payments)
        available_earnings = db.query(func.sum(Payment.seller_amount)).join(Order).filter(
            Order.seller_id == seller_id,
            Payment.status == "completed",
            Order.status == "completed"
        ).scalar() or 0
        
        # Pending earnings (in escrow)
        pending_earnings = db.query(func.sum(Payment.seller_amount)).join(Order).filter(
            Order.seller_id == seller_id,
            Payment.status == "pending",
            Order.status.in_(["pending", "in_progress", "delivered"])
        ).scalar() or 0
        
        # This month's earnings
        from datetime import datetime, timedelta
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        monthly_earnings = db.query(func.sum(Payment.seller_amount)).join(Order).filter(
            Order.seller_id == seller_id,
            Payment.status == "completed",
            Payment.created_at >= start_of_month
        ).scalar() or 0
        
        return {
            "total_earnings": total_earnings,
            "available_earnings": available_earnings,
            "pending_earnings": pending_earnings,
            "monthly_earnings": monthly_earnings,
            "currency": "USD"
        }

    @staticmethod
    def get_earnings_history(db: Session, seller_id: int) -> List[Payment]:
        """Get earnings history for a seller."""
        return db.query(Payment).join(Order).filter(
            Order.seller_id == seller_id,
            Payment.status == "completed"
        ).order_by(Payment.created_at.desc()).all()

    @staticmethod
    def request_withdrawal(db: Session, seller_id: int, withdrawal_data: WithdrawalRequest):
        """Request withdrawal of earnings."""
        # Check available balance
        available_earnings = db.query(func.sum(Payment.seller_amount)).join(Order).filter(
            Order.seller_id == seller_id,
            Payment.status == "completed",
            Order.status == "completed"
        ).scalar() or 0
        
        if withdrawal_data.amount > available_earnings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient available balance"
            )
        
        # NOTE(SAJJAD) : USING DUMMY LOGIC FOR PAYMENT...
        return True