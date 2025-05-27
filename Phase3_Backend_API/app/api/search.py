from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.gig import GigOut
from app.schemas.user import UserOut
from app.services.search import SearchService

router = APIRouter()

@router.get("/", response_model=List[GigOut])
def search_gigs(
    q: str = Query(..., min_length=1, description="Search query"),
    category_id: Optional[int] = Query(None),
    min_price: Optional[int] = Query(None, ge=0),
    max_price: Optional[int] = Query(None, ge=0),
    delivery_time: Optional[int] = Query(None, ge=1),
    seller_level: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("relevance", regex="^(relevance|price|delivery_time|rating)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Any:
    """Search for gigs."""
    return SearchService.search_gigs(
        db=db,
        query=q,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        delivery_time=delivery_time,
        seller_level=seller_level,
        sort_by=sort_by,
        skip=skip,
        limit=limit
    )

@router.get("/sellers", response_model=List[UserOut])
def search_sellers(
    q: str = Query(..., min_length=1, description="Search query"),
    category_id: Optional[int] = Query(None),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    account_level: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Any:
    """Search for sellers."""
    return SearchService.search_sellers(
        db=db,
        query=q,
        category_id=category_id,
        min_rating=min_rating,
        account_level=account_level,
        skip=skip,
        limit=limit
    )

@router.get("/suggestions")
def get_search_suggestions(
    q: str = Query(..., min_length=1, description="Search query"),
    db: Session = Depends(get_db)
) -> Any:
    """Get search suggestions."""
    return SearchService.get_search_suggestions(db=db, query=q)

@router.get("/filters")
def get_search_filters(
    category_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
) -> Any:
    """Get available search filters."""
    return SearchService.get_search_filters(db=db, category_id=category_id)