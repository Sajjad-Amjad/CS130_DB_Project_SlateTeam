from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, get_current_seller
from app.database.session import get_db
from app.models.user import User, SellerProfile
from app.schemas.user import UserOut, UserUpdate, PasswordChange
from app.schemas.seller import SellerProfileCreate, SellerProfileOut, SellerProfileUpdate
from app.services.user import UserService

router = APIRouter()

@router.get("/me", response_model=UserOut)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get current user profile."""
    return current_user

@router.put("/me", response_model=UserOut)
def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update current user profile."""
    return UserService.update_user(db=db, user_id=current_user.user_id, user_update=user_update)

@router.put("/me/password")
def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Change user password."""
    UserService.change_password(db=db, user_id=current_user.user_id, password_change=password_change)
    return {"message": "Password changed successfully"}

@router.post("/seller-profile", response_model=SellerProfileOut)
def create_seller_profile(
    seller_data: SellerProfileCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create seller profile for current user."""
    return UserService.create_seller_profile(db=db, user_id=current_user.user_id, seller_data=seller_data)

@router.get("/seller-profile", response_model=SellerProfileOut)
def get_current_seller_profile(
    current_seller: SellerProfile = Depends(get_current_seller)
) -> Any:
    """Get current user's seller profile."""
    return current_seller

@router.put("/seller-profile", response_model=SellerProfileOut)
def update_seller_profile(
    seller_update: SellerProfileUpdate,
    current_seller: SellerProfile = Depends(get_current_seller),
    db: Session = Depends(get_db)
) -> Any:
    """Update current seller profile."""
    return UserService.update_seller_profile(
        db=db, 
        seller_id=current_seller.seller_id, 
        seller_update=seller_update
    )

@router.get("/{user_id}", response_model=UserOut)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Get user by ID (public profile)."""
    user = UserService.get_user_by_id(db=db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.get("/seller/{seller_id}", response_model=SellerProfileOut)
def get_seller_by_id(
    seller_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Get seller profile by ID (public profile)."""
    seller = UserService.get_seller_profile(db=db, seller_id=seller_id)
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller not found"
        )
    return seller