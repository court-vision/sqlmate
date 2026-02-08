# ---- MySQL variant ----

MYSQL_CREATE_USER_TABLES_TABLE = """
CREATE TABLE IF NOT EXISTS sqlmate.user_tables (
	clerk_user_id VARCHAR(100) NOT NULL,
	table_name VARCHAR(100) NOT NULL,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (clerk_user_id, table_name)
);
"""

# ---- PostgreSQL variant ----

PG_CREATE_USER_TABLES_TABLE = """
CREATE TABLE IF NOT EXISTS sqlmate.user_tables (
	clerk_user_id VARCHAR(100) NOT NULL,
	table_name VARCHAR(100) NOT NULL,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (clerk_user_id, table_name)
);
"""

def get_table_ddl(db_type: str) -> list[str]:
    if db_type == "mysql":
        return [MYSQL_CREATE_USER_TABLES_TABLE]
    return [PG_CREATE_USER_TABLES_TABLE]
