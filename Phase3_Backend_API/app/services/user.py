from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User, SellerProfile
from app.schemas.user import UserUpdate, PasswordChange
from app.schemas.seller import SellerProfileCreate, SellerProfileUpdate
from app.services.auth import AuthService

class UserService:
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.user_id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def update_user(db: Session, user_id: int, user_update: UserUpdate) -> User:
        """Update user information."""
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def change_password(db: Session, user_id: int, password_change: PasswordChange) -> bool:
        """Change user password."""
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not AuthService.verify_password(password_change.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
        
        # Update password
        user.password_hash = AuthService.get_password_hash(password_change.new_password)
        db.commit()
        return True

    @staticmethod
    def create_seller_profile(db: Session, user_id: int, seller_data: SellerProfileCreate) -> SellerProfile:
        """Create a seller profile for a user."""
        # Check if user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if seller profile already exists
        existing_profile = db.query(SellerProfile).filter(SellerProfile.user_id == user_id).first()
        if existing_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Seller profile already exists"
            )
        
        # Create seller profile
        seller_profile = SellerProfile(
            user_id=user_id,
            professional_title=seller_data.professional_title,
            description=seller_data.description,
            portfolio_links=seller_data.portfolio_links,
            education=seller_data.education,
            certifications=seller_data.certifications,
            languages=seller_data.languages,
            personal_website=seller_data.personal_website,
            social_media_links=seller_data.social_media_links,
            account_level="new"
        )
        
        db.add(seller_profile)
        
        # Update user role if needed
        if user.user_role == "buyer":
            user.user_role = "both"
        elif user.user_role not in ["seller", "both", "admin"]:
            user.user_role = "seller"
        
        db.commit()
        db.refresh(seller_profile)
        
        return seller_profile

    @staticmethod
    def get_seller_profile(db: Session, seller_id: int) -> Optional[SellerProfile]:
        """Get seller profile by seller ID."""
        return db.query(SellerProfile).filter(SellerProfile.seller_id == seller_id).first()

    @staticmethod
    def update_seller_profile(db: Session, seller_id: int, seller_update: SellerProfileUpdate) -> SellerProfile:
        """Update seller profile."""
        seller_profile = db.query(SellerProfile).filter(SellerProfile.seller_id == seller_id).first()
        if not seller_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seller profile not found"
            )
        
        update_data = seller_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(seller_profile, field, value)
        
        db.commit()
        db.refresh(seller_profile)
        return seller_profile