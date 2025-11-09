from typing import List


def classify_reply_intent(message: str) -> str:
    """Simple rule-based classifier for reply intent."""
    message_lower = message.lower()

    confirm_patterns: List[str] = [
        "yes",
        "yeah",
        "yep",
        "confirm",
        "confirmed",
        "ok",
        "okay",
        "sure",
        "definitely",
        "will be there",
        "see you",
        "attending",
        "accept",
    ]

    cancel_patterns: List[str] = [
        "no",
        "nope",
        "cancel",
        "cancelled",
        "canceled",
        "stop",
        "end",
        "can't make it",
        "cannot come",
        "not coming",
        "unable to attend",
        "emergency",
        "sick",
        "ill",
    ]

    reschedule_patterns: List[str] = [
        "reschedule",
        "move",
        "change",
        "different time",
        "another time",
        "different day",
        "not available",
    ]

    confirm_matches = sum(1 for pattern in confirm_patterns if pattern in message_lower)
    cancel_matches = sum(1 for pattern in cancel_patterns if pattern in message_lower)
    reschedule_matches = sum(1 for pattern in reschedule_patterns if pattern in message_lower)

    if confirm_matches > cancel_matches and confirm_matches > reschedule_matches:
        return "confirmed"
    if cancel_matches > confirm_matches and cancel_matches > reschedule_matches:
        return "cancel"
    if reschedule_matches > confirm_matches and reschedule_matches > cancel_matches:
        return "reschedule"
    return "unknown"

