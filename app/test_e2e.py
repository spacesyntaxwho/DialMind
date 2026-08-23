from app.database import initialize_database
from app.appointment_router import handle_call_result


initialize_database()

# Simulated structured result from CALL-E.
fake_calle_result = {
    "action": "book",
    "customer_name": "Live Test Customer",
    "customer_phone": "+919555555555",
    "service": "Consultation",
    "appointment_date": "2026-08-31",
    "appointment_time": "11:00",
}

print("\n--- SIMULATED CALL-E RESULT ---")
print(fake_calle_result)

print("\n--- DIALMIND PROCESSING ---")

result = handle_call_result(fake_calle_result)

print(result)