from app.database import get_connection
from app.tools.availability import check_availability
from app.tools.reschedule import reschedule_appointment


def get_appointment_for_customer(
    customer_phone: str,
    appointment_date: str,
    appointment_time: str,
) -> dict | None:
    """Find a customer's existing appointment."""

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


def prepare_reschedule(
    customer_phone: str,
    appointment_date: str,
    appointment_time: str,
    new_date: str,
    new_time: str,
) -> dict:
    """
    Check whether a customer's appointment can be rescheduled
    to the requested date and time.
    """

    appointment = get_appointment_for_customer(
        customer_phone,
        appointment_date,
        appointment_time,
    )

    if appointment is None:
        return {
            "success": False,
            "message": "No confirmed appointment was found.",
        }

    available_slots = check_availability(new_date)

    if new_time not in available_slots:
        return {
            "success": False,
            "message": f"{new_time} is not available on {new_date}.",
            "available_slots": available_slots,
        }

    return {
        "success": True,
        "message": "Requested reschedule slot is available.",
        "appointment": appointment,
        "new_date": new_date,
        "new_time": new_time,
    }


def execute_reschedule(
    customer_phone: str,
    appointment_date: str,
    appointment_time: str,
    new_date: str,
    new_time: str,
) -> dict:
    """Actually reschedule the appointment after availability is confirmed."""

    check = prepare_reschedule(
        customer_phone,
        appointment_date,
        appointment_time,
        new_date,
        new_time,
    )

    if not check["success"]:
        return check

    return reschedule_appointment(
        customer_phone=customer_phone,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        new_date=new_date,
        new_time=new_time,
    )