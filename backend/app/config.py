"""
app/config.py - Konfigurasi Aplikasi UKK Assessment Platform
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Security & Tokens
SECRET_KEY = os.getenv("SECRET_KEY", "ukk-assessment-secret-key-2026-banyumas-cloud-secure")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Super Admin Default
SUPER_ADMIN_USERNAME = os.getenv("SUPER_ADMIN_USERNAME", "admin")
SUPER_ADMIN_PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD", "adminukk2026")
SUPER_ADMIN_NAME = os.getenv("SUPER_ADMIN_NAME", "Administrator Penilaian")

# Google Sheets
GOOGLE_SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID", "1Ri7F8T7YTQdr7F71aslfVpIfYrSva_F0dmtbT5tBJW8")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
GOOGLE_SERVICE_ACCOUNT_BASE64 = os.getenv("GOOGLE_SERVICE_ACCOUNT_BASE64", "")
STORAGE_MODE = os.getenv("STORAGE_MODE", "sheets")  # 'sheets' (with local fallback) or 'local'

# Local Fallback Data Directory
LOCAL_DATA_DIR = Path(os.getenv("LOCAL_DATA_DIR", str(BASE_DIR / "local_storage")))
LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Auto Play Defaults
DEFAULT_AUTO_PLAY_ENABLED = os.getenv("DEFAULT_AUTO_PLAY_ENABLED", "false").lower() == "true"
DEFAULT_AUTO_PLAY_INTERVAL_MINUTES = int(os.getenv("DEFAULT_AUTO_PLAY_INTERVAL_MINUTES", "180"))
MAX_AUTO_PLAY_RETRY = int(os.getenv("MAX_AUTO_PLAY_RETRY", "3"))

# CORS
CORS_ORIGINS = [
    origin.strip() 
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://localhost:8000").split(",")
    if origin.strip()
]

# App Metadata
APP_NAME = os.getenv("APP_NAME", "UKK Assessment Platform")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"


class Settings:
    SECRET_KEY = SECRET_KEY
    ALGORITHM = ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES = ACCESS_TOKEN_EXPIRE_MINUTES
    SUPER_ADMIN_USERNAME = SUPER_ADMIN_USERNAME
    SUPER_ADMIN_PASSWORD = SUPER_ADMIN_PASSWORD
    SUPER_ADMIN_NAME = SUPER_ADMIN_NAME
    GOOGLE_SPREADSHEET_ID = GOOGLE_SPREADSHEET_ID
    GOOGLE_SERVICE_ACCOUNT_JSON = GOOGLE_SERVICE_ACCOUNT_JSON
    GOOGLE_SERVICE_ACCOUNT_BASE64 = GOOGLE_SERVICE_ACCOUNT_BASE64
    STORAGE_MODE = STORAGE_MODE
    LOCAL_DATA_DIR = LOCAL_DATA_DIR
    DEFAULT_AUTO_PLAY_ENABLED = DEFAULT_AUTO_PLAY_ENABLED
    DEFAULT_AUTO_PLAY_INTERVAL_MINUTES = DEFAULT_AUTO_PLAY_INTERVAL_MINUTES
    MAX_AUTO_PLAY_RETRY = MAX_AUTO_PLAY_RETRY
    CORS_ORIGINS = CORS_ORIGINS
    APP_NAME = APP_NAME
    HOST = HOST
    PORT = PORT
    DEBUG = DEBUG


settings = Settings()

