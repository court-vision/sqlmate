import secrets
import getpass
from typing import Dict
from pathlib import Path
import os

TEMPLATE_DIR = Path(__file__).parent / "templates"
DOCKER_COMPOSE_FILE = "docker-compose.yaml"
SECRETS_FILE = os.path.join(os.path.expanduser("~"), ".sqlmate", "secrets.env")

DB_TYPE_DEFAULTS = {
    "mysql": {"DB_PORT": "3306", "DB_USER": "root"},
    "postgres": {"DB_PORT": "5432", "DB_USER": "postgres"},
}

def generate_defaults() -> dict:
    """Generate default values for database connection credentials."""

    defaults = {
        "DB_TYPE": "postgres",
        "PORT": 8080,
        "DB_HOST": "localhost",
        "DB_USER": "postgres",
        "DB_PASS": "",
        "DB_NAME": "sqlmate",
        "DB_PORT": "5432",
        "DB_SCHEMA": "public",
        "JWT_SECRET": secrets.token_urlsafe(16),
    }

    # If the secrets.env file already exists, read the existing values to be used as defaults
    if os.path.exists(SECRETS_FILE):
        with open(SECRETS_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                if key in defaults:
                    defaults[key] = value.strip("'\"")

    return defaults

def prompt_for_credentials(defaults: dict) -> dict:
    """Prompt the user for database connection credentials."""
    print("📝 Please enter your database connection details:")

    credentials = {}

    # Database type selection
    db_type_input = input(f"Database Type (mysql/postgres) [{defaults['DB_TYPE']}]: ").strip().lower() or defaults["DB_TYPE"]
    if db_type_input not in ("mysql", "postgres"):
        print(f"⚠️ Invalid database type '{db_type_input}'. Defaulting to 'postgres'.")
        db_type_input = "postgres"
    credentials["DB_TYPE"] = db_type_input

    # Adjust defaults based on selected DB type
    type_defaults = DB_TYPE_DEFAULTS[db_type_input]
    if defaults.get("DB_PORT") not in ("3306", "5432"):
        # User has a custom port, keep it
        port_default = defaults["DB_PORT"]
    else:
        port_default = type_defaults["DB_PORT"]

    if defaults.get("DB_USER") not in ("root", "postgres"):
        # User has a custom user, keep it
        user_default = defaults["DB_USER"]
    else:
        user_default = type_defaults["DB_USER"]

    credentials["PORT"] = input(f"API Port [{defaults['PORT']}]: ") or defaults["PORT"]
    credentials["DB_HOST"] = input(f"Database Host [{defaults['DB_HOST']}]: ") or defaults["DB_HOST"]
    credentials["DB_USER"] = input(f"Database User [{user_default}]: ") or user_default
    credentials["DB_PASS"] = getpass.getpass("Database Password: ") or defaults["DB_PASS"]
    credentials["DB_NAME"] = input(f"Database Name [{defaults['DB_NAME']}]: ") or defaults["DB_NAME"]
    credentials["DB_PORT"] = input(f"Database Port [{port_default}]: ") or port_default

    # Schema selection for PostgreSQL
    if db_type_input in ("postgres", "postgresql"):
        schema_default = defaults.get("DB_SCHEMA", "public")
        credentials["DB_SCHEMA"] = input(f"Database Schema [{schema_default}] (use * for all schemas): ") or schema_default

    credentials["JWT_SECRET"] = defaults["JWT_SECRET"]

    return credentials

def create_env_file(credentials, target_path):
    """Create a secrets.env file with the provided credentials."""
    env_content = "\n".join([f"{key}='{value}'" for key, value in credentials.items()])

    # Ensure the directory exists
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    # Write the env file
    with open(target_path, "w") as f:
        f.write(env_content)

    print(f"✅ Created configuration file at {target_path}")

def load_config() -> Dict[str, str]:
    """Load the configuration from the secrets.env file."""
    if not os.path.exists(SECRETS_FILE):
        print("⚠️ Configuration file not found. Please run `sqlmate init` first.")
        return {}

    config = {}
    with open(SECRETS_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue
            key, value = line.split("=", 1)
            config[key] = value.strip("'\"")

    return config
