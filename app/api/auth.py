from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from bson import ObjectId
from typing import Optional

from ..core import (
    get_database,
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user,
    settings
)
from ..models import UserCreate, UserResponse, Token, Address

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user."""
    db = get_database()
    
    # Check if email already exists
    existing_user = await db.users.find_one({"email": user_data.email.lower()})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user document
    now = datetime.utcnow()
    user_doc = {
        "email": user_data.email.lower(),
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "phone": user_data.phone,
        "hashed_password": get_password_hash(user_data.password),
        "is_active": True,
        "is_admin": False,
        "addresses": [],
        "wishlist": [],
        "created_at": now,
        "updated_at": now
    }
    
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    
    return {
        "id": str(user_doc["_id"]),
        "email": user_doc["email"],
        "first_name": user_doc["first_name"],
        "last_name": user_doc["last_name"],
        "phone": user_doc["phone"],
        "is_active": user_doc["is_active"],
        "is_admin": user_doc["is_admin"],
        "addresses": user_doc["addresses"],
        "wishlist": user_doc["wishlist"],
        "created_at": user_doc["created_at"]
    }


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token."""
    db = get_database()
    
    user = await db.users.find_one({"email": form_data.username.lower()})
    
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is disabled"
        )
    
    access_token = create_access_token(
        data={"sub": str(user["_id"])},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_active_user)):
    """Get current user information."""
    return {
        "id": str(current_user["_id"]),
        "email": current_user["email"],
        "first_name": current_user["first_name"],
        "last_name": current_user["last_name"],
        "phone": current_user.get("phone"),
        "is_active": current_user["is_active"],
        "is_admin": current_user.get("is_admin", False),
        "addresses": current_user.get("addresses", []),
        "wishlist": current_user.get("wishlist", []),
        "created_at": current_user["created_at"]
    }


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone: Optional[str] = None,
    current_user = Depends(get_current_active_user)
):
    """Update current user information."""
    db = get_database()
    
    update_data = {"updated_at": datetime.utcnow()}
    if first_name:
        update_data["first_name"] = first_name
    if last_name:
        update_data["last_name"] = last_name
    if phone:
        update_data["phone"] = phone
    
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": update_data}
    )
    
    updated_user = await db.users.find_one({"_id": current_user["_id"]})
    
    return {
        "id": str(updated_user["_id"]),
        "email": updated_user["email"],
        "first_name": updated_user["first_name"],
        "last_name": updated_user["last_name"],
        "phone": updated_user.get("phone"),
        "is_active": updated_user["is_active"],
        "is_admin": updated_user.get("is_admin", False),
        "addresses": updated_user.get("addresses", []),
        "wishlist": updated_user.get("wishlist", []),
        "created_at": updated_user["created_at"]
    }


@router.post("/me/addresses", response_model=UserResponse)
async def add_address(
    address: Address,
    current_user = Depends(get_current_active_user)
):
    """Add a new address."""
    db = get_database()
    
    address_dict = address.model_dump()
    
    # If this is set as default, unset other defaults
    if address.is_default:
        await db.users.update_one(
            {"_id": current_user["_id"]},
            {"$set": {"addresses.$[].is_default": False}}
        )
    
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {
            "$push": {"addresses": address_dict},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    updated_user = await db.users.find_one({"_id": current_user["_id"]})
    
    return {
        "id": str(updated_user["_id"]),
        "email": updated_user["email"],
        "first_name": updated_user["first_name"],
        "last_name": updated_user["last_name"],
        "phone": updated_user.get("phone"),
        "is_active": updated_user["is_active"],
        "is_admin": updated_user.get("is_admin", False),
        "addresses": updated_user.get("addresses", []),
        "wishlist": updated_user.get("wishlist", []),
        "created_at": updated_user["created_at"]
    }


@router.post("/me/wishlist/{product_id}")
async def toggle_wishlist(
    product_id: str,
    current_user = Depends(get_current_active_user)
):
    """Toggle product in wishlist."""
    db = get_database()
    
    wishlist = current_user.get("wishlist", [])
    
    if product_id in wishlist:
        # Remove from wishlist
        await db.users.update_one(
            {"_id": current_user["_id"]},
            {
                "$pull": {"wishlist": product_id},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return {"message": "Removed from wishlist", "in_wishlist": False}
    else:
        # Add to wishlist
        await db.users.update_one(
            {"_id": current_user["_id"]},
            {
                "$addToSet": {"wishlist": product_id},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return {"message": "Added to wishlist", "in_wishlist": True}


@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user = Depends(get_current_active_user)
):
    """Change user password."""
    db = get_database()
    
    if not verify_password(current_password, current_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {
            "$set": {
                "hashed_password": get_password_hash(new_password),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Password changed successfully"}







