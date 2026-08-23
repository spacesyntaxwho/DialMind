from app.database import get_connection


def cancel_appointment(
    customer_phone: str,
    appointment_date: str,
    appointment_time: str,
) -> dict:
    """Cancel a confirmed appointment."""

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

    connection.execute(
        """
        UPDATE appointments
        SET status = 'cancelled'
        WHERE id = ?
        """,
        (appointment_id,),
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "appointment_id": appointment_id,
        "customer_name": customer_name,
        "service": service,
        "date": appointment_date,
        "time": appointment_time,
        "message": (
            f"Appointment on {appointment_date} at "
            f"{appointment_time} has been cancelled."
        ),
    }
