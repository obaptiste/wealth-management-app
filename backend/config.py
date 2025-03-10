from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

class Settings(BaseSettings):
    database_url_: str = "sqlite://db.sqlite"
    database_url_async_: str = "sqlite+aiosqlite://db.sqlite"
    secret_key: str = "my_secret_key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    postgres_user: str = "postgres"
    postgres_password: str = "postgrespw"
    postgres_db: str = "postgresdb"

    class Config:
        env_file = ".env"
        extra = "allow"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_db}/{self.postgres_db}"
        
    @property
    def database_url_async(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_db}/{self.postgres_db}"

# Initialize settings
settings = Settings()