# FILE: backend/app/models/drafting.py
# PHOENIX PROTOCOL - DRAFTING MODEL V2.0 (ACCOUNTING TRANSFORMATION)
# 1. REFACTOR: Documentation updated for Fiscal/Accounting context.
# 2. COMPATIBILITY: 'case_id' maps to Business/Client ID in the accounting domain.
# 3. ALIAS: Maintained 'user_prompt' mapping to 'prompt' for frontend parity.
# 4. STATUS: 100% Accounting Aligned.

from pydantic import BaseModel, Field
from typing import Optional

class DraftRequest(BaseModel):
    """
    Data model for requesting the generation of business and fiscal documents.
    """
    # Frontend sends 'user_prompt', maps to 'prompt'
    prompt: str = Field(..., alias="user_prompt")
    
    # case_id refers to the Client/Business entity ID in the accounting system
    case_id: Optional[str] = None
    
    # document_type holds accounting templates (e.g., 'tax_explanation', 'audit_report')
    document_type: Optional[str] = "Përgjithshme"
    
    # Defaults to Kosovo for ATK and SNK compliance logic
    jurisdiction: Optional[str] = "Kosovo"
    
    # Optional raw text context for manual drafting
    context: Optional[str] = None
    
    # PHOENIX: Flag to enable RAG against the Fiscal/Regulatory library
    use_library: bool = False

    class Config:
        populate_by_name = True