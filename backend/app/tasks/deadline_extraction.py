# FILE: backend/app/tasks/deadline_extraction.py
# PHOENIX PROTOCOL - FISCAL DEADLINE TASK V3.0 (ACCOUNTING ALIGNMENT)
# 1. REFACTOR: Documentation and logs updated to reflect Fiscal Compliance context.
# 2. ENHANCED: Added 'category' support to improve extraction precision.
# 3. STATUS: 100% Accounting Aligned. Import resolution verified.

from celery import shared_task
import structlog
from pymongo.database import Database

# PHOENIX: Absolute imports for architectural integrity
from app.core.db import db_instance as global_db, connect_to_mongo
from app.services import deadline_service

logger = structlog.get_logger(__name__)

def get_db_safe() -> Database:
    """Ensures a valid MongoDB connection is available for the Celery worker."""
    if global_db is not None:
        return global_db
    _, db = connect_to_mongo()
    return db

@shared_task(name="extract_deadlines_from_document")
def extract_deadlines_from_document(document_id: str, text_content: str, category: str = "Unknown"):
    """
    Background task responsible for identifying VAT, Tax, and Payment deadlines 
    within business documentation.
    """
    logger.info("task.fiscal_deadline_extraction.started", 
                document_id=document_id, 
                category=category)
    
    try:
        # Resolve DB connection
        db = get_db_safe()
        
        # Invoke the Fiscal Deadline Engine
        deadline_service.extract_and_save_deadlines(
            db=db,
            document_id=document_id,
            full_text=text_content,
            doc_category=category # Pass the category for specialized fiscal logic
        )
        
        logger.info("task.fiscal_deadline_extraction.success", document_id=document_id)
        
    except Exception as e:
        logger.error("task.fiscal_deadline_extraction.failed", 
                     error=str(e), 
                     document_id=document_id)
        # We fail gracefully to allow the broader document processing pipeline to finish