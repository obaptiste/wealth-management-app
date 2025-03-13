# This file contains the application settings and configuration
# config.py
import os
import secrets
from pydantic_settings import BaseSettings
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
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def database_url(self) -> str:
        """Standard database URL for SQLAlchemy"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}/{self.postgres_db}"
        
    @property
    def database_url_async(self) -> str:
        """Async database URL for SQLAlchemy with asyncpg driver"""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}/{self.postgres_db}"
    
    @property
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