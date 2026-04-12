# # import asyncio
# # from motor.motor_asyncio import AsyncIOMotorClient
# # from bson import ObjectId
# # from config import settings

# # async def add_location_by_id():
# #     client = AsyncIOMotorClient(settings.mongodb_uri)
# #     db = client[settings.database_name]
    
# #     print("=" * 50)
# #     print("ADD LOCATION COORDINATES")
# #     print("=" * 50)
    
# #     # Get donor ID from user input
# #     donor_id = input("\nEnter Donor ID (or press Enter to skip): ").strip()
# #     if donor_id:
# #         try:
# #             if not ObjectId.is_valid(donor_id):
# #                 print(f"❌ Invalid donor ID format: {donor_id}")
# #             else:
# #                 donor = await db.donors.find_one({"_id": ObjectId(donor_id)})
# #                 if donor:
# #                     print(f"\n✅ Found donor: {donor.get('name')}")
# #                     lat = input("Enter latitude (default 19.0760): ").strip()
# #                     lng = input("Enter longitude (default 72.8777): ").strip()
                    
# #                     lat = float(lat) if lat else 39.9618
# #                     lng = float(lng) if lng else -75.1956
                    
# #                     await db.donors.update_one(
# #                         {"_id": ObjectId(donor_id)},
# #                         {"$set": {
# #                             "location.lat": lat,
# #                             "location.lng": lng
# #                         }}
# #                     )
# #                     print(f"✅ Added location ({lat}, {lng}) to donor: {donor.get('name')}")
# #                 else:
# #                     print(f"❌ Donor not found with ID: {donor_id}")
# #         except Exception as e:
# #             print(f"❌ Error: {e}")
    
# #     # Get hospital ID from user input
# #     hospital_id = input("\nEnter Hospital ID (or press Enter to skip): ").strip()
# #     if hospital_id:
# #         try:
# #             if not ObjectId.is_valid(hospital_id):
# #                 print(f"❌ Invalid hospital ID format: {hospital_id}")
# #             else:
# #                 hospital = await db.hospitals.find_one({"_id": ObjectId(hospital_id)})
# #                 if hospital:
# #                     print(f"\n✅ Found hospital: {hospital.get('name')}")
# #                     lat = input("Enter latitude (default 19.0760): ").strip()
# #                     lng = input("Enter longitude (default 72.8777): ").strip()
                    
# #                     lat = float(lat) if lat else 39.9515
# #                     lng = float(lng) if lng else 75.1926
                    
# #                     await db.hospitals.update_one(
# #                         {"_id": ObjectId(hospital_id)},
# #                         {"$set": {
# #                             "location.lat": lat,
# #                             "location.lng": lng
# #                         }}
# #                     )
# #                     print(f"✅ Added location ({lat}, {lng}) to hospital: {hospital.get('name')}")
# #                 else:
# #                     print(f"❌ Hospital not found with ID: {hospital_id}")
# #         except Exception as e:
# #             print(f"❌ Error: {e}")
    
# #     # Option to list all donors and hospitals
# #     print("\n" + "=" * 50)
# #     show_all = input("Show all donors and hospitals? (y/n): ").strip().lower()
# #     if show_all == 'y':
# #         print("\n--- DONORS ---")
# #         donors = await db.donors.find().to_list(length=None)
# #         for donor in donors:
# #             location = donor.get('location', {})
# #             has_location = "✅" if location.get('lat') else "❌"
# #             print(f"  {has_location} ID: {donor['_id']} | Name: {donor.get('name')} | Blood: {donor.get('medical', {}).get('blood_type')}")
        
# #         print("\n--- HOSPITALS ---")
# #         hospitals = await db.hospitals.find().to_list(length=None)
# #         for hospital in hospitals:
# #             location = hospital.get('location', {})
# #             has_location = "✅" if location.get('lat') else "❌"
# #             print(f"  {has_location} ID: {hospital['_id']} | Name: {hospital.get('name')} | Verified: {hospital.get('is_verified')}")
    
# #     client.close()
# #     print("\n✅ Done!")

# # if __name__ == "__main__":
# #     asyncio.run(add_location_by_id())

# import asyncio
# from motor.motor_asyncio import AsyncIOMotorClient
# from datetime import datetime
# from config import settings
# from utils.auth import hash_password

# async def create_local_donor():
#     client = AsyncIOMotorClient(settings.mongodb_uri)
#     db = client[settings.database_name]
    
#     # Get hospital to get its location
#     hospital = await db.hospitals.find_one({"username": "mokshu_sankhe"})
#     if not hospital:
#         print("❌ Hospital not found")
#         return
    
#     hospital_lat = hospital['location']['lat']
#     hospital_lng = hospital['location']['lng']
    
#     print(f"Hospital at: {hospital_lat}, {hospital_lng}")
    
#     # Create donor near hospital (within 10km)
#     donor_data = {
#         "name": "Local Donor",
#         "age": 28,
#         "gender": "Male",
#         "medical": {
#             "blood_type": "O-",  # Universal donor
#             "donation_types": ["whole_blood"],
#             "weight_kg": 75,
#             "illnesses": [],
#             "medications": [],
#             "last_donation_date": None
#         },
#         "location": {
#             "phone": "9988776655",
#             "email": "local@example.com",
#             "address": "Near Hospital",
#             "city": "Virar",
#             "pin_code": "401305",
#             "lat": hospital_lat + 0.05,  # Slightly offset
#             "lng": hospital_lng + 0.05
#         },
#         "preferences": {
#             "contact_method": "sms",
#             "availability": ["Morning", "Afternoon", "Evening"],
#             "language": "en",
#             "notify_types": ["Routine", "Urgent", "Critical", "SOS"],
#             "transport_available": True
#         },
#         "is_active": True,
#         "is_paused": False,
#         "reliability_score": 100,
#         "total_donations_completed": 3,
#         "created_at": datetime.utcnow(),
#         "updated_at": datetime.utcnow()
#     }
    
