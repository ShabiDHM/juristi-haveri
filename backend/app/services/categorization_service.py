# FILE: backend/app/services/categorization_service.py
# PHOENIX PROTOCOL - CATEGORIZATION SERVICE V2.0 (ACCOUNTING TRANSFORMATION)
# 1. FIX: Switched to Absolute Import from llm_service to resolve potential Pylance issues.
# 2. REFACTOR: Documentation updated to reflect Fiscal/Accounting document classification.
# 3. STATUS: 100% Accounting Aligned.

import logging
# PHOENIX: Absolute import for architectural integrity
from app.services.llm_service import categorize_document_text

logger = logging.getLogger(__name__)

class CategorizationService:
    """
    Service responsible for classifying business documents (Invoices, Tax Declarations, 
    Bank Statements, etc.) into predefined fiscal categories.
    """
    def categorize_document(self, text: str) -> str:
        """
        Invokes the LLM Intelligence to determine the fiscal category of a given text.
        """
        try:
            # Call the specialized accounting classifier in llm_service
            category = categorize_document_text(text)
            if not category:
                return "Të tjera" # Default Albanian "Other"
            return category
        except Exception as e:
            logger.error(f"Error during document categorization: {e}", exc_info=True)
            return "Gabim gjatë kategorizimit"

# --- CRITICAL INSTANTIATION ---
CATEGORIZATION_SERVICE = CategorizationService()