"""
Database utility functions for connecting to and interacting with the database.
"""

from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import pytz

from backend.src.classes.database import SQLAlchemyDB
from backend.src.utils.constants import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_TYPE


def get_timestamp() -> str:
    """
    Get current timestamp in formatted string.
    
    Returns:
        Formatted timestamp string
    """
    current_time_utc = datetime.now(pytz.utc)
    # Adjust for timezone if needed (assuming UTC-4)
    current_time_adjusted = current_time_utc - timedelta(hours=4)
    formatted_time = current_time_adjusted.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time

user_db_config = {
    "DB_HOST": DB_HOST,
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "DB_NAME": DB_NAME,
    "DB_TYPE": "mysql" 
}

sqlmate_db_config = {
    "DB_HOST": DB_HOST,
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "DB_TYPE": DB_TYPE,
    "DB_NAME": "sqlmate"
}

def _get_connection(which: str = "user") -> SQLAlchemyDB:
    """
    Context manager to get a database connection.
    
    Args:
        which: Which database to connect to ("user" or "sqlmate")

    Returns:
        An instance of SQLAlchemyDB configured for the specified database.
    """
    config = user_db_config if which == "user" else sqlmate_db_config
    return SQLAlchemyDB(config)

user_engine = _get_connection("user").engine
sqlmate_engine = _get_connection("sqlmate").engine

UserSessionLocal = sessionmaker(bind=user_engine, autoflush=False, expire_on_commit=False)
SQLMateSessionLocal = sessionmaker(bind=sqlmate_engine, autoflush=False, expire_on_commit=False)

@contextmanager
def user_session_scope():
    session = UserSessionLocal()
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

@contextmanager
def sqlmate_session_scope():
    session = SQLMateSessionLocal()
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
