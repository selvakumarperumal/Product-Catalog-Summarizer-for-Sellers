from fastapi import (
    APIRouter,
    UploadFile,
    File
)
from fastapi.responses import (
    JSONResponse,
    FileResponse
)
import os
from datetime import datetime, timezone
from app.exceptions.errors import (
    FileSizeLimitExceeded,
    FileTypeInvalid
)
from uuid import uuid4
from app.models.product import (
    UploadResponse
)
from app.config import settings
from typing import Any
from app.services.llm_service import summarize
from app.celery_app.tasks import summarize_csv
from app.celery_app.celery_app import celery_app

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

rag_router = APIRouter()

@rag_router.post("/upload")
async def upload_file(file: UploadFile = File(...)) ->Any:
    """
    Upload a file for processing.
    """

    if file.size and file.size > settings.MAX_FILE_SIZE_MB*1024*1024:  # Limit file size to 10MB
        raise FileSizeLimitExceeded(message=f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit")

    if not file.filename or not file.filename.endswith(('.csv','.xlsx', '.xls')):
        raise FileTypeInvalid(message="Invalid file type. Only .csv, .xlsx, and .xls files are allowed")

    job_id = str(uuid4())
    file_name = f"{job_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    output_file_path = os.path.join(OUTPUT_DIR, f"summary_{file_name}")
    task_summarize = summarize_csv.delay(file_path, output_file_path)

    return {"task_id": task_summarize.id}


@rag_router.get("/status/{task_id}")
async def get_result(task_id: str):
    """
    Get the result of a processing task.
    """
    task = celery_app.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        return {"status": "pending", "message": "Task is still processing"}
    elif task.state == 'SUCCESS':
        return {"status": "success", "result": task.result}
    elif task.state == 'FAILURE':
        return {"status": "failed", "error": str(task.info)}
    else:
        return {"status": task.state}
    
@rag_router.get("/download/{task_id}")
async def download_result(task_id: str):
    """
    Download the result of a processing task.
    """
    task = celery_app.AsyncResult(task_id)

    if task.state == 'SUCCESS':
        result = task.result
        if isinstance(result, dict) and 'output_path' in result:
            output_path = result['output_path']
            return FileResponse(output_path, media_type='application/octet-stream', filename=os.path.basename(output_path))
        else:
            return JSONResponse(status_code=500, content={"error": "Invalid task result format"})
    elif task.state == 'FAILURE':
        return JSONResponse(status_code=400, content={"error": str(task.info)})
    else:
        return JSONResponse(status_code=400, content={"error": "Task is not completed yet"})