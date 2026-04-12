# backend\fix_coordinate.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

async def fix_coordinates():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    
    print("=" * 50)
    print("FIXING COORDINATES IN DATABASE")
    print("=" * 50)
    
    # Fix donors
    print("\n📋 Fixing donors...")
    donors = await db.donors.find().to_list(length=None)
    fixed_donors = 0
    
    for donor in donors:
        updates = {}
        location = donor.get('location', {})
        
        # Check lat
        if 'lat' in location and isinstance(location['lat'], str):
            try:
                updates['location.lat'] = float(location['lat'])
                print(f"  Donor {donor.get('name')}: lat '{location['lat']}' -> {float(location['lat'])}")
            except:
                print(f"  ⚠️ Could not convert lat for {donor.get('name')}: {location['lat']}")
        
        # Check lng
        if 'lng' in location and isinstance(location['lng'], str):
            try:
                updates['location.lng'] = float(location['lng'])
                print(f"  Donor {donor.get('name')}: lng '{location['lng']}' -> {float(location['lng'])}")
            except:
                print(f"  ⚠️ Could not convert lng for {donor.get('name')}: {location['lng']}")
        
        if updates:
            await db.donors.update_one({"_id": donor["_id"]}, {"$set": updates})
            fixed_donors += 1
    
    print(f"✅ Fixed {fixed_donors} donors")
    
    # Fix hospitals
    print("\n🏥 Fixing hospitals...")
    hospitals = await db.hospitals.find().to_list(length=None)
    fixed_hospitals = 0
    
    for hospital in hospitals:
        updates = {}
        location = hospital.get('location', {})
        
        # Check lat
        if 'lat' in location and isinstance(location['lat'], str):
            try:
                updates['location.lat'] = float(location['lat'])
                print(f"  Hospital {hospital.get('name')}: lat '{location['lat']}' -> {float(location['lat'])}")
            except:
                print(f"  ⚠️ Could not convert lat for {hospital.get('name')}: {location['lat']}")
        
        # Check lng
        if 'lng' in location and isinstance(location['lng'], str):
            try:
                updates['location.lng'] = float(location['lng'])
                print(f"  Hospital {hospital.get('name')}: lng '{location['lng']}' -> {float(location['lng'])}")
            except:
                print(f"  ⚠️ Could not convert lng for {hospital.get('name')}: {location['lng']}")
        
        if updates:
            await db.hospitals.update_one({"_id": hospital["_id"]}, {"$set": updates})
            fixed_hospitals += 1
    
    print(f"✅ Fixed {fixed_hospitals} hospitals")
    
    # Verify the fix
    print("\n🔍 Verification:")
    donor = await db.donors.find_one({})
    if donor:
        lat = donor.get('location', {}).get('lat')
        lng = donor.get('location', {}).get('lng')
        print(f"  Donor location type: lat={type(lat).__name__}, lng={type(lng).__name__}")
        print(f"  Donor coordinates: {lat}, {lng}")
    
    hospital = await db.hospitals.find_one({})
    if hospital:
        lat = hospital.get('location', {}).get('lat')
        lng = hospital.get('location', {}).get('lng')
        print(f"  Hospital location type: lat={type(lat).__name__}, lng={type(lng).__name__}")
        print(f"  Hospital coordinates: {lat}, {lng}")
    
    client.close()
    print("\n✅ All done! Restart your backend and create a new blood request.")

if __name__ == "__main__":
    asyncio.run(fix_coordinates())