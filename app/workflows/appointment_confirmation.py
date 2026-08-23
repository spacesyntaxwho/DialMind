import os

from dotenv import load_dotenv
from calle import CalleClient

from app.database import get_connection
from app.workflows.confirmation_handler import handle_confirmation_result


load_dotenv()


CONFIRMATION_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "outcome": {
            "type": "string",
            "enum": [
                "confirmed",
                "cancelled",
                "reschedule_requested",
                "no_answer",
                "unknown",
            ],
        },
    },
    "required": ["outcome"],
}


def get_appointment(appointment_id: int) -> dict | None:
    """Get an appointment by ID."""

    connection = get_connection()

    row = connection.execute(
        """
        SELECT
            id,
            customer_name,
            customer_phone,
            service,
            appointment_date,
            appointment_time,
            status
        FROM appointments
        WHERE id = ?
        """,
        (appointment_id,),
    ).fetchone()

    connection.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "customer_name": row[1],
        "customer_phone": row[2],
        "service": row[3],
        "appointment_date": row[4],
        "appointment_time": row[5],
        "status": row[6],
    }


def build_confirmation_task(appointment: dict) -> str:
    """Build the CALL-E task for appointment confirmation."""

    return f"""
You are DialMind, an AI appointment confirmation assistant.

You are calling on behalf of a business.

Tell the customer that you are an AI voice assistant.

Your goal is to confirm whether the customer will attend their
existing appointment.

Appointment information:

Customer name: {appointment["customer_name"]}
Service: {appointment["service"]}
Appointment date: {appointment["appointment_date"]}
Appointment time: {appointment["appointment_time"]}

Say that you are calling to confirm this appointment.

Ask whether the customer will attend.

If the customer confirms, return:
confirmed

If the customer wants to cancel, return:
cancelled

If the customer wants to change the appointment, return:
reschedule_requested

If you cannot determine the outcome, return:
unknown

Do not invent information.
Do not create a new appointment.
Do not promise a new appointment.

Return only the structured outcome.
"""


def confirm_appointment(appointment_id: int) -> dict:
    """Call a customer and confirm an existing appointment."""

    appointment = get_appointment(appointment_id)

    if appointment is None:
        return {
            "success": False,
            "message": "Appointment not found.",
        }

    if appointment["status"] != "confirmed":
        return {
            "success": False,
            "message": "Only confirmed appointments can be called.",
        }

    api_key = os.getenv("CALLE_API_KEY")

    if not api_key:
        raise RuntimeError("CALLE_API_KEY is not set.")

    client = CalleClient(api_key=api_key)

    try:
        call = client.calls.create_and_wait(
            task=build_confirmation_task(appointment),
            recipient={
                "phone": appointment["customer_phone"],
            },
            result_schema=CONFIRMATION_RESULT_SCHEMA,
        )

        print("\nCALL-E RESULT:")
        print(call)

        if not call.get("task_completed"):
            return {
                "success": False,
                "message": "CALL-E did not complete the confirmation task.",
                "call": call,
            }

        result = call.get("structured_result")

        if not result:
            return {
                "success": False,
                "message": "CALL-E returned no confirmation result.",
                "call": call,
            }

        outcome = result["outcome"]

        handler_result = handle_confirmation_result(
            appointment,
            outcome,
        )

        return {
            "success": handler_result.get("success", False),
            "appointment": appointment,
            "outcome": outcome,
            "handler_result": handler_result,
            "call": call,
        }

    finally:
        client.close()