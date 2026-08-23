import os

from calle import CalleClient


DIALMIND_TASK = """
You are DialMind, an appointment management assistant.

Speak naturally and keep the call concise.

Your job is to understand what the customer wants:

- book an appointment
- reschedule an appointment
- cancel an appointment
- ask about availability

For a booking, collect:
- customer name
- service
- requested date
- requested time
- customer phone number if available

For a rescheduling request, collect:
- customer name
- current appointment date
- current appointment time
- new requested date
- new requested time

For cancellation, collect:
- customer name
- appointment date
- appointment time

Ask one question at a time.

Do not invent availability.
Do not claim that an appointment has been booked,
rescheduled, or cancelled.

At the end, return the information you collected
as structured data.
"""


RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": [
                "book",
                "reschedule",
                "cancel",
                "availability",
                "unknown",
            ],
        },
        "customer_name": {
            "type": "string",
        },
        "customer_phone": {
            "type": "string",
        },
        "service": {
            "type": "string",
        },
        "appointment_date": {
            "type": "string",
        },
        "appointment_time": {
            "type": "string",
        },
        "new_date": {
            "type": "string",
        },
        "new_time": {
            "type": "string",
        },
    },
    "required": ["action"],
}


def make_dialmind_call(phone_number: str):
    api_key = os.getenv("CALLE_API_KEY")

    if not api_key:
        raise RuntimeError("CALLE_API_KEY is not set.")

    client = CalleClient(api_key=api_key)

    try:
        return client.calls.create_and_wait(
            task=DIALMIND_TASK,
            recipient={
                "phone": phone_number,
            },
            result_schema=RESULT_SCHEMA,
        )
    finally:
        client.close()


if __name__ == "__main__":
    phone = input(
        "Enter authorized test phone number: "
    ).strip()

    print("\nStarting DialMind call...\n")

    result = make_dialmind_call(phone)

    print("\nCALL-E RESULT:")
    print(result)