"""
Database setup utilities for SQLMate CLI.

This module contains functions for initializing database tables
and other database setup tasks required for SQLMate to function properly.
"""
from .sql.database import get_init_ddl
from .sql.tables import get_table_ddl
from sqlmate.backend.classes.database import SQLAlchemyDB
from typing import Dict, List, Any
import os
import json

def initialize_database(credentials: dict) -> bool:
    """
    Main function to validate and initialize the database for SQLMate.
    Supports both MySQL and PostgreSQL through SQLAlchemy.

    Args:
        credentials (dict): Database credentials

    Returns:
        bool: True if successful, False otherwise
    """
    db_type = credentials.get("DB_TYPE", "mysql")
    print("\n🔧 Initializing database...")

    # Create database connection using SQLAlchemy
    db = SQLAlchemyDB(credentials)
    print("✅ Database server connection successful!")
    print(f"✅ Database '{credentials['DB_NAME']}' found.")

    print()
    # Create the 'sqlmate' database (MySQL) or schema (PostgreSQL)
    init_ddl = get_init_ddl(db_type)
    db.execute(init_ddl, err_msg="❌ Error creating 'sqlmate' database/schema. Make sure you have the necessary permissions.")

    # Generate JSON schema file for frontend use
    metadata = db.fetch_metadata()
    if metadata is None:
        print(f"❌ Failed to fetch metadata for database '{credentials['DB_NAME']}'.")
        return False

    # Prompt user to select tables for schema
    filtered_metadata = prompt_user_for_tables(metadata)

    # Generate schema in required format
    schema = generate_db_schema_json(filtered_metadata)

    # Write schema to file
    write_schema_files(schema, db)

    # Create tables
    print("🔧 Creating tables...")
    table_queries = get_table_ddl(db_type)
    db.execute_many(table_queries, err_msg="❌ Error creating tables. Make sure you have the necessary permissions.")

    db.close()

    print("✅ Database initialization completed successfully")
    return True

def prompt_user_for_tables(metadata: Dict[str, List[Dict[str, str]]]) -> Dict[str, List[Dict[str, str]]]:
    """
    Prompt the user for each table, asking if they want to keep it in the schema.

    Args:
        metadata (Dict[str, List[Dict[str, str]]]): Dictionary of tables and their columns

    Returns:
        Dict[str, List[Dict[str, str]]]: Filtered metadata with only the tables the user wants to keep
    """
    filtered_metadata = {}

    print("\n📋 Select tables to include in your schema:")

    # Get list of tables
    tables = list(metadata.keys())

    # Skip if there are no tables
    if not tables:
        print("❌ No tables found in the database.")
        return filtered_metadata

    # Ask for each table
    for table in tables:
        print(f"\nTable: {table} ({len(metadata[table])} columns)")
        print("Columns:")
        for column_info in metadata[table][:5]:  # Show only first 5 columns as preview
            print(f"  - {column_info['column']} ({column_info['data_type']})")

        if len(metadata[table]) > 5:
            print(f"  ... and {len(metadata[table]) - 5} more columns")

        keep_table = input(f"Include '{table}' in schema? (y/n): ").lower().strip()

        if keep_table == 'y' or keep_table == 'yes':
            filtered_metadata[table] = metadata[table]
            print(f"✅ Added '{table}' to schema")
        else:
            print(f"❌ Excluded '{table}' from schema")

    if not filtered_metadata:
        print("\n⚠️ Warning: No tables selected for schema.")
        confirm = input("Continue without any tables? (y/n): ").lower().strip()
        if confirm != 'y' and confirm != 'yes':
            print("Let's try again...")
            return prompt_user_for_tables(metadata)

    return filtered_metadata

def generate_db_schema_json(metadata: Dict[str, List[Dict[str, str]]]) -> List[Dict[str, Any]]:
    """
    Convert metadata to the format required for db_schema.json

    Args:
        metadata (Dict[str, List[Dict[str, str]]]): Dictionary of tables and their columns

    Returns:
        List[Dict[str, Any]]: List of tables with their columns in the required format
    """
    schema = []

    for table_name, columns in metadata.items():
        table_schema = {
            "table": table_name,
            "columns": []
        }

        for column_info in columns:
            column_name = column_info["column"]
            data_type = column_info["data_type"].upper()

            # Normalize data types across MySQL and PostgreSQL
            if data_type in ["INT", "INTEGER", "BIGINT", "SMALLINT", "TINYINT"]:
                type_name = "INT"
            elif data_type in ["VARCHAR", "CHAR", "TEXT", "CHARACTER VARYING"]:
                type_name = "VARCHAR(255)"
            elif data_type in ["DECIMAL", "NUMERIC", "DOUBLE PRECISION", "REAL"]:
                type_name = "DECIMAL(10,2)"
            elif data_type in ["FLOAT", "DOUBLE"]:
                type_name = "FLOAT"
            elif data_type in ["DATETIME", "TIMESTAMP", "TIMESTAMP WITHOUT TIME ZONE", "TIMESTAMP WITH TIME ZONE"]:
                type_name = "TIMESTAMP"
            elif data_type == "DATE":
                type_name = "DATE"
            elif data_type in ["BOOLEAN", "BOOL"]:
                type_name = "BOOLEAN"
            elif data_type == "SERIAL":
                type_name = "INT"
            else:
                type_name = data_type

            table_schema["columns"].append({
                "name": column_name,
                "type": type_name
            })

        schema.append(table_schema)

    return schema

def write_schema_files(schema: List[Dict[str, Any]], db) -> bool:
    try:
        # Use home directory to store the schema
        home_dir = os.path.expanduser("~")
        sqlmate_dir = os.path.join(home_dir, '.sqlmate')
        schema_path = os.path.join(sqlmate_dir, 'db_schema.json')

        # Ensure the directory exists
        os.makedirs(sqlmate_dir, exist_ok=True)

        # Write the schema to file
        with open(schema_path, 'w') as f:
            json.dump(schema, f, indent=2)

        print(f"✅ Schema file generated at {schema_path}")

        # Try to copy to frontend directory if it exists
        if not copy_schema_to_frontend(schema_path):
            raise Exception("Failed to copy schema to frontend")

        return True
    except Exception as e:
        print(f"❌ Error writing schema file: {e}")
        db.close()
        return False

def copy_schema_to_frontend(schema_path: str) -> bool:
    """
    Copy the schema file to the frontend public directory if needed.

    Args:
        schema_path (str): Path to the schema file

    Returns:
        bool: True if successful or not needed, False otherwise
    """
    try:
        # Check if we're running from the SQLMate project directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        frontend_public = os.path.join(project_root, 'frontend', 'public')

        # If frontend directory exists, copy the schema there too
        if os.path.exists(frontend_public):
            frontend_schema_path = os.path.join(frontend_public, 'db_schema.json')

            # Copy the schema file
            with open(schema_path, 'r') as src_file:
                schema_data = json.load(src_file)

            with open(frontend_schema_path, 'w') as dest_file:
                json.dump(schema_data, dest_file, indent=2)

            print(f"✅ Schema file also copied to {frontend_schema_path}")

        return True
    except Exception as e:
        print(f"⚠️ Note: Could not copy schema to frontend directory: {e}")
        return True  # Not a fatal error, just a warning
