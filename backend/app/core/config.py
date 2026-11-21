from pydantic_settings import BaseSettings
from typing import Optional, List
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_PATH = BASE_DIR / "storage"

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Data Intelligence Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security & JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-in-production-ai-data-intelligence-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{(STORAGE_PATH / 'ai_data_intelligence.db').as_posix()}")
    
    # Storage Directories (Always absolute to project root)
    STORAGE_DIR: str = str(STORAGE_PATH)
    UPLOAD_DIR: str = str(STORAGE_PATH / "uploads")
    REPORT_DIR: str = str(STORAGE_PATH / "reports")
    EXPORT_DIR: str = str(STORAGE_PATH / "exports")
    
    # File Ingestion Limits (in Megabytes)
    MAX_UPLOAD_SIZE_MB: int = 250
    
    # LLM / AI Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY", None)
    DEFAULT_AI_PROVIDER: str = os.getenv("DEFAULT_AI_PROVIDER", "gemini")
    
    # Power BI Configuration
    POWERBI_CLIENT_ID: Optional[str] = os.getenv("POWERBI_CLIENT_ID", None)
    POWERBI_CLIENT_SECRET: Optional[str] = os.getenv("POWERBI_CLIENT_SECRET", None)
    POWERBI_TENANT_ID: Optional[str] = os.getenv("POWERBI_TENANT_ID", None)
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    class Config:
        case_sensitive = True

settings = Settings()
