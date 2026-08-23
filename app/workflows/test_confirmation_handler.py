from app.database import initialize_database
from app.workflows.appointment_confirmation import get_appointment
from app.workflows.confirmation_handler import handle_confirmation_result


initialize_database()

appointment = get_appointment(1)

print("\n--- CONFIRMED TEST ---")
print(handle_confirmation_result(appointment, "confirmed"))

print("\n--- RESCHEDULE TEST ---")
print(handle_confirmation_result(appointment, "reschedule_requested"))

print("\n--- UNKNOWN TEST ---")
print(handle_confirmation_result(appointment, "unknown"))