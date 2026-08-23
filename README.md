# DialMind

DialMind is an AI-powered appointment receptionist designed to handle appointment management for businesses.

The system is designed around two main responsibilities:

1. Handle customer-initiated appointment requests.
2. Contact customers shortly before their appointment for confirmation/reminders.

The core appointment workflow is built locally and is designed to remain independent from the voice/telephony provider.

---

## Current Status

DialMind is currently in active development.

### Completed

- Appointment booking
- Availability checking
- Appointment cancellation
- Appointment rescheduling
- Appointment confirmation workflow
- 15-minute appointment reminder engine
- CALL-E integration layer
- Safe live-call wrapper
- Structured reminder result processing
- Customer booking conversation workflow
- Provider-independent voice adapter architecture
- SQLite-based appointment storage
- Automated test coverage for the implemented workflows

### Current limitation

The CALL-E live calling integration is currently blocked by a provider-side error:

```text
HTTP 503
error_code: provider_unavailable
The call plan could not be prepared.
