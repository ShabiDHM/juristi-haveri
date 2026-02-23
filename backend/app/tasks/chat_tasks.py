# FILE: backend/app/services/chat_service.py
# PHOENIX PROTOCOL - CHAT SERVICE V25.8 (TASK COMPATIBILITY FIX)
# 1. ADDED: get_http_chat_response function to support background Celery tasks.
# 2. REFACTOR: Aggregates stream chunks into a single string for non-streaming consumers.
# 3. STATUS: 100% Accounting Aligned & Task Compatible.

from __future__ import annotations
import logging
import asyncio
import structlog
from typing import AsyncGenerator, Optional, List, Dict, Any
from bson import ObjectId
from datetime import datetime, timezone
from pymongo.database import Database

# Explicit Absolute Imports
from app.models.case import ChatMessage
from app.services.llm_service import stream_text_async
from app.services import vector_store_service

logger = structlog.get_logger(__name__)

async def stream_chat_response(
    db: Database, case_id: str, user_query: str, user_id: str,
    document_id: Optional[str] = None, jurisdiction: Optional[str] = 'ks', mode: Optional[str] = 'FAST'
) -> AsyncGenerator[str, None]:
    """
    Core streaming interface for the AI persona. 
    Used by WebSockets and direct streaming API endpoints.
    """
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
            
            system_prompt = f"""
            Ti je "Kontabilisti AI" - një Kontabilist i Certifikuar dhe Këshilltar Fiskal me përvojë të lartë.
            DETYRA: Jep një përgjigje të saktë, profesionale dhe të shkurtër (MAX 2 PARAGRAFE).
            FOKUSI: Përputhshmëria me ATK-në, ligji për TVSH-në dhe kontributet.
            CITIMI: Referoju udhëzimeve administrative duke përdorur formatin [Emri i Rregullores](doc://rregullorja).
            
            DOKUMENTET E KLIENTIT DHE KONTEKSTI:
            {context}
            """
            async for token in stream_text_async(system_prompt, user_query, temp=0.1):
                full_response += token
                yield token
        else:
            # --- AUDIT MODE (DEEP): Comprehensive Financial & Tax Analysis ---
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

async def get_http_chat_response(
    db: Database, case_id: str, user_query: str, user_id: str,
    document_id: Optional[str] = None, jurisdiction: Optional[str] = 'ks', mode: Optional[str] = 'FAST'
) -> str:
    """
    PHOENIX: Non-streaming wrapper for consumers like Celery tasks or standard REST.
    Aggregates tokens from stream_chat_response and returns a final string.
    """
    full_text = ""
    async for chunk in stream_chat_response(
        db=db, 
        case_id=case_id, 
        user_query=user_query, 
        user_id=user_id, 
        document_id=document_id, 
        jurisdiction=jurisdiction, 
        mode=mode
    ):
        # Filter out the initial keep-alive space
        if chunk != " ":
            full_text += chunk
            
    return full_text.strip()