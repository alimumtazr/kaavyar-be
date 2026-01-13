from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime
from bson import ObjectId
from typing import Optional

from ..core import get_database, get_admin_user, get_password_hash
from ..models import OrderStatus, PaymentStatus

router = APIRouter(prefix="/admin", tags=["Admin"])


# Dashboard stats
@router.get("/dashboard")
async def get_dashboard_stats(admin = Depends(get_admin_user)):
    """Get dashboard statistics."""
    db = get_database()
    
    # Total products
    total_products = await db.products.count_documents({})
    
    # Total orders
    total_orders = await db.orders.count_documents({})
    
    # Total customers
    total_customers = await db.users.count_documents({"is_admin": False})
    
    # Revenue (paid orders)
    revenue_pipeline = [
        {"$match": {"payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$total"}}}
    ]
    revenue_result = await db.orders.aggregate(revenue_pipeline).to_list(length=1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0
    
    # Orders by status
    status_pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_result = await db.orders.aggregate(status_pipeline).to_list(length=10)
    orders_by_status = {item["_id"]: item["count"] for item in status_result}
    
    # Recent orders (last 5)
    recent_orders = await db.orders.find().sort("created_at", -1).limit(5).to_list(length=5)
    
    # Low stock products (less than 5 in stock or out of stock)
    out_of_stock = await db.products.count_documents({"in_stock": False})
    
    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "total_customers": total_customers,
        "total_revenue": total_revenue,
        "orders_by_status": orders_by_status,
        "pending_orders": orders_by_status.get("pending", 0),
        "out_of_stock_products": out_of_stock,
        "recent_orders": [
            {
                "id": str(o["_id"]),
                "order_number": o["order_number"],
                "email": o["email"],
                "total": o["total"],
                "status": o["status"],
                "created_at": o["created_at"]
            }
            for o in recent_orders
        ]
    }


# Customers management
@router.get("/customers")
async def get_all_customers(
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin = Depends(get_admin_user)
):
    """Get all customers."""
    db = get_database()
    
    query = {"is_admin": False}
    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}}
        ]
    
    total = await db.users.count_documents(query)
    
    skip = (page - 1) * page_size
    cursor = db.users.find(query).sort("created_at", -1).skip(skip).limit(page_size)
    customers = await cursor.to_list(length=page_size)
    
    # Get order counts for each customer
    customer_list = []
    for c in customers:
        order_count = await db.orders.count_documents({"user_id": str(c["_id"])})
        customer_list.append({
            "id": str(c["_id"]),
            "email": c["email"],
            "first_name": c["first_name"],
            "last_name": c["last_name"],
            "phone": c.get("phone"),
            "is_active": c.get("is_active", True),
            "order_count": order_count,
            "created_at": c["created_at"]
        })
    
    return {
        "customers": customer_list,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/customers/{customer_id}")
async def get_customer_details(
    customer_id: str,
    admin = Depends(get_admin_user)
):
    """Get customer details with their orders."""
    db = get_database()
    
    try:
        customer = await db.users.find_one({"_id": ObjectId(customer_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid customer ID")
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get customer orders
    orders = await db.orders.find({"user_id": customer_id}).sort("created_at", -1).to_list(length=100)
    
    return {
        "customer": {
            "id": str(customer["_id"]),
            "email": customer["email"],
            "first_name": customer["first_name"],
            "last_name": customer["last_name"],
            "phone": customer.get("phone"),
            "is_active": customer.get("is_active", True),
            "addresses": customer.get("addresses", []),
            "created_at": customer["created_at"]
        },
        "orders": [
            {
                "id": str(o["_id"]),
                "order_number": o["order_number"],
                "total": o["total"],
                "status": o["status"],
                "payment_status": o["payment_status"],
                "created_at": o["created_at"]
            }
            for o in orders
        ]
    }


@router.put("/customers/{customer_id}/status")
async def toggle_customer_status(
    customer_id: str,
    is_active: bool,
    admin = Depends(get_admin_user)
):
    """Enable/disable customer account."""
    db = get_database()
    
    try:
        oid = ObjectId(customer_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid customer ID")
    
    result = await db.users.update_one(
        {"_id": oid},
        {"$set": {"is_active": is_active, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return {"message": f"Customer {'enabled' if is_active else 'disabled'} successfully"}


# Seed admin user endpoint (for initial setup)
@router.post("/seed-admin")
async def seed_admin_user():
    """Create admin user if it doesn't exist."""
    db = get_database()
    
    admin_email = "admin.kavyaar@gmail.com"
    existing = await db.users.find_one({"email": admin_email})
    
    if existing:
        return {"message": "Admin user already exists"}
    
    now = datetime.utcnow()
    admin_user = {
        "email": admin_email,
        "first_name": "Admin",
        "last_name": "Kavyaar",
        "phone": "+92 300 0000000",
        "hashed_password": get_password_hash("Admin@kavyaar1805"),
        "is_active": True,
        "is_admin": True,
        "addresses": [],
        "wishlist": [],
        "created_at": now,
        "updated_at": now
    }
    
    await db.users.insert_one(admin_user)
    return {"message": "Admin user created successfully"}





