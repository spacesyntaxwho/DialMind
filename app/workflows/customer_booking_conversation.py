"""Local, structured customer booking conversation state for Phase 5A."""

from copy import deepcopy

from app.appointment_router import handle_call_result
from app.tools.availability import check_availability


SUPPORTED_ACTIONS = ("book", "availability", "reschedule", "cancel", "unknown")
CUSTOMER_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": list(SUPPORTED_ACTIONS)},
        "customer_name": {"type": "string"},
        "customer_phone": {"type": "string"},
        "service": {"type": "string"},
        "appointment_date": {"type": "string"},
        "appointment_time": {"type": "string"},
        "new_date": {"type": "string"},
        "new_time": {"type": "string"},
    },
    "required": ["action"],
    "additionalProperties": False,
}

BOOKING_FIELDS = (
    "service",
    "appointment_date",
    "appointment_time",
    "customer_name",
    "customer_phone",
)
FIELD_QUESTIONS = {
    "service": "Sure. What service do you need?",
    "appointment_date": "What date would you prefer?",
    "appointment_time": "What time would you prefer?",
    "customer_name": "What is your name?",
    "customer_phone": "What phone number should we use for this appointment?",
}


def create_conversation(action: str = "book") -> dict:
    """Create a local session with no customer details pre-filled."""

    return {
        "action": action,
        "details": {},
        "confirmation_requested": False,
        "completed": False,
    }


def get_missing_booking_field(details: dict) -> str | None:
    """Return the next required booking field in conversational order."""

    for field in BOOKING_FIELDS:
        if not details.get(field):
            return field
    return None


def submit_customer_request(conversation: dict, request: dict | None) -> dict:
    """Store one structured customer response and return the next safe state."""

    if not isinstance(request, dict):
        return {"status": "unknown_request", "message": "I could not understand the request."}

    action = request.get("action", conversation.get("action", "book"))
    if action not in SUPPORTED_ACTIONS:
        return {"status": "invalid_action", "message": "Unsupported appointment action."}
    if action == "unknown":
        return {"status": "unknown_request", "message": "I could not understand the request."}
    if action != "book":
        return {
            "status": "unsupported_action",
            "action": action,
            "message": "This local conversation currently supports booking only.",
        }
    if conversation.get("action") not in {"book", action}:
        return {"status": "invalid_action", "message": "The appointment action cannot change mid-conversation."}
    if conversation.get("completed"):
        return {"status": "already_completed", "message": "This booking conversation is complete."}

    conversation["action"] = action
    details = conversation.setdefault("details", {})
    for field in BOOKING_FIELDS:
        value = request.get(field)
        if isinstance(value, str) and value.strip():
            details[field] = value.strip()

    missing_field = get_missing_booking_field(details)
    if missing_field:
        return {
            "status": "needs_information",
            "missing_field": missing_field,
            "next_question": FIELD_QUESTIONS[missing_field],
        }

    try:
        available_slots = check_availability(details["appointment_date"])
    except ValueError:
        return {
            "status": "invalid_information",
            "message": "Please provide the appointment date as YYYY-MM-DD.",
        }

    if details["appointment_time"] not in available_slots:
        return {
            "status": "slot_unavailable",
            "available_slots": available_slots,
            "message": "That time is unavailable. Please choose one of the available slots.",
        }

    conversation["confirmation_requested"] = True
    return {
        "status": "confirmation_required",
        "action": "book",
        "message": (
            f"You requested a {details['service']} on "
            f"{details['appointment_date']} at {details['appointment_time']}. "
            "Would you like me to book it?"
        ),
        "appointment": deepcopy(details),
    }


def confirm_booking(conversation: dict, confirmed: bool) -> dict:
    """Book only after explicit confirmation using the existing router."""

    if conversation.get("completed"):
        return {"status": "already_completed", "message": "This booking conversation is complete."}
    if not conversation.get("confirmation_requested"):
        return {
            "status": "confirmation_required",
            "message": "Booking requires an explicit customer confirmation.",
        }
    if not confirmed:
        conversation["completed"] = True
        return {"status": "booking_declined", "message": "No appointment was booked."}

    details = conversation["details"]
    router_result = handle_call_result({"action": "book", **details})
    if router_result.get("success"):
        conversation["completed"] = True
        return {"status": "booked", "booking": router_result}

    return {"status": "booking_failed", "booking": router_result}
