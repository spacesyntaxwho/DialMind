"""CALL-E-ready, dry-run-only preparation for appointment reminders.

Phase 4A intentionally has no function that can place a reminder call. This
module builds the payload Phase 4B may later hand to the CALL-E SDK.
"""

import os

try:
    from dotenv import load_dotenv
except ImportError:  # Allows local dry-run tests without optional packages.
    def load_dotenv() -> bool:
        return False

try:
    from calle import CalleClient
except ImportError:  # The SDK is optional until live calling is enabled.
    CalleClient = None

from app.workflows.appointment_reminder import (
    REMINDER_RESULT_SCHEMA,
    build_reminder_task,
)


DRY_RUN = True


def get_calle_configuration() -> dict:
    """Report whether CALL-E is configured without returning its API key."""

    load_dotenv()
    return {
        "configured": bool(os.getenv("CALLE_API_KEY")),
        "sdk_available": CalleClient is not None,
        "mode": "dry_run",
    }


def prepare_reminder_call(appointment: dict) -> dict:
    """Create a CALL-E-ready payload without creating a client or a call.

    The payload has no call identifier or completion state because no call
    exists in Phase 4A.
    """

    if not DRY_RUN:
        raise RuntimeError("Live reminder execution is not available in Phase 4A.")

    return {
        "appointment_id": appointment["id"],
        "phone": appointment["customer_phone"],
        "task": build_reminder_task(appointment),
        "result_schema": REMINDER_RESULT_SCHEMA,
        "mode": "dry_run",
    }
