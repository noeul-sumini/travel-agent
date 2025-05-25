from pydantic_settings import BaseSettings
from typing import List
import json
from functools import lru_cache
import os

class Settings(BaseSettings):
    # Environment
    ENV: str = os.getenv("ENV", "dev")
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Travel Agent API"
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL_NAME: str = "gpt-4-turbo-preview"
    
    # Google Calendar
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    
    # Weather API
    WEATHER_API_KEY: str
    
    # Maps API
    MAPS_API_KEY: str
    
    # Flight API
    FLIGHT_API_KEY: str
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int
    RATE_LIMIT_WINDOW: int
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    env = os.getenv("ENV", "dev")
    return Settings(_env_file=f".env.{env}")

settings = get_settings() 