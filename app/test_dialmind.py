from app.database import initialize_database
from app.appointment_router import handle_call_result


initialize_database()


fake_call_result = {
    "action": "book",
    "customer_name": "DialMind Test",
    "customer_phone": "+919666666666",
    "service": "Consultation",
    "appointment_date": "2026-08-30",
    "appointment_time": "11:30",
}


print("\n--- DIALMIND DRY RUN ---")

result = handle_call_result(fake_call_result)

print(result)