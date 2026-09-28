from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Educator Discovery Platform"
    API_V1_STR: str = "/api"
    
    # API Keys
    ANAKIN_API_KEY: str = ""
    ANAKIN_SEARCH_API_KEY: str = ""
    ANAKIN_SCRAPER_API_KEY: str = ""
    
    # Caching
    SEARCH_CACHE_TTL_SECONDS: int = 86400 # 24 hours default
    
    # SUPABASE_KEY: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
