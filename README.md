
# Appointment Reminder Workflow Engine

A CLI-first, Dockerized service for managing appointment reminders with SMS notifications and reply processing.

## Features

- ✅ Patient management (add/list)
- ✅ Appointment management (add/list) 
- ✅ Template management (add/list)
- ✅ Idempotent reminder scheduling
- ✅ Atomic reminder dispatch with stub SMS provider
- ✅ CSV reply import with rule-based classification
- ✅ Automatic appointment status updates
- ✅ Reminder reports with CSV export
- ✅ Appointment history/audit trail
- ✅ MongoDB with proper indexing
- ✅ Docker containerization

## Quick Start

```bash
# Start services
docker-compose up -d

# Show help
docker-compose exec app python -m app.cli.main --help

# Add a patient
docker-compose exec app python -m app.cli.main patients add \
  --name "John Doe" \
  --phone "+15551234567" \
  --tz "America/New_York"

# Add an appointment
docker-compose exec app python -m app.cli.main appointments add \
  --patient-id "PATIENT_ID" \
  --start-at "2025-02-20T15:00:00Z" \
  --provider "Dr. Smith" \
  --location "Main Clinic"

# Schedule reminders
docker-compose exec app python -m app.cli.main schedule \
  --from 2025-02-10 \
  --to 2025-02-25 \
  --offsets 7,2

# Dispatch due reminders
docker-compose exec app python -m app.cli.main dispatch --now

# Process replies
docker-compose exec app python -m app.cli.main replies /app/data/sample_replies.csv

# Generate reports
docker-compose exec app python -m app.cli.main report reminders \
  --from 2025-01-01 \
  --to 2025-12-31 \
  --output /app/data/report.csv

# View appointment history
docker-compose exec app python -m app.cli.main history --appointment "APPOINTMENT_ID"

