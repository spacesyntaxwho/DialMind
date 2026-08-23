import os

from dotenv import load_dotenv
from calle import CalleClient

load_dotenv()

api_key = os.getenv("CALLE_API_KEY")

if not api_key:
    raise RuntimeError("CALLE_API_KEY is not set")

phone_number = os.getenv("TEST_PHONE_NUMBER")

if not phone_number:
    raise RuntimeError("TEST_PHONE_NUMBER is not set")

client = CalleClient(api_key=api_key)

print("Starting DialMind test call...")

result = client.calls.create_and_wait(
    task="""
You are DialMind, an AI appointment receptionist.

Call the recipient and have a short test conversation.

Introduce yourself as DialMind.
Explain that you are an AI appointment receptionist.
Ask the recipient what type of appointment they would like to book.
Ask for their preferred date and time.
Ask for their name.

Do not actually promise that an appointment has been booked.
This is only a conversation test.

Once you have collected the information, politely end the call.
""",
    recipient={
        "phone": phone_number,
    },
    result_schema={
        "type": "object",
        "properties": {
            "appointment_type": {
                "type": "string"
            },
            "preferred_date": {
                "type": "string"
            },
            "preferred_time": {
                "type": "string"
            },
            "customer_name": {
                "type": "string"
            }
        },
        "required": [
            "appointment_type",
            "preferred_date",
            "preferred_time",
            "customer_name"
        ]
    },
)

print("\nCall completed!")
print(result)