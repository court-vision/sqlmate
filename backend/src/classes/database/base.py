from backend.src.utils.error import Error
from backend.src.utils.constants import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
from contextlib import contextmanager
from typing import Generator, Any
from datetime import datetime
from mysql.connector import connect
from mysql.connector.abstracts import MySQLCursorAbstract
import pytz
from datetime import timedelta
from abc import ABC, abstractmethod

class DBInterface(ABC):
    def __init__(self, credentials: dict):
        self.host = credentials.get("DB_HOST", "localhost")
        self.user = credentials.get("DB_USER", "root")
        self.password = credentials.get("DB_PASSWORD", "")
        self.database = credentials.get("DB_NAME", "")

    @abstractmethod
    def _connect(self) -> Any:
        pass

    @abstractmethod
    def _get_cursor(self) -> Any:
        pass

    @abstractmethod
    def db_exists(self, db_name: str) -> bool:
        pass

    @abstractmethod
    def fetch_metadata(self, db_name: str) -> dict:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    def _raise_err(self, message: str) -> None:
        raise Error(message)


user_db_config = {
	"host": DB_HOST,
	"user": DB_USER,
	"password": DB_PASSWORD,
	"database": DB_NAME
}

sqlmate_db_config = {
	"host": DB_HOST,
	"user": DB_USER,
	"password": DB_PASSWORD,
	"database": "sqlmate"
}

@contextmanager
def get_cursor(whose: str = "user") -> Generator[MySQLCursorAbstract, None, None]:
    db = (
        connect(**user_db_config) if whose == "user"
        else connect(**sqlmate_db_config)
    )
    cursor = db.cursor()
    try:
        yield cursor
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        cursor.close()
        db.close()


def get_timestamp() -> str:
	current_time_utc = datetime.now(pytz.utc) - timedelta(hours=4)
	formatted_time = current_time_utc.strftime("%Y-%m-%d %H:%M:%S")

	return formatted_time