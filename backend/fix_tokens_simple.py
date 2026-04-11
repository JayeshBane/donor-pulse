# backend\fix_tokens_simple.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

async def fix_tokens():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    
    # Drop existing collections
    await db.update_tokens.drop()
    await db.rate_limits.drop()
    
    # Create new collections with proper indexes
    await db.update_tokens.create_index("hashed_token", unique=True)
    await db.update_tokens.create_index("expires_at")
    await db.update_tokens.create_index("donor_id")
    
    await db.rate_limits.create_index("donor_phone")
    await db.rate_limits.create_index("last_update_date")
    
    print("✅ Database fixed! Tokens will be deleted after use.")
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_tokens())