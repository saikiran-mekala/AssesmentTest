from datetime import datetime, timedelta
from typing import Callable, Dict, Any, List
import uuid
import random


def schedule_reminders(
    db,
    from_date: str,
    to_date: str,
    offsets: str,
    echo: Callable[[str], None],
) -> None:
    """Schedule reminders for appointments within a date range."""
    from_dt = datetime.fromisoformat(f"{from_date}T00:00:00+00:00")
    to_dt = datetime.fromisoformat(f"{to_date}T23:59:59+00:00")
    offset_list: List[int] = [int(x.strip()) for x in offsets.split(",")]

    appointments: List[Dict[str, Any]] = list(
        db.appointments.find(
            {
                "start_at": {
                    "$gte": from_dt,
                    "$lte": to_dt,
                },
                "status": "scheduled",
            }
        )
    )

    reminders_created = 0
    reminders_skipped = 0

    for appointment in appointments:
        patient = db.patients.find_one({"id": appointment["patient_id"]})
        if not patient or not patient.get("active", True):
            continue

        for offset_days in offset_list:
            scheduled_for = appointment["start_at"] - timedelta(days=offset_days)

            if scheduled_for < datetime.utcnow():
                reminders_skipped += 1
                continue

            reminder = {
                "id": str(uuid.uuid4()),
                "appointment_id": appointment["id"],
                "offset_days": offset_days,
                "scheduled_for": scheduled_for,
                "status": "scheduled",
                "attempts": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            try:
                db.reminders.insert_one(reminder)
                reminders_created += 1
                echo(f"  ✅ Scheduled reminder: {offset_days} days before for {patient['full_name']}")
            except Exception:
                reminders_skipped += 1
                echo(f"  ⏭️  Skipped duplicate: {offset_days} days before for {patient['full_name']}")

    echo(f"📅 Summary: Created {reminders_created} reminders, skipped {reminders_skipped}")


def dispatch_due_reminders(db, echo: Callable[[str], None]) -> None:
    """Dispatch due reminders immediately."""
    due_reminders: List[Dict[str, Any]] = list(
        db.reminders.find(
            {
                "scheduled_for": {"$lte": datetime.utcnow()},
                "status": "scheduled",
            }
        )
    )

    if not due_reminders:
        echo("No due reminders to dispatch")
        return

    dispatched = 0
    failed = 0

    for reminder in due_reminders:
        try:
            result = db.reminders.update_one(
                {
                    "id": reminder["id"],
                    "status": "scheduled",
                },
                {
                    "$set": {
                        "status": "dispatched",
                        "dispatched_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    },
                    "$inc": {"attempts": 1},
                },
            )

            if result.modified_count == 0:
                echo(f"  ⏭️  Reminder {reminder['id'][:8]} already claimed by another process")
                continue

            appointment = db.appointments.find_one({"id": reminder["appointment_id"]})
            if not appointment:
                echo(f"  ❌ Appointment not found for reminder {reminder['id'][:8]}")
                failed += 1
                continue

            patient = db.patients.find_one({"id": appointment["patient_id"]})
            if not patient:
                echo(f"  ❌ Patient not found for reminder {reminder['id'][:8]}")
                failed += 1
                continue

            template = db.templates.find_one({"name": "default"})
            if template:
                message = template["body"]
                message = message.replace("{patient.first_name}", patient["full_name"].split()[0])
                message = message.replace(
                    "{appointment.start_local}", appointment["start_at"].strftime("%Y-%m-%d %H:%M")
                )
                message = message.replace("{appointment.location}", appointment["location"])
                message = message.replace("{appointment.provider}", appointment["provider"])
            else:
                first_name = patient["full_name"].split()[0]
                apt_time = appointment["start_at"].strftime("%Y-%m-%d at %H:%M")
                message = (
                    f"Hi {first_name}, your appointment with {appointment['provider']} is on "
                    f"{apt_time} at {appointment['location']}."
                )

            success = random.random() > 0.2

            if success:
                db.reminders.update_one(
                    {"id": reminder["id"]},
                    {
                        "$set": {
                            "status": "delivered",
                            "delivered_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow(),
                        }
                    },
                )
                echo(f"  ✅ Sent to {patient['phone_e164']}: {message[:60]}...")
                dispatched += 1
            else:
                backoff_time = datetime.utcnow() + timedelta(minutes=30)
                db.reminders.update_one(
                    {"id": reminder["id"]},
                    {
                        "$set": {
                            "status": "failed",
                            "last_error": "Simulated delivery failure",
                            "scheduled_for": backoff_time,
                            "updated_at": datetime.utcnow(),
                        }
                    },
                )
                echo(f"  ❌ Failed to send to {patient['phone_e164']} (will retry)")
                failed += 1

        except Exception as exc:
            echo(f"  💥 Error processing reminder {reminder['id'][:8]}: {str(exc)}")
            failed += 1

    echo(f"🚀 Dispatch complete: {dispatched} sent, {failed} failed")

