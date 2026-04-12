# backend\database.py
import asyncio
from datetime import datetime

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
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
        await db.db.donors.create_index("created_at")
        
        # Hospital indexes
        await db.db.hospitals.create_index("username", unique=True)
        await db.db.hospitals.create_index("email", unique=True)
        await db.db.hospitals.create_index("phone", unique=True)
        await db.db.hospitals.create_index("license_number", unique=True)
        await db.db.hospitals.create_index("location.city")
        await db.db.hospitals.create_index("is_verified")
        await db.db.hospitals.create_index("is_active")
        
        # Token indexes
        await db.db.update_tokens.create_index("hashed_token", unique=True)
        await db.db.update_tokens.create_index("expires_at")
        await db.db.update_tokens.create_index("donor_id")
        await db.db.password_reset_tokens.create_index("hashed_token", unique=True)
        
        # Rate limiting indexes
        await db.db.rate_limits.create_index("donor_phone")
        await db.db.rate_limits.create_index("last_update_date")
        
        # SMS logs indexes
        await db.db.sms_logs.create_index("phone")
        await db.db.sms_logs.create_index("timestamp")
        await db.db.sms_logs.create_index([("phone", 1), ("timestamp", -1)])

        # Machine indexes
        await db.db.machines.create_index("hospital_id")
        await db.db.machines.create_index("machine_id")
        await db.db.machines.create_index([("hospital_id", 1), ("machine_id", 1)], unique=True)
        await db.db.machines.create_index("status")
        await db.db.machines.create_index("machine_type")
        await db.db.machines.create_index("is_active")
        
        # Maintenance logs indexes
        await db.db.maintenance_logs.create_index("machine_id")
        await db.db.maintenance_logs.create_index("hospital_id")
        await db.db.maintenance_logs.create_index("started_at")
        
        # Machine audit logs
        await db.db.machine_audit_logs.create_index("machine_id")
        await db.db.machine_audit_logs.create_index("changed_at")

        await db.db.admins.create_index("username", unique=True)
        await db.db.admins.create_index("email", unique=True)

        # Appointment indexes
        await db.db.appointments.create_index("hospital_id")
        await db.db.appointments.create_index("donor_id")
        await db.db.appointments.create_index("machine_id")
        await db.db.appointments.create_index("booking_token", unique=True)
        await db.db.appointments.create_index([("hospital_id", 1), ("appointment_date", 1)])
        await db.db.appointments.create_index("status")
        await db.db.appointments.create_index("appointment_date")

        # Waitlist indexes
        await db.db.waitlist.create_index("hospital_id")
        await db.db.waitlist.create_index("expires_at")

        # Booking session indexes
        await db.db.booking_sessions.create_index("phone", unique=True)
        await db.db.booking_sessions.create_index("expires_at")
        

        # Blood request indexes
        await db.db.blood_requests.create_index("hospital_id")
        await db.db.blood_requests.create_index("status")
        await db.db.blood_requests.create_index("expires_at")
        await db.db.blood_requests.create_index([("hospital_id", 1), ("created_at", -1)])

        # Matched donors indexes
        await db.db.matched_donors.create_index("request_id")
        await db.db.matched_donors.create_index("donor_id")
        await db.db.matched_donors.create_index([("request_id", 1), ("donor_id", 1)], unique=True)

        # Donor notifications indexes
        await db.db.donor_notifications.create_index("donor_id")
        await db.db.donor_notifications.create_index("sent_at")

        # Audit logs indexes
        await db.db.audit_logs.create_index("admin_id")
        await db.db.audit_logs.create_index("action")
        await db.db.audit_logs.create_index("timestamp")

        # Broadcast logs indexes
        await db.db.broadcast_logs.create_index("sent_at")
        await db.db.broadcast_logs.create_index("type")

        # Feedback indexes
        await db.db.feedback.create_index("donor_id")
        await db.db.feedback.create_index("request_id", unique=True)
        await db.db.feedback.create_index("hospital_id")
        await db.db.feedback.create_index("created_at")

        # Reliability history indexes
        await db.db.reliability_history.create_index("donor_id")
        await db.db.reliability_history.create_index("created_at")
        
        logger.info("✅ Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        raise

def get_db():
    """Dependency for getting database"""
    return db.db

async def cleanup_expired_tokens():
    """Delete expired tokens periodically"""
    while True:
        try:
            # Delete expired tokens every hour
            await asyncio.sleep(3600)
            result = await db.db.update_tokens.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            if result.deleted_count > 0:
                logger.info(f"Cleaned up {result.deleted_count} expired tokens")
        except Exception as e:
            logger.error(f"Error cleaning up tokens: {e}")

# Add to lifespan in main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting DonorPulse Backend...")
    await connect_to_mongo()
    
    # Start background task to clean up expired tokens
    asyncio.create_task(cleanup_expired_tokens())
    
    logger.info(f"✅ Backend ready on port {settings.port}")
    yield
    logger.info("🛑 Shutting down...")
    await close_mongo_connection()
