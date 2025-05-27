from typing import Optional, List
from pydantic import BaseModel

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    display_order: Optional[int] = None

class CategoryCreate(CategoryBase):
    parent_category_id: Optional[int] = None

class CategoryOut(CategoryBase):
    category_id: int
    parent_category_id: Optional[int] = None
    is_active: bool
    
    model_config = {"from_attributes": True}

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    
    model_config = {"from_attributes": True}