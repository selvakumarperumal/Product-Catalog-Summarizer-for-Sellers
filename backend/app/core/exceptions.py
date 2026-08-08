"""Custom exceptions and FastAPI exception handlers."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# ── Exception hierarchy ──────────────────────────────────────────────────────


class AppError(Exception):
    """Base for all application errors."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class LLMError(AppError):
    """Any error during LLM interaction."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=502)


class LLMApiKeyError(LLMError):
    """API key missing or invalid."""

    def __init__(self, message: str = "API key is not configured") -> None:
        super().__init__(message)


class LLMProcessingError(LLMError):
    """LLM returned an unparseable or failed response."""


class FileError(AppError):
    """File processing errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=400)


class FileTooLargeError(FileError):
    """Uploaded file exceeds size limit."""


class EmptyFileError(FileError):
    """Uploaded file has no data rows."""


class UnsupportedFormatError(FileError):
    """File format not supported."""


# ── FastAPI handler registration ─────────────────────────────────────────────


def register_exception_handlers(app: FastAPI) -> None:
    """Attach exception handlers to the FastAPI app."""

    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": type(exc).__name__, "detail": exc.message},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"error": "InternalServerError", "detail": str(exc)},
        )
