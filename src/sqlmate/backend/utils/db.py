"""
Database utility functions for connecting to and interacting with the database.
"""

from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import pytz

from sqlmate.backend.classes.database import SQLAlchemyDB
from sqlmate.backend.utils.constants import (
    DB_HOST, DB_USER, DB_PASS, DB_NAME, DB_PORT, DB_TYPE,
    DB_QUERY_USER, DB_QUERY_PASS, DB_APP_USER, DB_APP_PASS,
)


def get_timestamp() -> str:
    """
    Get current timestamp in formatted string (UTC).

    Returns:
        Formatted timestamp string in UTC
    """
    current_time_utc = datetime.now(pytz.utc)
    formatted_time = current_time_utc.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time

def _build_config(which: str = "user") -> dict:
    """
    Build a database config dict for the given target.

    For MySQL:
      - "user" connects to DB_NAME
      - "sqlmate" connects to a separate 'sqlmate' database

    For PostgreSQL:
      - Both connect to DB_NAME (same database)
      - "sqlmate" sets search_path=sqlmate,public so unqualified names resolve to the sqlmate schema
    """
    # The "user" scope executes client-authored SQL, so it gets the read-only
    # role when one is configured; "sqlmate" gets the role that may write to the
    # sqlmate schema. Both fall back to the shared pair. See ops/roles.sql.
    if which == "sqlmate":
        scope_user, scope_pass = DB_APP_USER, DB_APP_PASS
    else:
        scope_user, scope_pass = DB_QUERY_USER, DB_QUERY_PASS

    config = {
        "DB_HOST": DB_HOST,
        "DB_USER": scope_user or DB_USER,
        "DB_PASS": scope_pass or DB_PASS,
        "DB_PORT": DB_PORT,
        "DB_TYPE": DB_TYPE,
    }

    is_postgres = DB_TYPE in ("postgresql", "postgres")

    if which == "sqlmate":
        if is_postgres:
            # Same database, different schema via search_path
            config["DB_NAME"] = DB_NAME
            config["SEARCH_PATH"] = "sqlmate,public"
        else:
            # MySQL: separate database
            config["DB_NAME"] = "sqlmate"
    else:
        config["DB_NAME"] = DB_NAME

    return config

user_engine = SQLAlchemyDB(_build_config("user")).engine
sqlmate_engine = SQLAlchemyDB(_build_config("sqlmate")).engine

UserSessionLocal = sessionmaker(bind=user_engine, autoflush=False, expire_on_commit=False)
SQLMateSessionLocal = sessionmaker(bind=sqlmate_engine, autoflush=False, expire_on_commit=False)

@contextmanager
def session_scope(which: str = "user"):
    session = UserSessionLocal() if which == "user" else SQLMateSessionLocal()
    try:
        yield session
    except Exception as e:
        session.rollback()
        print(f"Error occurred: {e}")
        raise
    else:
        session.commit()
    finally:
        session.close()
