from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator

# Base User Schema
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    user_role: str
    country: Optional[str] = None
    language: Optional[str] = None

# Schema for creating a user
class UserCreate(UserBase):
    password: str
    
    @field_validator('password')
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

# Schema for user output
class UserOut(UserBase):
    user_id: int
    profile_picture: Optional[str] = None
    registration_date: datetime
    is_active: bool
    last_login: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

# Schema for updating a user
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    profile_picture: Optional[str] = None
    
    model_config = {"from_attributes": True}

# Schema for changing password
class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

# Login Schema
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Token Schema
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Token data schema
class TokenData(BaseModel):
    user_id: Optional[int] = None