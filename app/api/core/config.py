import os
import logging
from environs import Env

# Configure logging first
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
env = Env()
env.read_env(override=True)
os.environ["CLIENT_SECRET"] = env("CLIENT_SECRET")


class Config:
    """Application configuration class."""

    # Strava API Configuration
    CLIENT_ID = os.environ.get("CLIENT_ID")
    CLIENT_SECRET = os.environ.get("CLIENT_SECRET")

    # Flask Configuration
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))
    SESSION_TYPE = "filesystem"

    # Database Configuration
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{os.environ.get("DB_USER")}:{os.environ.get("DB_PASS")}@{os.environ.get("DB_HOST")}/{os.environ.get("DB_NAME")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # App Configuration
    APP_URL = os.getenv("APP_URL", "http://localhost:5000")

    @staticmethod
    def init_app(app):
        """Initialize app with configuration."""
        pass


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
