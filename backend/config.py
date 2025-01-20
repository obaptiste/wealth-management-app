from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

class Settings(BaseSettings):
    database_url: str
    database_url_async: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    postgres_user: str
    postgres_password: str
    postgres_db: str

    class Config:
        env_file = ".env"
        extra = "allow"

# Initialize settings
settings = Settings()