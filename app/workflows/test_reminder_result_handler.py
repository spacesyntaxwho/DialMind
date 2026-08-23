"""Temporary-database tests for Phase 4C reminder result processing."""

import tempfile
import unittest
from pathlib import Path

from app import database
from app.workflows.reminder_result_handler import handle_reminder_result


class ReminderResultHandlerTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.original_database_path = database.DATABASE_PATH
        database.DATABASE_PATH = Path(self.temporary_directory.name) / "test.db"
        database.initialize_database()

    def tearDown(self):
        database.DATABASE_PATH = self.original_database_path
        self.temporary_directory.cleanup()

    def create_appointment(
        self,
        *,
        status: str = "confirmed",
        reminder_status: str = "pending",
    ) -> int:
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
                "2026-08-25",
                "17:30",
                status,
                reminder_status,
            ),
        )
        connection.commit()
        connection.close()
        return cursor.lastrowid

    def appointment_row(self, appointment_id: int) -> tuple:
        connection = database.get_connection()
        row = connection.execute(
            """
            SELECT customer_name, customer_phone, service, appointment_date,
                   appointment_time, status, reminder_status
            FROM appointments WHERE id = ?
            """,
            (appointment_id,),
        ).fetchone()
        connection.close()
        return row

    def test_confirmed_updates_reminder_status_only(self):
        appointment_id = self.create_appointment()
        before = self.appointment_row(appointment_id)

        result = handle_reminder_result(appointment_id, {"outcome": "confirmed"})

        after = self.appointment_row(appointment_id)
        self.assertTrue(result["success"])
        self.assertEqual(result["reminder_status"], "confirmed")
        self.assertEqual(after[:-1], before[:-1])
        self.assertEqual(after[-1], "confirmed")

    def test_cancel_request_does_not_cancel_appointment(self):
        appointment_id = self.create_appointment()

        result = handle_reminder_result(
            appointment_id, {"outcome": "cancel_requested"}
        )

        row = self.appointment_row(appointment_id)
        self.assertTrue(result["success"])
        self.assertEqual(row[-2], "confirmed")
        self.assertEqual(row[-1], "cancel_requested")

    def test_reschedule_request_does_not_change_appointment_time(self):
        appointment_id = self.create_appointment()
        before = self.appointment_row(appointment_id)

        result = handle_reminder_result(
            appointment_id, {"outcome": "reschedule_requested"}
        )

        after = self.appointment_row(appointment_id)
        self.assertTrue(result["success"])
        self.assertEqual(after[3:6], before[3:6])
        self.assertEqual(after[-1], "reschedule_requested")

    def test_unknown_maps_to_failed_without_changing_appointment(self):
        appointment_id = self.create_appointment()
        before = self.appointment_row(appointment_id)

        result = handle_reminder_result(appointment_id, {"outcome": "unknown"})

        after = self.appointment_row(appointment_id)
        self.assertTrue(result["success"])
        self.assertEqual(result["reminder_status"], "failed")
        self.assertEqual(after[:-1], before[:-1])

    def test_missing_outcome_is_rejected_without_database_change(self):
        appointment_id = self.create_appointment()
        before = self.appointment_row(appointment_id)

        result = handle_reminder_result(appointment_id, {})

        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Invalid reminder outcome.")
        self.assertEqual(self.appointment_row(appointment_id), before)

    def test_invalid_outcome_is_rejected_without_database_change(self):
        appointment_id = self.create_appointment()
        before = self.appointment_row(appointment_id)

        result = handle_reminder_result(appointment_id, {"outcome": ["booked"]})

        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Invalid reminder outcome.")
        self.assertEqual(self.appointment_row(appointment_id), before)

    def test_missing_result_is_rejected_without_database_change(self):
        appointment_id = self.create_appointment()
        before = self.appointment_row(appointment_id)

        result = handle_reminder_result(appointment_id, None)

        self.assertFalse(result["success"])
        self.assertEqual(self.appointment_row(appointment_id), before)

    def test_appointment_not_found_is_rejected(self):
        result = handle_reminder_result(999, {"outcome": "confirmed"})

        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Appointment not found.")

    def test_non_confirmed_appointment_is_rejected(self):
        appointment_id = self.create_appointment(status="cancelled")

        result = handle_reminder_result(appointment_id, {"outcome": "confirmed"})

        self.assertFalse(result["success"])
        self.assertEqual(self.appointment_row(appointment_id)[-1], "pending")

    def test_duplicate_result_is_idempotent_and_conflicts_are_rejected(self):
        appointment_id = self.create_appointment()
        handle_reminder_result(appointment_id, {"outcome": "confirmed"})

        duplicate = handle_reminder_result(appointment_id, {"outcome": "confirmed"})
        conflict = handle_reminder_result(
            appointment_id, {"outcome": "cancel_requested"}
        )

        self.assertTrue(duplicate["success"])
        self.assertTrue(duplicate["idempotent"])
        self.assertFalse(conflict["success"])
        self.assertEqual(self.appointment_row(appointment_id)[-1], "confirmed")


if __name__ == "__main__":
    unittest.main()
