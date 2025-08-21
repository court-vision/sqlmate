import argparse
import os
import subprocess

from backend.src.classes.database.mysql import MySQLDB

from .setup.env_setup import generate_defaults, prompt_for_credentials, create_env_file, load_config, DOCKER_COMPOSE_FILE
from .setup.db_setup import initialize_database

def init():
    print("🔧 Initializing SQLMate project...")
    
    # Define the path for the env file in user's home directory
    env_file_path = os.path.join(
        os.path.expanduser('~'),
        '.sqlmate',
        'secrets.env'
    )

    defaults = generate_defaults()
    
    # Prompt for credentials and create env file
    credentials = prompt_for_credentials(defaults)
    create_env_file(credentials, env_file_path)
    
    # Validate and initialize the database with the provided credentials. Generate JSON schema file for frontend use.
    db_setup_successful = initialize_database(credentials)
    
    if db_setup_successful:
        print("✅ Project initialized. Run `sqlmate run` to start.")
    else:
        print("⚠️ Project initialized with warnings. Database setup had issues.")

def cleanup():
    print("🧹 Cleaning up SQLMate project...")
    
    credentials = load_config()
    db = MySQLDB(credentials)
    if not db.connection:
        print("❌ Failed to connect to the database for cleanup.")
        return
    
    # Remove the procedure in the user's source database and then the sqlmate database
    queries = [
        f"DROP PROCEDURE IF EXISTS {credentials['DB_NAME']}.save_user_table",
        "DROP DATABASE IF EXISTS sqlmate"
    ]

    try:
        success = db.execute_many(queries, err_msg="Error during cleanup")
        if success:
            print("✅ Cleanup completed")
        else:
            print("❌ Cleanup failed")
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")


def run():
    print("🚀 Starting SQLMate with Docker...")

    # Check if the Docker daemon is running
    try:
        subprocess.run(["docker", "info"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("❌ Docker daemon is not running. Please start Docker and try again.")
        return
    except FileNotFoundError:
        print("❌ Docker is not installed. Please install Docker and try again.")
        return
    # Check if Docker Compose is installed
    try:
        subprocess.run(["docker", "compose", "version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("❌ Docker Compose is not installed. Please install Docker Compose and try again.")
        return
    except FileNotFoundError:
        print("❌ Docker Compose is not installed. Please install Docker Compose and try again.")
        return
    
    # Check if 'sqlmate init' has been run (i.e., if the env file exists)
    env_file_path = os.path.join(
        os.path.expanduser('~'),
        '.sqlmate',
        'secrets.env'
    )
    if not os.path.exists(env_file_path):
        print("❌ Configuration file not found. Please run `sqlmate init` first.")
        return
    
    subprocess.run(["docker", "compose", "-f", str(DOCKER_COMPOSE_FILE), "up", "--build"], check=True)

def main():
    parser = argparse.ArgumentParser(prog="sqlmate")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init", help="Initialize the project")
    subparsers.add_parser("run", help="Run the Docker app")
    subparsers.add_parser("cleanup", help="Cleanup SQLMate project (removes procedures, triggers and database)")

    args = parser.parse_args()
    if args.command == "init":
        init()
    elif args.command == "run":
        run()
    elif args.command == "cleanup":
        cleanup()
    else:
        parser.print_help()
