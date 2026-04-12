# backend\routers\appointment.py
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, List
from datetime import datetime, timedelta
from bson import ObjectId
from database import get_db
from models.appointment import (
    AppointmentCreate, AppointmentInDB, AppointmentStatus,
    WalkInCreate, AppointmentResponse, WaitlistEntry
)
from config import settings
from models.machine import MachineStatus
from middleware.auth import get_verified_hospital, get_current_hospital
from utils.auth import generate_magic_token
import logging
import secrets

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/appointments", tags=["appointments"])

@router.get("/slots/available")
async def get_available_slots(
    hospital_id: str,
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    donation_type: Optional[str] = None,
    db=Depends(get_db)
):
    """Get available time slots for a hospital on a specific date"""
    try:
        if not ObjectId.is_valid(hospital_id):
            raise HTTPException(status_code=400, detail="Invalid hospital ID")
        
        # Check if hospital exists and is verified
        hospital = await db.hospitals.find_one({"_id": ObjectId(hospital_id)})
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        if not hospital.get("is_verified"):
            raise HTTPException(status_code=403, detail="Hospital not verified by admin")
        
        # Get available machines
        query = {
            "hospital_id": hospital_id,
            "status": "available",
            "is_active": True
        }
        
        if donation_type:
            query["donation_types"] = {"$in": [donation_type]}
        
        machines = await db.machines.find(query).to_list(length=None)
        
        print(f"Found {len(machines)} available machines for hospital {hospital_id}")
        
        if not machines:
            return {
                "slots": [],
                "message": f"No available machines found. Please ensure machines are active and available. Donation type: {donation_type}"
            }
        
        # Parse the date
        try:
            start_date = datetime.strptime(date, "%Y-%m-%d")
        except:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        end_date = start_date + timedelta(days=1)
        
        # Get existing appointments
        existing_appointments = await db.appointments.find({
            "hospital_id": hospital_id,
            "appointment_date": {"$gte": start_date, "$lt": end_date},
            "status": {"$nin": ["cancelled", "no_show"]}
        }).to_list(length=None)
        
        # Generate slots
        all_slots = []
        
        for machine in machines:
            slot_duration = machine.get("slot_duration_minutes", 30)
            buffer_time = machine.get("buffer_minutes", 15)
            operating_start = machine.get("operating_start", "09:00")
            operating_end = machine.get("operating_end", "17:00")
            
            try:
                current_time = datetime.strptime(operating_start, "%H:%M")
                end_time = datetime.strptime(operating_end, "%H:%M")
            except:
                current_time = datetime.strptime("09:00", "%H:%M")
                end_time = datetime.strptime("17:00", "%H:%M")
            
            while current_time < end_time:
                slot_key = current_time.strftime("%H:%M")
                
                # Check if slot is booked
                is_booked = False
                for apt in existing_appointments:
                    if (apt.get("machine_id") == str(machine["_id"]) and 
                        apt.get("appointment_time") == slot_key):
                        is_booked = True
                        break
                
                if not is_booked:
                    all_slots.append({
                        "machine_id": str(machine["_id"]),
                        "machine_name": machine["name"],
                        "machine_type": machine["machine_type"],
                        "time": slot_key,
                        "donation_types": machine.get("donation_types", []),
                        "floor": machine.get("floor"),
                        "room": machine.get("room")
                    })
                
                current_time = current_time + timedelta(minutes=slot_duration + buffer_time)
        
        print(f"Generated {len(all_slots)} slots")
        
        return {
            "date": date,
            "hospital_id": hospital_id,
            "total_slots": len(all_slots),
            "slots": all_slots
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting available slots: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get available slots: {str(e)}")

@router.post("/book", response_model=dict, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    appointment: AppointmentCreate,
    db=Depends(get_db)
):
    """Book an appointment for a donor"""
    try:
        print(f"Received appointment data: {appointment}")
        
        # Validate donor exists
        if not ObjectId.is_valid(appointment.donor_id):
            raise HTTPException(status_code=400, detail="Invalid donor ID format")
        
        donor = await db.donors.find_one({"_id": ObjectId(appointment.donor_id)})
        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")
        
        print(f"Found donor: {donor['name']}")
        
        # Validate hospital exists
        if not ObjectId.is_valid(appointment.hospital_id):
            raise HTTPException(status_code=400, detail="Invalid hospital ID format")
        
        hospital = await db.hospitals.find_one({
            "_id": ObjectId(appointment.hospital_id),
            "is_verified": True,
            "is_active": True
        })
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found or not verified")
        
        print(f"Found hospital: {hospital['name']}")
        
        # Validate machine exists
        if not ObjectId.is_valid(appointment.machine_id):
            raise HTTPException(status_code=400, detail="Invalid machine ID format")
        
        machine = await db.machines.find_one({
            "_id": ObjectId(appointment.machine_id),
            "hospital_id": appointment.hospital_id,
            "status": "available",
            "is_active": True
        })
        if not machine:
            raise HTTPException(status_code=400, detail="Machine not available")
        
        print(f"Found machine: {machine['name']}")
        
        # Parse date and time
        try:
            appointment_date = datetime.strptime(appointment.appointment_date, "%Y-%m-%d")
            appointment_time = appointment.appointment_time
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid date/time format: {str(e)}")
        
        # Check if slot is already booked
        existing = await db.appointments.find_one({
            "machine_id": appointment.machine_id,
            "appointment_date": {
                "$gte": appointment_date,
                "$lt": appointment_date + timedelta(days=1)
            },
            "appointment_time": appointment_time,
            "status": {"$nin": ["cancelled", "no_show"]}
        })
        
        if existing:
            raise HTTPException(status_code=400, detail="Time slot already booked")
        
        # Generate booking token
        booking_token = secrets.token_urlsafe(32)
        
        # Create appointment
        appointment_dict = {
            "donor_id": appointment.donor_id,
            "donor_name": donor["name"],
            "donor_phone": donor["location"]["phone"],
            "hospital_id": appointment.hospital_id,
            "hospital_name": hospital["name"],
            "machine_id": appointment.machine_id,
            "machine_name": machine["name"],
            "appointment_type": "scheduled",
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
            "donation_type": appointment.donation_type,
            "status": "booked",
            "booking_token": booking_token,
            "notes": appointment.notes,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.appointments.insert_one(appointment_dict)
        
        print(f"Appointment created with ID: {result.inserted_id}")
        
        return {
    "message": "Appointment booked successfully",
    "appointment_id": str(result.inserted_id),
    "booking_token": booking_token,
    "receipt_url": f"{settings.frontend_url}/donor/appointment/{booking_token}",
    "booking_link": f"{settings.frontend_url}/donor/appointment/{booking_token}"
}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error booking appointment: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to book appointment: {str(e)}")

@router.get("/hospital/{hospital_id}")
async def get_hospital_appointments(
    hospital_id: str,
    date: Optional[str] = None,
    status: Optional[str] = None,
    hospital: dict = Depends(get_verified_hospital),
    db=Depends(get_db)
):
    """Get all appointments for a hospital"""
    try:
        if hospital["id"] != hospital_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        query = {"hospital_id": hospital_id}
        
        if date:
            start_date = datetime.strptime(date, "%Y-%m-%d")
            end_date = start_date + timedelta(days=1)
            query["appointment_date"] = {"$gte": start_date, "$lt": end_date}
        
        if status:
            query["status"] = status
        
        appointments = await db.appointments.find(query).sort("appointment_date", 1).sort("appointment_time", 1).to_list(length=None)
        
        result = []
        for apt in appointments:
            result.append({
                "id": str(apt["_id"]),
                "donor_name": apt["donor_name"],
                "donor_phone": apt["donor_phone"],
                "machine_name": apt["machine_name"],
                "appointment_date": apt["appointment_date"].strftime("%Y-%m-%d"),
                "appointment_time": apt["appointment_time"],
                "donation_type": apt["donation_type"],
                "status": apt["status"],
                "checked_in_at": apt.get("checked_in_at").isoformat() if apt.get("checked_in_at") else None,
                "completed_at": apt.get("completed_at").isoformat() if apt.get("completed_at") else None
            })
        
        return {
            "total": len(result),
            "appointments": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting hospital appointments: {e}")
        raise HTTPException(status_code=500, detail="Failed to get appointments")

@router.get("/donor/{donor_id}")
async def get_donor_appointments(
    donor_id: str,
    db=Depends(get_db)
):
    """Get all appointments for a donor"""
    try:
        appointments = await db.appointments.find({
            "donor_id": donor_id,
            "status": {"$nin": ["cancelled", "completed"]}
        }).sort("appointment_date", 1).to_list(length=None)
        
        result = []
        for apt in appointments:
            result.append({
                "id": str(apt["_id"]),
                "hospital_name": apt["hospital_name"],
                "machine_name": apt["machine_name"],
                "appointment_date": apt["appointment_date"].strftime("%Y-%m-%d"),
                "appointment_time": apt["appointment_time"],
                "donation_type": apt["donation_type"],
                "status": apt["status"],
                "booking_token": apt["booking_token"]
            })
        
        return {
            "total": len(result),
            "appointments": result
        }
        
    except Exception as e:
        logger.error(f"Error getting donor appointments: {e}")
        raise HTTPException(status_code=500, detail="Failed to get appointments")

@router.get("/{appointment_id}")
async def get_appointment_by_id(
    appointment_id: str,
    hospital: dict = Depends(get_verified_hospital),
    db=Depends(get_db)
):
    """Get appointment details by ID"""
    try:
        if not ObjectId.is_valid(appointment_id):
            raise HTTPException(status_code=400, detail="Invalid appointment ID")
        
        appointment = await db.appointments.find_one({
            "_id": ObjectId(appointment_id),
            "hospital_id": hospital["id"]
        })
        
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return {
            "id": str(appointment["_id"]),
            "donor_name": appointment["donor_name"],
            "donor_phone": appointment["donor_phone"],
            "donor_id": appointment["donor_id"],
            "hospital_name": appointment["hospital_name"],
            "machine_name": appointment["machine_name"],
            "appointment_date": appointment["appointment_date"].strftime("%Y-%m-%d"),
            "appointment_time": appointment["appointment_time"],
            "donation_type": appointment["donation_type"],
            "status": appointment["status"],
            "booking_token": appointment["booking_token"],
            "checked_in_at": appointment.get("checked_in_at").isoformat() if appointment.get("checked_in_at") else None,
            "started_at": appointment.get("started_at").isoformat() if appointment.get("started_at") else None,
            "completed_at": appointment.get("completed_at").isoformat() if appointment.get("completed_at") else None,
            "cancelled_at": appointment.get("cancelled_at").isoformat() if appointment.get("cancelled_at") else None,
            "cancelled_reason": appointment.get("cancelled_reason"),
            "notes": appointment.get("notes")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting appointment: {e}")
        raise HTTPException(status_code=500, detail="Failed to get appointment")

@router.patch("/{appointment_id}/checkin")
async def checkin_appointment(
    appointment_id: str,
    hospital: dict = Depends(get_verified_hospital),
    db=Depends(get_db)
):
    """Check in a donor for their appointment"""
    try:
        if not ObjectId.is_valid(appointment_id):
            raise HTTPException(status_code=400, detail="Invalid appointment ID")
        
        appointment = await db.appointments.find_one({
            "_id": ObjectId(appointment_id),
            "hospital_id": hospital["id"]
        })
        
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        # Allow check-in only for booked appointments
        if appointment["status"] not in ["booked"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot check in appointment with status: {appointment['status']}. Only 'booked' appointments can be checked in."
            )
        
        await db.appointments.update_one(
            {"_id": ObjectId(appointment_id)},
            {
                "$set": {
                    "status": "checked_in",
                    "checked_in_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Update machine status
        await db.machines.update_one(
            {"_id": ObjectId(appointment["machine_id"])},
            {"$set": {"status": "in_use", "current_donor_id": appointment["donor_id"]}}
        )
        
        logger.info(f"Donor {appointment['donor_name']} checked in for appointment {appointment_id}")
        
        return {"message": "Donor checked in successfully", "status": "checked_in"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking in appointment: {e}")
        raise HTTPException(status_code=500, detail="Failed to check in donor")

@router.patch("/{appointment_id}/start")
async def start_donation(
    appointment_id: str,
    hospital: dict = Depends(get_verified_hospital),
    db=Depends(get_db)
):
    """Start the donation process"""
    try:
        if not ObjectId.is_valid(appointment_id):
            raise HTTPException(status_code=400, detail="Invalid appointment ID")
        
        appointment = await db.appointments.find_one({
            "_id": ObjectId(appointment_id),
            "hospital_id": hospital["id"]
        })
        
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        # Allow start only for checked_in appointments
        if appointment["status"] not in ["checked_in"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot start donation with status: {appointment['status']}. Only 'checked_in' appointments can be started."
            )
        
        await db.appointments.update_one(
            {"_id": ObjectId(appointment_id)},
            {
                "$set": {
                    "status": "in_progress",
                    "started_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Donation started for appointment {appointment_id}")
        
        return {"message": "Donation started successfully", "status": "in_progress"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting donation: {e}")
        raise HTTPException(status_code=500, detail="Failed to start donation")

@router.patch("/{appointment_id}/complete")
async def complete_donation(
    appointment_id: str,
    hospital: dict = Depends(get_verified_hospital),
    db=Depends(get_db)
):
    """Complete the donation process"""
    try:
        if not ObjectId.is_valid(appointment_id):
            raise HTTPException(status_code=400, detail="Invalid appointment ID")
        
        appointment = await db.appointments.find_one({
            "_id": ObjectId(appointment_id),
            "hospital_id": hospital["id"]
        })
        
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        # Allow complete only for in_progress appointments
        if appointment["status"] not in ["in_progress"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot complete donation with status: {appointment['status']}. Only 'in_progress' donations can be completed."
            )
        
        await db.appointments.update_one(
            {"_id": ObjectId(appointment_id)},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Update donor's last donation date and stats
        await db.donors.update_one(
            {"_id": ObjectId(appointment["donor_id"])},
            {
                "$set": {
                    "medical.last_donation_date": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                "$inc": {
                    "total_donations_completed": 1,
                    "reliability_score": 5  # Increase reliability for completing donation
                }
            }
        )
        
        # Update machine status back to available
        await db.machines.update_one(
            {"_id": ObjectId(appointment["machine_id"])},
            {
                "$set": {"status": "available"},
                "$unset": {"current_donor_id": ""}
            }
        )
        
        logger.info(f"Donation completed for appointment {appointment_id}")
        
        return {"message": "Donation completed successfully", "status": "completed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing donation: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete donation")

@router.patch("/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: str,
    reason: Optional[str] = None,
    hospital: dict = Depends(get_verified_hospital),
    db=Depends(get_db)
):
    """Cancel an appointment"""
    try:
        if not ObjectId.is_valid(appointment_id):
            raise HTTPException(status_code=400, detail="Invalid appointment ID")
        
        appointment = await db.appointments.find_one({
            "_id": ObjectId(appointment_id),
            "hospital_id": hospital["id"]
        })
        
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        # Can cancel appointments that are not already completed or cancelled
        if appointment["status"] in ["completed", "cancelled"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot cancel appointment with status: {appointment['status']}"
            )
        
        await db.appointments.update_one(
            {"_id": ObjectId(appointment_id)},
            {
                "$set": {
                    "status": "cancelled",
                    "cancelled_at": datetime.utcnow(),
                    "cancelled_reason": reason,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Free up the machine if it was in use
        if appointment["status"] in ["checked_in", "in_progress"]:
            await db.machines.update_one(
                {"_id": ObjectId(appointment["machine_id"])},
                {
                    "$set": {"status": "available"},
                    "$unset": {"current_donor_id": ""}
                }
            )
        
        logger.info(f"Appointment {appointment_id} cancelled")
        
        return {"message": "Appointment cancelled successfully", "status": "cancelled"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling appointment: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel appointment")

@router.post("/walkin")
async def create_walkin(
    walkin: WalkInCreate,
    hospital: dict = Depends(get_verified_hospital),
    db=Depends(get_db)
):
    """Create a walk-in appointment"""
    try:
        # Find available machine for the donation type
        machine = await db.machines.find_one({
            "hospital_id": walkin.hospital_id,
            "donation_types": {"$in": [walkin.donation_type]},
            "status": "available",
            "is_active": True
        })
        
        if not machine:
            raise HTTPException(status_code=400, detail="No available machine for walk-in")
        
        # Create walk-in appointment for current time
        now = datetime.utcnow()
        booking_token = generate_magic_token()
        
        appointment_data = {
            "donor_id": "walkin_" + secrets.token_hex(4),
            "donor_name": walkin.donor_name,
            "donor_phone": walkin.donor_phone,
            "hospital_id": walkin.hospital_id,
            "hospital_name": hospital["name"],
            "machine_id": str(machine["_id"]),
            "machine_name": machine["name"],
            "appointment_type": "walk_in",
            "appointment_date": now,
            "appointment_time": now.strftime("%H:%M"),
            "donation_type": walkin.donation_type,
            "status": "checked_in",  # Walk-ins are checked in immediately
            "booking_token": booking_token,
            "checked_in_at": now,
            "notes": walkin.notes,
            "created_at": now,
            "updated_at": now
        }
        
        result = await db.appointments.insert_one(appointment_data)
        
        # Update machine status
        await db.machines.update_one(
            {"_id": machine["_id"]},
            {"$set": {"status": "in_use", "current_donor_id": "walkin_" + secrets.token_hex(4)}}
        )
        
        logger.info(f"Walk-in created for {walkin.donor_name} at hospital {walkin.hospital_id}")
        
        return {
            "message": "Walk-in donor added successfully",
            "appointment_id": str(result.inserted_id),
            "machine": machine["name"],
            "status": "checked_in"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating walk-in: {e}")
        raise HTTPException(status_code=500, detail="Failed to create walk-in")

@router.patch("/{appointment_id}/noshow")
async def mark_no_show(
    appointment_id: str,
    hospital: dict = Depends(get_verified_hospital),
    db=Depends(get_db)
):
    """Mark appointment as no-show"""
    try:
        if not ObjectId.is_valid(appointment_id):
            raise HTTPException(status_code=400, detail="Invalid appointment ID")
        
        appointment = await db.appointments.find_one({
            "_id": ObjectId(appointment_id),
            "hospital_id": hospital["id"]
        })
        
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        if appointment["status"] != "booked":
            raise HTTPException(status_code=400, detail=f"Cannot mark as no-show with status: {appointment['status']}")
        
        await db.appointments.update_one(
            {"_id": ObjectId(appointment_id)},
            {
                "$set": {
                    "status": "no_show",
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Appointment {appointment_id} marked as no-show")
        
        return {"message": "Appointment marked as no-show"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking no-show: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark no-show")
    
@router.get("/token/{token}")
async def get_appointment_by_token(
    token: str,
    db=Depends(get_db)
):
    """Get appointment details by booking token"""
    try:
        appointment = await db.appointments.find_one({"booking_token": token})
        
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return {
            "id": str(appointment["_id"]),
            "donor_name": appointment["donor_name"],
            "donor_phone": appointment["donor_phone"],
            "hospital_name": appointment["hospital_name"],
            "machine_name": appointment["machine_name"],
            "appointment_date": appointment["appointment_date"].strftime("%Y-%m-%d"),
            "appointment_time": appointment["appointment_time"],
            "donation_type": appointment["donation_type"],
            "status": appointment["status"],
            "booking_token": appointment["booking_token"],
            "notes": appointment.get("notes")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting appointment by token: {e}")
        raise HTTPException(status_code=500, detail="Failed to get appointment")