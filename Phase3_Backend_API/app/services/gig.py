from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_, or_

from app.models.gig import Gig, GigPackage, GigImage
from app.models.user import SellerProfile
from app.models.category import Category
from app.schemas.gig import GigCreate, GigUpdate, GigPackageCreate

class GigService:
    @staticmethod
    def get_gigs(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        category_id: Optional[int] = None,
        subcategory_id: Optional[int] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        delivery_time: Optional[int] = None,
        seller_level: Optional[str] = None,
        sort_by: str = "ranking",
        sort_order: str = "desc",
        search: Optional[str] = None
    ) -> List[Gig]:
        """Get gigs with filtering and sorting."""
        query = db.query(Gig).filter(Gig.is_active == True)
        
        # Apply filters
        if category_id:
            query = query.filter(Gig.category_id == category_id)
        
        if subcategory_id:
            query = query.filter(Gig.subcategory_id == subcategory_id)
        
        if search:
            search_filter = or_(
                Gig.title.ilike(f"%{search}%"),
                Gig.description.ilike(f"%{search}%"),
                Gig.search_tags.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Price filtering (get min price from packages)
        if min_price or max_price:
            from sqlalchemy import func
            subquery = db.query(
                GigPackage.gig_id,
                func.min(GigPackage.price).label('min_price')
            ).filter(GigPackage.is_active == True).group_by(GigPackage.gig_id).subquery()
            
            query = query.join(subquery, Gig.gig_id == subquery.c.gig_id)
            
            if min_price:
                query = query.filter(subquery.c.min_price >= min_price)
            if max_price:
                query = query.filter(subquery.c.min_price <= max_price)
        
        # Delivery time filtering
        if delivery_time:
            from sqlalchemy import func
            delivery_subquery = db.query(
                GigPackage.gig_id,
                func.min(GigPackage.delivery_time).label('min_delivery')
            ).filter(GigPackage.is_active == True).group_by(GigPackage.gig_id).subquery()
            
            query = query.join(delivery_subquery, Gig.gig_id == delivery_subquery.c.gig_id)
            query = query.filter(delivery_subquery.c.min_delivery <= delivery_time)
        
        # Seller level filtering
        if seller_level:
            query = query.join(SellerProfile, Gig.seller_id == SellerProfile.seller_id)
            query = query.filter(SellerProfile.account_level == seller_level)
        
        # Apply sorting
        if sort_by == "ranking":
            order_field = Gig.ranking_score
        elif sort_by == "price":
            # This would require a subquery for min price
            order_field = Gig.created_at  # Fallback
        elif sort_by == "delivery_time":
            order_field = Gig.created_at  # Fallback
        else:  # rating or default
            order_field = Gig.ranking_score
        
        if sort_order == "desc":
            query = query.order_by(desc(order_field))
        else:
            query = query.order_by(asc(order_field))
        
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_gig_by_id(db: Session, gig_id: int) -> Optional[Gig]:
        """Get gig by ID."""
        return db.query(Gig).filter(Gig.gig_id == gig_id, Gig.is_active == True).first()

    @staticmethod
    def create_gig(db: Session, gig_data: GigCreate, seller_id: int) -> Gig:
        """Create a new gig."""
        # Check seller exists
        seller = db.query(SellerProfile).filter(SellerProfile.seller_id == seller_id).first()
        if not seller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seller not found"
            )
        
        # Check gig limit (max 5 active gigs per seller)
        active_gigs_count = db.query(Gig).filter(
            Gig.seller_id == seller_id,
            Gig.is_active == True
        ).count()
        
        if active_gigs_count >= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum number of active gigs (5) reached"
            )
        
        # Verify category exists
        category = db.query(Category).filter(Category.category_id == gig_data.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Verify subcategory if provided
        if gig_data.subcategory_id:
            subcategory = db.query(Category).filter(
                Category.category_id == gig_data.subcategory_id,
                Category.parent_category_id == gig_data.category_id
            ).first()
            if not subcategory:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid subcategory for the selected category"
                )
        
        # Create gig
        gig = Gig(
            seller_id=seller_id,
            category_id=gig_data.category_id,
            subcategory_id=gig_data.subcategory_id,
            title=gig_data.title,
            description=gig_data.description,
            gig_metadata=gig_data.gig_metadata,
            search_tags=gig_data.search_tags,
            requirements=gig_data.requirements,
            faqs=gig_data.faqs,
            is_active=True,
            ranking_score=0.0
        )
        
        db.add(gig)
        db.commit()
        db.refresh(gig)
        
        return gig

    @staticmethod
    def update_gig(db: Session, gig_id: int, gig_update: GigUpdate, seller_id: int) -> Gig:
        """Update a gig."""
        gig = db.query(Gig).filter(
            Gig.gig_id == gig_id,
            Gig.seller_id == seller_id
        ).first()
        
        if not gig:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gig not found or you don't have permission to edit it"
            )
        
        update_data = gig_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(gig, field, value)
        
        db.commit()
        db.refresh(gig)
        return gig

    @staticmethod
    def delete_gig(db: Session, gig_id: int, seller_id: int) -> bool:
        """Delete a gig (set inactive)."""
        gig = db.query(Gig).filter(
            Gig.gig_id == gig_id,
            Gig.seller_id == seller_id
        ).first()
        
        if not gig:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gig not found or you don't have permission to delete it"
            )
        
        gig.is_active = False
        db.commit()
        return True

    @staticmethod
    def create_gig_package(db: Session, gig_id: int, package_data: GigPackageCreate, seller_id: int) -> GigPackage:
        """Create a package for a gig."""
        # Verify gig exists and belongs to seller
        gig = db.query(Gig).filter(
            Gig.gig_id == gig_id,
            Gig.seller_id == seller_id
        ).first()
        
        if not gig:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gig not found or you don't have permission to edit it"
            )
        
        # Check if package type already exists for this gig
        existing_package = db.query(GigPackage).filter(
            GigPackage.gig_id == gig_id,
            GigPackage.package_type == package_data.package_type,
            GigPackage.is_active == True
        ).first()
        
        if existing_package:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Package type '{package_data.package_type}' already exists for this gig"
            )
        
        # Create package
        package = GigPackage(
            gig_id=gig_id,
            package_type=package_data.package_type,
            title=package_data.title,
            description=package_data.description,
            price=package_data.price,
            delivery_time=package_data.delivery_time,
            revision_count=package_data.revision_count,
            features=package_data.features,
            is_active=True
        )
        
        db.add(package)
        db.commit()
        db.refresh(package)
        
        return package