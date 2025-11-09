from datetime import datetime
from typing import Callable, Dict, Any, List
import uuid


def add_template(db, name: str, body: str, echo: Callable[[str], None]) -> None:
    """Add a new template."""
    if db.templates.find_one({"name": name}):
        echo(f"❌ Template '{name}' already exists")
        return

    template: Dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "name": name,
        "channel": "sms",
        "language": "en",
        "body": body,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    db.templates.insert_one(template)
    echo(f"✅ Template created: {template['id']}")


def list_templates(db, echo: Callable[[str], None]) -> None:
    """List all templates."""
    templates: List[Dict[str, Any]] = list(db.templates.find({}).limit(20))

    if not templates:
        echo("No templates found")
        return

    for template in templates:
        body_preview = (
            template["body"][:50] + "..." if len(template["body"]) > 50 else template["body"]
        )
        echo(f"{template['id'][:8]} {template['name']}: {body_preview}")

