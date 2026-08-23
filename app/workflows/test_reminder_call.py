"""Tests for Phase 4A's local-only CALL-E reminder preparation layer."""

import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from app import database
from app.reminder_scheduler import run_reminder_dry_run
from app.workflows import reminder_call
from app.workflows.appointment_reminder import REMINDER_RESULT_SCHEMA


class ReminderCallPreparationTests(unittest.TestCase):
    def setUp(self):
        self.appointment = {
            "id": 42,
            "customer_name": "Test Customer",
            "customer_phone": "+919999999999",
            "service": "Dental Consultation",
            "appointment_date": "2026-08-25",
            "appointment_time": "17:30",
            "status": "confirmed",
            "reminder_status": "pending",
        }

    def test_valid_appointment_produces_dry_run_payload(self):
        payload = reminder_call.prepare_reminder_call(self.appointment)

        self.assertEqual(payload["appointment_id"], 42)
        self.assertEqual(payload["phone"], "+919999999999")
        self.assertEqual(payload["result_schema"], REMINDER_RESULT_SCHEMA)
        self.assertEqual(payload["mode"], "dry_run")
        self.assertIn("Dental Consultation", payload["task"])
        self.assertIn("2026-08-25", payload["task"])
        self.assertIn("17:30", payload["task"])
        self.assertNotIn("call_id", payload)
        self.assertNotIn("completion_status", payload)

    def test_preparation_never_instantiates_or_calls_the_sdk(self):
        sdk_client = Mock()
        with patch.object(reminder_call, "CalleClient", sdk_client):
            reminder_call.prepare_reminder_call(self.appointment)

        sdk_client.assert_not_called()

    def test_missing_api_key_is_reported_without_exposing_a_secret(self):
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.object(reminder_call, "load_dotenv", return_value=False),
        ):
            configuration = reminder_call.get_calle_configuration()

        self.assertFalse(configuration["configured"])
        self.assertEqual(configuration["mode"], "dry_run")
        self.assertNotIn("api_key", configuration)

    def test_present_api_key_is_reported_only_as_configured(self):
        with (
            patch.dict(os.environ, {"CALLE_API_KEY": "test-secret"}, clear=True),
            patch.object(reminder_call, "load_dotenv", return_value=True),
        ):
            configuration = reminder_call.get_calle_configuration()

        self.assertTrue(configuration["configured"])
        self.assertNotIn("test-secret", configuration.values())

    def test_scheduler_dry_run_does_not_change_database_state(self):
        original_database_path = database.DATABASE_PATH
        with tempfile.TemporaryDirectory() as temporary_directory:
            database.DATABASE_PATH = Path(temporary_directory) / "test.db"
            try:
                database.initialize_database()
                appointment_time = datetime(2026, 8, 25, 17, 30)
                connection = database.get_connection()
                cursor = connection.execute(
                    """
                    INSERT INTO appointments (
                        customer_name, customer_phone, service, appointment_date,
                        appointment_time, status, reminder_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "Test Customer",
                        "+919999999999",
                        "Dental Consultation",
                        appointment_time.strftime("%Y-%m-%d"),
                        appointment_time.strftime("%H:%M"),
                        "confirmed",
                        "pending",
                    ),
                )
                appointment_id = cursor.lastrowid
                connection.commit()
                connection.close()

                results = run_reminder_dry_run(
                    appointment_time - timedelta(minutes=15)
                )

                connection = database.get_connection()
                row = connection.execute(
                    "SELECT status, reminder_status FROM appointments WHERE id = ?",
                    (appointment_id,),
                ).fetchone()
                connection.close()
            finally:
                database.DATABASE_PATH = original_database_path

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["call_payload"]["mode"], "dry_run")
        self.assertEqual(row, ("confirmed", "pending"))


if __name__ == "__main__":
    unittest.main()
