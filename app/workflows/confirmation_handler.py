from app.tools.cancellation import cancel_appointment
from app.workflows.appointment_reschedule import prepare_reschedule


def handle_confirmation_result(
    appointment: dict,
    outcome: str,
    new_date: str | None = None,
    new_time: str | None = None,
) -> dict:
    """Process a customer's appointment confirmation result."""

    if outcome == "confirmed":
        return {
            "success": True,
            "action": "confirmed",
            "message": (
                f"Appointment for {appointment['customer_name']} "
                f"remains confirmed for "
                f"{appointment['appointment_date']} "
                f"at {appointment['appointment_time']}."
            ),
        }

    if outcome == "cancelled":
        result = cancel_appointment(
            customer_phone=appointment["customer_phone"],
            appointment_date=appointment["appointment_date"],
            appointment_time=appointment["appointment_time"],
        )

        return {
            "success": result.get("success", False),
            "action": "cancelled",
            "appointment_result": result,
        }

    if outcome == "reschedule_requested":
        if not new_date or not new_time:
            return {
                "success": False,
                "action": "reschedule_requested",
                "message": (
                    "Customer requested a reschedule, "
                    "but the new date and time were not provided."
                ),
            }

        result = prepare_reschedule(
            customer_phone=appointment["customer_phone"],
            appointment_date=appointment["appointment_date"],
            appointment_time=appointment["appointment_time"],
            new_date=new_date,
            new_time=new_time,
        )

        return {
            "success": result.get("success", False),
            "action": "reschedule_requested",
            "reschedule_result": result,
        }

    return {
        "success": False,
        "action": "unknown",
        "message": (
            "The customer's response could not be safely determined."
        ),
    }