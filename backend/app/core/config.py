from typing import Optional, Dict, Any, List
from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "Agent Framework"
    API_V1_STR: str = "/api"
    
    # Authentication
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Database
    DATABASE_URL: str
    
    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    FRONTEND_URL: str 
    WS_URL: str
    API_URL: str
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_CONNECTION_TIMEOUT: int = 3600
    
    # OpenAI
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: Optional[str] = None
    DEFAULT_AGENT_MODEL: str = "gpt-4o"
    
    # Google OAuth and Services
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_SEARCH_ENGINE_ID: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    # Microsoft OAuth
    MICROSOFT_CLIENT_ID: str
    MICROSOFT_CLIENT_SECRET: str
    MICROSOFT_TENANT_ID: Optional[str] = None
    
    # RAG (Retrieval Augmented Generation)
    CHROMA_PERSIST_DIR: str
    BUFFER_SAVE_DIR: str
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 200
    RAG_DEFAULT_RETRIEVAL_K: int = 4
    
    # Email and notifications
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_FROM_EMAIL: str
    SMTP_FROM_NAME: str
    
    # URLs
    BASE_URL: str
    PRIVACY_POLICY_URL: str
    TERMS_OF_SERVICE_URL: str

    # Create necessary directories if they don't exist
    def create_directories(self):
        os.makedirs(self.CHROMA_PERSIST_DIR, exist_ok=True)
        os.makedirs(self.BUFFER_SAVE_DIR, exist_ok=True)
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
settings.create_directories()