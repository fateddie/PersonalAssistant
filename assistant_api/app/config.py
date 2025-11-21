"""
Configuration
=============
Environment and database configuration
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./assistant_api.db")

    # API
    api_title: str = "Assistant API"
    api_version: str = "0.1.0"

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from shared .env


settings = Settings()
