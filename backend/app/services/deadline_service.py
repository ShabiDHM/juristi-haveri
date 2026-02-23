# FILE: backend/app/services/deadline_service.py
# PHOENIX PROTOCOL - FISCAL DEADLINE ENGINE V9.1 (IMPORT FIX)
# 1. FIX: Switched to Absolute Imports (app.models...) to resolve Pylance/Runtime resolution errors.
# 2. STATUS: Import paths are now strictly defined.

import os
import json
import structlog
import dateparser
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from bson import ObjectId
from pymongo.database import Database
from openai import OpenAI 

from app.services import document_service 
from app.models.document import DocumentOut
# CHANGED: Absolute import to prevent resolution errors
from app.models.calendar import EventType, EventStatus, EventPriority, EventCategory

logger = structlog.get_logger(__name__)

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY") 
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "deepseek/deepseek-chat" 

AL_MONTHS = {
    "janar": "January", "shkurt": "February", "mars": "March", "prill": "April",
    "maj": "May", "qershor": "June", "korrik": "July", "gusht": "August",
    "shtator": "September", "tetor": "October", "nëntor": "November", "nentor": "November",
    "dhjetor": "December"
}

# FISCAL KEYWORDS: Triggers for accounting deadlines
ACCOUNTING_KEYWORDS = [
    "tvsh", "tatim", "paga", "kontribute", "qs", "tak", "bilanc", "deklarim", 
    "faturë", "invoice", "pagesë", "këst", "audit", "inventar", "afat pagese"
]

def _preprocess_date_text(text: str) -> str:
    text_lower = text.lower()
    for sq, en in AL_MONTHS.items():
        text_lower = text_lower.replace(sq, en)
    return text_lower

def _extract_dates_with_llm(full_text: str, doc_category: str) -> List[Dict[str, str]]:
    truncated_text = full_text[:25000]
    current_date = datetime.now().strftime("%d %B %Y")
    
    logger.info(f"LLM input text length: {len(truncated_text)}")
    logger.info(f"LLM input text preview: {truncated_text[:500]}...")
    
    # NEW PROMPT: Focused on Tax & Accounting
    system_prompt = f"""
    Ti je "Senior Tax Accountant & Compliance Officer". DATA SOT: {current_date}.
    DETYRA: Analizo këtë dokument financiar ({doc_category}) dhe nxirr afatet e pagesave dhe deklarimeve.
    
    RREGULLA TË RREPTA:
    - **AGENDA** (Veprime të Detyrueshme):
        * Afati i fundit për deklarimin e TVSH-së (zakonisht data 20).
        * Afati i fundit për pagesën e Kontributeve (QS) dhe TAP (zakonisht data 15).
        * Afati i pagesës së faturës (Invoice Due Date).
        * Afati për dorëzimin e Bilancit Vjetor (31 Mars).
        * Këste të Tatimit në Fitim (TAK).
    - **FACT** (Informacion):
        * Data e lëshimit të faturës (Invoice Date).
        * Data e transaksionit bankar.
        * Data e fillimit të kontratës së punës.
    
    Kategoritë e Lejuara për 'event_type': 
    - "TAX_DEADLINE" (për TVSH, TAK, QS, Bilanc)
    - "PAYMENT_DUE" (për Fatura furnitorësh, pagesa kleringu)
    - "TASK" (për deklarime rutinë)
    
    Kthe JSON: {{ "events": [ {{ "title": "...", "date_text": "...", "category": "AGENDA|FACT", "event_type": "TAX_DEADLINE|PAYMENT_DUE|TASK", "description": "..." }} ] }}
    """

    if DEEPSEEK_API_KEY:
        try:
            client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=OPENROUTER_BASE_URL)
            response = client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": truncated_text}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            raw_content = response.choices[0].message.content or "{}"
            logger.info(f"LLM raw response: {raw_content}")
            data = json.loads(raw_content)
            events = data.get("events", [])
            logger.info(f"LLM extracted events count: {len(events)}")
            return events
        except Exception as e:
            logger.warning(f"LLM Extraction Failed: {e}")
            logger.exception("Full traceback:")
    return []

