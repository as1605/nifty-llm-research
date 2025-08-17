"""
Configuration settings for the Nifty Stock Research project.
"""

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings
from pydantic import Field

# Base project directory
BASE_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """Main settings class for the application."""

    # Google AI
    google_api_key: str = Field(..., env="GOOGLE_API_KEY")

    # MongoDB
    mongodb_uri: str = Field(..., env="MONGODB_URI")
    mongodb_db_name: str = Field(..., env="MONGODB_DB_NAME")

    # Zerodha API (optional for existing users)
    zerodha_api_key: str = Field("", env="ZERODHA_API_KEY")
    zerodha_api_secret: str = Field("", env="ZERODHA_API_SECRET")
    
    # Encryption key for storing tokens (optional)
    encryption_key: str = Field("", env="ENCRYPTION_KEY")

    # Application
    log_level: str = Field("INFO", env="LOG_LEVEL")
    cache_dir: Path = Field(BASE_DIR / "cache", env="CACHE_DIR")
    data_dir: Path = Field(BASE_DIR / "data", env="DATA_DIR")

    class Config:
        env_file = ".env"
        case_sensitive = False  # Allow case-insensitive environment variables
        env_file_encoding = 'utf-8'

    def get_google_api_keys(self) -> List[str]:
        """Return list of Google API keys parsed from comma-separated `GOOGLE_API_KEY`.
        Accepts either a single key or multiple keys separated by commas.
        """
        if not self.google_api_key:
            return []
        # Split on comma, strip whitespace, drop empties
        keys = [k.strip() for k in self.google_api_key.split(",")]
        return [k for k in keys if k]


# Global settings instance
settings = Settings()

# Ensure directories exist
settings.cache_dir.mkdir(parents=True, exist_ok=True)
settings.data_dir.mkdir(parents=True, exist_ok=True)
