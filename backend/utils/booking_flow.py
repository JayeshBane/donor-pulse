import logging
import re
import secrets
from datetime import datetime, timedelta
from typing import Any, Optional

from bson import ObjectId

from config import settings

logger = logging.getLogger(__name__)

SESSION_TTL_MINUTES = 30
MAX_SLOT_OPTIONS = 5


def _now() -> datetime:
    return datetime.utcnow()


def _session_expiry() -> datetime:
    return _now() + timedelta(minutes=SESSION_TTL_MINUTES)


def normalize_phone(phone: str) -> str:
    if not phone:
        return ""

    normalized = phone.strip()
    if ":" in normalized:
        normalized = normalized.split(":")[-1]

    return normalized.lstrip("+").strip()


async def _find_donor_by_phone(db, phone: str) -> Optional[dict[str, Any]]:
    normalized_phone = normalize_phone(phone)
    candidates = [phone, normalized_phone]

    digits_only = re.sub(r"\D", "", normalized_phone)
    if digits_only:
        candidates.append(digits_only)

    for candidate in dict.fromkeys(filter(None, candidates)):
        donor = await db.donors.find_one({"location.phone": candidate})
        if donor:
            return donor

    return None


async def _get_active_session(db, phone: str) -> Optional[dict[str, Any]]:
    normalized_phone = normalize_phone(phone)
    session = await db.booking_sessions.find_one({"phone": normalized_phone})

    if not session:
        return None

    if session.get("expires_at") and session["expires_at"] < _now():
        await db.booking_sessions.delete_one({"_id": session["_id"]})
        return None

    return session


async def _save_session(db, session: dict[str, Any]) -> None:
    session["phone"] = normalize_phone(session["phone"])
    session["updated_at"] = _now()
    session["expires_at"] = _session_expiry()

    await db.booking_sessions.update_one(
        {"phone": session["phone"]},
        {"$set": session, "$setOnInsert": {"created_at": _now()}},
        upsert=True,
    )


async def _clear_session(db, phone: str) -> None:
    await db.booking_sessions.delete_one({"phone": normalize_phone(phone)})


