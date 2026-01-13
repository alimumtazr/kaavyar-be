from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    CARD = "card"
    COD = "cod"
    BANK_TRANSFER = "bank"


class OrderItem(BaseModel):
    product_id: str
    name: str
    price: int
    quantity: int
    size: str
    image: str


class ShippingAddress(BaseModel):
    first_name: str
    last_name: str
    address: str
    apartment: Optional[str] = None
    city: str
    postal_code: Optional[str] = None
    country: str = "Pakistan"
    phone: str


class OrderCreate(BaseModel):
    items: List[OrderItem]
    shipping_address: ShippingAddress
    email: str
    payment_method: PaymentMethod
    shipping_method: str = "standard"
    notes: Optional[str] = None


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None


class OrderInDB(BaseModel):
    id: str = Field(alias="_id")
    order_number: str
    user_id: Optional[str] = None
    items: List[OrderItem]
    shipping_address: ShippingAddress
    email: str
    subtotal: int
    shipping_cost: int
    total: int
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    shipping_method: str
    status: OrderStatus
    tracking_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


class OrderResponse(BaseModel):
    id: str
    order_number: str
    items: List[OrderItem]
    shipping_address: ShippingAddress
    email: str
    subtotal: int
    shipping_cost: int
    total: int
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    shipping_method: str
    status: OrderStatus
    tracking_number: Optional[str] = None
    created_at: datetime
    
    class Config:
        populate_by_name = True


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
    page: int
    page_size: int







