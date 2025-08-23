# Pydantic models (request/response)
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional

class UploadResponse(BaseModel):
    """Response model for successful file upload"""
    message: str = Field(..., description="Success message")
    file_name: str = Field(..., description="Original filename") 
    file_path: str = Field(..., description="Path where file is stored")
    job_id: str = Field(..., description="Unique job identifier for tracking")
    content_type: str = Field(..., description="MIME type of uploaded file")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    upload_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Upload timestamp")