# backend\setup_admin.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
from utils.auth import hash_password

async def setup_admin():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    
    # Check if admin exists
    admin = await db.admins.find_one({"username": "admin"})
    
    if not admin:
        admin_data = {
            "username": "admin",
            "email": "admin@donorpulse.com",
            "full_name": "Super Admin",
            "role": "super_admin",
            "hashed_password": hash_password("Admin@123"),
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        
        result = await db.admins.insert_one(admin_data)
        print(f"✅ Admin created with ID: {result.inserted_id}")
        print("   Username: admin")
        print("   Password: Admin@123")
    else:
        print("✅ Admin already exists")
    
    client.close()

if __name__ == "__main__":
    from datetime import datetime
    asyncio.run(setup_admin())