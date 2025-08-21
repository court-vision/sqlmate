from collections import defaultdict
from backend.src.classes.database.base import DBInterface

from typing import Any, Generator, List, Optional
from contextlib import contextmanager
from mysql.connector.abstracts import MySQLConnectionAbstract, MySQLCursorAbstract
from mysql.connector.pooling import PooledMySQLConnection
import mysql.connector as mysql

class MySQLDB(DBInterface):
	def __init__(self, credentials: dict):
		super().__init__(credentials)
		self.connection: Optional[MySQLConnectionAbstract | PooledMySQLConnection] = self._connect()

	def _connect(self) -> Optional[MySQLConnectionAbstract | PooledMySQLConnection]:
		try:
			conn: MySQLConnectionAbstract | PooledMySQLConnection = mysql.connect(
				host=self.host,
				user=self.user,
				password=self.password,
				database=self.database
			)
			return conn
		except mysql.Error as err:
			super()._raise_err(f"Error connecting to MySQL database: {err}")
	
	def close(self) -> None:
		if self.connection:
			self.connection.close()
			print("MySQL database connection closed.")
		else:
			print("No active MySQL database connection to close.")

	@contextmanager
	def _get_cursor(self) -> Generator[MySQLCursorAbstract, None, None]:
		if not self.connection:
			super()._raise_err("No active database connection.")
			return
		cursor = self.connection.cursor()
		try:
			yield cursor
			self.connection.commit()
		except Exception as e:
			self.connection.rollback()
			raise e
		finally:
			cursor.close()

	def execute(self, query: str, err_msg: str = "") -> Optional[list]:
		with self._get_cursor() as cursor:
			try:
				cursor.execute(query)
				# Always attempt to fetch results to prevent "Unread result found" errors
				try:
					result = cursor.fetchall()
					return result
				except Exception:
					# If there are no results to fetch (e.g., for INSERT, UPDATE), return empty list
					return []
			except mysql.Error as err:
				super()._raise_err(f"{err_msg}: {err}" if err_msg else f"Error executing query: {query}")
	
	def execute_many(self, queries: List[str], err_msg: str = "") -> bool:
		with self._get_cursor() as cursor:
			try:
				for query in queries:
					cursor.execute(query)
					# Make sure to fetch any results to avoid "Unread result found" errors
					try:
						cursor.fetchall()
					except Exception:
						pass
				return True
			except mysql.Error as err:
				super()._raise_err(f"{err_msg}: {err}" if err_msg else f"Error executing queries: {queries}")
				return False

	def db_exists(self) -> bool:
		query = f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{self.database}'"
		result = self.execute(query)
		if result is not None:
			return len(result) > 0
		return False

	def fetch_metadata(self, db_name: str) -> dict:
		try:
			with self._get_cursor() as cursor:
				cursor.execute(
					"""
					SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
					FROM INFORMATION_SCHEMA.COLUMNS
					WHERE TABLE_SCHEMA = %s AND TABLE_NAME NOT LIKE 'u_%'
					ORDER BY TABLE_NAME, ORDINAL_POSITION;
					""", (db_name,)
				)
				rows: List[Any] = cursor.fetchall()
				metadata = defaultdict(list)
				for table, column, data_type in rows:
					metadata[table].append({
						"column": column,
						"data_type": data_type
					})
				return dict(metadata)
		except mysql.Error as err:
			super()._raise_err(f"Error fetching schema: {err}")
			return dict()
		