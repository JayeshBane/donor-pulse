import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

async def reset_database():
    """Reset database - drop all collections"""
    try:
        client = AsyncIOMotorClient(settings.mongodb_uri)
        db = client[settings.database_name]
        
        await db.donors.drop()
        await db.hospitals.drop()
        await db.update_tokens.drop()
        await db.password_reset_tokens.drop()
        await db.rate_limits.drop()
        await db.sms_logs.drop()
        
        print("✅ Dropped all collections")
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(reset_database())