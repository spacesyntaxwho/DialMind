from app.database import initialize_database
from app.tools.availability import check_availability
from app.tools.booking import book_appointment


initialize_database()

date = "2026-08-25"

print("AVAILABLE BEFORE BOOKING:")
print(check_availability(date))

result = book_appointment(
    customer_name="Test Customer",
    customer_phone="+919999999999",
    service="Dental Consultation",
    appointment_date=date,
    appointment_time="17:30",
)

print("\nBOOKING RESULT:")
print(result)

print("\nAVAILABLE AFTER BOOKING:")
print(check_availability(date))