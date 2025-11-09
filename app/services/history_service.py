from typing import Callable, Dict, Any, List


def show_appointment_history(db, appointment_id: str, echo: Callable[[str], None]) -> None:
    """Display appointment history."""
    appointment_data = db.appointments.find_one({"id": appointment_id})
    if not appointment_data:
        echo(f"❌ Appointment {appointment_id} not found")
        return

    patient = db.patients.find_one({"id": appointment_data["patient_id"]})
    patient_name = patient["full_name"] if patient else "Unknown"

    events: List[Dict[str, Any]] = list(
        db.events.find(
            {
                "$or": [
                    {"entity_type": "appointment", "entity_id": appointment_id},
                    {"entity_type": "reminder", "payload.appointment_id": appointment_id},
                ]
            }
        ).sort("occurred_at", 1)
    )

    if not events:
        echo(f"No history found for appointment {appointment_id}")
        return

    echo(f"📋 History for: {patient_name}")
    echo(
        f"Appointment: {appointment_data['start_at'].strftime('%Y-%m-%d %H:%M')} "
        f"with {appointment_data['provider']} at {appointment_data['location']}"
    )
    echo(f"Current Status: {appointment_data['status']}")
    echo("")
    echo("Event History:")
    echo("-" * 80)

    for event in events:
        time_str = event["occurred_at"].strftime("%m/%d %H:%M")
        event_type = event["type"]
        details = ""

        if event_type == "status_changed":
            payload = event.get("payload", {})
            details = f"{payload.get('previous_status', '?')} → {payload.get('new_status', '?')}"
        elif event_type == "reminder_scheduled":
            details = f"Offset: {event['payload'].get('offset_days')} days"
        elif event_type == "reminder_dispatched":
            details = f"SMS: {event['payload'].get('message_preview', '')[:50]}..."
        elif event_type == "reply_received":
            details = f"Reply: {event['payload'].get('message', '')[:50]}..."
            if "classification" in event["payload"]:
                classification = event["payload"]["classification"]
                details += f" → {classification.get('intent', 'unknown')}"
        elif event_type == "classification":
            details = f"Intent: {event['payload'].get('intent', '')} (conf: {event['payload'].get('confidence', '')})"
        elif event_type == "error":
            details = f"Error: {event['payload'].get('error', '')}"

        echo(f"{time_str} | {event_type:20} | {details}")