def extract_and_save_deadlines(db: Database, document_id: str, full_text: str, doc_category: str = "Unknown"):
    log = logger.bind(document_id=document_id, category=doc_category)
    try:
        doc_oid = ObjectId(document_id)
        document_raw = db.documents.find_one({"_id": doc_oid})
        if not document_raw: return
        document = DocumentOut.model_validate(document_raw)
    except Exception:
        return

    extracted_items = _extract_dates_with_llm(full_text, doc_category)
    if not extracted_items:
        log.info("No events extracted from document.")
        return

    calendar_events = []
    metadata_chronology = []
    now = datetime.now()

    for item in extracted_items:
        raw_date = item.get("date_text", "")
        if not raw_date:
            log.debug("Skipping item with empty date_text", item=item)
            continue
        
        log.debug("Processing date", raw_date=raw_date)
        
        parsed = dateparser.parse(_preprocess_date_text(raw_date), settings={'DATE_ORDER': 'DMY'})
        if not parsed:
            log.warning("Could not parse date", raw_date=raw_date)
            continue
        
        log.debug("Parsed date", parsed_date=parsed.isoformat())
        
        llm_category = item.get("category", "FACT")
        event_type = item.get("event_type", "OTHER") # Default fallback
        description = item.get("description", "")
        title = item.get("title", "")
        
        # --- FALLBACK RULE: Force AGENDA for accounting keywords if clearly in future ---
        is_future = parsed >= now
        is_not_log = doc_category.upper() not in ["LOG", "AUDIT_TRAIL"]
        contains_keyword = any(kw in description.lower() or kw in title.lower() for kw in ACCOUNTING_KEYWORDS)
        
        final_category = llm_category
        if is_future and is_not_log and contains_keyword:
            if final_category != "AGENDA":
                logger.info(f"Fallback: overriding {llm_category} to AGENDA for date {raw_date} (accounting keyword match)")
                final_category = "AGENDA"
                # Auto-classify type if missing
                if "tvsh" in title.lower() or "tatim" in title.lower():
                    event_type = "TAX_DEADLINE"
                elif "fatur" in title.lower() or "invoice" in title.lower():
                    event_type = "PAYMENT_DUE"
        
        # Build chronology item
        metadata_chronology.append({
            "title": title,
            "date": parsed,
            "category": final_category,
            "event_type": event_type,
            "description": description
        })

        is_agenda = final_category == "AGENDA"

        if is_agenda and is_future and is_not_log:
            # Determine Priority based on Type
            priority = EventPriority.MEDIUM
            if event_type == "TAX_DEADLINE": priority = EventPriority.CRITICAL
            elif event_type == "PAYMENT_DUE": priority = EventPriority.HIGH

            calendar_events.append({
                "case_id": str(document.case_id) if document.case_id else None,       
                "owner_id": document.owner_id,
                "document_id": document_id,
                "title": title,
                "category": EventCategory.AGENDA,
                "description": f"{description}\n(Burimi: {document.file_name})", 
                "start_date": parsed,         
                "end_date": parsed,           
                "is_all_day": True,
                "event_type": event_type, 
                "status": EventStatus.PENDING,     
                "priority": priority, 
                "created_at": datetime.now(timezone.utc)
            })
            log.info("Added to calendar", title=title, date=parsed.isoformat(), type=event_type)

    # Save chronology metadata
    db.documents.update_one(
        {"_id": doc_oid}, 
        {"$set": {"ai_metadata.financial_chronology": metadata_chronology}} 
    )
    log.info("Saved financial chronology items", count=len(metadata_chronology))

    # Replace calendar events for this document
    db.calendar_events.delete_many({"document_id": document_id}) 
    if calendar_events:
        db.calendar_events.insert_many(calendar_events)
        log.info("calendar.events_synced", count=len(calendar_events))
    else:
        log.info("calendar.no_actionable_events_found")