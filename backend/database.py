from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

db = Database()

async def connect_to_mongo():
    """Connect to MongoDB"""
    try:
        db.client = AsyncIOMotorClient(settings.mongodb_uri)
        db.db = db.client[settings.database_name]
        
        # Test connection
        await db.client.admin.command('ping')
        logger.info(f"✅ Connected to MongoDB: {settings.database_name}")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        raise

async def close_mongo_connection():
    """Close MongoDB connection"""
    if db.client:
        db.client.close()
        logger.info("✅ MongoDB connection closed")

async def create_indexes():
    """Create database indexes"""
    try:
        # Donor indexes
        await db.db.donors.create_index("location.phone", unique=True)
        await db.db.donors.create_index("location.email", unique=True, sparse=True)
        await db.db.donors.create_index("medical.blood_type")
        await db.db.donors.create_index("location.city")
        await db.db.donors.create_index("is_active")
        
        # Hospital indexes
        await db.db.hospitals.create_index("username", unique=True)
        await db.db.hospitals.create_index("email", unique=True)
        await db.db.hospitals.create_index("phone", unique=True)
        await db.db.hospitals.create_index("location.city")
        await db.db.hospitals.create_index("is_verified")
        
        # Token indexes
        await db.db.update_tokens.create_index("token", unique=True)
        await db.db.update_tokens.create_index("expires_at")
        await db.db.password_reset_tokens.create_index("token", unique=True)
        await db.db.rate_limits.create_index("donor_phone")
        
        logger.info("✅ Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        raise

def get_db():
    """Dependency for getting database"""
    return db.db