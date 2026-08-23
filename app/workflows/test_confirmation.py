from app.database import initialize_database
from app.workflows.appointment_confirmation import (
    get_appointment,
    build_confirmation_task,
)


initialize_database()

appointment = get_appointment(1)

print("\n--- APPOINTMENT ---")
print(appointment)

if appointment:
    print("\n--- GENERATED CALL TASK ---")
    print(build_confirmation_task(appointment))
else:
    print("Appointment 1 was not found.")