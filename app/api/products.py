from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Query
from datetime import datetime
from bson import ObjectId
from typing import Optional, List
import uuid

from ..core import get_database, get_admin_user, upload_file, delete_file
from ..models import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse

router = APIRouter(prefix="/products", tags=["Products"])


def serialize_product(product: dict) -> dict:
    """Convert MongoDB product document to response format."""
    return {
        "id": str(product["_id"]),
        "name": product["name"],
        "price": product["price"],
        "original_price": product.get("original_price"),
        "category": product["category"],
        "subcategory": product["subcategory"],
        "description": product["description"],
        "fabric": product["fabric"],
        "care": product["care"],
        "sku": product["sku"],
        "sizes": product["sizes"],
        "colors": product["colors"],
        "badges": product.get("badges", []),
        "in_stock": product.get("in_stock", True),
        "images": product.get("images", []),
        "created_at": product["created_at"]
    }


@router.get("", response_model=ProductListResponse)
async def get_products(
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    in_stock: Optional[bool] = None,
    badges: Optional[str] = None,
    sort_by: str = Query("created_at", enum=["created_at", "price", "name"]),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """Get paginated list of products with filters."""
    db = get_database()
    
    # Build query
    query = {}
    
    if category:
        query["category"] = category
    if subcategory:
        query["subcategory"] = subcategory
    if search:
        query["$text"] = {"$search": search}
    if min_price is not None:
        query["price"] = {"$gte": min_price}
    if max_price is not None:
        query.setdefault("price", {})["$lte"] = max_price
    if in_stock is not None:
        query["in_stock"] = in_stock
    if badges:
        badge_list = badges.split(",")
        query["badges"] = {"$in": badge_list}
    
    # Count total
    total = await db.products.count_documents(query)
    
    # Sort
    sort_direction = 1 if sort_order == "asc" else -1
    
    # Get products
    skip = (page - 1) * page_size
    cursor = db.products.find(query).sort(sort_by, sort_direction).skip(skip).limit(page_size)
    products = await cursor.to_list(length=page_size)
    
    return {
        "products": [serialize_product(p) for p in products],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/featured")
async def get_featured_products(limit: int = Query(8, ge=1, le=20)):
    """Get featured/curated products."""
    db = get_database()
    
    # Get a mix of new and artisanal products
    cursor = db.products.find(
        {"badges": {"$in": ["new", "artisanal"]}, "in_stock": True}
    ).limit(limit)
    
    products = await cursor.to_list(length=limit)
    
    # If not enough, fill with random products
    if len(products) < limit:
        existing_ids = [p["_id"] for p in products]
        additional = await db.products.find(
            {"_id": {"$nin": existing_ids}, "in_stock": True}
        ).limit(limit - len(products)).to_list(length=limit - len(products))
        products.extend(additional)
    
    return [serialize_product(p) for p in products]


@router.get("/new-arrivals")
async def get_new_arrivals(limit: int = Query(8, ge=1, le=20)):
    """Get new arrival products."""
    db = get_database()
    
    cursor = db.products.find(
        {"badges": "new", "in_stock": True}
    ).sort("created_at", -1).limit(limit)
    
    products = await cursor.to_list(length=limit)
    return [serialize_product(p) for p in products]


@router.get("/categories")
async def get_categories():
    """Get all product categories with counts."""
    db = get_database()
    
    pipeline = [
        {"$group": {"_id": "$subcategory", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    
    result = await db.products.aggregate(pipeline).to_list(length=100)
    
    return {item["_id"]: item["count"] for item in result if item["_id"]}


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    """Get a single product by ID."""
    db = get_database()
    
    try:
        product = await db.products.find_one({"_id": ObjectId(product_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return serialize_product(product)


@router.get("/sku/{sku}", response_model=ProductResponse)
async def get_product_by_sku(sku: str):
    """Get a single product by SKU."""
    db = get_database()
    
    product = await db.products.find_one({"sku": sku})
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return serialize_product(product)


@router.get("/{product_id}/related")
async def get_related_products(product_id: str, limit: int = Query(4, ge=1, le=10)):
    """Get related products."""
    db = get_database()
    
    try:
        product = await db.products.find_one({"_id": ObjectId(product_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Find products in same subcategory
    cursor = db.products.find({
        "_id": {"$ne": product["_id"]},
        "subcategory": product["subcategory"],
        "in_stock": True
    }).limit(limit)
    
    related = await cursor.to_list(length=limit)
    
    # If not enough, get from same category
    if len(related) < limit:
        existing_ids = [p["_id"] for p in related] + [product["_id"]]
        additional = await db.products.find({
            "_id": {"$nin": existing_ids},
            "category": product["category"],
            "in_stock": True
        }).limit(limit - len(related)).to_list(length=limit - len(related))
        related.extend(additional)
    
    return [serialize_product(p) for p in related]


# Admin routes
@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    admin = Depends(get_admin_user)
):
    """Create a new product (admin only)."""
    db = get_database()
    
    # Check if SKU exists
    existing = await db.products.find_one({"sku": product_data.sku})
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")
    
    now = datetime.utcnow()
    product_doc = {
        **product_data.model_dump(),
        "images": [],
        "created_at": now,
        "updated_at": now
    }
    
    result = await db.products.insert_one(product_doc)
    product_doc["_id"] = result.inserted_id
    
    return serialize_product(product_doc)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    admin = Depends(get_admin_user)
):
    """Update a product (admin only)."""
    db = get_database()
    
    try:
        oid = ObjectId(product_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    update_data = {k: v for k, v in product_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.products.update_one(
        {"_id": oid},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = await db.products.find_one({"_id": oid})
    return serialize_product(product)


@router.post("/{product_id}/images")
async def upload_product_image(
    product_id: str,
    file: UploadFile = File(...),
    admin = Depends(get_admin_user)
):
    """Upload product image (admin only)."""
    db = get_database()
    
    try:
        oid = ObjectId(product_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    product = await db.products.find_one({"_id": oid})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    object_name = f"products/{product_id}/{uuid.uuid4()}.{ext}"
    
    # Upload to MinIO
    file_data = await file.read()
    image_url = await upload_file(file_data, object_name, file.content_type)
    
    # Add to product images
    await db.products.update_one(
        {"_id": oid},
        {
            "$push": {"images": image_url},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return {"url": image_url, "message": "Image uploaded successfully"}


@router.delete("/{product_id}/images")
async def delete_product_image(
    product_id: str,
    image_url: str,
    admin = Depends(get_admin_user)
):
    """Delete product image (admin only)."""
    db = get_database()
    
    try:
        oid = ObjectId(product_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    # Extract object name from URL
    parts = image_url.split("/")
    object_name = "/".join(parts[-3:]) if len(parts) >= 3 else None
    
    if object_name:
        await delete_file(object_name)
    
    await db.products.update_one(
        {"_id": oid},
        {
            "$pull": {"images": image_url},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return {"message": "Image deleted successfully"}


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    admin = Depends(get_admin_user)
):
    """Delete a product (admin only)."""
    db = get_database()
    
    try:
        oid = ObjectId(product_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    result = await db.products.delete_one({"_id": oid})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return None


