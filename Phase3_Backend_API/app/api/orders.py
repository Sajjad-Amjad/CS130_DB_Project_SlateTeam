from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, get_current_seller
from app.database.session import get_db
from app.models.user import User, SellerProfile
from app.schemas.order import OrderCreate, OrderOut, OrderUpdate, OrderDeliveryCreate, OrderRevisionCreate
from app.services.order import OrderService

router = APIRouter()

@router.post("/", response_model=OrderOut)
def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create a new order."""
    return OrderService.create_order(db=db, order_data=order_data, buyer_id=current_user.user_id)

@router.get("/buyer", response_model=List[OrderOut])
def get_buyer_orders(
    status_filter: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get orders for current buyer."""
    return OrderService.get_buyer_orders(db=db, buyer_id=current_user.user_id, status_filter=status_filter)

@router.get("/seller", response_model=List[OrderOut])
def get_seller_orders(
    status_filter: Optional[str] = Query(None),
    current_seller: SellerProfile = Depends(get_current_seller),
    db: Session = Depends(get_db)
) -> Any:
    """Get orders for current seller."""
    return OrderService.get_seller_orders(db=db, seller_id=current_seller.user_id, status_filter=status_filter)

@router.get("/{order_id}", response_model=OrderOut)
def get_order_by_id(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get order by ID."""
    return OrderService.get_order_by_id(db=db, order_id=order_id, user_id=current_user.user_id)

@router.put("/{order_id}/status")
def update_order_status(
    order_id: int,
    order_update: OrderUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update order status."""
    OrderService.update_order_status(
        db=db, 
        order_id=order_id, 
        order_update=order_update, 
        user_id=current_user.user_id
    )
    return {"message": "Order status updated successfully"}

@router.post("/{order_id}/deliver")
def deliver_order(
    order_id: int,
    delivery_data: OrderDeliveryCreate,
    current_seller: SellerProfile = Depends(get_current_seller),
    db: Session = Depends(get_db)
) -> Any:
    """Deliver an order."""
    OrderService.deliver_order(
        db=db, 
        order_id=order_id, 
        delivery_data=delivery_data, 
        seller_id=current_seller.user_id
    )
    return {"message": "Order delivered successfully"}

@router.post("/{order_id}/request-revision")
def request_revision(
    order_id: int,
    revision_data: OrderRevisionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Request a revision for an order."""
    OrderService.request_revision(
        db=db, 
        order_id=order_id, 
        revision_data=revision_data, 
        user_id=current_user.user_id
    )
    return {"message": "Revision requested successfully"}

@router.post("/{order_id}/complete")
def complete_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Complete an order (buyer only)."""
    OrderService.complete_order(db=db, order_id=order_id, buyer_id=current_user.user_id)
    return {"message": "Order completed successfully"}

@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Cancel an order."""
    OrderService.cancel_order(db=db, order_id=order_id, user_id=current_user.user_id)
    return {"message": "Order cancelled successfully"}