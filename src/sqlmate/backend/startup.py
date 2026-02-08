"""
Non-interactive startup routine.

Called once via the FastAPI lifespan hook. It:
1. Creates the sqlmate schema / database
2. Creates the user_tables table
3. Introspects database metadata
4. Filters by SQLMATE_ALLOWED_SCHEMAS / SQLMATE_BLOCKED_TABLES
5. Generates db_schema.json and writes it to SQLMATE_SCHEMA_DIR
"""

import json
import os

from sqlmate.backend.classes.database import SQLAlchemyDB
from sqlmate.backend.utils.constants import (
    DB_HOST, DB_USER, DB_PASS, DB_NAME, DB_PORT, DB_TYPE, DB_SCHEMA,
    SQLMATE_ALLOWED_SCHEMAS, SQLMATE_BLOCKED_TABLES, SQLMATE_SCHEMA_DIR,
)
from sqlmate.cli.setup.sql.database import get_init_ddl
from sqlmate.cli.setup.sql.tables import get_table_ddl
from sqlmate.cli.setup.db_setup import generate_db_schema_json


def _build_startup_db() -> SQLAlchemyDB:
    """Build a SQLAlchemyDB instance for startup operations."""
    credentials = {
        "DB_HOST": DB_HOST,
        "DB_USER": DB_USER,
        "DB_PASS": DB_PASS,
        "DB_NAME": DB_NAME,
        "DB_PORT": DB_PORT,
        "DB_TYPE": DB_TYPE,
        "DB_SCHEMA": DB_SCHEMA,
    }
    return SQLAlchemyDB(credentials)


def _filter_metadata(metadata: dict) -> dict:
    """
    Filter introspected metadata by allowed schemas and blocked tables.

    If SQLMATE_ALLOWED_SCHEMAS is set, only tables in those schemas are kept.
    Tables in SQLMATE_BLOCKED_TABLES are always excluded.
    Tables starting with 'u_' (user-created) are excluded.
    """
    filtered = {}
    for table_name, columns in metadata.items():
        # Skip user-created tables
        bare_name = table_name.split(".")[-1] if "." in table_name else table_name
        if bare_name.startswith("u_"):
            continue

        # Skip blocked tables
        if bare_name in SQLMATE_BLOCKED_TABLES or table_name in SQLMATE_BLOCKED_TABLES:
            continue

        # If allowed schemas filter is set, enforce it
        if SQLMATE_ALLOWED_SCHEMAS:
            if "." in table_name:
                schema_part = table_name.split(".")[0]
                if schema_part not in SQLMATE_ALLOWED_SCHEMAS:
                    continue
            else:
                # Unqualified name -- only keep if "public" (or equivalent) is allowed
                if "public" not in SQLMATE_ALLOWED_SCHEMAS:
                    continue

        filtered[table_name] = columns

    return filtered


def run_startup() -> None:
    """Execute all startup tasks."""
    print("[startup] Beginning startup sequence...")

    db = _build_startup_db()

    # 1. Create sqlmate schema/database
    init_ddl = get_init_ddl(DB_TYPE)
    db.execute(init_ddl, err_msg="Failed to create sqlmate schema/database")
    print("[startup] sqlmate schema/database ensured.")

    # 2. Create user_tables table
    table_queries = get_table_ddl(DB_TYPE)
    db.execute_many(table_queries, err_msg="Failed to create user_tables table")
    print("[startup] user_tables table ensured.")

    # 4. Introspect metadata
    metadata = db.fetch_metadata()
    if metadata is None:
        print("[startup] WARNING: Could not fetch metadata, skipping schema generation.")
        db.close()
        return

    # 5. Filter
    filtered = _filter_metadata(metadata)
    print(f"[startup] Introspected {len(metadata)} tables, {len(filtered)} after filtering.")

    # 6. Generate and write db_schema.json
    schema = generate_db_schema_json(filtered)

    os.makedirs(SQLMATE_SCHEMA_DIR, exist_ok=True)
    schema_path = os.path.join(SQLMATE_SCHEMA_DIR, "db_schema.json")
    with open(schema_path, "w") as f:
        json.dump(schema, f, indent=2)
    print(f"[startup] Schema written to {schema_path}")

    db.close()
    print("[startup] Startup complete.")
