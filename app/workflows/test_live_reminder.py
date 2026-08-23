"""Explicit, one-shot manual live test for a DialMind reminder call.

This module is intentionally separate from the scheduler.  Running it without
``--live`` cannot create a CALL-E client or place a call.
"""

import argparse
import json
import os
import re

from app.database import get_connection
from app.workflows.calle_diagnostic import (
    INDIA_ENGLISH_LOCALE,
    INDIA_REGION,
    build_reminder_call_payload,
    extract_safe_calle_error,
)
from app.workflows.reminder_call import (
    CalleClient,
    get_calle_configuration,
    prepare_reminder_call,
)
from app.workflows.reminder_result_handler import handle_reminder_result

try:
    from calle.generated.models.call_task_recipient_request import (
        CallTaskRecipientRequest,
    )
except ImportError:  # The manual live path reports a clear SDK error below.
    CallTaskRecipientRequest = None


LIVE_CALL = False
E164_PHONE_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")


def mask_phone_number(phone: str) -> str:
    """Return a display-safe E.164 phone number."""

    return f"{phone[:3]}{'*' * (len(phone) - 7)}{phone[-4:]}"


def get_live_reminder_appointment(appointment_id: int) -> dict | None:
    """Fetch a confirmed appointment with a pending reminder, without writing."""

    connection = get_connection()
    row = connection.execute(
        """
        SELECT
            id,
            customer_name,
            customer_phone,
            service,
            appointment_date,
            appointment_time,
            status,
            reminder_status
        FROM appointments
        WHERE id = ?
          AND status = 'confirmed'
          AND reminder_status = 'pending'
        """,
        (appointment_id,),
    ).fetchone()
    connection.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "customer_name": row[1],
        "customer_phone": row[2],
        "service": row[3],
        "appointment_date": row[4],
        "appointment_time": row[5],
        "status": row[6],
        "reminder_status": row[7],
    }


def build_live_call_request_payload(payload: dict) -> dict:
    """Build the JSON body used by the installed SDK's ``calls.create``.

    ``CalleCalls.create`` accepts JSON recipient dictionaries and forwards
    them unchanged as the ``recipients`` member of the POST body.  The
    generated model supplies the documented recipient shape before it is
    serialized for that convenience client.
    """

    if CallTaskRecipientRequest is None:
        raise RuntimeError("The calle-ai recipient model is not installed.")

    recipient = CallTaskRecipientRequest(
        phones=[payload["phone"]],
        region=INDIA_REGION,
        locale=INDIA_ENGLISH_LOCALE,
    )
    request_payload = build_reminder_call_payload(payload)
    request_payload["recipients"] = [recipient.to_dict()]
    return request_payload


def execute_live_reminder(
    appointment: dict,
    phone: str,
    *,
    live_call: bool = LIVE_CALL,
) -> dict:
    """Place exactly one explicitly enabled live reminder call.

    There is intentionally no retry and this function never updates the
    appointment record, regardless of the result.
    """

    if not live_call:
        print("Live calling is disabled. Re-run with --live to place one call.")
        return {"executed": False, "mode": "dry_run"}

    if not E164_PHONE_PATTERN.fullmatch(phone):
        raise ValueError("The phone number must be a valid E.164 number.")

    if appointment["status"] != "confirmed":
        raise ValueError("Only confirmed appointments can receive a reminder.")

    if appointment["reminder_status"] != "pending":
        raise ValueError("Only appointments with a pending reminder can be called.")

    if phone != appointment["customer_phone"]:
        raise ValueError("The supplied phone number must match the appointment.")

    configuration = get_calle_configuration()
    if not configuration["configured"]:
        raise RuntimeError("CALLE_API_KEY is not configured.")
    if CalleClient is None:
        raise RuntimeError("The calle-ai SDK is not installed.")
    payload = prepare_reminder_call(appointment)
    request_payload = build_live_call_request_payload(payload)
    api_key = os.getenv("CALLE_API_KEY")
    try:
        client = CalleClient(api_key=api_key)
        try:
            # This is the single, deliberate Phase 4B call. There is no retry.
            call = client.calls.create_and_wait(
                task=request_payload["task"],
                recipients=request_payload["recipients"],
                result_schema=request_payload["result_schema"],
            )
        finally:
            client.close()
    except Exception as error:
        # The SDK preserves status, code, and details on CalleAPIError.  Print
        # only a redacted diagnostic if a future user explicitly runs --live.
        print("CALL-E ERROR DIAGNOSTIC:")
        print(json.dumps(extract_safe_calle_error(error), indent=2))
        raise

    return {
        "executed": True,
        "appointment_id": payload["appointment_id"],
        "result": call.get("structured_result"),
        "call": call,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Place one explicitly authorized DialMind reminder test call."
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Required: place one real CALL-E phone call.",
    )
    parser.add_argument(
        "--appointment-id",
        type=int,
        required=True,
        help="ID of a confirmed appointment with a pending reminder.",
    )
    parser.add_argument(
        "--phone",
        required=True,
        help="Authorized E.164 phone number that matches the appointment.",
    )
    parser.add_argument(
        "--apply-result",
        action="store_true",
        help="After a live call, persist its validated reminder outcome.",
    )
    arguments = parser.parse_args()

    appointment = get_live_reminder_appointment(arguments.appointment_id)
    if appointment is None:
        parser.error(
            "No confirmed appointment with a pending reminder exists for that ID."
        )

    if not E164_PHONE_PATTERN.fullmatch(arguments.phone):
        parser.error("--phone must be a valid E.164 number.")
    if arguments.phone != appointment["customer_phone"]:
        parser.error("--phone must match the selected appointment.")

    print(f"Authorized test recipient: {mask_phone_number(arguments.phone)}")
    result = execute_live_reminder(
        appointment,
        arguments.phone,
        live_call=arguments.live,
    )
    if result["executed"]:
        print("CALL-E RESULT:")
        print(json.dumps(result["result"], indent=2))
        if arguments.apply_result:
            handler_result = handle_reminder_result(
                appointment["id"], result["result"]
            )
            print("REMINDER RESULT HANDLER:")
            print(json.dumps(handler_result, indent=2))


if __name__ == "__main__":
    main()
