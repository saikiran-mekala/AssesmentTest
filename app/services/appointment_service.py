from datetime import datetime
from typing import Callable, Dict, Any, List
import uuid


def add_appointment(
    db,
    patient_id: str,
    start_at: str,
    provider: str,
    location: str,
    echo: Callable[[str], None],
) -> None:
    """Add a new appointment."""
    patient = db.patients.find_one({"id": patient_id})
    if not patient:
        echo(f"❌ Patient {patient_id} not found")
        return

    try:
        start_datetime = datetime.fromisoformat(start_at.replace("Z", "+00:00"))
    except ValueError:
        echo("❌ Invalid datetime format. Use: 2025-02-20T15:00:00Z")
        return

    appointment: Dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "patient_id": patient_id,
        "start_at": start_datetime,
        "provider": provider,
        "location": location,
        "status": "scheduled",
        "version": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    db.appointments.insert_one(appointment)
    echo(f"✅ Appointment created: {appointment['id']}")


def list_appointments(db, echo: Callable[[str], None]) -> None:
    """List all appointments."""
    appointments: List[Dict[str, Any]] = list(db.appointments.find({}).limit(50))

    if not appointments:
        echo("No appointments found")
        return

    for apt in appointments:
        patient = db.patients.find_one({"id": apt["patient_id"]})
        patient_name = patient["full_name"] if patient else "Unknown"
        if isinstance(apt["start_at"], datetime):
            apt_time = apt["start_at"].strftime("%Y-%m-%d %H:%M")
        else:
            apt_time = str(apt["start_at"])
        echo(
            f"{apt['id'][:8]} {patient_name} {apt_time} {apt['provider']} {apt['status']}"
        )

