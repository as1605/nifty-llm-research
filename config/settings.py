"""
Configuration settings for the Nifty Stock Research project.
"""

from pathlib import Path

from pydantic import BaseSettings
from pydantic import Field

# Base project directory
BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    """Main settings class for the application."""

    # OpenAI
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")

    # MongoDB
    mongodb_uri: str = Field(..., env="MONGODB_URI")
    mongodb_db_name: str = Field(..., env="MONGODB_DB_NAME")

    # AWS
    aws_access_key_id: str = Field(..., env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(..., env="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field("ap-south-1", env="AWS_REGION")

    # Email
    sender_email: str = Field(..., env="SENDER_EMAIL")
    recipient_email: str = Field(..., env="RECIPIENT_EMAIL")

    # Application
    log_level: str = Field("INFO", env="LOG_LEVEL")
    cache_dir: Path = Field(BASE_DIR / "cache", env="CACHE_DIR")
    data_dir: Path = Field(BASE_DIR / "data", env="DATA_DIR")

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

# Ensure directories exist
settings.cache_dir.mkdir(parents=True, exist_ok=True)
settings.data_dir.mkdir(parents=True, exist_ok=True)
