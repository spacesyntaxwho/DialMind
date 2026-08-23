from datetime import datetime, timedelta


BUSINESS_HOURS = {
    "start": 9,
    "end": 18,
}

APPOINTMENT_DURATION = 30


def generate_slots(date: str) -> list[str]:
    """Generate available appointment slots for a given date."""

    requested_date = datetime.strptime(date, "%Y-%m-%d")

    slots = []

    current = requested_date.replace(
        hour=BUSINESS_HOURS["start"],
        minute=0,
        second=0,
        microsecond=0,
    )

    end = requested_date.replace(
        hour=BUSINESS_HOURS["end"],
        minute=0,
        second=0,
        microsecond=0,
    )

    while current <= end - timedelta(minutes=APPOINTMENT_DURATION):
        slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=APPOINTMENT_DURATION)

    return slots


def check_availability(date: str) -> list[str]:
    """Return appointment slots that are not already booked."""

    from app.database import get_connection

    all_slots = generate_slots(date)

    connection = get_connection()

    cursor = connection.execute(
        """
        SELECT appointment_time
        FROM appointments
        WHERE appointment_date = ?
        AND status = 'confirmed'
        """,
        (date,),
    )

    booked_slots = {row[0] for row in cursor.fetchall()}

    connection.close()

    return [
        slot
        for slot in all_slots
        if slot not in booked_slots
    ]