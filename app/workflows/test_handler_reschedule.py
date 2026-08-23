from app.database import initialize_database
from app.workflows.appointment_confirmation import get_appointment
from app.workflows.confirmation_handler import handle_confirmation_result


initialize_database()

appointment = get_appointment(1)

print("\n--- RESCHEDULE THROUGH HANDLER ---")

result = handle_confirmation_result(
    appointment=appointment,
    outcome="reschedule_requested",
    new_date="2026-08-27",
    new_time="14:30",
)

print(result)