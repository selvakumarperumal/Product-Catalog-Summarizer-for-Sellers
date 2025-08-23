from fastapi.exceptions import HTTPException
from fastapi import status

class FileSizeLimitExceeded(HTTPException):
    def __init__(self, message: str = "File size exceeds 10MB limit"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

class FileTypeInvalid(HTTPException):
    def __init__(self, message: str = "Invalid file type. Only .csv, .xls, and .xlsx files are allowed"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

# LLM Service Exceptions
class LLMServiceError(HTTPException):
    def __init__(self, message: str = "LLM service encountered an error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )

class LLMInitializationError(HTTPException):
    def __init__(self, message: str = "Failed to initialize LLM service"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )

class LLMAPIKeyError(HTTPException):
    def __init__(self, message: str = "Invalid or missing API key for LLM service"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )

class LLMProcessingError(HTTPException):
    def __init__(self, message: str = "Error occurred during LLM processing"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )

class LLMPromptError(HTTPException):
    def __init__(self, message: str = "Error in LLM prompt configuration"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )

# File Processing Exceptions
class FileProcessingError(HTTPException):
    def __init__(self, message: str = "Error occurred while processing the file"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

class EmptyFileError(HTTPException):
    def __init__(self, message: str = "File is empty or contains no valid data"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

class FileNotFoundError(HTTPException):
    def __init__(self, message: str = "Requested file was not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )

# File Service Specific Exceptions
class CSVReadError(HTTPException):
    def __init__(self, message: str = "Error reading CSV file"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

class DataFrameError(HTTPException):
    def __init__(self, message: str = "Error processing DataFrame"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

class ChunkingError(HTTPException):
    def __init__(self, message: str = "Error creating text chunks"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )

class FileValidationError(HTTPException):
    def __init__(self, message: str = "File validation failed"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

class FileAccessError(HTTPException):
    def __init__(self, message: str = "Unable to access file"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message
        )

class FileCorruptedError(HTTPException):
    def __init__(self, message: str = "File appears to be corrupted or invalid"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )