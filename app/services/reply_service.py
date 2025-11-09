import os
import csv
import uuid
from datetime import datetime
from typing import Callable, Dict, Any, List

from app.utils.classification import classify_reply_intent


def process_replies(db, file_path: str, classify: bool, echo: Callable[[str], None]) -> None:
    """Import and process replies from CSV."""
    if not os.path.exists(file_path):
        echo(f"❌ File not found: {file_path}")
        return

    processed = 0
    classified = 0
    errors = 0

    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row_num, row in enumerate(reader, 1):
            try:
                if not all(field in row for field in ["from", "to", "message", "received_at"]):
                    echo(f"  ❌ Row {row_num}: Missing required fields")
                    errors += 1
                    continue

                received_at = datetime.fromisoformat(row["received_at"].replace("Z", "+00:00"))

                patient = db.patients.find_one({"phone_e164": row["from"]})
                if not patient:
                    echo(f"  ❌ Row {row_num}: Patient not found for phone {row['from']}")
                    errors += 1
                    continue

                appointments: List[Dict[str, Any]] = list(
                    db.appointments.find(
                        {
                            "patient_id": patient["id"],
                            "status": "scheduled",
                        }
                    )
                )

                if not appointments:
                    echo(f"  ❌ Row {row_num}: No scheduled appointments found for patient")
                    errors += 1
                    continue

                appointment = max(appointments, key=lambda x: x["start_at"])

                intent = classify_reply_intent(row["message"])
                confidence = "high" if intent != "unknown" else "low"

                event = {
                    "id": str(uuid.uuid4()),
                    "occurred_at": datetime.utcnow(),
                    "type": "reply_received",
                    "entity_type": "appointment",
                    "entity_id": appointment["id"],
                    "payload": {
                        "from_phone": row["from"],
                        "to_phone": row["to"],
                        "message": row["message"],
                        "received_at": received_at.isoformat(),
                        "classification": {
                            "intent": intent,
                            "confidence": confidence,
                        },
                    },
                    "trace_id": str(uuid.uuid4()),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
                db.events.insert_one(event)

                if classify and intent != "unknown":
                    old_status = appointment["status"]
                    new_status = old_status

                    if intent == "confirmed" and old_status == "scheduled":
                        new_status = "confirmed"
                    elif intent == "cancel" and old_status == "scheduled":
                        new_status = "canceled"
                    elif intent == "reschedule" and old_status == "scheduled":
                        new_status = "reschedule_requested"

                    if new_status != old_status:
                        db.appointments.update_one(
                            {"id": appointment["id"]},
                            {
                                "$set": {
                                    "status": new_status,
                                    "updated_at": datetime.utcnow(),
                                    "version": appointment["version"] + 1,
                                }
                            },
                        )

                        status_event = {
                            "id": str(uuid.uuid4()),
                            "occurred_at": datetime.utcnow(),
                            "type": "status_changed",
                            "entity_type": "appointment",
                            "entity_id": appointment["id"],
                            "payload": {
                                "previous_status": old_status,
                                "new_status": new_status,
                                "reason": "reply_classification",
                            },
                            "trace_id": str(uuid.uuid4()),
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow(),
                        }
                        db.events.insert_one(status_event)

                        classified += 1
                        echo(
                            f"  ✅ Row {row_num}: {patient['full_name']} - {intent} "
                            f"→ {old_status}→{new_status}"
                        )
                    else:
                        echo(f"  ℹ️  Row {row_num}: {patient['full_name']} - {intent} (no status change)")
                else:
                    echo(f"  ℹ️  Row {row_num}: {patient['full_name']} - {intent} (not classified)")

                processed += 1

            except Exception as exc:
                echo(f"  ❌ Row {row_num}: Error - {str(exc)}")
                errors += 1

    echo(f"📥 Import complete: {processed} processed, {classified} status changes, {errors} errors")

