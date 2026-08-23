from fastmcp import FastMCP

from app.tools.availability import check_availability
from app.tools.booking import book_appointment
from app.tools.reschedule import reschedule_appointment
from app.tools.cancellation import cancel_appointment


mcp = FastMCP("DialMind")


@mcp.tool()
def get_available_slots(date: str) -> list[str]:
    """Get available appointment slots for a date."""
    return check_availability(date)


@mcp.tool()
def book(
    customer_name: str,
    customer_phone: str,
    service: str,
    appointment_date: str,
    appointment_time: str,
) -> dict:
    """Book an appointment after availability has been confirmed."""
    return book_appointment(
        customer_name=customer_name,
        customer_phone=customer_phone,
        service=service,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
    )


@mcp.tool()
def reschedule(
    customer_phone: str,
    appointment_date: str,
    appointment_time: str,
    new_date: str,
    new_time: str,
) -> dict:
    """Reschedule an existing appointment."""
    return reschedule_appointment(
        customer_phone=customer_phone,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        new_date=new_date,
        new_time=new_time,
    )


@mcp.tool()
def cancel(
    customer_phone: str,
    appointment_date: str,
    appointment_time: str,
) -> dict:
    """Cancel an existing appointment."""
    return cancel_appointment(
        customer_phone=customer_phone,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
    )


if __name__ == "__main__":
    mcp.run()
    