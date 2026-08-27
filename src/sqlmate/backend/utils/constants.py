from dotenv import load_dotenv
import os

ENV_PATH = os.path.join(os.path.expanduser('~'), '.sqlmate', 'secrets.env')

# Load environment variables from multiple sources
# Railway and other cloud providers set environment variables directly
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
elif os.path.exists('secrets.env'):
    load_dotenv('secrets.env')
# Otherwise, rely on environment variables already set by the deployment platform

# Port
PORT = int(os.getenv("PORT", 8080))

# JWT configuration (optional, kept for backward compat during migration)
SECRET_KEY = os.getenv("JWT_SECRET", None)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# DB configuration
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")
DB_TYPE = os.getenv("DB_TYPE", "mysql")  # Default to mysql if not specified
DB_SCHEMA = os.getenv("DB_SCHEMA", "public")  # PostgreSQL schema to search for tables

# Clerk authentication
CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL")
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")


# Schema introspection filters
# Comma-separated list of schemas to include (e.g. "public,analytics")

# Per-scope database credentials.
#
# The "user" scope is the connection that executes client-authored SQL
# (routers/query.py). It should be a READ ONLY role with no access to usr.*.
# The "sqlmate" scope owns saved user tables and needs write access to the
# sqlmate schema. See ops/roles.sql.
#
# Both fall back to DB_USER/DB_PASS so an existing single-role deployment keeps
# working, but a deployment that has run ops/roles.sql should set all four.
DB_QUERY_USER = os.getenv("DB_QUERY_USER", "")
DB_QUERY_PASS = os.getenv("DB_QUERY_PASS", "")
DB_APP_USER = os.getenv("DB_APP_USER", "")
DB_APP_PASS = os.getenv("DB_APP_PASS", "")

SQLMATE_ALLOWED_SCHEMAS = [s.strip() for s in os.getenv("SQLMATE_ALLOWED_SCHEMAS", "").split(",") if s.strip()]
# Comma-separated list of tables to exclude (e.g. "migrations,internal_logs")
SQLMATE_BLOCKED_TABLES = [s.strip() for s in os.getenv("SQLMATE_BLOCKED_TABLES", "").split(",") if s.strip()]

# Directory to write db_schema.json during startup
SQLMATE_SCHEMA_DIR = os.getenv("SQLMATE_SCHEMA_DIR", "/app/schema")
