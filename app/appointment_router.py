from app.tools.booking import book_appointment
from app.tools.reschedule import reschedule_appointment
from app.tools.cancellation import cancel_appointment
from app.tools.availability import check_availability


def handle_call_result(result: dict) -> dict:
    """
    Process the structured result returned by CALL-E
    and execute the requested appointment operation.
    """

    action = result.get("action")

    if action == "book":
        return book_appointment(
            customer_name=result["customer_name"],
            customer_phone=result["customer_phone"],
            service=result["service"],
            appointment_date=result["appointment_date"],
            appointment_time=result["appointment_time"],
        )

    if action == "reschedule":
        return reschedule_appointment(
            customer_phone=result["customer_phone"],
            appointment_date=result["appointment_date"],
            appointment_time=result["appointment_time"],
            new_date=result["new_date"],
            new_time=result["new_time"],
        )

    if action == "cancel":
        return cancel_appointment(
            customer_phone=result["customer_phone"],
            appointment_date=result["appointment_date"],
            appointment_time=result["appointment_time"],
        )

    if action == "availability":
        slots = check_availability(
            result["appointment_date"]
        )

        return {
            "success": True,
            "available_slots": slots,
        }

    return {
        "success": False,
        "message": "Unknown appointment action.",
    }