#     # Check if donor already exists
#     existing = await db.donors.find_one({"location.phone": "9988776655"})
#     if existing:
#         print("Local donor already exists!")
#         return
    
#     result = await db.donors.insert_one(donor_data)
#     print(f"✅ Local donor created with ID: {result.inserted_id}")
#     print(f"   Name: Local Donor")
#     print(f"   Blood Type: O- (Universal Donor)")
#     print(f"   Phone: 9988776655")
#     print(f"   Location: {donor_data['location']['lat']}, {donor_data['location']['lng']}")
    
#     client.close()

# if __name__ == "__main__":
#     asyncio.run(create_local_donor())

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from config import settings
from math import radians, sin, cos, sqrt, atan2
from utils.blood_compatibility import get_compatible_donors_for_blood_type

def calculate_distance(lat1, lon1, lat2, lon2):
    if not lat1 or not lon1 or not lat2 or not lon2:
        return None
    R = 6371
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

async def debug_matching():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    
    print("=" * 60)
    print("BLOOD REQUEST MATCHING DEBUG")
    print("=" * 60)
    
    # Get the most recent blood request
    request = await db.blood_requests.find_one({}, sort=[("created_at", -1)])
    if not request:
        print("❌ No blood requests found!")
        return
    
    print(f"\n📋 BLOOD REQUEST:")
    print(f"  ID: {request['_id']}")
    print(f"  Blood Type Needed: {request['blood_type']}")
    print(f"  Urgency: {request['urgency']}")
    print(f"  Quantity: {request['quantity_units']}")
    print(f"  Status: {request['status']}")
    
    # Get hospital
    hospital = await db.hospitals.find_one({"_id": ObjectId(request['hospital_id'])})
    if hospital:
        print(f"\n🏥 HOSPITAL:")
        print(f"  Name: {hospital['name']}")
        print(f"  Location: ({hospital['location'].get('lat')}, {hospital['location'].get('lng')})")
    
    # Get compatible blood types
    compatible_types = get_compatible_donors_for_blood_type(request['blood_type'])
    print(f"\n🩸 Compatible donor blood types for {request['blood_type']}: {compatible_types}")
    
    # Find all eligible donors
    print(f"\n🔍 SEARCHING FOR ELIGIBLE DONORS...")
    
    donor_query = {
        "medical.blood_type": {"$in": compatible_types},
        "is_active": True,
        "is_paused": False
    }
    
    donors = await db.donors.find(donor_query).to_list(length=None)
    print(f"  Found {len(donors)} donors with compatible blood type")
    
    # Check each donor
    eligible_donors = []
    for donor in donors:
        print(f"\n  --- Checking donor: {donor['name']} ---")
        print(f"    Blood Type: {donor['medical']['blood_type']}")
        print(f"    is_active: {donor.get('is_active')}")
        print(f"    is_paused: {donor.get('is_paused')}")
        
        # Check location
        donor_lat = donor.get('location', {}).get('lat')
        donor_lng = donor.get('location', {}).get('lng')
        print(f"    Location: ({donor_lat}, {donor_lng})")
        
        if not donor_lat or not donor_lng:
            print(f"    ❌ No location coordinates!")
            continue
        
        # Check cooldown
        last_donation = donor.get('medical', {}).get('last_donation_date')
        if last_donation:
            from datetime import datetime, timedelta
            if isinstance(last_donation, str):
                last_donation = datetime.fromisoformat(last_donation)
            days_since = (datetime.utcnow() - last_donation).days
            if days_since < 56:
                print(f"    ❌ On cooldown ({days_since} days since last donation)")
                continue
        
        # Calculate distance
        if hospital and hospital['location'].get('lat'):
            distance = calculate_distance(
                donor_lat, donor_lng,
                hospital['location']['lat'], hospital['location']['lng']
            )
            print(f"    Distance: {distance:.2f} km")
            
            # Check radius limit
            radius_limits = {"routine": 50, "urgent": 100, "critical": 200, "sos": 999999}
            max_distance = radius_limits.get(request['urgency'], 50)
            
            if distance > max_distance:
                print(f"    ❌ Too far! (max {max_distance} km for {request['urgency']} urgency)")
                continue
        
        print(f"    ✅ ELIGIBLE!")
        eligible_donors.append(donor)
    
    print(f"\n📊 SUMMARY:")
    print(f"  Total compatible donors: {len(donors)}")
    print(f"  Eligible donors: {len(eligible_donors)}")
    
    if len(eligible_donors) == 0:
        print(f"\n❌ No eligible donors found! Possible reasons:")
        print(f"   1. Donors missing location coordinates")
        print(f"   2. Donors on cooldown (last donation < 56 days)")
        print(f"   3. Donors too far from hospital for this urgency level")
        print(f"   4. Donors not active or paused")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(debug_matching())