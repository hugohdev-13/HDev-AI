"""Environment-aware configuration for local SQL Server and Azure SQL."""

import os
from urllib.parse import quote_plus

from dotenv import load_dotenv


load_dotenv()


def _boolean(name: str, default: bool) -> bool:
    """Read an explicit environment boolean with a safe fallback."""
    value = os.getenv(name)
    return default if value is None else value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    """Base runtime configuration shared by development and production."""

    def __init__(self) -> None:
        self.APP_ENV = os.getenv("APP_ENV", "development").lower()
        self.FLASK_ENV = os.getenv("FLASK_ENV", self.APP_ENV)
        self.SECRET_KEY = os.getenv("SECRET_KEY")
        self.N8N_API_KEY = os.getenv("N8N_API_KEY")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
        self.APP_TIMEZONE = os.getenv("APP_TIMEZONE", "America/Mexico_City")
        self.SQLALCHEMY_DATABASE_URI = self._database_uri()
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 1800}
        self.SESSION_COOKIE_HTTPONLY = True
        self.SESSION_COOKIE_SAMESITE = "Lax"
        self.LOGIN_SESSION_PROTECTION = "basic"

    @staticmethod
    def _database_uri() -> str:
        mode = os.getenv("DB_AUTH_MODE", "trusted").strip().lower()
        driver = os.getenv("DB_DRIVER")
        server = os.getenv("DB_SERVER")
        database = os.getenv("DB_DATABASE")
        missing = [name for name, value in {"DB_DRIVER": driver, "DB_SERVER": server, "DB_DATABASE": database}.items() if not value]
        if missing:
            raise RuntimeError(f"Database configuration missing required variables: {', '.join(missing)}")
        parts = [f"DRIVER={{{driver}}}", f"SERVER={server}", f"DATABASE={database}"]
        if mode == "trusted":
            parts.extend(["Trusted_Connection=yes", "TrustServerCertificate=yes"])
        elif mode == "sql":
            username, password = os.getenv("DB_USERNAME"), os.getenv("DB_PASSWORD")
            if not username or not password:
                raise RuntimeError("Database configuration missing required variables: DB_USERNAME, DB_PASSWORD")
            parts.extend([f"UID={username}", f"PWD={password}", f"Encrypt={os.getenv('DB_ENCRYPT', 'yes')}", f"TrustServerCertificate={os.getenv('DB_TRUST_SERVER_CERTIFICATE', 'no')}"])
        else:
            raise RuntimeError("DB_AUTH_MODE must be 'trusted' or 'sql'")
        return "mssql+pyodbc:///?odbc_connect=" + quote_plus(";".join(parts) + ";")


class DevelopmentConfig(Config):
    """Local Windows development defaults."""

    def __init__(self) -> None:
        super().__init__()
        self.DEBUG = _boolean("FLASK_DEBUG", True)
        self.SESSION_COOKIE_SECURE = False
        self.LOGIN_SESSION_PROTECTION = "strong"


class ProductionConfig(Config):
    """Secure Azure App Service defaults."""

    def __init__(self) -> None:
        super().__init__()
        self.DEBUG = False
        self.SESSION_COOKIE_SECURE = True
        # Azure can change the proxy-observed client address between requests.
        # ``basic`` preserves authentication while still marking the session stale.
        self.LOGIN_SESSION_PROTECTION = "basic"


class TestingConfig(Config):
    """Isolated test defaults that avoid SQL Server connectivity."""

    def __init__(self) -> None:
        self.APP_ENV = "testing"
        self.FLASK_ENV = "testing"
        self.TESTING = True
        self.DEBUG = False
        self.SECRET_KEY = "testing-only-secret"
        self.N8N_API_KEY = os.getenv("N8N_API_KEY", "test-n8n-key")
        self.LOG_LEVEL = "WARNING"
        self.APP_TIMEZONE = "America/Mexico_City"
        self.SQLALCHEMY_DATABASE_URI = "sqlite://"
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.SQLALCHEMY_ENGINE_OPTIONS = {}
        self.SESSION_COOKIE_SECURE = False
        self.SESSION_COOKIE_HTTPONLY = True
        self.SESSION_COOKIE_SAMESITE = "Lax"


def get_config() -> Config:
    """Select configuration exclusively through APP_ENV."""
    environment = os.getenv("APP_ENV", "development").lower()
    return {"production": ProductionConfig, "testing": TestingConfig}.get(environment, DevelopmentConfig)()
