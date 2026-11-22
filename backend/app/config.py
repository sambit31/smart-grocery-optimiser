"""Application configuration.

All secrets and environment-specific values come from environment variables
(loaded from backend/.env). Nothing secret is hardcoded here.
"""
import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def _bool_env(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _build_mysql_url():
    """Build the SQLAlchemy URL from individual MySQL settings."""
    user = os.getenv("MYSQL_USER", "grocery_user")
    password = os.getenv("MYSQL_PASSWORD", "")
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    database = os.getenv("MYSQL_DATABASE", "smart_grocery")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or _build_mysql_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}

    # --- JWT stored in HttpOnly cookies, protected by double-submit CSRF ---
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-jwt-change-me")
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_EXPIRES_HOURS", "24")))
    JWT_COOKIE_SECURE = _bool_env("JWT_COOKIE_SECURE", False)  # True in production (HTTPS)
    JWT_COOKIE_SAMESITE = os.getenv("JWT_COOKIE_SAMESITE", "Lax")
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_CSRF_IN_COOKIES = True
    JWT_SESSION_COOKIE = False  # cookie persists until the token expires

    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    RATELIMIT_ENABLED = _bool_env("RATELIMIT_ENABLED", True)
    RATELIMIT_STORAGE_URI = "memory://"
    AUTH_RATE_LIMIT = os.getenv("AUTH_RATE_LIMIT", "10 per minute")

    # --- Business settings ---
    PREDICTION_HISTORY_PERIODS = int(os.getenv("PREDICTION_HISTORY_PERIODS", "3"))

    DEBUG = _bool_env("FLASK_DEBUG", False)


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    SQLALCHEMY_ENGINE_OPTIONS = {}
    RATELIMIT_ENABLED = False
    JWT_SECRET_KEY = "test-jwt-secret-key-that-is-long-enough-123"
    SECRET_KEY = "test-secret"
