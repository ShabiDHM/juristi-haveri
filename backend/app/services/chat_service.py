# FILE: backend/app/services/chat_service.py
# PHOENIX PROTOCOL - CHAT SERVICE V25.7 (COMPILER RESOLUTION FIX)
# 1. FIX: Switched to explicit function import from llm_service to resolve Pylance 'unknown attribute' error.
# 2. REFACTOR: Persona remains 'Senior Certified Accountant & Tax Advisor'.
# 3. STATUS: 100% Type Clean & Accounting Aligned.

from __future__ import annotations
import logging
import asyncio
import structlog
from typing import AsyncGenerator, Optional, List, Dict, Any
from bson import ObjectId
from datetime import datetime, timezone
from pymongo.database import Database

# Explicit Absolute Imports to resolve Pylance attribute issues
from app.models.case import ChatMessage
from app.services.llm_service import stream_text_async
from app.services import vector_store_service

logger = structlog.get_logger(__name__)

async def stream_chat_response(
    db: Database, case_id: str, user_query: str, user_id: str,
    document_id: Optional[str] = None, jurisdiction: Optional[str] = 'ks', mode: Optional[str] = 'FAST'
) -> AsyncGenerator[str, None]:
    try:
        oid, user_oid = ObjectId(case_id), ObjectId(user_id)
        # Verify access to the client/business data
        case = db.cases.find_one({"_id": oid, "owner_id": user_oid})
        if not case: 
            yield "Gabim: Qasja në të dhënat e këtij klienti u refuzua."; 
            return

        # Sync User Message to History
        db.cases.update_one({"_id": oid}, {"$push": {"chat_history": ChatMessage(role="user", content=user_query, timestamp=datetime.now(timezone.utc)).model_dump()}})
        
        full_response = ""
        yield " " # Keep-alive

        if not mode or mode.upper() == 'FAST':
            # --- FAST MODE: Direct, Concise Accounting Guidance ---
            snippets = vector_store_service.query_case_knowledge_base(user_id=user_id, query_text=user_query, n_results=10, case_context_id=case_id)
            context = "\n".join([f"- {s['text']} (Burimi: {s['source']})" for s in snippets])
            
            # Accounting Persona Mandate
            system_prompt = f"""
            Ti je "Kontabilisti AI" - një Kontabilist i Certifikuar dhe Këshilltar Fiskal me përvojë të lartë.
            DETYRA: Jep një përgjigje të saktë, profesionale dhe të shkurtër (MAX 2 PARAGRAFE).
            FOKUSI: Përputhshmëria me ATK-në, ligji për TVSH-në, kontributet pensionale dhe standardet financiare.
            CITIMI: Referoju udhëzimeve administrative ose neneve të ligjit duke përdorur formatin [Emri i Rregullores](doc://rregullorja).
            
            DOKUMENTET E KLIENTIT DHE KONTEKSTI:
            {context}
            """
            # Using the explicitly imported stream_text_async
            async for token in stream_text_async(system_prompt, user_query, temp=0.1):
                full_response += token
                yield token
        else:
            # --- AUDIT MODE (DEEP): Comprehensive Financial & Tax Analysis ---
            # LOCAL IMPORT: Prevents circular dependency and ensures resolution
            from app.services.albanian_rag_service import AlbanianRAGService
            
            agent_service = AlbanianRAGService(db=db)
            async for token in agent_service.chat(
                query=user_query, 
                user_id=user_id, 
                case_id=case_id, 
                document_ids=[document_id] if document_id else None,
                jurisdiction=jurisdiction or 'ks'
            ):
                full_response += token
                yield token

        # Sync AI Message to History
        if full_response.strip():
            db.cases.update_one({"_id": oid}, {"$push": {"chat_history": ChatMessage(role="ai", content=full_response.strip(), timestamp=datetime.now(timezone.utc)).model_dump()}})
            
    except Exception as e:
        logger.error(f"Streaming Error: {e}")
        yield "\n\n[Gabim Teknik: Shërbimi i asistencës financiare dështoi.]"