from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    database_url: str
    database_url_async:str
    secret_key: str
    algorithm: str 
    access_token_expire_minutes: int 

    class Config:
        env_file = ".env"

settings = Settings()