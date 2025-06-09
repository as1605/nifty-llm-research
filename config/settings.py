"""
Configuration settings for the Nifty Stock Research project.
"""

from pathlib import Path

# from pydantic import BaseSettings
from pydantic_settings import BaseSettings
from pydantic import Field

# Base project directory
BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    """Main settings class for the application."""

    # Google AI
    google_api_key: str = Field(..., env="GOOGLE_API_KEY")

    # MongoDB
    mongodb_uri: str = Field(..., env="MONGODB_URI")
    mongodb_db_name: str = Field(..., env="MONGODB_DB_NAME")

    # Application
    log_level: str = Field("INFO", env="LOG_LEVEL")
    cache_dir: Path = Field(BASE_DIR / "cache", env="CACHE_DIR")
    data_dir: Path = Field(BASE_DIR / "data", env="DATA_DIR")

    class Config:
        env_file = ".env"
        case_sensitive = False  # Allow case-insensitive environment variables
        env_file_encoding = 'utf-8'


# Global settings instance
settings = Settings()

# Ensure directories exist
settings.cache_dir.mkdir(parents=True, exist_ok=True)
settings.data_dir.mkdir(parents=True, exist_ok=True)
