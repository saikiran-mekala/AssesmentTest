from datetime import datetime
from typing import Callable, List, Dict, Any
import uuid


def add_patient(db, name: str, phone: str, tz: str, echo: Callable[[str], None]) -> None:
    """Add a new patient."""
    if db.patients.find_one({"phone_e164": phone}):
        echo(f"❌ Patient with phone {phone} already exists")
        return

    patient: Dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "full_name": name,
        "phone_e164": phone,
        "tz": tz,
        "active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    db.patients.insert_one(patient)
    echo(f"✅ Patient created: {patient['id']}")


def list_patients(db, echo: Callable[[str], None]) -> None:
    """List all patients."""
    patients: List[Dict[str, Any]] = list(db.patients.find({}).limit(50))

    if not patients:
        echo("No patients found")
        return

    for patient in patients:
        status = "✓" if patient.get("active", True) else "✗"
        echo(
            f"{status} {patient['id'][:8]} {patient['full_name']} "
            f"{patient['phone_e164']} {patient['tz']}"
        )

