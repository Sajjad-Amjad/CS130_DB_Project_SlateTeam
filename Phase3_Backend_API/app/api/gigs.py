from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from app.api.dependencies import get_current_active_user, get_current_seller
from app.database.session import get_db
from app.models.gig import Gig, GigPackage, GigImage
from app.models.user import User, SellerProfile
from app.schemas.gig import GigCreate, GigOut, GigUpdate, GigPackageCreate, GigPackageOut
from app.services.gig import GigService

router = APIRouter()

@router.get("/", response_model=List[GigOut])
def get_gigs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = Query(None),
    subcategory_id: Optional[int] = Query(None),
    min_price: Optional[int] = Query(None, ge=0),
    max_price: Optional[int] = Query(None, ge=0),
    delivery_time: Optional[int] = Query(None, ge=1),
    seller_level: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("ranking", regex="^(ranking|price|delivery_time|rating)$"),
    sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$"),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> Any:
    """Get gigs with filtering and sorting."""
    return GigService.get_gigs(
        db=db,
        skip=skip,
        limit=limit,
        category_id=category_id,
        subcategory_id=subcategory_id,
        min_price=min_price,
        max_price=max_price,
        delivery_time=delivery_time,
        seller_level=seller_level,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search
    )

@router.get("/featured", response_model=List[GigOut])
def get_featured_gigs(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
) -> Any:
    """Get featured gigs."""
    gigs = db.query(Gig).filter(
        Gig.is_featured == True,
        Gig.is_active == True
    ).order_by(desc(Gig.ranking_score)).limit(limit).all()
    
    return gigs

@router.get("/my-gigs", response_model=List[GigOut])
def get_my_gigs(
    current_seller: SellerProfile = Depends(get_current_seller),
    db: Session = Depends(get_db)
) -> Any:
    """Get current seller's gigs."""
    gigs = db.query(Gig).filter(Gig.seller_id == current_seller.seller_id).all()
    return gigs

@router.post("/", response_model=GigOut)
def create_gig(
    gig_data: GigCreate,
    current_seller: SellerProfile = Depends(get_current_seller),
    db: Session = Depends(get_db)
) -> Any:
    """Create a new gig."""
    return GigService.create_gig(db=db, gig_data=gig_data, seller_id=current_seller.seller_id)

@router.get("/{gig_id}", response_model=GigOut)
def get_gig_by_id(
    gig_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Get gig by ID."""
    gig = GigService.get_gig_by_id(db=db, gig_id=gig_id)
    if not gig:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gig not found"
        )
    
    # Increment view count
    gig.impression_count += 1
    db.commit()
    
    return gig

@router.put("/{gig_id}", response_model=GigOut)
def update_gig(
    gig_id: int,
    gig_update: GigUpdate,
    current_seller: SellerProfile = Depends(get_current_seller),
    db: Session = Depends(get_db)
) -> Any:
    """Update a gig."""
    return GigService.update_gig(
        db=db, 
        gig_id=gig_id, 
        gig_update=gig_update, 
        seller_id=current_seller.seller_id
    )

@router.delete("/{gig_id}")
def delete_gig(
    gig_id: int,
    current_seller: SellerProfile = Depends(get_current_seller),
    db: Session = Depends(get_db)
) -> Any:
    """Delete a gig (set inactive)."""
    GigService.delete_gig(db=db, gig_id=gig_id, seller_id=current_seller.seller_id)
    return {"message": "Gig deleted successfully"}

@router.get("/{gig_id}/packages", response_model=List[GigPackageOut])
def get_gig_packages(
    gig_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Get packages for a gig."""
    # Verify gig exists
    gig = db.query(Gig).filter(Gig.gig_id == gig_id).first()
    if not gig:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gig not found"
        )
    
    packages = db.query(GigPackage).filter(
        GigPackage.gig_id == gig_id,
        GigPackage.is_active == True
    ).order_by(GigPackage.price).all()
    
    return packages

@router.post("/{gig_id}/packages", response_model=GigPackageOut)
def create_gig_package(
    gig_id: int,
    package_data: GigPackageCreate,
    current_seller: SellerProfile = Depends(get_current_seller),
    db: Session = Depends(get_db)
) -> Any:
    """Create a package for a gig."""
    return GigService.create_gig_package(
        db=db, 
        gig_id=gig_id, 
        package_data=package_data, 
        seller_id=current_seller.seller_id
    )

@router.get("/category/{category_id}", response_model=List[GigOut])
def get_gigs_by_category(
    category_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Any:
    """Get gigs by category."""
    gigs = db.query(Gig).filter(
        Gig.category_id == category_id,
        Gig.is_active == True
    ).order_by(desc(Gig.ranking_score)).offset(skip).limit(limit).all()
    
    return gigs