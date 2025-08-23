# FastAPI app entry point
from fastapi import FastAPI
from app.exceptions.error_handler import register_exception_handlers
from app.api.v1 import rag_endpoint
import logging
import sys
from datetime import datetime
import os

# Configure logging
def setup_logging():
    """Configure application logging"""
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # File handler for all logs
    log_filename = f"logs/app_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Error file handler
    error_filename = f"logs/errors_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.FileHandler(error_filename)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # Configure specific loggers
    logging.getLogger("app").setLevel(logging.DEBUG)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("🚀 Logging system initialized")
    logger.info(f"📁 Log files: {log_filename}, {error_filename}")

# Setup logging before creating the app
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Product Catalog Summarizer API",
    description="AI-powered product catalog summarization service",
    version="1.0.0"
)

# Log app initialization
logger.info("🔧 Initializing FastAPI application...")

register_exception_handlers(app)
app.include_router(rag_endpoint.rag_router, prefix="/api/v1/rag", tags=["rag"])

logger.info("✅ FastAPI application initialized successfully")

@app.get("/")
def read_root():
    logger.info("📋 Root endpoint accessed")
    return {"message": "Welcome to the Product Catalog Summarizer API!"}

@app.get("/health")
def health_check():
    logger.info("💓 Health check endpoint accessed")
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

