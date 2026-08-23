import os

from dotenv import load_dotenv
from calle import CalleClient

from app.appointment_router import handle_call_result


load_dotenv()


DIALMIND_TASK = """
You are DialMind, an AI appointment management assistant.

Tell the customer you are an AI voice assistant.

Help the customer with:
- booking an appointment
- checking availability
- rescheduling an appointment
- cancelling an appointment

Ask one question at a time.

For booking, collect:
customer name, phone number, service, date, and time.

For rescheduling, collect:
customer phone number, current appointment date and time,
and the new date and time.

For cancellation, collect:
customer phone number, appointment date, and appointment time.

Do not invent availability.

Before finishing, clearly confirm what action the customer requested.

Return the request as structured data.
"""


RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": [
                "book",
                "availability",
                "reschedule",
                "cancel",
                "unknown",
            ],
        },
        "customer_name": {"type": "string"},
        "customer_phone": {"type": "string"},
        "service": {"type": "string"},
        "appointment_date": {"type": "string"},
        "appointment_time": {"type": "string"},
        "new_date": {"type": "string"},
        "new_time": {"type": "string"},
    },
    "required": ["action"],
}


def run_dialmind_call(phone_number: str) -> dict:
    api_key = os.getenv("CALLE_API_KEY")

    if not api_key:
        raise RuntimeError("CALLE_API_KEY is not set.")

    client = CalleClient(api_key=api_key)

    try:
        call = client.calls.create_and_wait(
            task=DIALMIND_TASK,
            recipient={"phone": phone_number},
            result_schema=RESULT_SCHEMA,
        )

        print("\nCALL-E RESULT:")
        print(call)

        if not call.get("task_completed"):
            return {
                "success": False,
                "message": "CALL-E did not complete the requested task.",
                "call": call,
            }

        result = call.get("structured_result")

        if not result:
            return {
                "success": False,
                "message": "CALL-E returned no structured appointment request.",
                "call": call,
            }

        appointment_result = handle_call_result(result)

        return {
            "success": appointment_result.get("success", False),
            "call": call,
            "appointment": appointment_result,
        }

    finally:
        client.close()


if __name__ == "__main__":
    phone = input(
        "Enter an authorized test phone number: "
    ).strip()

    print("\nStarting DialMind...")

    result = run_dialmind_call(phone)

    print("\nDIALMIND RESULT:")
    print(result)