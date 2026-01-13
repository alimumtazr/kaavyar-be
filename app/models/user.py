from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId


class Address(BaseModel):
    first_name: str
    last_name: str
    address: str
    apartment: Optional[str] = None
    city: str
    postal_code: Optional[str] = None
    country: str = "Pakistan"
    phone: str
    is_default: bool = False


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class UserInDB(UserBase):
    id: str = Field(alias="_id")
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    addresses: List[Address] = []
    wishlist: List[str] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class UserResponse(UserBase):
    id: str
    is_active: bool
    is_admin: bool
    addresses: List[Address] = []
    wishlist: List[str] = []
    created_at: datetime
    
    class Config:
        populate_by_name = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None







