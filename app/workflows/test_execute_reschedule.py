from app.database import initialize_database
from app.workflows.appointment_reschedule import execute_reschedule
from app.workflows.appointment_reschedule import get_appointment_for_customer


initialize_database()

print("\n--- BEFORE RESCHEDULE ---")

before = get_appointment_for_customer(
    customer_phone="+919999999999",
    appointment_date="2026-08-25",
    appointment_time="17:30",
)

print(before)


print("\n--- EXECUTE RESCHEDULE ---")

result = execute_reschedule(
    customer_phone="+919999999999",
    appointment_date="2026-08-25",
    appointment_time="17:30",
    new_date="2026-08-26",
    new_time="10:00",
)

print(result)


print("\n--- AFTER RESCHEDULE ---")

after = get_appointment_for_customer(
    customer_phone="+919999999999",
    appointment_date="2026-08-26",
    appointment_time="10:00",
)

print(after)