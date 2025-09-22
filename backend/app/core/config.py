from pydantic_settings import BaseSettings
from typing import Optional, List
from pydantic import field_validator

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./housing_recommender.db"

    # API Keys
    estated_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    rapidapi_key: Optional[str] = None
    rapidapi_host: str = "realty-in-us.p.rapidapi.com"

    # Redis Cache
    redis_url: str = "redis://localhost:6379"

    # App Settings
    app_name: str = "Housing Recommender API"
    debug: bool = False

    # CORS
    allowed_origins: List[str] = ["http://localhost:3000"]

    @field_validator("allowed_origins", mode="before")
    def split_origins(cls, v):
        """Allow comma-separated or JSON-style lists in .env"""
        if isinstance(v, str):
            # Remove brackets if passed like '["url1","url2"]'
            v = v.strip("[]").replace('"', "")
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    class Config:
        env_file = ".env"

    def get_allowed_origins(self) -> List[str]:
        return self.allowed_origins


settings = Settings()
