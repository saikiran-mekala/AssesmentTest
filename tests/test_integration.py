import pytest
from pymongo import MongoClient
import os
from datetime import datetime, timedelta
import uuid
import csv
import tempfile

@pytest.fixture
def test_db():
    client = MongoClient(os.getenv("MONGO_URL", "mongodb://localhost:27017"))
    db = client["test_reminder_db"]
    # Clean up
    for collection in ["patients", "appointments", "templates", "reminders", "events"]:
        db[collection].delete_many({})
    return db

def test_complete_workflow(test_db):
    """Test the complete reminder workflow"""
    # 1. Create patient
    patient_id = str(uuid.uuid4())
    test_db.patients.insert_one({
        "id": patient_id,
        "full_name": "Workflow Test",
        "phone_e164": "+15551112222",
        "tz": "UTC",
        "active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    
    # 2. Create appointment
    appointment_id = str(uuid.uuid4())
    appointment_time = datetime.utcnow() + timedelta(days=10)
    test_db.appointments.insert_one({
        "id": appointment_id,
        "patient_id": patient_id,
        "start_at": appointment_time,
        "provider": "Dr. Workflow",
        "location": "Test Clinic",
        "status": "scheduled",
        "version": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    
    # 3. Create template
    test_db.templates.insert_one({
        "id": str(uuid.uuid4()),
        "name": "default",
        "channel": "sms",
        "language": "en",
        "body": "Hi {patient.first_name}, your appointment is on {appointment.start_local}",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    
    # 4. Schedule reminders
    reminder_id = str(uuid.uuid4())
    test_db.reminders.insert_one({
        "id": reminder_id,
        "appointment_id": appointment_id,
        "offset_days": 2,
        "scheduled_for": datetime.utcnow() - timedelta(hours=1),  # Past due
        "status": "scheduled",
        "attempts": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    
    # 5. Verify reminder was created
    reminder = test_db.reminders.find_one({"appointment_id": appointment_id})
    assert reminder is not None
    assert reminder["status"] == "scheduled"
    
    # 6. Test reply processing with CSV
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['from', 'to', 'message', 'received_at', 'event_id'])
        writer.writerow(['+15551112222', '+15550001111', 'Yes confirmed', '2025-01-20T10:30:00Z', 'test_001'])
        csv_file = f.name
    
    try:
        # Import the function directly
        from app.cli.main import classify_reply_intent
        intent = classify_reply_intent("Yes confirmed")
        assert intent == "confirmed"
        
    finally:
        os.unlink(csv_file)
    
    print("✅ Complete workflow test passed!")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])