# backend\fix_machine_active.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from config import settings

async def fix_machine_active():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    
    # Update all machines to set is_active = True only if it's None
    result = await db.machines.update_many(
        {"is_active": None},
        {"$set": {"is_active": True}}
    )
    
    print(f"✅ Updated {result.modified_count} machines: set is_active = True")
    
    # Show current machines with their status
    machines = await db.machines.find().to_list(length=None)
    for machine in machines:
        print(f"\nMachine: {machine.get('name')}")
        print(f"  is_active: {machine.get('is_active')} (hospital can change this)")
        print(f"  status: {machine.get('status')} (hospital can change this)")
        print(f"  donation_types: {machine.get('donation_types')}")
    
    print("\n✅ Hospitals can now activate/deactivate machines from the frontend")
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_machine_active())