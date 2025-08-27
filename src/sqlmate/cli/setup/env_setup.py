import secrets
import getpass
from typing import Dict
from pathlib import Path
# from importlib.resources import files
import os

TEMPLATE_DIR = Path(__file__).parent / "templates"
DOCKER_COMPOSE_FILE = "docker-compose.yaml"
SECRETS_FILE = os.path.join(os.path.expanduser("~"), ".sqlmate", "secrets.env")

def generate_defaults() -> dict:
    """Generate default values for database connection credentials."""

    defaults = {
        "PORT": 5432,
        "DB_HOST": "localhost",
        "DB_USER": "root",
        "DB_PASS": "",
        "DB_NAME": "sqlmate",
        "JWT_SECRET": secrets.token_urlsafe(16),
    }

    # If the secrets.env file already exists, read the existing values to be used as defaults
    if os.path.exists(SECRETS_FILE):
        with open(SECRETS_FILE, "r") as f:
            for line in f:
                key, value = line.strip().split("=", 1)
                if key in defaults:
                    defaults[key] = value.strip("'\"")

    return defaults

def prompt_for_credentials(defaults: dict) -> dict:
    """Prompt the user for database connection credentials."""
    print("📝 Please enter your database connection details:")
    
    # Collect credentials with defaults
    credentials = {}
    credentials["PORT"] = input(f"API Port [{defaults['PORT']}]: ") or defaults["PORT"]
    credentials["DB_HOST"] = input(f"Database Host [{defaults['DB_HOST']}]: ") or defaults["DB_HOST"]
    credentials["DB_USER"] = input(f"Database User [{defaults['DB_USER']}]: ") or defaults["DB_USER"]
    credentials["DB_PASS"] = getpass.getpass("Database Password: ") or defaults["DB_PASS"]
    credentials["DB_NAME"] = input(f"Database Name [{defaults['DB_NAME']}]: ") or defaults["DB_NAME"]
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
            key, value = line.strip().split("=", 1)
            config[key] = value.strip("'\"")

    return config