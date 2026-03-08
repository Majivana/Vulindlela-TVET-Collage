"""
Application Configuration Module

This module handles all application settings using Pydantic Settings.
It loads configuration from environment variables and .env files.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os


class Settings(BaseSettings):
    """
    Application settings class.
    
    All configuration values are loaded from environment variables
    with sensible defaults for development.
    """
    
    # Application Info
    APP_NAME: str = Field(default="Student Management System")
    APP_VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=False)
    SECRET_KEY: str = Field(default="change-this-in-production")
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./sms_dev.db")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = Field(default="your-jwt-secret-key")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    
    # File Uploads
    UPLOAD_DIR: str = Field(default="uploads")
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024)  # 10MB
    ALLOWED_EXTENSIONS: str = Field(default="pdf,doc,docx,jpg,jpeg,png")
    
    # Google APIs
    GOOGLE_CLIENT_ID: Optional[str] = Field(default=None)
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(default=None)
    GOOGLE_REDIRECT_URI: str = Field(default="http://localhost:8000/api/auth/google/callback")
    GOOGLE_CALENDAR_ID: Optional[str] = Field(default=None)
    GOOGLE_MAPS_API_KEY: Optional[str] = Field(default=None)
    
    # Campus Geofence
    CAMPUS_LAT: float = Field(default=-33.9249)
    CAMPUS_LNG: float = Field(default=18.4241)
    CAMPUS_RADIUS: float = Field(default=500.0)  # meters
    
    # Map Provider
    MAP_PROVIDER: str = Field(default="leaflet")
    
    # Email
    SMTP_HOST: Optional[str] = Field(default=None)
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: Optional[str] = Field(default=None)
    SMTP_PASSWORD: Optional[str] = Field(default=None)
    
    # CORS
    CORS_ORIGINS: str = Field(default="http://localhost:8000,http://127.0.0.1:8000")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    
    @validator("CORS_ORIGINS")
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in v.split(",")]
    
    @validator("ALLOWED_EXTENSIONS")
    def parse_allowed_extensions(cls, v: str) -> List[str]:
        """Parse comma-separated file extensions into a list."""
        return [ext.strip().lower() for ext in v.split(",")]
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return self.CORS_ORIGINS if isinstance(self.CORS_ORIGINS, list) else []
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Get allowed file extensions as a list."""
        return self.ALLOWED_EXTENSIONS if isinstance(self.ALLOWED_EXTENSIONS, list) else []
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_upload_path(subdirectory: str = "") -> str:
    """
    Get the full path for file uploads.
    
    Args:
        subdirectory: Optional subdirectory within uploads
        
    Returns:
        Full path to the upload directory
    """
    base_path = os.path.abspath(settings.UPLOAD_DIR)
    if subdirectory:
        path = os.path.join(base_path, subdirectory)
    else:
        path = base_path
    
    # Ensure directory exists
    os.makedirs(path, exist_ok=True)
    return path
