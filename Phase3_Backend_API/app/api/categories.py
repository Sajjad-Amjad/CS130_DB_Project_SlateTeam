from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.category import Category
from app.schemas.category import CategoryOut

router = APIRouter()

@router.get("/", response_model=List[CategoryOut])
def get_all_categories(
    db: Session = Depends(get_db)
) -> Any:
    """Get all categories."""
    categories = db.query(Category).filter(Category.is_active == True).order_by(Category.display_order).all()
    return categories

@router.get("/{category_id}", response_model=CategoryOut)
def get_category_by_id(
    category_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Get category by ID."""
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category

@router.get("/{category_id}/subcategories", response_model=List[CategoryOut])
def get_subcategories(
    category_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Get subcategories for a category."""
    # First verify parent category exists
    parent_category = db.query(Category).filter(Category.category_id == category_id).first()
    if not parent_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    subcategories = db.query(Category).filter(
        Category.parent_category_id == category_id,
        Category.is_active == True
    ).order_by(Category.display_order).all()
    
    return subcategories