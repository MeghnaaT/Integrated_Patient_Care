# =============================================================================
# INTEGRATED PATIENT CARE MANAGEMENT SYSTEM
# Configuration Module
# =============================================================================
#
# Reads all sensitive values from .env — never hardcoded here.
# Three config classes: base Config, DevelopmentConfig, ProductionConfig.
# =============================================================================

import os


def _load_env():
    """
    Minimal .env loader — no external dependency required.
    Sets os.environ values only if they are not already set
    (so real environment variables always take priority).
    """
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if not os.path.exists(env_path):
        return
    with open(env_path, 'r', encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            os.environ.setdefault(key.strip(), value.strip())


# Load .env before any config class is evaluated
_load_env()


def _build_db_uri() -> str:
    """Assemble MySQL URI from individual env vars."""
    user = os.environ.get('DB_USER', 'root')
    password = os.environ.get('DB_PASSWORD', '')
    host = os.environ.get('DB_HOST', 'localhost')
    port = os.environ.get('DB_PORT', '3306')
    name = os.environ.get('DB_NAME', 'hospital_db')
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"


class Config:
    """Base configuration — shared by all environments."""

    # -------------------------------------------------------------------------
    # Core Flask
    # -------------------------------------------------------------------------
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'change-this-in-production!')
    DEBUG: bool = False
    TESTING: bool = False

    # -------------------------------------------------------------------------
    # SQLAlchemy / MySQL
    # -------------------------------------------------------------------------
    SQLALCHEMY_DATABASE_URI: str = _build_db_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_POOL_RECYCLE: int = 280          # Recycle connections before MySQL timeout (300 s)
    SQLALCHEMY_POOL_PRE_PING: bool = True        # Verify connection liveness before use

    # -------------------------------------------------------------------------
    # Flask-Login
    # -------------------------------------------------------------------------
    LOGIN_VIEW: str = 'auth.login'              # Redirect target when @login_required fires
    LOGIN_MESSAGE: str = 'Please log in to access this page.'
    LOGIN_MESSAGE_CATEGORY: str = 'warning'

    # -------------------------------------------------------------------------
    # Session / Cookie Security
    # -------------------------------------------------------------------------
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = 'Lax'
    PERMANENT_SESSION_LIFETIME: int = 1200      # 20 minutes of inactivity


class DevelopmentConfig(Config):
    """Development — debug on, relaxed cookie rules."""
    DEBUG: bool = True
    SESSION_COOKIE_SECURE: bool = False         # HTTP is fine locally


class ProductionConfig(Config):
    """Production — debug off, HTTPS-only cookies."""
    DEBUG: bool = False
    SESSION_COOKIE_SECURE: bool = True          # Requires HTTPS


# Map string names → config classes (used in create_app)
config: dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
