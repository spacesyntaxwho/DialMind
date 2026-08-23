"""Mock-only tests for the Phase 4B live reminder wrapper."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app import database
from app.workflows import test_live_reminder as live_reminder
from app.workflows.appointment_reminder import REMINDER_RESULT_SCHEMA


class LiveReminderWrapperTests(unittest.TestCase):
    def setUp(self):
        self.appointment = {
            "id": 12,
            "customer_name": "Authorized Test Customer",
            "customer_phone": "+919999999999",
            "service": "Dental Consultation",
            "appointment_date": "2026-08-25",
            "appointment_time": "17:30",
            "status": "confirmed",
            "reminder_status": "pending",
        }
        self.payload = {
            "appointment_id": 12,
            "phone": "+919999999999",
            "task": "Prepared reminder task",
            "result_schema": REMINDER_RESULT_SCHEMA,
            "mode": "dry_run",
        }

    def test_live_call_disabled_does_not_create_a_client(self):
        client_class = MagicMock()
        with patch.object(live_reminder, "CalleClient", client_class):
            result = live_reminder.execute_live_reminder(
                self.appointment,
                self.appointment["customer_phone"],
                live_call=False,
            )

        self.assertEqual(result, {"executed": False, "mode": "dry_run"})
        client_class.assert_not_called()

    def test_missing_api_key_is_handled_before_client_creation(self):
        client_class = MagicMock()
        with (
            patch.object(
                live_reminder,
                "get_calle_configuration",
                return_value={"configured": False},
            ),
            patch.object(live_reminder, "CalleClient", client_class),
            self.assertRaisesRegex(RuntimeError, "CALLE_API_KEY is not configured"),
        ):
            live_reminder.execute_live_reminder(
                self.appointment,
                self.appointment["customer_phone"],
                live_call=True,
            )

        client_class.assert_not_called()

    def test_enabled_call_reuses_payload_and_returns_structured_result(self):
        client = MagicMock()
        client.calls.create_and_wait.return_value = {
            "structured_result": {"outcome": "confirmed"}
        }
        client_class = MagicMock(return_value=client)
        recipient = MagicMock()
        recipient.to_dict.return_value = {
            "phones": [self.appointment["customer_phone"]],
            "region": "IN",
            "locale": "en-IN",
        }
        recipient_class = MagicMock(return_value=recipient)

        with (
            patch.object(
                live_reminder,
                "get_calle_configuration",
                return_value={"configured": True},
            ),
            patch.object(live_reminder, "prepare_reminder_call", return_value=self.payload) as prepare,
            patch.object(live_reminder, "CalleClient", client_class),
            patch.object(live_reminder, "CallTaskRecipientRequest", recipient_class),
            patch.object(live_reminder.os, "getenv", return_value="test-secret"),
        ):
            result = live_reminder.execute_live_reminder(
                self.appointment,
                self.appointment["customer_phone"],
                live_call=True,
            )

        prepare.assert_called_once_with(self.appointment)
        recipient_class.assert_called_once_with(
            phones=[self.appointment["customer_phone"]],
            region="IN",
            locale="en-IN",
        )
        recipient.to_dict.assert_called_once_with()
        client_class.assert_called_once_with(api_key="test-secret")
        client.calls.create_and_wait.assert_called_once_with(
            task=self.payload["task"],
            recipients=[
                {
                    "phones": [self.appointment["customer_phone"]],
                    "region": "IN",
                    "locale": "en-IN",
                }
            ],
            result_schema=self.payload["result_schema"],
        )
        client.close.assert_called_once_with()
        self.assertEqual(result["result"], {"outcome": "confirmed"})

    def test_request_body_matches_installed_sdk_serialization_shape(self):
        recipient = MagicMock()
        recipient.to_dict.return_value = {
            "phones": [self.appointment["customer_phone"]],
            "region": "IN",
            "locale": "en-IN",
        }
        recipient_class = MagicMock(return_value=recipient)

        with patch.object(live_reminder, "CallTaskRecipientRequest", recipient_class):
            request_body = live_reminder.build_live_call_request_payload(self.payload)

        self.assertEqual(
            request_body,
            {
                "task": "Prepared reminder task",
                "recipients": [
                    {
                        "phones": [self.appointment["customer_phone"]],
                        "region": "IN",
                        "locale": "en-IN",
                    }
                ],
                "result_schema": REMINDER_RESULT_SCHEMA,
            },
        )
        self.assertEqual(
            request_body["result_schema"]["properties"]["outcome"]["enum"],
            ["confirmed", "cancel_requested", "reschedule_requested", "unknown"],
        )

    def test_invalid_or_mismatched_phone_is_rejected_before_api_use(self):
        with self.assertRaisesRegex(ValueError, "E.164"):
            live_reminder.execute_live_reminder(
                self.appointment, "9999999999", live_call=True
            )
        with self.assertRaisesRegex(ValueError, "must match"):
            live_reminder.execute_live_reminder(
                self.appointment, "+918888888888", live_call=True
            )

    def test_wrapper_does_not_modify_appointment_database_state(self):
        original_database_path = database.DATABASE_PATH
        with tempfile.TemporaryDirectory() as temporary_directory:
            database.DATABASE_PATH = Path(temporary_directory) / "test.db"
            try:
                database.initialize_database()
                connection = database.get_connection()
                connection.execute(
                    """
                    INSERT INTO appointments (
                        customer_name, customer_phone, service, appointment_date,
                        appointment_time, status, reminder_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        self.appointment["customer_name"],
                        self.appointment["customer_phone"],
                        self.appointment["service"],
                        self.appointment["appointment_date"],
                        self.appointment["appointment_time"],
                        self.appointment["status"],
                        self.appointment["reminder_status"],
                    ),
                )
                connection.commit()
                appointment = live_reminder.get_live_reminder_appointment(1)
                before = connection.execute(
                    "SELECT status, reminder_status FROM appointments WHERE id = 1"
                ).fetchone()
                connection.close()

                client = MagicMock()
                client.calls.create_and_wait.return_value = {
                    "structured_result": {"outcome": "unknown"}
                }
                with (
                    patch.object(
                        live_reminder,
                        "get_calle_configuration",
                        return_value={"configured": True},
                    ),
                    patch.object(live_reminder, "CalleClient", return_value=client),
                    patch.object(
                        live_reminder,
                        "CallTaskRecipientRequest",
                        side_effect=lambda **kwargs: type(
                            "Recipient",
                            (),
                            {"to_dict": lambda self: kwargs},
                        )(),
                    ),
                    patch.object(live_reminder.os, "getenv", return_value="test-secret"),
                ):
                    live_reminder.execute_live_reminder(
                        appointment,
                        appointment["customer_phone"],
                        live_call=True,
                    )

                connection = database.get_connection()
                after = connection.execute(
                    "SELECT status, reminder_status FROM appointments WHERE id = 1"
                ).fetchone()
                connection.close()
            finally:
                database.DATABASE_PATH = original_database_path

        self.assertEqual(before, after)
        self.assertEqual(after, ("confirmed", "pending"))


if __name__ == "__main__":
    unittest.main()
