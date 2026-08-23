"""Local-only tests for the Phase 3 appointment reminder engine."""

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from app import database
from app.reminder_scheduler import run_reminder_dry_run
from app.tools.booking import book_appointment
from app.workflows.appointment_reminder import (
    REMINDER_RESULT_SCHEMA,
    build_reminder_task,
    get_appointments_due_for_reminder,
)


class AppointmentReminderTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.original_database_path = database.DATABASE_PATH
        database.DATABASE_PATH = Path(self.temporary_directory.name) / "test.db"
        database.initialize_database()
        self.now = datetime(2026, 8, 25, 17, 15)

    def tearDown(self):
        database.DATABASE_PATH = self.original_database_path
        self.temporary_directory.cleanup()

    def create_appointment(
        self,
        *,
        appointment_datetime: datetime,
        status: str = "confirmed",
        reminder_status: str = "pending",
        customer_name: str = "Test Customer",
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
                customer_name,
                "+919999999999",
                "Dental Consultation",
                appointment_datetime.strftime("%Y-%m-%d"),
                appointment_datetime.strftime("%H:%M"),
                status,
                reminder_status,
            ),
        )
        connection.commit()
        connection.close()
        return cursor.lastrowid

    def test_appointment_exactly_fifteen_minutes_away_is_due(self):
        appointment_id = self.create_appointment(
            appointment_datetime=self.now + timedelta(minutes=15)
        )

        due = get_appointments_due_for_reminder(self.now)

        self.assertEqual([appointment["id"] for appointment in due], [appointment_id])

    def test_appointment_more_than_fifteen_minutes_away_is_not_due(self):
        self.create_appointment(appointment_datetime=self.now + timedelta(minutes=16))

        self.assertEqual(get_appointments_due_for_reminder(self.now), [])

    def test_past_appointment_is_not_due(self):
        self.create_appointment(appointment_datetime=self.now - timedelta(minutes=1))

        self.assertEqual(get_appointments_due_for_reminder(self.now), [])

    def test_non_confirmed_appointment_is_not_due(self):
        self.create_appointment(
            appointment_datetime=self.now + timedelta(minutes=15), status="cancelled"
        )

        self.assertEqual(get_appointments_due_for_reminder(self.now), [])

    def test_processed_reminder_is_not_due(self):
        self.create_appointment(
            appointment_datetime=self.now + timedelta(minutes=15),
            reminder_status="confirmed",
        )

        self.assertEqual(get_appointments_due_for_reminder(self.now), [])

    def test_only_eligible_appointments_are_returned(self):
        eligible_id = self.create_appointment(
            appointment_datetime=self.now + timedelta(minutes=15),
            customer_name="Eligible Customer",
        )
        self.create_appointment(appointment_datetime=self.now + timedelta(minutes=16))
        self.create_appointment(
            appointment_datetime=self.now + timedelta(minutes=10), status="cancelled"
        )

        due = get_appointments_due_for_reminder(self.now)

        self.assertEqual([appointment["id"] for appointment in due], [eligible_id])

    def test_task_contains_appointment_details_and_reminder_instructions(self):
        appointment = {
            "customer_name": "Test Customer",
            "service": "Dental Consultation",
            "appointment_date": "2026-08-25",
            "appointment_time": "17:30",
        }

        task = build_reminder_task(appointment)

        for expected_text in (
            "Dental Consultation",
            "2026-08-25",
            "17:30",
            "AI voice assistant",
            "Do not create a new appointment.",
        ):
            self.assertIn(expected_text, task)

    def test_result_schema_allows_only_expected_outcomes(self):
        outcomes = REMINDER_RESULT_SCHEMA["properties"]["outcome"]["enum"]

        self.assertEqual(
            outcomes,
            ["confirmed", "cancel_requested", "reschedule_requested", "unknown"],
        )

    def test_dry_run_does_not_change_reminder_status(self):
        appointment_id = self.create_appointment(
            appointment_datetime=self.now + timedelta(minutes=15)
        )

        results = run_reminder_dry_run(self.now)

        connection = database.get_connection()
        reminder_status = connection.execute(
            "SELECT reminder_status FROM appointments WHERE id = ?",
            (appointment_id,),
        ).fetchone()[0]
        connection.close()
        self.assertEqual(len(results), 1)
        self.assertEqual(reminder_status, "pending")

    def test_new_booking_defaults_to_pending_reminder(self):
        result = book_appointment(
            customer_name="New Customer",
            customer_phone="+918888888888",
            service="Dental Consultation",
            appointment_date="2026-08-25",
            appointment_time="17:30",
        )

        connection = database.get_connection()
        reminder_status = connection.execute(
            "SELECT reminder_status FROM appointments"
        ).fetchone()[0]
        connection.close()
        self.assertTrue(result["success"])
        self.assertEqual(reminder_status, "pending")


if __name__ == "__main__":
    unittest.main()
