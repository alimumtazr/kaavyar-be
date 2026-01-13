"""
Seed script to populate database with initial product data.
Run with: python -m app.seed_data
"""
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from .core import settings

# Sample product data
PRODUCTS = [
    {
        "name": "Zara Embroidered Kurta",
        "price": 58000,
        "original_price": None,
        "category": "kurtas",
        "subcategory": "ready-to-wear",
        "description": "A timeless ivory kurta featuring intricate hand-embroidered details inspired by traditional Ajrak motifs. Crafted from premium cotton silk blend for ultimate comfort and elegance.",
        "fabric": "Cotton Silk Blend",
        "care": "Dry clean only",
        "sku": "AJR-KRT-001",
        "sizes": ["XS", "S", "M", "L", "XL"],
        "colors": ["Ivory", "Blush"],
        "badges": ["new"],
        "in_stock": True,
        "images": [
            "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=600&h=800&fit=crop",
            "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=600&h=800&fit=crop"
        ]
    },
    {
        "name": "Meera Bridal Lehenga",
        "price": 285000,
        "original_price": None,
        "category": "bridal-lehengas",
        "subcategory": "couture",
        "description": "An opulent bridal lehenga adorned with zardozi and resham embroidery. This masterpiece takes over 800 hours of handcraftsmanship.",
        "fabric": "Raw Silk with Velvet Border",
        "care": "Professional dry clean only",
        "sku": "AJR-BRD-001",
        "sizes": ["S", "M", "L"],
        "colors": ["Deep Red", "Maroon"],
        "badges": ["artisanal"],
        "in_stock": True,
        "images": [
            "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=600&h=800&fit=crop",
            "https://images.unsplash.com/photo-1594552072238-b8a33785b261?w=600&h=800&fit=crop"
        ]
    },
    {
        "name": "Ayesha Silk Kaftan",
        "price": 45000,
        "original_price": 55000,
        "category": "kaftans",
        "subcategory": "ready-to-wear",
        "description": "Flowing silk kaftan with delicate block print patterns. Perfect for intimate gatherings or elegant evening occasions.",
        "fabric": "Pure Silk",
        "care": "Dry clean recommended",
        "sku": "AJR-KFT-001",
        "sizes": ["One Size"],
        "colors": ["Sage Green", "Dusty Rose"],
        "badges": ["sale"],
        "in_stock": True,
        "images": [
            "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=600&h=800&fit=crop",
            "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=600&h=800&fit=crop"
        ]
    },
    {
        "name": "Sana Formal Gown",
        "price": 125000,
        "original_price": None,
        "category": "gowns",
        "subcategory": "couture",
        "description": "A stunning formal gown featuring cascading layers of tulle with hand-applied crystal embellishments.",
        "fabric": "Tulle with Silk Lining",
        "care": "Professional care only",
        "sku": "AJR-GWN-001",
        "sizes": ["XS", "S", "M", "L"],
        "colors": ["Midnight Blue"],
        "badges": ["new", "artisanal"],
        "in_stock": True,
        "images": [
            "https://images.unsplash.com/photo-1594552072238-b8a33785b261?w=600&h=800&fit=crop",
            "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=600&h=800&fit=crop"
        ]
    },
    {
        "name": "Raza Heritage Sherwani",
        "price": 175000,
        "original_price": None,
        "category": "sherwanis",
        "subcategory": "menswear",
        "description": "An exquisite sherwani showcasing the finest in traditional craftsmanship with gold thread work.",
        "fabric": "Jamawar Silk",
        "care": "Dry clean only",
        "sku": "AJR-SHR-001",
        "sizes": ["38", "40", "42", "44", "46"],
        "colors": ["Ivory Gold", "Black Gold"],
        "badges": ["artisanal"],
        "in_stock": True,
        "images": [
            "https://images.unsplash.com/photo-1593030761757-71fae45fa0e7?w=600&h=800&fit=crop",
            "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&h=800&fit=crop"
        ]
    },
    {
        "name": "Nadia Anarkali Set",
        "price": 78000,
        "original_price": None,
        "category": "anarkalis",
        "subcategory": "ready-to-wear",
        "description": "A graceful anarkali featuring a fitted bodice and flowing floor-length flare with gota patti work.",
        "fabric": "Georgette with Silk Lining",
        "care": "Dry clean only",
        "sku": "AJR-ANK-001",
        "sizes": ["XS", "S", "M", "L", "XL"],
        "colors": ["Emerald", "Ruby"],
        "badges": [],
        "in_stock": True,
        "images": [
            "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=600&h=800&fit=crop",
            "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=600&h=800&fit=crop"
        ]
    },
    {
        "name": "Layla Embroidered Top",
        "price": 28000,
        "original_price": None,
        "category": "tops",
        "subcategory": "ready-to-wear",
        "description": "A versatile embroidered top with mirror work details and subtle thread embroidery.",
        "fabric": "Premium Cotton",
        "care": "Machine wash cold",
        "sku": "AJR-TOP-001",
        "sizes": ["XS", "S", "M", "L"],
        "colors": ["White", "Black"],
        "badges": ["new"],
        "in_stock": True,
        "images": [
            "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=600&h=800&fit=crop",
            "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=600&h=800&fit=crop"
        ]
    },
    {
        "name": "Amara Palazzo Set",
        "price": 52000,
        "original_price": 65000,
        "category": "sets",
        "subcategory": "ready-to-wear",
        "description": "An effortlessly chic matching set with tailored kurta and wide-leg palazzo pants.",
        "fabric": "Cotton Lawn",
        "care": "Machine wash cold",
        "sku": "AJR-SET-001",
        "sizes": ["S", "M", "L"],
        "colors": ["Coral", "Teal"],
        "badges": ["sale"],
        "in_stock": True,
        "images": [
            "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=600&h=800&fit=crop",
            "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=600&h=800&fit=crop"
        ]
    },
    {
        "name": "Farah Bridal Saree",
        "price": 195000,
        "original_price": None,
        "category": "bridal-sarees",
        "subcategory": "couture",
        "description": "A breathtaking bridal saree featuring hand-woven zari work. Comes with stitched blouse.",
        "fabric": "Banarasi Silk",
        "care": "Professional dry clean only",
        "sku": "AJR-BSR-001",
        "sizes": ["One Size"],
        "colors": ["Champagne Gold"],
        "badges": ["artisanal"],
        "in_stock": True,
        "images": [
            "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=600&h=800&fit=crop",
            "https://images.unsplash.com/photo-1594552072238-b8a33785b261?w=600&h=800&fit=crop"
        ]
    },
    {
        "name": "Hassan Kurta Shalwar",
        "price": 48000,
        "original_price": None,
        "category": "kurta-shalwar",
        "subcategory": "menswear",
        "description": "Classic kurta shalwar set with subtle tone-on-tone embroidery on neckline and cuffs.",
        "fabric": "Swiss Cotton",
        "care": "Machine wash cold",
        "sku": "AJR-MKS-001",
        "sizes": ["38", "40", "42", "44"],
        "colors": ["Off White", "Beige"],
        "badges": [],
        "in_stock": True,
        "images": [
            "https://images.unsplash.com/photo-1593030761757-71fae45fa0e7?w=600&h=800&fit=crop",
            "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&h=800&fit=crop"
        ]
    },
    {
        "name": "Sadia Velvet Jacket",
        "price": 68000,
        "original_price": None,
        "category": "jackets",
        "subcategory": "ready-to-wear",
        "description": "Luxurious velvet jacket with antique gold embroidery. Perfect for layering.",
        "fabric": "Velvet with Silk Lining",
        "care": "Dry clean only",
        "sku": "AJR-JKT-001",
        "sizes": ["XS", "S", "M", "L"],
        "colors": ["Burgundy", "Forest Green"],
        "badges": ["new"],
        "in_stock": True,
        "images": [
            "https://images.unsplash.com/photo-1594552072238-b8a33785b261?w=600&h=800&fit=crop",
            "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=600&h=800&fit=crop"
        ]
    },
    {
        "name": "Ayaan Waistcoat",
        "price": 42000,
        "original_price": None,
        "category": "waistcoats",
        "subcategory": "menswear",
        "description": "Sophisticated waistcoat featuring subtle geometric embroidery.",
        "fabric": "Wool Blend",
        "care": "Dry clean only",
        "sku": "AJR-WST-001",
        "sizes": ["38", "40", "42", "44", "46"],
        "colors": ["Navy", "Charcoal"],
        "badges": [],
        "in_stock": True,
        "images": [
            "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&h=800&fit=crop",
            "https://images.unsplash.com/photo-1593030761757-71fae45fa0e7?w=600&h=800&fit=crop"
        ]
    },
    {
        "name": "Aria Silk Scarf",
        "price": 12000,
        "original_price": None,
        "category": "accessories",
        "subcategory": "accessories",
        "description": "Hand-printed silk scarf featuring traditional Ajrak patterns.",
        "fabric": "Pure Silk",
        "care": "Dry clean only",
        "sku": "AJR-SCF-001",
        "sizes": ["One Size"],
        "colors": ["Multi"],
        "badges": [],
        "in_stock": True,
        "images": [
            "https://images.unsplash.com/photo-1611085583191-a3b181a88401?w=600&h=800&fit=crop",
            "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=600&h=800&fit=crop"
        ]
    },
    {
        "name": "Hira Statement Clutch",
        "price": 18000,
        "original_price": None,
        "category": "accessories",
        "subcategory": "accessories",
        "description": "Elegant box clutch with intricate metalwork and semi-precious stones.",
        "fabric": "Metal & Silk Lining",
        "care": "Store in dust bag",
        "sku": "AJR-CLT-001",
        "sizes": ["One Size"],
        "colors": ["Gold", "Silver"],
        "badges": ["new"],
        "in_stock": True,
        "images": [
            "https://images.unsplash.com/photo-1611085583191-a3b181a88401?w=600&h=800&fit=crop",
            "https://images.unsplash.com/photo-1594552072238-b8a33785b261?w=600&h=800&fit=crop"
        ]
    },
    {
        "name": "Kiran Formal Lehenga",
        "price": 145000,
        "original_price": 165000,
        "category": "lehengas",
        "subcategory": "couture",
        "description": "Elegant formal lehenga perfect for engagement ceremonies with pearl embellishments.",
        "fabric": "Organza with Silk Base",
        "care": "Professional dry clean only",
        "sku": "AJR-FLH-001",
        "sizes": ["S", "M", "L"],
        "colors": ["Powder Pink", "Mint Green"],
        "badges": ["sale", "artisanal"],
        "in_stock": True,
        "images": [
            "https://images.unsplash.com/photo-1594552072238-b8a33785b261?w=600&h=800&fit=crop",
            "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=600&h=800&fit=crop"
        ]
    }
]

# Use neutral, people-free imagery across all seed products
NEUTRAL_IMAGES = [
    "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600&h=800&fit=crop",
    "https://images.unsplash.com/photo-1503341455253-b2e723bb3dbb?w=600&h=800&fit=crop",
]

for product in PRODUCTS:
    product["images"] = NEUTRAL_IMAGES


async def seed_database():
    """Seed the database with initial data."""
    client = AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
    db = client[settings.DATABASE_NAME]
    
    # Check if products already exist
    existing_count = await db.products.count_documents({})
    if existing_count > 0:
        print(f"Database already has {existing_count} products. Skipping seed.")
        return
    
    # Insert products
    now = datetime.utcnow()
    for product in PRODUCTS:
        product["created_at"] = now
        product["updated_at"] = now
    
    result = await db.products.insert_many(PRODUCTS)
    print(f"Inserted {len(result.inserted_ids)} products")
    
    # Create admin user with specified credentials
    from .core import get_password_hash
    admin_email = "admin.kavyaar@gmail.com"
    admin_exists = await db.users.find_one({"email": admin_email})
    if not admin_exists:
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
        print(f"Created admin user: {admin_email}")
    
    client.close()
    print("Seed completed!")


if __name__ == "__main__":
    asyncio.run(seed_database())

