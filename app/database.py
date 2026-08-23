import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).parent.parent / "dialmind.db"


def get_connection():
    """Create a connection to the DialMind database."""
    return sqlite3.connect(DATABASE_PATH)


def initialize_database():
    """Create the appointments table and apply safe schema upgrades."""

    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            service TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'confirmed',
            reminder_status TEXT NOT NULL DEFAULT 'pending'
        )
        """
    )

    # Existing DialMind installations may have been initialized before the
    # reminder engine existed.  Add the column in-place so their appointments
    # are preserved rather than requiring the database to be recreated.
    columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(appointments)")
    }
    if "reminder_status" not in columns:
        connection.execute(
            """
            ALTER TABLE appointments
            ADD COLUMN reminder_status TEXT NOT NULL DEFAULT 'pending'
            """
        )

    connection.commit()
    connection.close()


if __name__ == "__main__":
    initialize_database()
    print("DialMind database initialized successfully.")
