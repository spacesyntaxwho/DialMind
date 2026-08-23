"""Offline diagnostics and an explicitly enabled minimal CALL-E test."""

import argparse
import json
import os
import re
from copy import deepcopy

try:
    from dotenv import load_dotenv
except ImportError:  # Keeps offline diagnostics runnable without optional deps.
    def load_dotenv() -> bool:
        return False

try:
    from calle import CalleClient
except ImportError:  # The live command reports this only after --live.
    CalleClient = None


E164_PHONE_PATTERN = re.compile(r"\+[1-9]\d{7,14}")
INDIA_REGION = "IN"
INDIA_ENGLISH_LOCALE = "en-IN"
MINIMUM_RESULT_SCHEMA = {
    "type": "object",
    "required": ["can_hear_clearly"],
    "properties": {
        "can_hear_clearly": {
            "type": "string",
            "enum": ["yes", "no", "unknown"],
        }
    },
}
SECRET_DETAIL_KEYS = {"api_key", "authorization", "token", "secret", "password"}
API_KEY_PATTERN = re.compile(r"\b(?:calle|iams)_(?:live|test)_[A-Za-z0-9_-]+\b", re.I)
PLACEHOLDER_API_KEY_VALUES = {
    "calle_api_key",
    "your_api_key",
    "your_calle_api_key",
    "replace_me",
    "placeholder",
}


def mask_phone_number(phone: str) -> str:
    """Mask an E.164 number while retaining only its prefix and last four digits."""

    if len(phone) <= 7:
        return "***"
    return f"{phone[:3]}{'*' * (len(phone) - 7)}{phone[-4:]}"


def build_minimum_call_payload(phone: str) -> dict:
    """Build the official task-only quickstart request without sending it."""

    return {
        "task": (
            f"Call {phone} and say hello. Ask whether they can hear you clearly."
        ),
        "result_schema": deepcopy(MINIMUM_RESULT_SCHEMA),
    }


def build_reminder_call_payload(reminder_payload: dict) -> dict:
    """Build the documented explicit-recipient reminder request without sending."""

    return {
        "task": reminder_payload["task"],
        "recipients": [
            {
                "phones": [reminder_payload["phone"]],
                "region": INDIA_REGION,
                "locale": INDIA_ENGLISH_LOCALE,
            }
        ],
        "result_schema": reminder_payload["result_schema"],
    }


def build_offline_diagnostic_report(phone: str, reminder_payload: dict) -> dict:
    """Return the two display-safe request bodies for side-by-side diagnosis."""

    return {
        "minimum_task_only": mask_payload(build_minimum_call_payload(phone)),
        "reminder_explicit_recipient": mask_payload(
            build_reminder_call_payload(reminder_payload)
        ),
    }


def mask_payload(payload: dict) -> dict:
    """Return a display-safe copy of a request body with E.164 numbers masked."""

    def mask_value(value):
        if isinstance(value, dict):
            return {key: mask_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [mask_value(item) for item in value]
        if isinstance(value, str):
            return E164_PHONE_PATTERN.sub(
                lambda match: mask_phone_number(match.group(0)), value
            )
        return value

    return mask_value(payload)


def inspect_api_key_configuration() -> dict:
    """Report API-key configuration booleans without exposing the key."""

    load_dotenv()
    api_key = os.getenv("CALLE_API_KEY", "").strip()
    normalized_key = api_key.lower()
    return {
        "present": bool(api_key),
        "non_empty": len(api_key) > 0,
        "not_placeholder": bool(api_key)
        and normalized_key not in PLACEHOLDER_API_KEY_VALUES
        and not normalized_key.startswith("your_"),
    }


def extract_safe_calle_error(error: Exception) -> dict:
    """Extract redacted status/code/details retained by the installed SDK."""

    def redact(value, key: str = ""):
        normalized_key = key.lower()
        if any(secret_key in normalized_key for secret_key in SECRET_DETAIL_KEYS):
            return "<redacted>"
        if isinstance(value, dict):
            return {item_key: redact(item, item_key) for item_key, item in value.items()}
        if isinstance(value, list):
            return [redact(item) for item in value]
        if isinstance(value, str):
            value = API_KEY_PATTERN.sub("<redacted>", value)
            return E164_PHONE_PATTERN.sub(
                lambda match: mask_phone_number(match.group(0)), value
            )
        return value

    details = getattr(error, "details", {})
    return {
        "http_status": getattr(error, "status_code", None),
        "error_code": getattr(error, "code", error.__class__.__name__),
        "message": redact(str(error)),
        "details": redact(details) if isinstance(details, dict) else {},
    }


def run_minimal_live_diagnostic(phone: str, *, live_call: bool = False) -> dict:
    """Make one documented diagnostic call only when explicitly enabled.

    This function has no database or appointment-workflow dependency and has
    no retry behavior.  Calling it with the default value cannot create a
    CALL-E client or send a request.
    """

    if not live_call:
        print("Live diagnostic calling is disabled. Re-run with --live.")
        return {"executed": False, "mode": "dry_run"}

    if not re.fullmatch(r"\+[1-9]\d{7,14}", phone):
        raise ValueError("The phone number must be a valid E.164 number.")

    configuration = inspect_api_key_configuration()
    if not all(configuration.values()):
        raise RuntimeError("CALLE_API_KEY is not configured safely.")
    if CalleClient is None:
        raise RuntimeError("The calle-ai SDK is not installed.")

    request_payload = build_minimum_call_payload(phone)
    api_key = os.getenv("CALLE_API_KEY")
    try:
        client = CalleClient(api_key=api_key)
        try:
            # Exactly one API operation; intentionally no retry.
            call = client.calls.create_and_wait(**request_payload)
        finally:
            client.close()
    except Exception as error:
        print("CALL-E ERROR DIAGNOSTIC:")
        print(json.dumps(extract_safe_calle_error(error), indent=2))
        raise

    return {"executed": True, "call": call}


def main() -> None:
    """Run the minimal diagnostic only with an explicit live opt-in."""

    parser = argparse.ArgumentParser(
        description="Place one minimal, explicitly authorized CALL-E diagnostic call."
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Required: place one real CALL-E diagnostic phone call.",
    )
    parser.add_argument(
        "--phone",
        required=True,
        help="Authorized E.164 phone number for the diagnostic call.",
    )
    arguments = parser.parse_args()

    if not arguments.live:
        parser.error("--live is required to place the diagnostic call.")
    if not re.fullmatch(r"\+[1-9]\d{7,14}", arguments.phone):
        parser.error("--phone must be a valid E.164 number.")

    print(f"Authorized diagnostic recipient: {mask_phone_number(arguments.phone)}")
    result = run_minimal_live_diagnostic(arguments.phone, live_call=True)
    print("CALL-E DIAGNOSTIC RESULT:")
    print(json.dumps(result["call"].get("structured_result"), indent=2))


if __name__ == "__main__":
    main()
