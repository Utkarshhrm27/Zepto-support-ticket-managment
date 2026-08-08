from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./tickets.db"
    GOOGLE_API_KEY: str = ""
    AUTO_RESOLVE_CONFIDENCE_THRESHOLD: float = 0.55
    AGREEMENT_REQUIRED: bool = True
    CORS_ORIGINS: str = "http://localhost:5173"

    class Config:
        env_file = ".env"

settings = Settings()
