from sqlmate.backend.utils.error import Error

from typing import Dict, List, Optional, Generator
from contextlib import contextmanager

from sqlalchemy import Connection, text, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool

class SQLAlchemyDB:
    """
    A unified database interface using SQLAlchemy to abstract away database-specific details.
    This replaces the separate MySQL and PostgreSQL implementations.
    """
    
    def __init__(self, credentials: dict):
        """
        Initialize the database connection with the given credentials.
        
        Args:
            credentials: Dictionary containing connection parameters
                - DB_HOST: Database host (default: "localhost")
                - DB_USER: Database user (default: "root")
                - DB_PASS: Database password (default: "")
                - DB_NAME: Database name (default: "")
                - DB_PORT: Database port (optional)
                - DB_TYPE: Database type ("mysql", "postgresql", etc.) (default: "mysql")
        """
        self.host = credentials.get("DB_HOST", "localhost")
        self.user = credentials.get("DB_USER", "root")
        self.password = credentials.get("DB_PASS", "")
        self.database = credentials.get("DB_NAME", "")
        self.port = credentials.get("DB_PORT", "")
        self.db_type = credentials.get("DB_TYPE", "mysql")
        
        # Set up the connection string based on the database type
        if self.db_type == "mysql":
            port_str = f":{self.port}" if self.port else ""
            conn_string = f"mysql+mysqlconnector://{self.user}:{self.password}@{self.host}{port_str}/{self.database}"
        elif self.db_type in ("postgresql", "postgres"):
            port_str = f":{self.port}" if self.port else ""
            conn_string = f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}{port_str}/{self.database}"
        else:
            raise Error(f"Unsupported database type: {self.db_type}")
        
        # Create engine with connection pooling
        self.engine = create_engine(
            conn_string, 
            poolclass=QueuePool,
            pool_pre_ping=True,  # Check connection validity before use
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800  # Recycle connections after 30 minutes
        )
    
    def close(self) -> None:
        """Close the database connection pool."""
        if self.engine:
            self.engine.dispose()
            print(f"{self.db_type.capitalize()} database connection pool disposed.")
        else:
            print("No active database connection pool to dispose.")
    
    @contextmanager
    def _get_connection(self) -> Generator[Connection, None, None]:
        """
        context manager to get a connection from the pool and handle transactions.
        
        Yields:
            SQLAlchemy AsyncConnection object
        
        Raises:
            Error: If there is an issue with the database connection
        """
        if not self.engine:
            raise Error("No active database engine.")
        
        connection = self.engine.connect()
        try:
            # Start a transaction
            transaction = connection.begin()
            yield connection
            # Commit the transaction on success
            transaction.commit()
        except Exception as e:
            # Rollback the transaction on error
            if transaction:
                transaction.rollback()
            raise e
        finally:
            # Return the connection to the pool
            connection.close()
    
    def execute(self, query: str, params: Optional[Dict] = None, err_msg: str = "") -> Optional[List[Dict]]:
        """
        Execute a single SQL query and return results.
        
        Args:
            query: SQL query string to execute
            params: Optional dictionary of parameters for the query
            err_msg: Optional custom error message prefix
            
        Returns:
            List of dictionaries representing rows, or empty list for non-SELECT queries
            
        Raises:
            Error: If there is an issue executing the query
        """
        params = params or {}
        with self._get_connection() as connection:
            try:
                # Convert query to SQLAlchemy text object with parameter binding
                sql = text(query)
                result = connection.execute(sql, params)
                
                # Return results as list of dictionaries if available
                if result.is_insert or result.returns_rows:
                    return [dict(row._mapping) for row in result]
                return []
            except SQLAlchemyError as err:
                self._raise_err(f"{err_msg}: {err}" if err_msg else f"Error executing query: {query}")
    
    def execute_many(self, queries: List[str], err_msg: str = "", warning_message: str = "") -> bool:
        """
        Execute multiple SQL queries in a single transaction.
        
        Args:
            queries: List of SQL query strings to execute
            err_msg: Optional custom error message prefix
            warning_message: Optional warning message to print instead of raising an error
            
        Returns:
            True if all queries executed successfully, False otherwise
            
        Raises:
            Error: If there is an issue executing the queries (unless warning_message is provided)
        """
        with self._get_connection() as connection:
            try:
                for query in queries:
                    result = connection.execute(text(query))
                    # Make sure to exhaust any results
                    if result.returns_rows:
                        result.fetchall()  # This is not an method in SQLAlchemy 2.0
                return True
            except SQLAlchemyError as err:
                if warning_message:
                    print(f"{warning_message}: {err}")
                    return False
                else:
                    self._raise_err(f"{err_msg}: {err}" if err_msg else f"Error executing queries: {queries}")
                return False
    
    def db_exists(self) -> bool:
        """
        Check if the configured database exists.
        
        Returns:
            True if the database exists, False otherwise
        """
        # For SQLAlchemy, we need to use appropriate drivers
        # We will need to use the sync API here as we're creating a temp engine
        # for database existence check
        if self.db_type == "mysql":
            # Using aiomysql driver for MySQL operations
            temp_conn_string = f"mysql+aiomysql://{self.user}:{self.password}@{self.host}"
            query = f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{self.database}'"
        elif self.db_type in ("postgresql", "postgres"):
            # Using asyncpg driver for PostgreSQL operations
            temp_conn_string = f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}/postgres"
            query = f"SELECT 1 FROM pg_database WHERE datname = '{self.database}'"
        else:
            self._raise_err(f"Unsupported database type: {self.db_type}")
            return False
        
        try:
            # Create a temporary engine
            temp_engine = create_engine(temp_conn_string)
            
            # Use with for connection
            with temp_engine.connect() as conn:
                result = conn.execute(text(query))
                rows = result.fetchall()
                return len(rows) > 0
        except SQLAlchemyError as err:
            self._raise_err(f"Error checking if database exists: {err}")
            return False
        finally:
            if 'temp_engine' in locals():
                temp_engine.dispose()
    
    def fetch_metadata(self) -> Dict:
        """
        Fetch database schema metadata.
        
        Args:
            db_name: Name of the database to fetch metadata for
            
        Returns:
            Dictionary with table names as keys and column information as values
            
        Raises:
            Error: If there is an issue fetching the metadata
        """
        try:
            result_dict = {}
            
            # For SQLAlchemy, we need to explicitly reflect tables
            with self.engine.connect() as conn:
                # Get all table names first
                if self.db_type == "mysql":
                    query = text("SHOW TABLES")
                elif self.db_type in ("postgresql", "postgres"):
                    query = text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'")
                else:
                    self._raise_err(f"Unsupported database type: {self.db_type}")
                    return {}
                
                result = conn.execute(query)
                tables = result.fetchall()
                
                # Filter out tables that start with 'u_'
                table_names = [t[0] for t in tables if not str(t[0]).startswith('u_')]
                
                # Get column information for each table
                for table_name in table_names:
                    if self.db_type == "mysql":
                        col_query = text(f"SHOW COLUMNS FROM {table_name}")
                    elif self.db_type in ("postgresql", "postgres"):
                        col_query = text(f"""
                            SELECT column_name, data_type 
                            FROM information_schema.columns 
                            WHERE table_name = '{table_name}' 
                            AND table_schema = 'public'
                        """)
                    
                    col_result = conn.execute(col_query)
                    columns = col_result.fetchall()
                    
                    result_dict[table_name] = [
                        {
                            "column": col[0],
                            "data_type": str(col[1])
                        }
                        for col in columns
                    ]
            
            return result_dict
        except SQLAlchemyError as err:
            self._raise_err(f"Error fetching schema: {err}")
            return {}
    
    def _raise_err(self, message: str) -> None:
        """
        Raise an error with the given message.
        
        Args:
            message: Error message
            
        Raises:
            Error: With the provided message
        """
        raise Error(message)