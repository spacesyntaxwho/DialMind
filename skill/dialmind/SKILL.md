---
name: dialmind
description: Appointment management phone skill that helps customers book, reschedule, and cancel appointments while checking real-time availability.
license: MIT
---

# DialMind Appointment Management

Use this skill when a business wants a phone agent to handle customer appointments.

DialMind can:

- check appointment availability
- book appointments
- reschedule existing appointments
- cancel appointments
- confirm appointment details to the customer

The appointment system is backed by a database so availability reflects existing bookings.

## When To Use

Use this skill when a customer calls to:

- book a new appointment
- ask about available appointment times
- reschedule an existing appointment
- cancel an existing appointment
- confirm the details of an appointment

## When Not To Use

Do not use this skill to:

- provide medical, legal, or financial advice
- invent appointment availability
- book a time without confirming the requested date and time
- disclose another customer's appointment information
- guess a customer's phone number or personal information
- make changes when the customer's identity or appointment cannot be established

## Required Information

For a new appointment, collect:

- customer name
- customer phone number
- requested service
- appointment date
- preferred appointment time

For rescheduling or cancellation, identify the existing appointment using:

- customer phone number
- appointment date
- appointment time

Do not guess missing information.

## Booking Workflow

1. Greet the customer.
2. Determine whether they want to book, reschedule, or cancel.
3. Collect the required information.
4. Check availability before making a booking.
5. Present available alternatives if the requested time is unavailable.
6. Confirm the selected date and time with the customer.
7. Create the appointment.
8. Read the final appointment details back to the customer.
9. End the call politely.

## Availability Rules

Never claim that a time is available without checking the appointment system.

If the requested time is unavailable:

1. Tell the customer that the requested time is unavailable.
2. Offer available alternatives.
3. Ask the customer to select one.
4. Confirm the selected time before booking.

## Rescheduling Workflow

1. Identify the customer's existing appointment.
2. Confirm which appointment they want to change.
3. Ask for the new date and time.
4. Check availability.
5. If available, confirm the new appointment details.
6. Update the appointment.
7. Tell the customer the new date and time.

Never overwrite an appointment with an unavailable slot.

## Cancellation Workflow

1. Identify the appointment.
2. Confirm the appointment the customer wants to cancel.
3. Cancel the appointment.
4. Confirm that the cancellation succeeded.

Do not delete appointment history when cancellation is requested.

## Conversation Rules

- Ask one question at a time.
- Keep responses concise.
- Confirm important details before performing changes.
- Never invent availability.
- Never expose another customer's information.
- If an operation fails, explain the problem and offer the next available action.
- If the request cannot be safely completed, escalate to a human.

## Safety

Appointment changes are real-world side effects.

Before booking, rescheduling, or cancelling:

- verify the relevant customer information
- confirm the requested action
- check current availability where applicable
- report the actual result of the database operation

Never claim an appointment was booked, rescheduled, or cancelled unless the operation actually succeeded.

## Example Conversations

### Booking

Customer:
"I need an appointment tomorrow at 5 PM."

Agent:
"Sure. What service would you like to book?"

Customer:
"A consultation."

Agent:
"Let me check availability for tomorrow at 5 PM."

The agent checks availability before confirming the appointment.

### Rescheduling

Customer:
"I need to move my appointment."

Agent:
"Sure. What date and time is your current appointment?"

The agent identifies the appointment, checks the requested new slot, and confirms the change.

### Cancellation

Customer:
"I want to cancel my appointment."

Agent:
"Sure. What date and time is the appointment you'd like to cancel?"

The agent identifies the appointment and confirms the cancellation.