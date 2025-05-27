from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.order import Order, OrderDelivery, OrderRevision
from app.models.gig import Gig, GigPackage
from app.models.user import User, SellerProfile
from app.models.payment import Payment
from app.models.notification import Notification
from app.schemas.order import OrderCreate, OrderUpdate, OrderDeliveryCreate, OrderRevisionCreate

class OrderService:
    @staticmethod
    def create_order(db: Session, order_data: OrderCreate, buyer_id: int) -> Order:
        """Create a new order."""
        # Verify gig exists
        gig = db.query(Gig).filter(Gig.gig_id == order_data.gig_id, Gig.is_active == True).first()
        if not gig:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gig not found"
            )
        
        # Verify package exists
        package = db.query(GigPackage).filter(
            GigPackage.package_id == order_data.package_id,
            GigPackage.gig_id == order_data.gig_id,
            GigPackage.is_active == True
        ).first()
        if not package:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package not found"
            )
        
        # Get seller info
        seller = db.query(SellerProfile).filter(SellerProfile.seller_id == gig.seller_id).first()
        if not seller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seller not found"
            )
        
        # Check if buyer is trying to order their own gig
        if buyer_id == seller.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot order your own gig"
            )
        
        # Calculate expected delivery date
        expected_delivery = datetime.utcnow() + timedelta(days=package.delivery_time)
        
        # Create order
        order = Order(
            gig_id=order_data.gig_id,
            package_id=order_data.package_id,
            buyer_id=buyer_id,
            seller_id=seller.user_id,
            requirements=order_data.requirements,
            price=package.price,
            delivery_time=package.delivery_time,
            expected_delivery_date=expected_delivery,
            revision_count=package.revision_count,
            revisions_used=0,
            status="pending",
            is_late=False
        )
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        # Create payment record
        platform_fee = int(order.price * 0.2)  # 20% platform fee
        seller_amount = order.price - platform_fee
        
        payment = Payment(
            order_id=order.order_id,
            amount=order.price,
            platform_fee=platform_fee,
            seller_amount=seller_amount,
            currency="USD",
            payment_method="credit_card",
            status="pending"
        )
        
        db.add(payment)
        
        # Create notification for seller
        notification = Notification(
            user_id=seller.user_id,
            type="new_order",
            content="You have received a new order",
            related_entity_id=order.order_id,
            related_entity_type="order"
        )
        
        db.add(notification)
        db.commit()
        
        return order

    @staticmethod
    def get_order_by_id(db: Session, order_id: int, user_id: int) -> Order:
        """Get order by ID with permission check."""
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Check if user has permission to view this order
        if order.buyer_id != user_id and order.seller_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this order"
            )
        
        return order

    @staticmethod
    def get_buyer_orders(db: Session, buyer_id: int, status_filter: Optional[str] = None) -> List[Order]:
        """Get orders for a buyer."""
        query = db.query(Order).filter(Order.buyer_id == buyer_id)
        
        if status_filter:
            query = query.filter(Order.status == status_filter)
        
        return query.order_by(Order.created_at.desc()).all()

    @staticmethod
    def get_seller_orders(db: Session, seller_id: int, status_filter: Optional[str] = None) -> List[Order]:
        """Get orders for a seller."""
        query = db.query(Order).filter(Order.seller_id == seller_id)
        
        if status_filter:
            query = query.filter(Order.status == status_filter)
        
        return query.order_by(Order.created_at.desc()).all()

    @staticmethod
    def update_order_status(db: Session, order_id: int, order_update: OrderUpdate, user_id: int) -> Order:
        """Update order status."""
        order = OrderService.get_order_by_id(db, order_id, user_id)
        
        # Check valid status transitions
        valid_transitions = {
            "pending": ["in_progress", "cancelled"],
            "in_progress": ["delivered", "cancelled"],
            "delivered": ["completed", "in_progress"],  # in_progress for revisions
            "completed": [],  # Final state
            "cancelled": [],  # Final state
            "disputed": ["in_progress", "cancelled"]
        }
        
        if order_update.status not in valid_transitions.get(order.status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot change status from {order.status} to {order_update.status}"
            )
        
        order.status = order_update.status
        db.commit()
        db.refresh(order)
        
        return order

    @staticmethod
    def deliver_order(db: Session, order_id: int, delivery_data: OrderDeliveryCreate, seller_id: int):
        """Deliver an order."""
        order = db.query(Order).filter(
            Order.order_id == order_id,
            Order.seller_id == seller_id
        ).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found or you don't have permission"
            )
        
        if order.status not in ["pending", "in_progress"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order cannot be delivered in its current state"
            )
        
        # Create delivery record
        delivery = OrderDelivery(
            order_id=order_id,
            message=delivery_data.message,
            files=delivery_data.files,
            is_final_delivery=delivery_data.is_final_delivery
        )
        
        db.add(delivery)
        
        # Update order status
        if delivery_data.is_final_delivery:
            order.status = "delivered"
            order.actual_delivery_date = datetime.utcnow()
        else:
            order.status = "in_progress"
        
        # Create notification for buyer
        notification = Notification(
            user_id=order.buyer_id,
            type="order_delivered" if delivery_data.is_final_delivery else "order_update",
            content="Your order has been delivered" if delivery_data.is_final_delivery else "Your order has been updated",
            related_entity_id=order_id,
            related_entity_type="order"
        )
        
        db.add(notification)
        db.commit()

    @staticmethod
    def request_revision(db: Session, order_id: int, revision_data: OrderRevisionCreate, user_id: int):
        """Request a revision for an order."""
        order = db.query(Order).filter(
            Order.order_id == order_id,
            Order.buyer_id == user_id
        ).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found or you don't have permission"
            )
        
        if order.status != "delivered":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only request revisions for delivered orders"
            )
        
        if order.revisions_used >= order.revision_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No revisions left for this order"
            )
        
        # Create revision request
        revision = OrderRevision(
            order_id=order_id,
            requested_by=user_id,
            request_message=revision_data.request_message,
            status="pending"
        )
        
        db.add(revision)
        
        # Update order
        order.status = "in_progress"
        order.revisions_used += 1
        
        # Create notification for seller
        notification = Notification(
            user_id=order.seller_id,
            type="revision_requested",
            content="A revision has been requested for your order",
            related_entity_id=order_id,
            related_entity_type="order"
        )
        
        db.add(notification)
        db.commit()

    @staticmethod
    def complete_order(db: Session, order_id: int, buyer_id: int):
        """Complete an order (buyer only)."""
        order = db.query(Order).filter(
            Order.order_id == order_id,
            Order.buyer_id == buyer_id
        ).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found or you don't have permission"
            )
        
        if order.status != "delivered":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only complete delivered orders"
            )
        
        # Update order status
        order.status = "completed"
        
        # Update payment status
        payment = db.query(Payment).filter(Payment.order_id == order_id).first()
        if payment:
            payment.status = "completed"
        
        # Create notification for seller
        notification = Notification(
            user_id=order.seller_id,
            type="order_completed",
            content="Your order has been completed and payment released",
            related_entity_id=order_id,
            related_entity_type="order"
        )
        
        db.add(notification)
        db.commit()

    @staticmethod
    def cancel_order(db: Session, order_id: int, user_id: int):
        """Cancel an order."""
        order = db.query(Order).filter(Order.order_id == order_id).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Check permission
        if order.buyer_id != user_id and order.seller_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to cancel this order"
            )
        
        if order.status not in ["pending", "in_progress"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel order in its current state"
            )
        
        # Update order status
        order.status = "cancelled"
        
        # Update payment status
        payment = db.query(Payment).filter(Payment.order_id == order_id).first()
        if payment:
            payment.status = "refunded"
        
        # Create notification for the other party
        notify_user_id = order.seller_id if user_id == order.buyer_id else order.buyer_id
        notification = Notification(
            user_id=notify_user_id,
            type="order_cancelled",
            content="An order has been cancelled",
            related_entity_id=order_id,
            related_entity_type="order"
        )
        
        db.add(notification)
        db.commit()