from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./housing_recommender.db"

    # API Keys
    estated_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    rapidapi_key: Optional[str] = None
    rapidapi_host: str = "realtor.p.rapidapi.com"


    # Redis Cache
    redis_url: str = "redis://localhost:6379"

    # App Settings
    app_name: str = "Housing Recommender API"
    debug: bool = False

    # CORS Origins (string in .env, parsed into list here)
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    class Config:
        env_file = ".env"

    def get_allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
