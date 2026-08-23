from app.database import initialize_database
from app.appointment_router import handle_call_result


initialize_database()

phone = "+919777777777"


print("\n--- BOOK ---")

print(
    handle_call_result({
        "action": "book",
        "customer_name": "Full Flow Test",
        "customer_phone": phone,
        "service": "Consultation",
        "appointment_date": "2026-08-29",
        "appointment_time": "10:00",
    })
)


print("\n--- RESCHEDULE ---")

print(
    handle_call_result({
        "action": "reschedule",
        "customer_phone": phone,
        "appointment_date": "2026-08-29",
        "appointment_time": "10:00",
        "new_date": "2026-08-29",
        "new_time": "15:30",
    })
)


print("\n--- CANCEL ---")

print(
    handle_call_result({
        "action": "cancel",
        "customer_phone": phone,
        "appointment_date": "2026-08-29",
        "appointment_time": "15:30",
    })
)