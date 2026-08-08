"""Product Catalog Summarizer — FastAPI application entry point."""

from fastapi import FastAPI

from app.api.routes import router
from app.core.exceptions import register_exception_handlers
from app.core.logging_config import get_logger, setup_logging

# ── Logging first ────────────────────────────────────────────────────────────
setup_logging()
logger = get_logger(__name__)

# ── App factory ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Product Catalog Summarizer",
    description="AI-powered product catalog summarization for e-commerce sellers",
    version="1.0.0",
)

# Register exception handlers
register_exception_handlers(app)

# Mount routes
app.include_router(router)

logger.info("App started — Product Catalog Summarizer v1.0.0")
