# app/config.py

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    GITHUB_TOKEN: str

# Instantiate settings
settings = Settings()
