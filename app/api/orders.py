from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime
from bson import ObjectId
from typing import Optional
import random
import string

from ..core import get_database, get_current_user_optional, get_current_active_user, get_admin_user
from ..models import (
    OrderCreate, OrderUpdate, OrderResponse, OrderListResponse,
    OrderStatus, PaymentStatus
)

router = APIRouter(prefix="/orders", tags=["Orders"])


def generate_order_number() -> str:
    """Generate unique order number."""
    timestamp = datetime.utcnow().strftime("%y%m%d")
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"AJR-{timestamp}-{random_part}"


def serialize_order(order: dict) -> dict:
    """Convert MongoDB order document to response format."""
    return {
        "id": str(order["_id"]),
        "order_number": order["order_number"],
        "items": order["items"],
        "shipping_address": order["shipping_address"],
        "email": order["email"],
        "subtotal": order["subtotal"],
        "shipping_cost": order["shipping_cost"],
        "total": order["total"],
        "payment_method": order["payment_method"],
        "payment_status": order["payment_status"],
        "shipping_method": order["shipping_method"],
        "status": order["status"],
        "tracking_number": order.get("tracking_number"),
        "created_at": order["created_at"]
    }


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user = Depends(get_current_user_optional)
):
    """Create a new order."""
    db = get_database()
    
    # Calculate totals
    subtotal = sum(item.price * item.quantity for item in order_data.items)
    
    # Shipping cost logic
    if order_data.shipping_method == "express":
        shipping_cost = 3000
    elif subtotal >= 50000:
        shipping_cost = 0
    else:
        shipping_cost = 1500
    
    total = subtotal + shipping_cost
    
    # Create order document
    now = datetime.utcnow()
    order_doc = {
        "order_number": generate_order_number(),
        "user_id": str(current_user["_id"]) if current_user else None,
        "items": [item.model_dump() for item in order_data.items],
        "shipping_address": order_data.shipping_address.model_dump(),
        "email": order_data.email,
        "subtotal": subtotal,
        "shipping_cost": shipping_cost,
        "total": total,
        "payment_method": order_data.payment_method,
        "payment_status": PaymentStatus.PENDING if order_data.payment_method != "cod" else PaymentStatus.PENDING,
        "shipping_method": order_data.shipping_method,
        "status": OrderStatus.PENDING,
        "notes": order_data.notes,
        "created_at": now,
        "updated_at": now
    }
    
    # For COD, set payment as pending until delivery
    # For card/bank, in real scenario we'd process payment here
    if order_data.payment_method == "card":
        # Mock successful payment
        order_doc["payment_status"] = PaymentStatus.PAID
        order_doc["status"] = OrderStatus.CONFIRMED
    
    result = await db.orders.insert_one(order_doc)
    order_doc["_id"] = result.inserted_id
    
    return serialize_order(order_doc)


@router.get("", response_model=OrderListResponse)
async def get_user_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user = Depends(get_current_active_user)
):
    """Get current user's orders."""
    db = get_database()
    
    user_id = str(current_user["_id"])
    
    # Count total
    total = await db.orders.count_documents({"user_id": user_id})
    
    # Get orders
    skip = (page - 1) * page_size
    cursor = db.orders.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(page_size)
    orders = await cursor.to_list(length=page_size)
    
    return {
        "orders": [serialize_order(o) for o in orders],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user = Depends(get_current_user_optional)
):
    """Get order by ID or order number."""
    db = get_database()
    
    # Try to find by ID first, then by order number
    order = None
    try:
        order = await db.orders.find_one({"_id": ObjectId(order_id)})
    except:
        order = await db.orders.find_one({"order_number": order_id})
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check authorization - user can only view their own orders
    if current_user:
        user_id = str(current_user["_id"])
        if order.get("user_id") and order["user_id"] != user_id and not current_user.get("is_admin"):
            raise HTTPException(status_code=403, detail="Not authorized to view this order")
    
    return serialize_order(order)


@router.get("/track/{order_number}", response_model=OrderResponse)
async def track_order(order_number: str, email: str):
    """Track order by order number and email (for guests)."""
    db = get_database()
    
    order = await db.orders.find_one({
        "order_number": order_number,
        "email": email.lower()
    })
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return serialize_order(order)


# Admin routes
@router.get("/admin/all", response_model=OrderListResponse)
async def get_all_orders(
    status: Optional[OrderStatus] = None,
    payment_status: Optional[PaymentStatus] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin = Depends(get_admin_user)
):
    """Get all orders (admin only)."""
    db = get_database()
    
    query = {}
    if status:
        query["status"] = status
    if payment_status:
        query["payment_status"] = payment_status
    
    total = await db.orders.count_documents(query)
    
    skip = (page - 1) * page_size
    cursor = db.orders.find(query).sort("created_at", -1).skip(skip).limit(page_size)
    orders = await cursor.to_list(length=page_size)
    
    return {
        "orders": [serialize_order(o) for o in orders],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    order_data: OrderUpdate,
    admin = Depends(get_admin_user)
):
    """Update order status (admin only)."""
    db = get_database()
    
    try:
        oid = ObjectId(order_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid order ID")
    
    update_data = {k: v for k, v in order_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.orders.update_one(
        {"_id": oid},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = await db.orders.find_one({"_id": oid})
    return serialize_order(order)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: str,
    current_user = Depends(get_current_active_user)
):
    """Cancel an order (user can cancel pending orders)."""
    db = get_database()
    
    try:
        oid = ObjectId(order_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid order ID")
    
    order = await db.orders.find_one({"_id": oid})
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check authorization
    user_id = str(current_user["_id"])
    if order.get("user_id") != user_id and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Can only cancel pending or confirmed orders
    if order["status"] not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel order in current status"
        )
    
    await db.orders.update_one(
        {"_id": oid},
        {
            "$set": {
                "status": OrderStatus.CANCELLED,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    order = await db.orders.find_one({"_id": oid})
    return serialize_order(order)


@router.get("/admin/stats")
async def get_order_stats(admin = Depends(get_admin_user)):
    """Get order statistics (admin only)."""
    db = get_database()
    
    # Total orders
    total_orders = await db.orders.count_documents({})
    
    # Orders by status
    status_pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_result = await db.orders.aggregate(status_pipeline).to_list(length=10)
    orders_by_status = {item["_id"]: item["count"] for item in status_result}
    
    # Revenue
    revenue_pipeline = [
        {"$match": {"payment_status": PaymentStatus.PAID}},
        {"$group": {"_id": None, "total": {"$sum": "$total"}}}
    ]
    revenue_result = await db.orders.aggregate(revenue_pipeline).to_list(length=1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0
    
    # Pending orders
    pending_orders = await db.orders.count_documents({"status": OrderStatus.PENDING})
    
    return {
        "total_orders": total_orders,
        "orders_by_status": orders_by_status,
        "total_revenue": total_revenue,
        "pending_orders": pending_orders
    }


