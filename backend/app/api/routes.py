"""FastAPI routes for product catalog summarization."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, File, UploadFile
from fastapi.responses import FileResponse

from app.core.logging_config import get_logger
from app.services.file_service import (
    cleanup_files,
    read_bytes,
    save_output,
    save_upload,
    validate_upload,
)
from app.services.llm_service import LLMService

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["catalog"])

# Lazy-initialised LLM service (created on first use)
_llm_service: LLMService | None = None


def _get_llm() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


@router.post("/summarize")
async def summarize(
    bg: BackgroundTasks,
    file: UploadFile = File(...),
) -> FileResponse:
    """Upload a CSV/XLSX product catalog and get the summarized CSV back directly."""
    content = await file.read()
    filename = file.filename or "upload.csv"

    # Validate
    validate_upload(filename, content)

    # Save upload to /tmp/pcs/uploads
    upload_path = save_upload(filename, content)

    # Read into DataFrame
    df = read_bytes(filename, content)

    # Summarize via LLM
    llm = _get_llm()
    result_df = await llm.summarize_dataframe(df)

    # Save output to /tmp/pcs/downloads
    output_path = save_output(filename, result_df)

    output_name = f"summary_{filename}"
    logger.info("Returning summarized file: %s (%d rows)", output_name, len(result_df))

    # Clean up both files after the response has been sent
    bg.add_task(cleanup_files, upload_path, output_path)

    return FileResponse(
        path=output_path,
        filename=output_name,
        media_type="text/csv",
    )


@router.get("/health")
async def health() -> dict:
    """Health check."""
    return {"status": "ok"}
