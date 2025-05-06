import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Base directory of the application
BASE_DIR = Path(__file__).resolve().parent.parent

# Application settings
APP_TITLE = "GPP Portal API"
APP_DESCRIPTION = "Government Polytechnic Palanpur Portal API (FastAPI version)"
APP_VERSION = "1.0.0"
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = APP_ENV == "development"

# Server settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "9001"))

# Database settings
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:seagate@localhost:5432/gpp_fastapi"
)

# JWT settings
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# CORS settings
CORS_ORIGINS = [
    "http://localhost:3000",  # React app
    "http://localhost:8000",
]

# File upload settings
UPLOAD_DIR = BASE_DIR / "uploads"
TEMP_DIR = BASE_DIR / "temp"
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)