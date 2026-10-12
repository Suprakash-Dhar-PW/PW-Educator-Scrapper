import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
env_file = os.path.join(backend_dir, ".env")
if os.path.exists(env_file):
    load_dotenv(env_file, override=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "Educator Discovery Platform"
    API_V1_STR: str = "/api"
    
    # Supabase Configuration
    SUPABASE_URL: str = "https://wzpxmsiiqmzdkxyygvvy.supabase.co"
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    
    # Anakin Discovery & Scraping API Keys
    ANAKIN_API_KEY: str = ""
    ANAKIN_SEARCH_API_KEY: str = ""
    ANAKIN_SCRAPER_API_KEY: str = ""
    
    # Caching & Timeouts
    SEARCH_CACHE_TTL_SECONDS: int = 86400  # 24 hours default
    REQUEST_TIMEOUT_SECONDS: int = 30
    
    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = Settings()
