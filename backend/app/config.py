"""Application settings loaded from environment variables (supports both TF_ prefix and no prefix)."""

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All config comes from env vars, supporting both TF_ prefix and no prefix."""

    # LLM
    GOOGLE_API_KEY: str = Field(
        "your-api-key",
        validation_alias=AliasChoices("TF_GOOGLE_API_KEY", "GOOGLE_API_KEY"),
    )
    MODEL_NAME: str = Field(
        "gemini-1.5-flash",
        validation_alias=AliasChoices("MODEL_NAME", "TF_MODEL_NAME"),
    )
    MODEL_TEMPERATURE: float = Field(
        0.3,
        validation_alias=AliasChoices("TF_MODEL_TEMPERATURE", "MODEL_TEMPERATURE"),
    )

    # File handling
    MAX_FILE_SIZE: int = Field(
        10,
        validation_alias=AliasChoices("TF_MAX_FILE_SIZE", "MAX_FILE_SIZE"),
    )  # MB
    UPLOAD_DIR: str = Field(
        "/tmp/pcs/uploads",
        validation_alias=AliasChoices("TF_UPLOAD_DIR", "UPLOAD_DIR"),
    )
    OUTPUT_DIR: str = Field(
        "/tmp/pcs/downloads",
        validation_alias=AliasChoices("TF_OUTPUT_DIR", "OUTPUT_DIR"),
    )

    # Processing
    CHUNK_SIZE: int = Field(
        25,
        validation_alias=AliasChoices("TF_CHUNK_SIZE", "CHUNK_SIZE"),
    )  # rows per LLM call


settings = Settings()

