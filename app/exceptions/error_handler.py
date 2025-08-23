from app.exceptions.errors import (
    FileSizeLimitExceeded,
    FileTypeInvalid,
    LLMServiceError,
    LLMInitializationError,
    LLMAPIKeyError,
    LLMProcessingError,
    LLMPromptError,
    FileProcessingError,
    EmptyFileError,
    FileNotFoundError,
    CSVReadError,
    DataFrameError,
    ChunkingError,
    FileValidationError,
    FileAccessError,
    FileCorruptedError
)

from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
import logging

logger = logging.getLogger(__name__)


def register_exception_handlers(app : FastAPI):

    @app.exception_handler(FileSizeLimitExceeded)
    async def file_size_limit_exceeded_handler(request: Request, exc: FileSizeLimitExceeded):
        logger.error(f"File size limit exceeded: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )

    @app.exception_handler(FileTypeInvalid)
    async def file_type_invalid_handler(request: Request, exc: FileTypeInvalid):
        logger.error(f"Invalid file type: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )
    
    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(request: Request, exc: FileNotFoundError):
        logger.error(f"File not found: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )
    
    @app.exception_handler(EmptyFileError)
    async def empty_file_handler(request: Request, exc: EmptyFileError):
        logger.error(f"Empty file error: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )
    
    @app.exception_handler(FileProcessingError)
    async def file_processing_error_handler(request: Request, exc: FileProcessingError):
        logger.error(f"File processing error: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )
    
    @app.exception_handler(LLMInitializationError)
    async def llm_initialization_error_handler(request: Request, exc: LLMInitializationError):
        logger.error(f"LLM initialization error: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "LLM service is currently unavailable. Please try again later."}
        )
    
    @app.exception_handler(LLMAPIKeyError)
    async def llm_api_key_error_handler(request: Request, exc: LLMAPIKeyError):
        logger.error(f"LLM API key error: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "LLM service configuration error. Please contact support."}
        )
    
    @app.exception_handler(LLMProcessingError)
    async def llm_processing_error_handler(request: Request, exc: LLMProcessingError):
        logger.error(f"LLM processing error: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "Error processing your request. Please try again."}
        )
    
    @app.exception_handler(LLMPromptError)
    async def llm_prompt_error_handler(request: Request, exc: LLMPromptError):
        logger.error(f"LLM prompt error: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "Invalid prompt configuration. Please contact support."}
        )
    
    @app.exception_handler(LLMServiceError)
    async def llm_service_error_handler(request: Request, exc: LLMServiceError):
        logger.error(f"LLM service error: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "LLM service error. Please try again later."}
        )
    
    @app.exception_handler(ChatGoogleGenerativeAIError)
    async def chat_google_generative_ai_error_handler(request: Request, exc: ChatGoogleGenerativeAIError):
        logger.error(f"Google Generative AI error: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={"error": "An error occurred while processing the request with the LLM service."}
        )
    
    # File Service Exception Handlers
    @app.exception_handler(CSVReadError)
    async def csv_read_error_handler(request: Request, exc: CSVReadError):
        logger.error(f"CSV read error: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )
    
    @app.exception_handler(DataFrameError)
    async def dataframe_error_handler(request: Request, exc: DataFrameError):
        logger.error(f"DataFrame processing error: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )
    
    @app.exception_handler(ChunkingError)
    async def chunking_error_handler(request: Request, exc: ChunkingError):
        logger.error(f"Text chunking error: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "Error processing file content. Please try again."}
        )
    
    @app.exception_handler(FileValidationError)
    async def file_validation_error_handler(request: Request, exc: FileValidationError):
        logger.error(f"File validation error: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )
    
    @app.exception_handler(FileAccessError)
    async def file_access_error_handler(request: Request, exc: FileAccessError):
        logger.error(f"File access error: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "Unable to access the requested file. Please check permissions."}
        )
    
    @app.exception_handler(FileCorruptedError)
    async def file_corrupted_error_handler(request: Request, exc: FileCorruptedError):
        logger.error(f"File corrupted error: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "The file appears to be corrupted or in an invalid format. Please upload a valid file."}
        )
    