def _is_cancel_command(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in {"cancel", "exit", "stop", "quit"}


def _format_hospital_options(hospitals: list[dict[str, Any]]) -> str:
    lines = ["Please choose a hospital by replying with a number:"]
    for index, hospital in enumerate(hospitals, start=1):
        lines.append(f"{index}. {hospital['name']} ({hospital['city']})")
    lines.append("Reply CANCEL anytime to stop booking.")
    return "\n".join(lines)


def _format_slot_options(slot_options: list[dict[str, Any]], date: str) -> str:
    lines = [f"Available slots for {date}. Reply with the slot number:"]
    for index, slot in enumerate(slot_options, start=1):
        location_bits = [slot.get("machine_name")]
        if slot.get("room"):
            location_bits.append(f"Room {slot['room']}")
        lines.append(f"{index}. {slot['time']} - {' | '.join(filter(None, location_bits))}")
    lines.append("Reply CANCEL to stop or send another date to see different slots.")
    return "\n".join(lines)


def _extract_numeric_choice(text: str, max_value: int) -> Optional[int]:
    try:
        choice = int(text.strip())
    except ValueError:
        return None

    if 1 <= choice <= max_value:
        return choice

    return None


def _parse_date(text: str) -> Optional[str]:
    try:
        requested_date = datetime.strptime(text.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None

    if requested_date < datetime.utcnow().date():
        return None

    return requested_date.strftime("%Y-%m-%d")


def _get_preferred_donation_type(donor: dict[str, Any]) -> str:
    donation_types = donor.get("medical", {}).get("donation_types", [])
    if donation_types:
        return donation_types[0]
    return "whole_blood"


async def _select_hospitals_for_donor(db, donor: dict[str, Any]) -> list[dict[str, Any]]:
    donor_city = donor.get("location", {}).get("city")
    query = {"is_verified": True, "is_active": True}

    hospitals = []
    if donor_city:
        hospitals = await db.hospitals.find(
            {**query, "location.city": donor_city}
        ).sort("name", 1).to_list(length=5)

    if not hospitals:
        hospitals = await db.hospitals.find(query).sort("name", 1).to_list(length=5)

    return [
        {
            "hospital_id": str(hospital["_id"]),
            "name": hospital["name"],
            "city": hospital.get("location", {}).get("city", "Unknown"),
        }
        for hospital in hospitals
    ]


async def _get_available_slots_for_hospital(
    db,
    hospital_id: str,
    date: str,
    donation_type: str,
) -> list[dict[str, Any]]:
    start_date = datetime.strptime(date, "%Y-%m-%d")
    end_date = start_date + timedelta(days=1)

    machine_query = {
        "hospital_id": hospital_id,
        "status": "available",
        "is_active": True,
    }
    if donation_type:
        machine_query["donation_types"] = {"$in": [donation_type]}

    machines = await db.machines.find(machine_query).sort("name", 1).to_list(length=None)
    if not machines:
        return []

    existing_appointments = await db.appointments.find(
        {
            "hospital_id": hospital_id,
            "appointment_date": {"$gte": start_date, "$lt": end_date},
            "status": {"$nin": ["cancelled", "no_show"]},
        }
    ).to_list(length=None)

    slots: list[dict[str, Any]] = []
    for machine in machines:
        slot_duration = machine.get("slot_duration_minutes", 30)
        buffer_minutes = machine.get("buffer_minutes", 15)
        operating_start = machine.get("operating_start", "09:00")
        operating_end = machine.get("operating_end", "17:00")

        current_time = datetime.strptime(operating_start, "%H:%M")
        end_time = datetime.strptime(operating_end, "%H:%M")

        while current_time < end_time:
            slot_time = current_time.strftime("%H:%M")
            is_booked = any(
                appointment.get("machine_id") == str(machine["_id"])
                and appointment.get("appointment_time") == slot_time
                for appointment in existing_appointments
            )

            if not is_booked:
                slots.append(
                    {
                        "machine_id": str(machine["_id"]),
                        "machine_name": machine["name"],
                        "time": slot_time,
                        "room": machine.get("room"),
                    }
                )

            current_time += timedelta(minutes=slot_duration + buffer_minutes)

    slots.sort(key=lambda slot: (slot["time"], slot["machine_name"]))
    return slots[:MAX_SLOT_OPTIONS]


async def _create_appointment_from_session(
    db,
    donor: dict[str, Any],
    session: dict[str, Any],
) -> dict[str, str]:
    hospital_id = session["hospital_id"]
    machine_id = session["selected_slot"]["machine_id"]
    appointment_date = datetime.strptime(session["appointment_date"], "%Y-%m-%d")
    appointment_time = session["selected_slot"]["time"]

    hospital = await db.hospitals.find_one(
        {
            "_id": ObjectId(hospital_id),
            "is_verified": True,
            "is_active": True,
        }
    )
    if not hospital:
        raise ValueError("Selected hospital is no longer available.")

    machine = await db.machines.find_one(
        {
            "_id": ObjectId(machine_id),
            "hospital_id": hospital_id,
            "status": "available",
            "is_active": True,
        }
    )
    if not machine:
        raise ValueError("Selected machine is no longer available.")

    existing = await db.appointments.find_one(
        {
            "machine_id": machine_id,
            "appointment_date": {
                "$gte": appointment_date,
                "$lt": appointment_date + timedelta(days=1),
            },
            "appointment_time": appointment_time,
            "status": {"$nin": ["cancelled", "no_show"]},
        }
    )
    if existing:
        raise ValueError("That slot was just booked. Please choose another slot.")

    booking_token = secrets.token_urlsafe(32)
    appointment = {
        "donor_id": str(donor["_id"]),
        "donor_name": donor["name"],
        "donor_phone": donor["location"]["phone"],
        "hospital_id": hospital_id,
        "hospital_name": hospital["name"],
        "machine_id": machine_id,
        "machine_name": machine["name"],
        "appointment_type": "scheduled",
        "appointment_date": appointment_date,
        "appointment_time": appointment_time,
        "donation_type": session["donation_type"],
        "status": "booked",
        "booking_token": booking_token,
        "notes": "Booked via WhatsApp assistant",
        "created_at": _now(),
        "updated_at": _now(),
    }

    result = await db.appointments.insert_one(appointment)
    return {
        "appointment_id": str(result.inserted_id),
        "booking_token": booking_token,
        "booking_link": f"{settings.frontend_url}/donor/appointment/{booking_token}",
    }


async def _start_schedule_session(db, donor: dict[str, Any], phone: str) -> str:
    existing_appointment = await db.appointments.find_one(
        {
            "donor_id": str(donor["_id"]),
            "status": {"$nin": ["cancelled", "completed", "no_show"]},
            "appointment_date": {"$gte": datetime.utcnow() - timedelta(days=1)},
        }
    )
    if existing_appointment:
        appointment_date = existing_appointment["appointment_date"].strftime("%Y-%m-%d")
        return (
            "You already have an active appointment on "
            f"{appointment_date} at {existing_appointment['appointment_time']} "
            f"with {existing_appointment['hospital_name']}."
        )

    hospitals = await _select_hospitals_for_donor(db, donor)
    if not hospitals:
        return "I couldn't find any active hospitals for booking right now."

    session = {
        "phone": phone,
        "donor_id": str(donor["_id"]),
        "donor_name": donor["name"],
        "donation_type": _get_preferred_donation_type(donor),
        "flow": "schedule_appointment",
    }

    if len(hospitals) == 1:
        session["state"] = "awaiting_date"
        session["hospital_id"] = hospitals[0]["hospital_id"]
        session["hospital_name"] = hospitals[0]["name"]
        await _save_session(db, session)
        return (
            f"Let's book your {session['donation_type']} appointment at "
            f"{session['hospital_name']}. What date would you like? "
            "Please reply in YYYY-MM-DD format."
        )

    session["state"] = "awaiting_hospital"
    session["hospital_options"] = hospitals
    await _save_session(db, session)
    return _format_hospital_options(hospitals)


async def handle_schedule_appointment_message(
    db,
    phone: str,
    text: str,
    force_start: bool = False,
) -> Optional[str]:
    session = await _get_active_session(db, phone)

    if _is_cancel_command(text):
        if session:
            await _clear_session(db, phone)
            return "Your appointment booking has been cancelled."
        return None

    donor = await _find_donor_by_phone(db, phone)
    if not donor:
        if session or force_start:
            return "I couldn't find your donor profile. Please register first on the website."
        return None

    if not session:
        if not force_start:
            return None
        return await _start_schedule_session(db, donor, phone)

    state = session.get("state")

    if state == "awaiting_hospital":
        hospital_options = session.get("hospital_options", [])
        choice = _extract_numeric_choice(text, len(hospital_options))
        if choice is None:
            return "Please reply with a valid hospital number from the list."

        selected_hospital = hospital_options[choice - 1]
        session["hospital_id"] = selected_hospital["hospital_id"]
        session["hospital_name"] = selected_hospital["name"]
        session["state"] = "awaiting_date"
        session.pop("hospital_options", None)
        await _save_session(db, session)

        return (
            f"Great, we'll use {selected_hospital['name']}. "
            "What date would you like? Please reply in YYYY-MM-DD format."
        )

    if state == "awaiting_date":
        appointment_date = _parse_date(text)
        if not appointment_date:
            return "Please send a valid future date in YYYY-MM-DD format."

        slot_options = await _get_available_slots_for_hospital(
            db,
            session["hospital_id"],
            appointment_date,
            session["donation_type"],
        )
        if not slot_options:
            return (
                f"I couldn't find open slots on {appointment_date}. "
                "Please send another date in YYYY-MM-DD format."
            )

        session["appointment_date"] = appointment_date
        session["slot_options"] = slot_options
        session["state"] = "awaiting_slot"
        await _save_session(db, session)
        return _format_slot_options(slot_options, appointment_date)

    if state == "awaiting_slot":
        slot_options = session.get("slot_options", [])
        choice = _extract_numeric_choice(text, len(slot_options))
        if choice is None:
            alternative_date = _parse_date(text)
            if alternative_date:
                session["state"] = "awaiting_date"
                session.pop("slot_options", None)
                await _save_session(db, session)
                return await handle_schedule_appointment_message(
                    db,
                    phone,
                    alternative_date,
                    force_start=False,
                )

            return "Please reply with a valid slot number, or send another date in YYYY-MM-DD format."

        selected_slot = slot_options[choice - 1]
        session["selected_slot"] = selected_slot
        session["state"] = "awaiting_confirmation"
        await _save_session(db, session)

        return (
            "Please confirm your appointment:\n"
            f"Hospital: {session['hospital_name']}\n"
            f"Date: {session['appointment_date']}\n"
            f"Time: {selected_slot['time']}\n"
            f"Type: {session['donation_type']}\n"
            "Reply YES to confirm or NO to pick another slot."
        )

    if state == "awaiting_confirmation":
        normalized = text.strip().lower()
        if normalized in {"no", "n"}:
            session["state"] = "awaiting_slot"
            session.pop("selected_slot", None)
            await _save_session(db, session)
            return _format_slot_options(session.get("slot_options", []), session["appointment_date"])

        if normalized not in {"yes", "y", "confirm", "book"}:
            return "Please reply YES to confirm or NO to pick another slot."

        try:
            booking_result = await _create_appointment_from_session(db, donor, session)
        except ValueError as exc:
            session["state"] = "awaiting_date"
            session.pop("slot_options", None)
            session.pop("selected_slot", None)
            await _save_session(db, session)
            return f"{exc} Please send another date in YYYY-MM-DD format."

        await _clear_session(db, phone)
        return (
            "Your appointment is booked.\n"
            f"Hospital: {session['hospital_name']}\n"
            f"Date: {session['appointment_date']}\n"
            f"Time: {session['selected_slot']['time']}\n"
            f"Booking reference: {booking_result['booking_token']}\n"
            f"Details: {booking_result['booking_link']}"
        )

    logger.warning("Unknown booking state for %s: %s", phone, state)
    await _clear_session(db, phone)
    return "Something went wrong with your booking session. Please send a new scheduling request."
