from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ProductCategory(str, Enum):
    KURTAS = "kurtas"
    KAFTANS = "kaftans"
    TOPS = "tops"
    PANTS = "pants"
    SETS = "sets"
    ANARKALIS = "anarkalis"
    KURTA_SETS = "kurta-sets"
    SAREES = "sarees"
    JACKETS = "jackets"
    LEHENGAS = "lehengas"
    GOWNS = "gowns"
    SHERWANIS = "sherwanis"
    KURTA_SHALWAR = "kurta-shalwar"
    WAISTCOATS = "waistcoats"
    BRIDAL_LEHENGAS = "bridal-lehengas"
    BRIDAL_SAREES = "bridal-sarees"
    FORMAL_KURTAS = "formal-kurtas"
    ACCESSORIES = "accessories"


class ProductSubcategory(str, Enum):
    READY_TO_WEAR = "ready-to-wear"
    COUTURE = "couture"
    MENSWEAR = "menswear"
    ACCESSORIES = "accessories"
    BRIDAL = "bridal"


class ProductBadge(str, Enum):
    NEW = "new"
    SALE = "sale"
    ARTISANAL = "artisanal"
    SOLD_OUT = "sold-out"


class ProductBase(BaseModel):
    name: str
    price: int
    original_price: Optional[int] = None
    category: str
    subcategory: str
    description: str
    fabric: str
    care: str
    sku: str
    sizes: List[str]
    colors: List[str]
    badges: List[str] = []
    in_stock: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[int] = None
    original_price: Optional[int] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: Optional[str] = None
    fabric: Optional[str] = None
    care: Optional[str] = None
    sizes: Optional[List[str]] = None
    colors: Optional[List[str]] = None
    badges: Optional[List[str]] = None
    in_stock: Optional[bool] = None


class ProductInDB(ProductBase):
    id: str = Field(alias="_id")
    images: List[str] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


class ProductResponse(ProductBase):
    id: str
    images: List[str] = []
    created_at: datetime
    
    class Config:
        populate_by_name = True


class ProductListResponse(BaseModel):
    products: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int







