from app.database import initialize_database
from app.tools.availability import check_availability
from app.tools.booking import book_appointment
from app.tools.reschedule import reschedule_appointment
from app.tools.cancellation import cancel_appointment


initialize_database()

phone = "+919999999999"

print("\n--- BOOK ---")

booking = book_appointment(
    customer_name="Test Customer",
    customer_phone=phone,
    service="Dental Consultation",
    appointment_date="2026-08-26",
    appointment_time="10:00",
)

print(booking)


print("\n--- RESCHEDULE ---")

rescheduled = reschedule_appointment(
    customer_phone=phone,
    appointment_date="2026-08-26",
    appointment_time="10:00",
    new_date="2026-08-27",
    new_time="14:30",
)

print(rescheduled)


print("\n--- CANCEL ---")

cancelled = cancel_appointment(
    customer_phone=phone,
    appointment_date="2026-08-27",
    appointment_time="14:30",
)

print(cancelled)


print("\n--- FINAL AVAILABILITY ---")

print(check_availability("2026-08-27"))