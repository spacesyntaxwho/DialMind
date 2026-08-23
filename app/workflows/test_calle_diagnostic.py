"""Offline-only tests for CALL-E request and error diagnostics."""

import os
import sys
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

from app.workflows.appointment_reminder import REMINDER_RESULT_SCHEMA
from app.workflows import calle_diagnostic


class FakeCalleAPIError(Exception):
    def __init__(self):
        super().__init__("The recipient +919999999999 could not be prepared.")
        self.status_code = 422
        self.code = "call_plan_unavailable"
        self.details = {
            "recipient": "+919999999999",
            "authorization": "never-disclose",
            "reason": "Unsupported route",
        }


class CalleDiagnosticTests(unittest.TestCase):
    phone = "+919999999999"

    def setUp(self):
        self.reminder_payload = {
            "phone": self.phone,
            "task": "Existing appointment reminder task.",
            "result_schema": REMINDER_RESULT_SCHEMA,
        }

    def test_minimum_documented_task_only_payload(self):
        payload = calle_diagnostic.build_minimum_call_payload(self.phone)

        self.assertEqual(
            payload["task"],
            "Call +919999999999 and say hello. Ask whether they can hear you clearly.",
        )
        self.assertNotIn("recipients", payload)
        self.assertEqual(
            payload["result_schema"], calle_diagnostic.MINIMUM_RESULT_SCHEMA
        )

    def test_reminder_payload_matches_explicit_recipient_contract(self):
        payload = calle_diagnostic.build_reminder_call_payload(self.reminder_payload)

        self.assertEqual(payload["task"], self.reminder_payload["task"])
        self.assertEqual(
            payload["recipients"],
            [{"phones": [self.phone], "region": "IN", "locale": "en-IN"}],
        )
        self.assertEqual(payload["result_schema"], REMINDER_RESULT_SCHEMA)

    def test_payload_display_masks_phone_numbers(self):
        minimum_payload = calle_diagnostic.build_minimum_call_payload(self.phone)
        masked_payload = calle_diagnostic.mask_payload(minimum_payload)

        self.assertNotIn(self.phone, str(masked_payload))
        self.assertIn("+91******9999", masked_payload["task"])
        self.assertEqual(calle_diagnostic.mask_phone_number(self.phone), "+91******9999")

        report = calle_diagnostic.build_offline_diagnostic_report(
            self.phone, self.reminder_payload
        )
        self.assertNotIn(self.phone, str(report))
        self.assertEqual(
            report["reminder_explicit_recipient"]["recipients"][0]["region"], "IN"
        )

    def test_api_key_configuration_uses_booleans_only(self):
        with (
            patch.dict(os.environ, {"CALLE_API_KEY": "test-key"}, clear=True),
            patch.object(calle_diagnostic, "load_dotenv", return_value=False),
        ):
            configuration = calle_diagnostic.inspect_api_key_configuration()

        self.assertEqual(
            configuration,
            {"present": True, "non_empty": True, "not_placeholder": True},
        )
        self.assertNotIn("test-key", configuration.values())

    def test_placeholder_or_missing_api_key_is_not_accepted(self):
        with (
            patch.dict(os.environ, {"CALLE_API_KEY": "YOUR_API_KEY"}, clear=True),
            patch.object(calle_diagnostic, "load_dotenv", return_value=False),
        ):
            placeholder = calle_diagnostic.inspect_api_key_configuration()
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.object(calle_diagnostic, "load_dotenv", return_value=False),
        ):
            missing = calle_diagnostic.inspect_api_key_configuration()

        self.assertFalse(placeholder["not_placeholder"])
        self.assertFalse(missing["present"])

    def test_api_errors_preserve_safe_status_code_and_redacted_details(self):
        diagnostic = calle_diagnostic.extract_safe_calle_error(FakeCalleAPIError())

        self.assertEqual(diagnostic["http_status"], 422)
        self.assertEqual(diagnostic["error_code"], "call_plan_unavailable")
        self.assertEqual(diagnostic["details"]["recipient"], "+91******9999")
        self.assertEqual(diagnostic["details"]["authorization"], "<redacted>")
        self.assertNotIn(self.phone, str(diagnostic))

    def test_live_diagnostic_disabled_never_creates_a_client(self):
        client_class = MagicMock()
        with patch.object(calle_diagnostic, "CalleClient", client_class):
            result = calle_diagnostic.run_minimal_live_diagnostic(self.phone)

        self.assertEqual(result, {"executed": False, "mode": "dry_run"})
        client_class.assert_not_called()

    def test_live_diagnostic_sends_exactly_one_documented_request_when_mocked(self):
        client = MagicMock()
        client.calls.create_and_wait.return_value = {
            "structured_result": {"can_hear_clearly": "yes"}
        }
        client_class = MagicMock(return_value=client)
        with (
            patch.object(
                calle_diagnostic,
                "inspect_api_key_configuration",
                return_value={"present": True, "non_empty": True, "not_placeholder": True},
            ),
            patch.object(calle_diagnostic, "CalleClient", client_class),
            patch.object(calle_diagnostic.os, "getenv", return_value="test-secret"),
        ):
            result = calle_diagnostic.run_minimal_live_diagnostic(
                self.phone, live_call=True
            )

        client_class.assert_called_once_with(api_key="test-secret")
        client.calls.create_and_wait.assert_called_once_with(
            task="Call +919999999999 and say hello. Ask whether they can hear you clearly.",
            result_schema=calle_diagnostic.MINIMUM_RESULT_SCHEMA,
        )
        client.close.assert_called_once_with()
        self.assertEqual(result["call"]["structured_result"]["can_hear_clearly"], "yes")

    def test_live_error_output_is_safely_redacted(self):
        client = MagicMock()
        client.calls.create_and_wait.side_effect = FakeCalleAPIError()
        output = StringIO()
        with (
            patch.object(
                calle_diagnostic,
                "inspect_api_key_configuration",
                return_value={"present": True, "non_empty": True, "not_placeholder": True},
            ),
            patch.object(calle_diagnostic, "CalleClient", return_value=client),
            patch.object(calle_diagnostic.os, "getenv", return_value="test-secret"),
            patch("sys.stdout", output),
            self.assertRaises(FakeCalleAPIError),
        ):
            calle_diagnostic.run_minimal_live_diagnostic(self.phone, live_call=True)

        self.assertIn('"http_status": 422', output.getvalue())
        self.assertNotIn(self.phone, output.getvalue())
        self.assertNotIn("test-secret", output.getvalue())

    def test_command_requires_live_flag_without_creating_a_client(self):
        client_class = MagicMock()
        with (
            patch.object(calle_diagnostic, "CalleClient", client_class),
            patch.object(sys, "argv", ["calle_diagnostic", "--phone", self.phone]),
            self.assertRaises(SystemExit),
        ):
            calle_diagnostic.main()

        client_class.assert_not_called()


if __name__ == "__main__":
    unittest.main()
