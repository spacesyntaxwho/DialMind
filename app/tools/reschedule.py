from app.database import get_connection
from app.tools.availability import check_availability


def reschedule_appointment(
    customer_phone: str,
    appointment_date: str,
    appointment_time: str,
    new_date: str,
    new_time: str,
) -> dict:
    """Move an existing appointment to a new available slot."""

    connection = get_connection()

    cursor = connection.execute(
        """
        SELECT id, customer_name, service
        FROM appointments
        WHERE customer_phone = ?
        AND appointment_date = ?
        AND appointment_time = ?
        AND status = 'confirmed'
        """,
        (
            customer_phone,
            appointment_date,
            appointment_time,
        ),
    )

    appointment = cursor.fetchone()

    if appointment is None:
        connection.close()

        return {
            "success": False,
            "message": "No confirmed appointment was found.",
        }

    appointment_id, customer_name, service = appointment

    available_slots = check_availability(new_date)

    if new_time not in available_slots:
        connection.close()

        return {
            "success": False,
            "message": f"{new_time} on {new_date} is not available.",
        }

    connection.execute(
        """
        UPDATE appointments
        SET appointment_date = ?,
            appointment_time = ?
        WHERE id = ?
        """,
        (
            new_date,
            new_time,
            appointment_id,
        ),
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "appointment_id": appointment_id,
        "customer_name": customer_name,
        "service": service,
        "old_date": appointment_date,
        "old_time": appointment_time,
        "new_date": new_date,
        "new_time": new_time,
        "message": (
            f"Appointment successfully rescheduled to "
            f"{new_date} at {new_time}."
        ),
    }