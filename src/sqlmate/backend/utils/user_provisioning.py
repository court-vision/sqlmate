"""
User provisioning for Clerk-authenticated users.

Auto-creates a local sqlmate.clerk_users row on first login so that
downstream tables (user_tables, etc.) can reference a stable integer PK.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_or_create_sqlmate_user(session: Session, clerk_user_id: str, email: str | None) -> int:
    """
    Look up the local user by clerk_user_id. If missing, insert a new row.

    Args:
        session: An active SQLAlchemy session (sqlmate schema).
        clerk_user_id: The Clerk 'sub' claim (e.g. 'user_xxx').
        email: Email address from Clerk (may be None).

    Returns:
        The integer id from sqlmate.clerk_users.
    """
    result = session.execute(
        text("SELECT id FROM clerk_users WHERE clerk_user_id = :cid"),
        {"cid": clerk_user_id},
    )
    row = result.fetchone()
    if row:
        return row[0]

    # Auto-provision
    display_name = email.split("@")[0] if email else clerk_user_id
    result = session.execute(
        text(
            "INSERT INTO clerk_users (clerk_user_id, email, display_name) "
            "VALUES (:cid, :email, :display_name) "
            "RETURNING id"
        ),
        {"cid": clerk_user_id, "email": email, "display_name": display_name},
    )
    new_row = result.fetchone()
    return new_row[0]
