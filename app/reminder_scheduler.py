"""Phase 3 dry-run scheduler for appointment reminders."""

from datetime import datetime, timedelta

from app.workflows.appointment_reminder import (
    REMINDER_MINUTES,
    get_appointments_due_for_reminder,
)
from app.workflows.reminder_call import prepare_reminder_call


def run_reminder_dry_run(
    current_datetime: datetime | None = None,
) -> list[dict]:
    """Display pending reminders that would be sent, without changing state."""

    now = current_datetime or datetime.now()
    appointments = get_appointments_due_for_reminder(now)

    print("--- REMINDER DRY RUN ---")
    for appointment in appointments:
        reminder_time = (
            datetime.strptime(
                f'{appointment["appointment_date"]} '
                f'{appointment["appointment_time"]}',
                "%Y-%m-%d %H:%M",
            )
            - timedelta(minutes=REMINDER_MINUTES)
        )
        print("\nReminder due:")
        print(f"Customer: {appointment['customer_name']}")
        print(
            "Appointment: "
            f"{appointment['appointment_date']} {appointment['appointment_time']}"
        )
        print(f"Reminder time: {reminder_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"Reminder status: {appointment['reminder_status']}")
        print("Would trigger CALL-E.")

    # The execution layer only prepares a CALL-E-ready payload in Phase 4A.
    # It has no call-creation function, so this path cannot send a reminder.
    return [
        {
            "appointment": appointment,
            "task": payload["task"],
            "call_payload": payload,
        }
        for appointment in appointments
        for payload in [prepare_reminder_call(appointment)]
    ]


if __name__ == "__main__":
    run_reminder_dry_run()
