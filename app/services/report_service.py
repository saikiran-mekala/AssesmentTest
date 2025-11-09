import csv
from datetime import datetime
from typing import Callable, Dict, Any, List, Optional


def generate_reminders_report(
    db,
    from_date: str,
    to_date: str,
    output: Optional[str],
    echo: Callable[[str], None],
) -> None:
    """Generate reminders report for a date range."""
    from_dt = datetime.fromisoformat(f"{from_date}T00:00:00+00:00")
    to_dt = datetime.fromisoformat(f"{to_date}T23:59:59+00:00")

    reminders: List[Dict[str, Any]] = list(
        db.reminders.find(
            {
                "scheduled_for": {
                    "$gte": from_dt,
                    "$lte": to_dt,
                }
            }
        )
    )

    if not reminders:
        echo("No reminders found for the specified date range")
        return

    report_data: List[Dict[str, Any]] = []
    for reminder in reminders:
        appointment = db.appointments.find_one({"id": reminder["appointment_id"]})
        patient = db.patients.find_one({"id": appointment["patient_id"]}) if appointment else None

        report_data.append(
            {
                "reminder_id": reminder["id"],
                "appointment_id": reminder["appointment_id"],
                "patient_name": patient["full_name"] if patient else "Unknown",
                "phone": patient["phone_e164"] if patient else "Unknown",
                "offset_days": reminder["offset_days"],
                "scheduled_for": reminder["scheduled_for"].isoformat(),
                "status": reminder["status"],
                "attempts": reminder["attempts"],
                "last_error": reminder.get("last_error", ""),
                "dispatched_at": reminder.get("dispatched_at", ""),
                "delivered_at": reminder.get("delivered_at", ""),
            }
        )

    echo(f"📊 Reminders Report: {from_date} to {to_date}")
    echo(f"Found {len(report_data)} reminders")
    echo("")

    for item in report_data:
        status_icon = {
            "scheduled": "⏰",
            "dispatched": "🚀",
            "delivered": "✅",
            "failed": "❌",
            "canceled": "🚫",
        }.get(item["status"], "❓")

        echo(
            f"{status_icon} {item['reminder_id'][:8]} {item['patient_name']} "
            f"Offset: {item['offset_days']}d "
            f"Scheduled: {item['scheduled_for'][:16]} "
            f"Status: {item['status']} "
            f"Attempts: {item['attempts']}"
        )

    if output:
        try:
            with open(output, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = [
                    "reminder_id",
                    "appointment_id",
                    "patient_name",
                    "phone",
                    "offset_days",
                    "scheduled_for",
                    "status",
                    "attempts",
                    "last_error",
                    "dispatched_at",
                    "delivered_at",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(report_data)

            echo(f"✅ Report exported to: {output}")
        except Exception as exc:
            echo(f"❌ Error exporting CSV: {exc}")

