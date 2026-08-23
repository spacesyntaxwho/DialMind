from app.database import get_connection
from app.tools.availability import check_availability


def book_appointment(
    customer_name: str,
    customer_phone: str,
    service: str,
    appointment_date: str,
    appointment_time: str,
) -> dict:
    """Book an appointment if the requested slot is available."""

    available_slots = check_availability(appointment_date)

    if appointment_time not in available_slots:
        return {
            "success": False,
            "message": f"{appointment_time} is not available.",
        }

    connection = get_connection()

    connection.execute(
        """
        INSERT INTO appointments (
            customer_name,
            customer_phone,
            service,
            appointment_date,
            appointment_time,
            status,
            reminder_status
        )
        VALUES (?, ?, ?, ?, ?, 'confirmed', 'pending')
        """,
        (
            customer_name,
            customer_phone,
            service,
            appointment_date,
            appointment_time,
        ),
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "message": (
            f"Appointment booked for {customer_name} "
            f"on {appointment_date} at {appointment_time}."
        ),
    }
