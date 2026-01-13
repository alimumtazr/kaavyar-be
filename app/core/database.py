from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.database import Database
from typing import Optional
from .config import settings


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[Database] = None


mongo = MongoDB()


async def connect_to_mongo():
    """Create database connection."""
    mongo.client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000
    )
    mongo.db = mongo.client[settings.DATABASE_NAME]
    
    # Test connection
    try:
        await mongo.client.admin.command('ping')
        print(f"Connected to MongoDB Atlas: {settings.DATABASE_NAME}")
    except Exception as e:
        print(f"MongoDB connection error: {e}")
        raise
    
    # Create indexes
    await create_indexes()


async def close_mongo_connection():
    """Close database connection."""
    if mongo.client:
        mongo.client.close()
        print("Closed MongoDB connection")


async def create_indexes():
    """Create necessary indexes."""
    # Users collection indexes
    await mongo.db.users.create_index("email", unique=True)
    
    # Products collection indexes
    await mongo.db.products.create_index("sku", unique=True)
    await mongo.db.products.create_index("category")
    await mongo.db.products.create_index("subcategory")
    await mongo.db.products.create_index([("name", "text"), ("description", "text")])
    
    # Orders collection indexes
    await mongo.db.orders.create_index("user_id")
    await mongo.db.orders.create_index("order_number", unique=True)
    await mongo.db.orders.create_index("created_at")


def get_database() -> Database:
    """Get database instance."""
    return mongo.db

