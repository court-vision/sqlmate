"""
Python replacements for the MySQL stored procedures (save_user_table,
process_tables_to_drop) and the before_delete_user_tables trigger.

These functions work identically on MySQL and PostgreSQL via SQLAlchemy.
"""

import re
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


def save_user_table(session, user_id, username: str, table_name: str, created_at: str, query: str) -> None:
    """
    Create a user table from a query and register it in sqlmate.user_tables.
    Replaces the MySQL save_user_table stored procedure.

    Raises:
        IntegrityError: If the table name already exists for this user.
        ValueError: If the table name contains invalid characters.
    """
    # Check for duplicate
    result = session.execute(
        text("SELECT COUNT(*) FROM sqlmate.user_tables WHERE user_id = :user_id AND table_name = :table_name"),
        {"user_id": user_id, "table_name": table_name},
    )
    if result.scalar() > 0:
        raise IntegrityError("Table already exists", params=None, orig=None)

    # Validate table name format
    if not re.match(r"^[a-zA-Z0-9_]+$", table_name) or not re.match(r"^[a-zA-Z0-9_]+$", username):
        raise ValueError("Invalid table name format")

    full_table_name = f"sqlmate.u_{username}_{table_name}"

    # Create the table from the query
    session.execute(text(f"CREATE TABLE {full_table_name} AS {query}"))

    # Insert mapping into user_tables
    session.execute(
        text("INSERT INTO sqlmate.user_tables (user_id, table_name, created_at) VALUES (:user_id, :table_name, :created_at)"),
        {"user_id": user_id, "table_name": table_name, "created_at": created_at},
    )


def drop_user_tables(session, user_id, username: str, table_names: list[str]) -> list[str]:
    """
    Drop one or more user tables and remove their user_tables entries.
    Replaces the trigger + process_tables_to_drop stored procedure.

    Returns:
        List of table names that were successfully dropped.
    """
    dropped = []
    for table_name in table_names:
        if not table_name or not re.match(r"^[a-zA-Z0-9_]+$", table_name):
            continue

        full_table_name = f"sqlmate.u_{username}_{table_name}"

        # Drop the physical table
        session.execute(text(f"DROP TABLE IF EXISTS {full_table_name}"))

        # Remove the mapping
        session.execute(
            text("DELETE FROM sqlmate.user_tables WHERE user_id = :user_id AND table_name = :table_name"),
            {"user_id": user_id, "table_name": table_name},
        )
        dropped.append(table_name)

    return dropped


def drop_all_user_tables(session, user_id, username: str) -> None:
    """
    Drop all tables belonging to a user, then delete the user.
    Used during account deletion. Replaces the CASCADE + trigger + procedure flow.
    """
    # Get all table names for this user
    result = session.execute(
        text("SELECT table_name FROM sqlmate.user_tables WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    table_names = [row[0] for row in result.fetchall()]

    # Drop each physical table
    for table_name in table_names:
        if not re.match(r"^[a-zA-Z0-9_]+$", table_name):
            continue
        full_table_name = f"sqlmate.u_{username}_{table_name}"
        session.execute(text(f"DROP TABLE IF EXISTS {full_table_name}"))

    # Delete the user (CASCADE will clean up user_tables entries)
    session.execute(
        text("DELETE FROM sqlmate.users WHERE id = :user_id"),
        {"user_id": user_id},
    )
