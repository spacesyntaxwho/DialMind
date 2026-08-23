"""Offline Phase 5A tests for customer-initiated booking conversations."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import database
from app.tools.booking import book_appointment
from app.workflows import customer_booking_conversation as conversation_module


class CustomerBookingConversationTests(unittest.TestCase):
    appointment_date = "2026-09-15"
    appointment_time = "10:00"

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.original_database_path = database.DATABASE_PATH
        database.DATABASE_PATH = Path(self.temporary_directory.name) / "test.db"
        database.initialize_database()
        self.conversation = conversation_module.create_conversation()

    def tearDown(self):
        database.DATABASE_PATH = self.original_database_path
        self.temporary_directory.cleanup()

    def booking_request(self, **overrides) -> dict:
        request = {
            "action": "book",
            "customer_name": "Test Customer",
            "customer_phone": "+15555550100",
            "service": "Dental Consultation",
            "appointment_date": self.appointment_date,
            "appointment_time": self.appointment_time,
        }
        request.update(overrides)
        return request

    def prepare_confirmation(self) -> dict:
        return conversation_module.submit_customer_request(
            self.conversation, self.booking_request()
        )

    def appointment_count(self) -> int:
        connection = database.get_connection()
        count = connection.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
        connection.close()
        return count

    def test_empty_booking_request_asks_for_service(self):
        result = conversation_module.submit_customer_request(
            self.conversation, {"action": "book"}
        )

        self.assertEqual(result["status"], "needs_information")
        self.assertEqual(result["missing_field"], "service")

    def test_service_is_collected_once_and_date_is_next(self):
        result = conversation_module.submit_customer_request(
            self.conversation, {"action": "book", "service": "Dental Consultation"}
        )

        self.assertEqual(result["missing_field"], "appointment_date")
        self.assertEqual(self.conversation["details"]["service"], "Dental Consultation")

    def test_date_is_collected_and_time_is_next(self):
        result = conversation_module.submit_customer_request(
            self.conversation,
            {"action": "book", "service": "Dental Consultation", "appointment_date": self.appointment_date},
        )

        self.assertEqual(result["missing_field"], "appointment_time")

    def test_time_is_collected_and_name_is_next(self):
        result = conversation_module.submit_customer_request(
            self.conversation,
            {
                "action": "book",
                "service": "Dental Consultation",
                "appointment_date": self.appointment_date,
                "appointment_time": self.appointment_time,
            },
        )

        self.assertEqual(result["missing_field"], "customer_name")

    def test_all_required_information_requires_confirmation(self):
        result = self.prepare_confirmation()

        self.assertEqual(result["status"], "confirmation_required")
        self.assertEqual(result["action"], "book")
        self.assertEqual(self.appointment_count(), 0)

    def test_missing_customer_name_is_requested(self):
        request = self.booking_request(customer_name="")
        result = conversation_module.submit_customer_request(self.conversation, request)

        self.assertEqual(result["missing_field"], "customer_name")

    def test_missing_customer_phone_is_requested(self):
        request = self.booking_request(customer_phone="")
        result = conversation_module.submit_customer_request(self.conversation, request)

        self.assertEqual(result["missing_field"], "customer_phone")

    def test_unavailable_slot_returns_existing_available_slots(self):
        book_appointment(
            "Other Customer", "+15555550101", "Dental Consultation", self.appointment_date, self.appointment_time
        )

        result = self.prepare_confirmation()

        self.assertEqual(result["status"], "slot_unavailable")
        self.assertNotIn(self.appointment_time, result["available_slots"])

    def test_available_slot_requires_confirmation(self):
        result = self.prepare_confirmation()

        self.assertEqual(result["status"], "confirmation_required")
        self.assertTrue(self.conversation["confirmation_requested"])

    def test_customer_confirmation_books_appointment(self):
        self.prepare_confirmation()

        result = conversation_module.confirm_booking(self.conversation, confirmed=True)

        self.assertEqual(result["status"], "booked")
        self.assertEqual(self.appointment_count(), 1)

    def test_customer_rejection_does_not_book(self):
        self.prepare_confirmation()

        result = conversation_module.confirm_booking(self.conversation, confirmed=False)

        self.assertEqual(result["status"], "booking_declined")
        self.assertEqual(self.appointment_count(), 0)

    def test_existing_router_is_used_after_confirmation(self):
        self.prepare_confirmation()
        with patch.object(
            conversation_module,
            "handle_call_result",
            return_value={"success": True, "message": "booked"},
        ) as router:
            result = conversation_module.confirm_booking(self.conversation, confirmed=True)

        router.assert_called_once_with({"action": "book", **self.conversation["details"]})
        self.assertEqual(result["status"], "booked")

    def test_duplicate_confirmation_does_not_create_another_appointment(self):
        self.prepare_confirmation()
        conversation_module.confirm_booking(self.conversation, confirmed=True)

        duplicate = conversation_module.confirm_booking(self.conversation, confirmed=True)

        self.assertEqual(duplicate["status"], "already_completed")
        self.assertEqual(self.appointment_count(), 1)

    def test_invalid_action_is_rejected(self):
        result = conversation_module.submit_customer_request(
            self.conversation, {"action": "delete"}
        )

        self.assertEqual(result["status"], "invalid_action")

    def test_unknown_or_ambiguous_request_is_rejected(self):
        unknown = conversation_module.submit_customer_request(
            self.conversation, {"action": "unknown"}
        )
        ambiguous = conversation_module.submit_customer_request(self.conversation, None)

        self.assertEqual(unknown["status"], "unknown_request")
        self.assertEqual(ambiguous["status"], "unknown_request")

    def test_schema_allows_only_supported_actions(self):
        actions = conversation_module.CUSTOMER_REQUEST_SCHEMA["properties"]["action"]["enum"]

        self.assertEqual(actions, ["book", "availability", "reschedule", "cancel", "unknown"])


if __name__ == "__main__":
    unittest.main()
