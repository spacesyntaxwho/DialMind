from app.database import initialize_database
from app.workflows.appointment_reschedule import prepare_reschedule


initialize_database()


print("\n--- RESCHEDULE AVAILABLE SLOT ---")

result = prepare_reschedule(
    customer_phone="+919999999999",
    appointment_date="2026-08-25",
    appointment_time="17:30",
    new_date="2026-08-26",
    new_time="10:00",
)

print(result)