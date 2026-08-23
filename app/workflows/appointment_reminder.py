"""Dry-run appointment reminder workflow.

This module deliberately only prepares reminder work.  It does not import or
invoke CALL-E, so Phase 3 cannot place a phone call.
"""

from datetime import datetime, timedelta

from app.database import get_connection


REMINDER_MINUTES = 15

REMINDER_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "outcome": {
            "type": "string",
            "enum": [
                "confirmed",
                "cancel_requested",
                "reschedule_requested",
                "unknown",
            ],
        },
    },
    "required": ["outcome"],
}


def get_appointments_due_for_reminder(
    current_datetime: datetime | None = None,
    reminder_minutes: int = REMINDER_MINUTES,
) -> list[dict]:
    """Return pending, confirmed appointments occurring within the window.

    ``current_datetime`` is injectable to make scheduling deterministic in
    tests.  Date and time are parsed as a real ``datetime`` rather than being
    compared as strings.
    """

    if reminder_minutes < 0:
        raise ValueError("reminder_minutes must not be negative.")

    now = current_datetime or datetime.now()
    latest_due_time = now + timedelta(minutes=reminder_minutes)

    connection = get_connection()
    rows = connection.execute(
        """
        SELECT
            id,
            customer_name,
            customer_phone,
            service,
            appointment_date,
            appointment_time,
            status,
            reminder_status
        FROM appointments
        WHERE status = 'confirmed'
          AND reminder_status = 'pending'
        """
    ).fetchall()
    connection.close()

    due_appointments = []
    for row in rows:
        appointment_datetime = datetime.strptime(
            f"{row[4]} {row[5]}", "%Y-%m-%d %H:%M"
        )
        if now <= appointment_datetime <= latest_due_time:
            due_appointments.append(
                {
                    "id": row[0],
                    "customer_name": row[1],
                    "customer_phone": row[2],
                    "service": row[3],
                    "appointment_date": row[4],
                    "appointment_time": row[5],
                    "status": row[6],
                    "reminder_status": row[7],
                }
            )

    return due_appointments


def build_reminder_task(appointment: dict) -> str:
    """Build the future CALL-E reminder task without sending it."""

    return f"""
You are DialMind, an AI appointment reminder assistant.

You are calling approximately {REMINDER_MINUTES} minutes before a customer's
scheduled appointment. Identify yourself as an AI voice assistant.

Remind the customer about their existing appointment and ask whether they
still plan to attend.

Appointment information:

Customer name: {appointment["customer_name"]}
Service: {appointment["service"]}
Appointment date: {appointment["appointment_date"]}
Appointment time: {appointment["appointment_time"]}

Use only one of these outcomes:
- confirmed
- cancel_requested
- reschedule_requested
- unknown

Do not invent information. Do not create a new appointment. Do not promise a
new appointment. Return only the structured outcome.
""".strip()
