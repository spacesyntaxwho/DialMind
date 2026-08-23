"""Safe persistence of validated CALL-E reminder outcomes."""

from app.database import get_connection
from app.workflows.appointment_reminder import REMINDER_RESULT_SCHEMA


OUTCOME_TO_REMINDER_STATUS = {
    "confirmed": "confirmed",
    "cancel_requested": "cancel_requested",
    "reschedule_requested": "reschedule_requested",
    "unknown": "failed",
}
ALLOWED_REMINDER_OUTCOMES = set(
    REMINDER_RESULT_SCHEMA["properties"]["outcome"]["enum"]
)


def handle_reminder_result(appointment_id: int, result: dict | None) -> dict:
    """Validate a reminder result and update only ``reminder_status``.

    A matching duplicate result is idempotent.  Once any other terminal
    reminder status is stored, conflicting/stale results cannot overwrite it.
    """

    if not isinstance(result, dict) or "outcome" not in result:
        return {"success": False, "message": "Invalid reminder outcome."}

    outcome = result["outcome"]
    if not isinstance(outcome, str) or outcome not in ALLOWED_REMINDER_OUTCOMES:
        return {"success": False, "message": "Invalid reminder outcome."}

    reminder_status = OUTCOME_TO_REMINDER_STATUS[outcome]
    connection = get_connection()
    appointment = connection.execute(
        """
        SELECT status, reminder_status
        FROM appointments
        WHERE id = ?
        """,
        (appointment_id,),
    ).fetchone()

    if appointment is None:
        connection.close()
        return {"success": False, "message": "Appointment not found."}

    appointment_status, current_reminder_status = appointment
    if appointment_status != "confirmed":
        connection.close()
        return {
            "success": False,
            "message": "Only confirmed appointments can process reminder results.",
        }

    if current_reminder_status == reminder_status:
        connection.close()
        return {
            "success": True,
            "appointment_id": appointment_id,
            "outcome": outcome,
            "reminder_status": reminder_status,
            "idempotent": True,
        }

    if current_reminder_status != "pending":
        connection.close()
        return {
            "success": False,
            "message": "Reminder result has already been processed.",
        }

    connection.execute(
        """
        UPDATE appointments
        SET reminder_status = ?
        WHERE id = ?
        """,
        (reminder_status, appointment_id),
    )
    connection.commit()
    connection.close()

    return {
        "success": True,
        "appointment_id": appointment_id,
        "outcome": outcome,
        "reminder_status": reminder_status,
        "idempotent": False,
    }
