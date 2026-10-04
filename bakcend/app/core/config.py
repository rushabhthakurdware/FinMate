import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_JWT_SECRET: str
    EMBEDDING_DIMENSION: int = 768

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()