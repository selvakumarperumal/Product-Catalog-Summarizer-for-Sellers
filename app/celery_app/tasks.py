import asyncio
import logging
from app.celery_app.celery_app import celery_app
from app.services.llm_service import summarize

# Initialize logger for this module
logger = logging.getLogger(__name__)

@celery_app.task
def test_task(message: str):
    """Simple test task to verify Celery is working"""
    logger.info(f"Test task received message: {message}")
    return {"status": "SUCCESS", "message": f"Test completed: {message}"}

@celery_app.task(bind=True)
def summarize_csv(self, file_path: str, output_path: str):
    """
    Celery task to summarize CSV data using LLM service.
    """
    try:
        logger.info(f"Starting CSV summarization task for file: {file_path}")
        
        # Check if file exists
        import os
        if not os.path.exists(file_path):
            return {
                "status": "FAILURE",
                "message": f"File not found: {file_path}",
                "error": "FileNotFoundError"
            }
        
        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'current_step': 'Reading file', 'file_path': file_path}
        )
        
        # Import here to catch import errors
        try:
            from app.services.llm_service import summarize
        except Exception as import_error:
            logger.error(f"Import error: {str(import_error)}")
            return {
                "status": "FAILURE",
                "message": f"Import error: {str(import_error)}",
                "error": "ImportError"
            }
        
        # Run the async summarize function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Update task state
            self.update_state(
                state='PROCESSING',
                meta={'current_step': 'Processing with LLM', 'file_path': file_path}
            )
            
            # Call the actual summarize function from llm_service
            logger.info("Calling summarize function...")
            summary_df = loop.run_until_complete(summarize(file_path))
            logger.info(f"LLM processing completed, got {len(summary_df)} records")
            
            # Update task state
            self.update_state(
                state='PROCESSING',
                meta={'current_step': 'Saving results', 'output_path': output_path}
            )
            
            # Save the DataFrame to CSV
            summary_df.to_csv(output_path, index=False)
            
            logger.info(f"CSV summarization completed successfully. Output saved to: {output_path}")
            
            return {
                "status": "SUCCESS",
                "message": "Summary generated successfully using LLM", 
                "output_path": output_path,
                "records_processed": len(summary_df) if summary_df is not None else 0
            }
            
        except Exception as llm_error:
            logger.error(f"LLM processing error: {str(llm_error)}")
            return {
                "status": "FAILURE",
                "message": f"LLM processing failed: {str(llm_error)}",
                "error": str(type(llm_error).__name__)
            }
        finally:
            if loop and not loop.is_closed():
                loop.close()
        
    except Exception as e:
        logger.error(f"Error in summarize_csv task: {str(e)}")
        return {
            "status": "FAILURE",
            "message": f"Task failed: {str(e)}",
            "error": str(type(e).__name__)
        }
