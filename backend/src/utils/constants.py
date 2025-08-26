from dotenv import load_dotenv
import os

ENV_PATH = os.path.join(os.path.expanduser('~'), '.sqlmate', 'secrets.env')

load_dotenv(ENV_PATH if os.path.exists(ENV_PATH) else 'secrets.env')

# Port
PORT = int(os.getenv("PORT", 8080))

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# DB configuration
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_TYPE = os.getenv("DB_TYPE", "mysql")  # Default to mysql if not specified
