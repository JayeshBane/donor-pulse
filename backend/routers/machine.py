from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, List
from datetime import datetime, timedelta
from bson import ObjectId
from database import get_db
from models.machine import (
    MachineCreate, MachineInDB, MachineStatusUpdate, 
    MachineMaintenanceLog, MachineMaintenanceType, 
    MachineStatus, BulkMachineCreate, MachineSchedule
)
from middleware.auth import get_verified_hospital
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/machines", tags=["machines"])

@router.post("/add", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_machine(
    machine: MachineCreate,
    hospital: dict = Depends(get_verified_hospital),
    db=Depends(get_db)
):
    """Add a new machine to hospital"""
    try:
        hospital_id = hospital["id"]
        
        # Check if machine_id already exists for this hospital
        existing = await db.machines.find_one({
            "hospital_id": hospital_id,
            "machine_id": machine.machine_id
        })
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Machine with ID {machine.machine_id} already exists"
            )
        
        # Get hospital name
        hospital_data = await db.hospitals.find_one({"_id": ObjectId(hospital_id)})
        hospital_name = hospital_data.get("name") if hospital_data else None
        
        machine_dict = machine.dict()
        machine_dict.update({
            "hospital_id": hospital_id,
            "hospital_name": hospital_name,
            "status": MachineStatus.AVAILABLE,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        result = await db.machines.insert_one(machine_dict)
        
        logger.info(f"Machine {machine.machine_id} added to hospital {hospital_id}")
        
        return {
            "message": "Machine added successfully",
            "machine_id": str(result.inserted_id),
            "display_id": machine.machine_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding machine: {e}")
        raise HTTPException(status_code=500, detail="Failed to add machine")

@router.get("/hospital/{hospital_id}", response_model=List[MachineInDB])
async def get_hospital_machines(
    hospital_id: str,
    status: Optional[str] = None,
    machine_type: Optional[str] = None,
    db=Depends(get_db)
):
    """Get all machines for a hospital (public endpoint)"""
    try:
        if not ObjectId.is_valid(hospital_id):
            raise HTTPException(status_code=400, detail="Invalid hospital ID")
        
        query = {"hospital_id": hospital_id}
        
        if status:
            query["status"] = status
        if machine_type:
            query["machine_type"] = machine_type
        
        cursor = db.machines.find(query).sort("machine_id", 1)
        machines = []
        
        async for machine in cursor:
            machine["_id"] = str(machine["_id"])
            machines.append(MachineInDB(**machine))
        
        return machines
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting machines: {e}")
        raise HTTPException(status_code=500, detail="Failed to get machines")

@router.get("/available/{hospital_id}")
async def get_available_machines(
    hospital_id: str,
    donation_type: Optional[str] = None,
    db=Depends(get_db)
):
    """Get available machines for a hospital"""
    try:
        if not ObjectId.is_valid(hospital_id):
            raise HTTPException(status_code=400, detail="Invalid hospital ID")
        
        query = {
            "hospital_id": hospital_id,
            "status": MachineStatus.AVAILABLE,
            "is_active": True
        }
        
        cursor = db.machines.find(query)
        machines = []
        
        async for machine in cursor:
            # Check if machine supports this donation type
            if donation_type and donation_type not in machine.get("donation_types", []):
                continue
                
            machines.append({
                "id": str(machine["_id"]),
                "machine_id": machine["machine_id"],
                "name": machine["name"],
                "machine_type": machine["machine_type"],
                "donation_types": machine.get("donation_types", []),
                "floor": machine.get("floor"),
                "room": machine.get("room")
            })
        
        return {
            "total_available": len(machines),
            "machines": machines
        }
        
    except Exception as e:
        logger.error(f"Error getting available machines: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available machines")

@router.get("/{machine_id}/schedule")
async def get_machine_schedule(
    machine_id: str,
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    db=Depends(get_db)
):
    """Get machine schedule for a specific date"""
    try:
        if not ObjectId.is_valid(machine_id):
            raise HTTPException(status_code=400, detail="Invalid machine ID")
        
        machine = await db.machines.find_one({"_id": ObjectId(machine_id)})
        if not machine:
            raise HTTPException(status_code=404, detail="Machine not found")
        
        # Use provided date or today
        if not date:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Get appointments for this machine on this date
        start_of_day = datetime.strptime(date, "%Y-%m-%d")
        end_of_day = start_of_day + timedelta(days=1)
        
        appointments = await db.appointments.find({
            "machine_id": machine_id,
            "appointment_date": {"$gte": start_of_day, "$lt": end_of_day},
            "status": {"$nin": ["cancelled", "no_show"]}
        }).to_list(length=None)
        
        # Generate time slots
        slot_duration = machine.get("slot_duration_minutes", 30)
        buffer_time = machine.get("buffer_minutes", 15)
        operating_start = machine.get("operating_start", "09:00")
        operating_end = machine.get("operating_end", "17:00")
        
        slots = []
        current_time = datetime.strptime(operating_start, "%H:%M")
        end_time = datetime.strptime(operating_end, "%H:%M")
        
        while current_time < end_time:
            slot_end = current_time + timedelta(minutes=slot_duration)
            slot_key = current_time.strftime("%H:%M")
            
            # Check if slot is booked
            is_booked = False
            donor_name = None
            for apt in appointments:
                apt_time = apt.get("appointment_time")
                if apt_time and apt_time.startswith(slot_key):
                    is_booked = True
                    donor_name = apt.get("donor_name")
                    break
            
            slots.append({
                "time": slot_key,
                "available": not is_booked,
                "donor_name": donor_name
            })
            
            current_time = slot_end + timedelta(minutes=buffer_time)
        
        return {
            "machine_id": machine_id,
            "date": date,
            "slots": slots,
            "total_slots": len(slots),
            "booked_slots": len([s for s in slots if not s["available"]]),
            "available_slots": len([s for s in slots if s["available"]])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting machine schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to get machine schedule")

@router.patch("/{machine_id}/status")
async def update_machine_status(
    machine_id: str,
    status_update: MachineStatusUpdate,
    hospital: dict = Depends(get_verified_hospital),
    db=Depends(get_db)
):
    """Update machine status"""
    try:
        if not ObjectId.is_valid(machine_id):
            raise HTTPException(status_code=400, detail="Invalid machine ID")
        
        # Verify machine belongs to hospital
        machine = await db.machines.find_one({
            "_id": ObjectId(machine_id),
            "hospital_id": hospital["id"]
        })
        
        if not machine:
            raise HTTPException(status_code=404, detail="Machine not found")
        
        # Update status
        result = await db.machines.update_one(
            {"_id": ObjectId(machine_id)},
            {
                "$set": {
                    "status": status_update.status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Log status change
        await db.machine_audit_logs.insert_one({
            "machine_id": machine_id,
            "hospital_id": hospital["id"],
            "old_status": machine["status"],
            "new_status": status_update.status,
            "reason": status_update.reason,
            "changed_by": hospital["username"],
            "changed_at": datetime.utcnow()
        })
        
        logger.info(f"Machine {machine_id} status updated to {status_update.status}")
        
        return {
            "message": f"Machine status updated to {status_update.status}",
            "machine_id": machine_id,
            "status": status_update.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating machine status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update machine status")

@router.post("/{machine_id}/maintenance/log")
async def add_maintenance_log(
    machine_id: str,
    log: MachineMaintenanceLog,
    hospital: dict = Depends(get_verified_hospital),
    db=Depends(get_db)
):
    """Add maintenance log for a machine"""
    try:
        if not ObjectId.is_valid(machine_id):
            raise HTTPException(status_code=400, detail="Invalid machine ID")
        
        # Verify machine belongs to hospital
        machine = await db.machines.find_one({
            "_id": ObjectId(machine_id),
            "hospital_id": hospital["id"]
        })
        
        if not machine:
            raise HTTPException(status_code=404, detail="Machine not found")
        
        log_dict = log.dict()
        log_dict.update({
            "machine_id": machine_id,
            "hospital_id": hospital["id"],
            "created_at": datetime.utcnow()
        })
        
        result = await db.maintenance_logs.insert_one(log_dict)
        
        # If maintenance is ongoing, update machine status
        if not log.ended_at:
            await db.machines.update_one(
                {"_id": ObjectId(machine_id)},
                {"$set": {"status": MachineStatus.MAINTENANCE, "updated_at": datetime.utcnow()}}
            )
        
        logger.info(f"Maintenance log added for machine {machine_id}")
        
        return {
            "message": "Maintenance log added successfully",
            "log_id": str(result.inserted_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding maintenance log: {e}")
        raise HTTPException(status_code=500, detail="Failed to add maintenance log")

@router.get("/capacity/{hospital_id}")
async def get_hospital_capacity(
    hospital_id: str,
    date: Optional[str] = None,
    db=Depends(get_db)
):
    """Get total capacity for a hospital on a specific date"""
    try:
        if not ObjectId.is_valid(hospital_id):
            raise HTTPException(status_code=400, detail="Invalid hospital ID")
        
        if not date:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Get all active machines
        machines = await db.machines.find({
            "hospital_id": hospital_id,
            "is_active": True,
            "status": {"$ne": MachineStatus.OFFLINE}
        }).to_list(length=None)
        
        total_capacity = 0
        machine_breakdown = []
        
        for machine in machines:
            # Calculate daily capacity for this machine
            slot_duration = machine.get("slot_duration_minutes", 30)
            buffer_time = machine.get("buffer_minutes", 15)
            operating_start = datetime.strptime(machine.get("operating_start", "09:00"), "%H:%M")
            operating_end = datetime.strptime(machine.get("operating_end", "17:00"), "%H:%M")
            
            total_minutes = (operating_end - operating_start).seconds / 60
            slot_cycle = slot_duration + buffer_time
            daily_slots = int(total_minutes / slot_cycle) if slot_cycle > 0 else 0
            daily_capacity = min(daily_slots, machine.get("max_daily_donations", 10))
            
            total_capacity += daily_capacity
            
            machine_breakdown.append({
                "machine_id": machine["machine_id"],
                "name": machine["name"],
                "machine_type": machine["machine_type"],
                "daily_capacity": daily_capacity
            })
        
        return {
            "hospital_id": hospital_id,
            "date": date,
            "total_capacity": total_capacity,
            "total_machines": len(machines),
            "machines": machine_breakdown
        }
        
    except Exception as e:
        logger.error(f"Error getting hospital capacity: {e}")
        raise HTTPException(status_code=500, detail="Failed to get hospital capacity")

@router.post("/bulk-add", response_model=dict)
async def bulk_add_machines(
    bulk_data: BulkMachineCreate,
    hospital: dict = Depends(get_verified_hospital),
    db=Depends(get_db)
):
    """Add multiple machines at once"""
    try:
        # Verify hospital matches
        if bulk_data.hospital_id != hospital["id"]:
            raise HTTPException(status_code=403, detail="Cannot add machines to another hospital")
        
        added = 0
        failed = 0
        errors = []
        
        for machine in bulk_data.machines:
            try:
                # Check for duplicate
                existing = await db.machines.find_one({
                    "hospital_id": hospital["id"],
                    "machine_id": machine.machine_id
                })
                
                if existing:
                    failed += 1
                    errors.append(f"Machine {machine.machine_id} already exists")
                    continue
                
                machine_dict = machine.dict()
                machine_dict.update({
                    "hospital_id": hospital["id"],
                    "hospital_name": hospital.get("name"),
                    "status": MachineStatus.AVAILABLE,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
                
                await db.machines.insert_one(machine_dict)
                added += 1
                
            except Exception as e:
                failed += 1
                errors.append(f"Failed to add {machine.machine_id}: {str(e)}")
        
        logger.info(f"Bulk add completed: {added} added, {failed} failed for hospital {hospital['id']}")
        
        return {
            "message": f"Bulk add completed",
            "added": added,
            "failed": failed,
            "errors": errors[:10]  # Return first 10 errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk add: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete bulk add")
    
@router.patch("/{machine_id}/toggle-active")
async def toggle_machine_active(
    machine_id: str,
    hospital: dict = Depends(get_verified_hospital),
    db=Depends(get_db)
):
    """Toggle machine active status (activate/deactivate)"""
    try:
        if not ObjectId.is_valid(machine_id):
            raise HTTPException(status_code=400, detail="Invalid machine ID")
        
        # Verify machine belongs to hospital
        machine = await db.machines.find_one({
            "_id": ObjectId(machine_id),
            "hospital_id": hospital["id"]
        })
        
        if not machine:
            raise HTTPException(status_code=404, detail="Machine not found")
        
        # Toggle is_active
        new_status = not machine.get("is_active", True)
        
        await db.machines.update_one(
            {"_id": ObjectId(machine_id)},
            {
                "$set": {
                    "is_active": new_status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Machine {machine_id} active status toggled to {new_status}")
        
        return {
            "message": f"Machine {'activated' if new_status else 'deactivated'}",
            "is_active": new_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling machine active: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle machine status")