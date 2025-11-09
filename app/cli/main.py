import os
from datetime import datetime

import typer
from pymongo import MongoClient

from app.services import (
    add_patient,
    list_patients,
    add_appointment,
    list_appointments,
    add_template,
    list_templates,
    schedule_reminders,
    dispatch_due_reminders,
    process_replies,
    generate_reminders_report,
    show_appointment_history,
)
from app.utils.classification import classify_reply_intent

app = typer.Typer(
    name="reminderctl",
    help="Appointment Reminder Workflow Engine CLI"
)

# MongoDB connection
def get_db():
    client = MongoClient(os.getenv("MONGO_URL", "mongodb://mongo:27017"))
    return client[os.getenv("DB_NAME", "reminder_dev")]

# Patients commands
patients_app = typer.Typer()
app.add_typer(patients_app, name="patients")

@patients_app.command("add")
def patients_add(
    name: str = typer.Option(..., "--name", help="Patient full name"),
    phone: str = typer.Option(..., "--phone", help="Phone in E.164 format"),
    tz: str = typer.Option(..., "--tz", help="IANA timezone")
):
    """Add a new patient"""
    db = get_db()
    add_patient(db, name, phone, tz, typer.echo)

@patients_app.command("list")
def patients_list():
    """List all patients"""
    db = get_db()
    list_patients(db, typer.echo)

# Appointments commands
appointments_app = typer.Typer()
app.add_typer(appointments_app, name="appointments")

@appointments_app.command("add")
def appointments_add(
    patient_id: str = typer.Option(..., "--patient-id", help="Patient ID"),
    start_at: str = typer.Option(..., "--start-at", help="Appointment time (ISO format)"),
    provider: str = typer.Option(..., "--provider", help="Healthcare provider"),
    location: str = typer.Option(..., "--location", help="Appointment location")
):
    """Add a new appointment"""
    db = get_db()
    add_appointment(db, patient_id, start_at, provider, location, typer.echo)

@appointments_app.command("list")
def appointments_list():
    """List all appointments"""
    db = get_db()
    list_appointments(db, typer.echo)

# Templates commands
templates_app = typer.Typer()
app.add_typer(templates_app, name="templates")

@templates_app.command("add")
def templates_add(
    name: str = typer.Option(..., "--name", help="Template name"),
    body: str = typer.Option(..., "--body", help="Template body")
):
    """Add a new template"""
    db = get_db()
    add_template(db, name, body, typer.echo)

@templates_app.command("list")
def templates_list():
    """List all templates"""
    db = get_db()
    list_templates(db, typer.echo)

# Workflow commands
@app.command()
def schedule(
    from_date: str = typer.Option(..., "--from", help="Start date (YYYY-MM-DD)"),
    to_date: str = typer.Option(..., "--to", help="End date (YYYY-MM-DD)"),
    offsets: str = typer.Option("7,2", "--offsets", help="Comma-separated offset days")
):
    """Schedule reminders"""
    db = get_db()
    schedule_reminders(db, from_date, to_date, offsets, typer.echo)

@app.command()
def dispatch(
    now: bool = typer.Option(False, "--now", help="Dispatch due reminders immediately")
):
    """Dispatch due reminders"""
    if now:
        db = get_db()
        dispatch_due_reminders(db, typer.echo)
    else:
        typer.echo("ℹ️  Use --now to dispatch due reminders")

def classify_reply_intent(message: str) -> str:
    """Simple rule-based classifier for reply intent"""
    message_lower = message.lower()
    
    confirm_patterns = [
        'yes', 'yeah', 'yep', 'confirm', 'confirmed', 'ok', 'okay', 'sure',
        'definitely', 'will be there', 'see you', 'attending', 'accept'
    ]
    
    cancel_patterns = [
        'no', 'nope', 'cancel', 'cancelled', 'canceled', 'stop', 'end',
        "can't make it", 'cannot come', 'not coming', 'unable to attend',
        'emergency', 'sick', 'ill'
    ]
    
    reschedule_patterns = [
        'reschedule', 'move', 'change', 'different time', 'another time',
        'different day', 'not available'
    ]
    
    # Check patterns
    confirm_matches = sum(1 for pattern in confirm_patterns if pattern in message_lower)
    cancel_matches = sum(1 for pattern in cancel_patterns if pattern in message_lower)
    reschedule_matches = sum(1 for pattern in reschedule_patterns if pattern in message_lower)
    
    if confirm_matches > cancel_matches and confirm_matches > reschedule_matches:
        return "confirmed"
    elif cancel_matches > confirm_matches and cancel_matches > reschedule_matches:
        return "cancel"
    elif reschedule_matches > confirm_matches and reschedule_matches > cancel_matches:
        return "reschedule"
    else:
        return "unknown"

@app.command()
def replies(
    file_path: str = typer.Argument(..., help="CSV file path"),
    classify: bool = typer.Option(True, "--classify/--no-classify", help="Classify replies and update status")
):
    """Import and process replies from CSV"""
    try:
        db = get_db()
        process_replies(db, file_path, classify, typer.echo)
    except Exception as e:
        typer.echo(f"❌ Error processing CSV: {str(e)}")

@app.command()
def report(
    type: str = typer.Argument("reminders", help="Report type: reminders"),
    from_date: str = typer.Option(..., "--from", help="Start date (YYYY-MM-DD)"),
    to_date: str = typer.Option(..., "--to", help="End date (YYYY-MM-DD)"),
    output: str = typer.Option(None, "--output", "-o", help="Output CSV file path")
):
    """Generate reports"""
    if type == "reminders":
        db = get_db()
        generate_reminders_report(db, from_date, to_date, output, typer.echo)

@app.command()
def history(
    appointment: str = typer.Option(..., "--appointment", help="Appointment ID")
):
    """View appointment history"""
    db = get_db()
    show_appointment_history(db, appointment, typer.echo)

if __name__ == "__main__":
    app()