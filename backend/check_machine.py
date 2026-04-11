# backend/check_machine.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

async def check_machine():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    
    # Find all machines
    machines = await db.machines.find().to_list(length=None)
    
    print(f"Total machines found: {len(machines)}")
    for machine in machines:
        print(f"\nMachine: {machine.get('name')}")
        print(f"  ID: {machine.get('_id')}")
        print(f"  Hospital ID: {machine.get('hospital_id')}")
        print(f"  Status: {machine.get('status')}")
        print(f"  Machine Type: {machine.get('machine_type')}")
        print(f"  Donation Types: {machine.get('donation_types')}")
        print(f"  Operating Hours: {machine.get('operating_start')} - {machine.get('operating_end')}")
        print(f"  Is Active: {machine.get('is_active')}")
    
    # Find the specific hospital
    hospital = await db.hospitals.find_one({"name": "Mokshad Sankhe"})
    if hospital:
        print(f"\nHospital found: {hospital.get('name')}")
        print(f"  ID: {hospital.get('_id')}")
        print(f"  Verified: {hospital.get('is_verified')}")
        print(f"  Active: {hospital.get('is_active')}")
    else:
        print("\nHospital 'Mokshad Sankhe' not found!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_machine())