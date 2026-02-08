# MySQL: 'sqlmate' is a separate database
CREATE_SQLMATE_DATABASE = """
CREATE DATABASE IF NOT EXISTS sqlmate
"""

# PostgreSQL: 'sqlmate' is a schema within the user's database
CREATE_SQLMATE_SCHEMA = """
CREATE SCHEMA IF NOT EXISTS sqlmate
"""

def get_init_ddl(db_type: str) -> str:
    if db_type == "mysql":
        return CREATE_SQLMATE_DATABASE
    return CREATE_SQLMATE_SCHEMA
