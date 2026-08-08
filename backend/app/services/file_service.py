"""File processing service — CSV/XLSX validation, reading, storage, and chunking."""

from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import pandas as pd

from app.config import settings
from app.core.exceptions import EmptyFileError, FileTooLargeError, UnsupportedFormatError
from app.core.logging_config import get_logger

logger = get_logger(__name__)

SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
OUTPUT_DIR = Path(settings.OUTPUT_DIR)


def _ensure_dirs() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def validate_upload(filename: str, content: bytes) -> None:
    """Validate file extension and size."""
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFormatError(f"Unsupported format: {ext}. Use {SUPPORTED_EXTENSIONS}")

    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE:
        raise FileTooLargeError(f"File {size_mb:.1f}MB exceeds {settings.MAX_FILE_SIZE}MB limit")

    logger.info("Upload validated: %s (%.1f MB)", filename, size_mb)


def save_upload(filename: str, content: bytes) -> Path:
    """Persist the uploaded file to /tmp/pcs/uploads."""
    _ensure_dirs()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    saved_path = UPLOAD_DIR / f"{timestamp}_{filename}"
    saved_path.write_bytes(content)
    logger.info("Saved upload: %s → %s", filename, saved_path.name)
    return saved_path


def read_bytes(filename: str, content: bytes) -> pd.DataFrame:
    """Read CSV or XLSX bytes into a DataFrame."""
    ext = Path(filename).suffix.lower()
    buf = BytesIO(content)

    if ext == ".csv":
        df = pd.read_csv(buf)
    elif ext == ".xlsx":
        df = pd.read_excel(buf)
    else:
        raise UnsupportedFormatError(f"Cannot read {ext}")

    if df.empty:
        raise EmptyFileError("File contains no data rows")

    logger.info("Read %d rows × %d cols from %s", len(df), len(df.columns), filename)
    return df


def chunk_dataframe(df: pd.DataFrame, chunk_size: int | None = None) -> list[pd.DataFrame]:
    """Split DataFrame into chunks for batch LLM processing."""
    size = chunk_size or settings.CHUNK_SIZE
    chunks = [df.iloc[i : i + size] for i in range(0, len(df), size)]
    logger.info("Split %d rows into %d chunks (size=%d)", len(df), len(chunks), size)
    return chunks


def df_to_csv_string(df: pd.DataFrame) -> str:
    """Convert a DataFrame chunk to a CSV string for prompt injection."""
    return df.to_csv(index=True, index_label="row_id")


def save_output(filename: str, df: pd.DataFrame) -> Path:
    """Persist summarization output to /tmp/pcs/downloads."""
    _ensure_dirs()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_DIR / f"summary_{timestamp}_{filename}"
    df.to_csv(output_path, index=False)
    logger.info("Saved output: %s (%d rows)", output_path.name, len(df))
    return output_path


def cleanup_files(*paths: Path) -> None:
    """Delete temporary files after the response has been sent."""
    for path in paths:
        try:
            if path.exists():
                path.unlink()
                logger.info("Cleaned up: %s", path.name)
        except OSError as e:
            logger.warning("Failed to clean up %s: %s", path, e)
