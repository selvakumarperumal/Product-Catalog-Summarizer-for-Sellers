# Settings (env vars)
from pydantic import BaseModel
import os

class Settings(BaseModel):
    """Configuration settings for the application"""
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "your-default-api-key")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "outputs")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", 10))  # Maximum file size in MB
    ALLOWED_FILE_TYPES: list[str] = os.getenv("ALLOWED_FILE_TYPES", ".csv,.xlsx,.xls").split(",")  # Allowed file types for upload
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_TO_FILE: bool = os.getenv("LOG_TO_FILE", "true").lower() == "true"
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")

# Example usage:
settings = Settings()