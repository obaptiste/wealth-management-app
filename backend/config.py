# This file contains the application settings and configuration
# config.py
import os
import secrets
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from functools import lru_cache

# Load environment variables from the .env file
load_dotenv()

class Settings(BaseSettings):
    # Database settings
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    postgres_db: str = os.getenv("POSTGRES_DB", "wealth_management")
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")  # Allow configuring host
    
    # Authentication
    secret_key: str = os.getenv("SECRET_KEY", secrets.token_hex(32))  # Generate secure default
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Twitter API (optional)
    twitter_api_key: str = os.getenv("TWITTER_API_KEY", "")
    twitter_api_secret: str = os.getenv("TWITTER_API_SECRET", "")
    twitter_bearer_token: str = os.getenv("TWITTER_BEARER_TOKEN", "")
    
    # Application settings
    env_name: str = os.getenv("ENV_NAME", "development")
    debug: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
    
    # Database URLs as computed fields
    database_url: str = ""
    database_url_async: str = ""
    database_url_local: str = ""  # Add this field to match the error message
    
    # Update to Pydantic v2 configuration style
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Important: allow extra fields
    )

    @field_validator("database_url", mode="before")
    def set_database_url(cls, v, values):
        """Set the standard database URL for SQLAlchemy"""
        if v:  # If already set (e.g., from environment), use that value
            return v
        user = values.data.get("postgres_user", "postgres")
        password = values.data.get("postgres_password", "postgres")
        host = values.data.get("postgres_host", "localhost")
        db = values.data.get("postgres_db", "wealth_management")
        return f"postgresql://{user}:{password}@{host}/{db}"
        
    @field_validator("database_url_async", mode="before")
    def set_database_url_async(cls, v, values):
        """Set the async database URL for SQLAlchemy with asyncpg driver"""
        if v:  # If already set, use that value
            return v
        user = values.data.get("postgres_user", "postgres")
        password = values.data.get("postgres_password", "postgres")
        host = values.data.get("postgres_host", "localhost")
        db = values.data.get("postgres_db", "wealth_management")
        return f"postgresql+asyncpg://{user}:{password}@{host}/{db}"
    
    @field_validator("database_url_local", mode="before")
    def set_database_url_local(cls, v, values):
        """Set the local database URL (same as standard but explicitly for local development)"""
        if v:  # If already set, use that value
            return v
        user = values.data.get("postgres_user", "postgres")
        password = values.data.get("postgres_password", "postgres")
        host = values.data.get("postgres_host", "localhost")
        db = values.data.get("postgres_db", "wealth_management")
        return f"postgresql://{user}:{password}@{host}/{db}"
    
    def is_production(self) -> bool:
        """Check if the application is running in production mode"""
        return self.env_name.lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings as a singleton to avoid reloading from
    environment variables multiple times.
    """
    return Settings()

# Initialize settings - accessible as settings.property_name
settings = get_settings()