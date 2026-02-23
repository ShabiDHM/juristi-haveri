# FILE: backend/app/services/drafting_service.py
# PHOENIX PROTOCOL - DRAFTING SERVICE V23.0 (ACCOUNTING TRANSFORMATION)
# 1. REFACTOR: Domains transformed from Legal (Criminal/Family) to Fiscal (Tax/Audit/SNK).
# 2. PERSONA: AI now acts as a 'Senior Certified Accountant & Tax Advisor'.
# 3. STRUCTURE: Mandatory formatting updated for professional business and ATK reports.
# 4. STATUS: 100% Accounting Aligned.

import os
import asyncio
import structlog
from datetime import datetime, timezone
from typing import Optional, Dict, List, AsyncGenerator
from pymongo.database import Database

# PHOENIX: Absolute imports for architectural integrity
from app.services import llm_service, vector_store_service

logger = structlog.get_logger(__name__)

# --- PHOENIX PROTOCOL: ACCOUNTING & FISCAL KNOWLEDGE BASE ---
# Maps specific keywords to Kosovo's Financial & Tax Frameworks.
ACCOUNTING_DOMAINS = {
    "TAXATION": {
        "keywords": ["tvsh", "vat", "atk", "tatim", "deklarim", "fiskal", "këst", "gjobë tatimore", "procedurë tatimore"],
        "law": "Ligji Nr. 05/L-037 për TVSH dhe Ligji për Procedurën Tatimore dhe Ndëshkimet",
        "context_note": "Fokus: Përputhshmëria me ATK-në, deklarimi i saktë i TVSH-së dhe TAK-ut."
    },
    "CORPORATE": {
        "keywords": ["shpk", "aksion", "biznes", "bord", "divident", "falimentim", "statut", "marrëveshje aksionarësh"],
        "law": "Ligji Nr. 06/L-016 për Shoqëritë Tregtare",
        "context_note": "Fokus: Qeverisja e biznesit, ndarja e dividentit dhe përgjegjësia korporative."
    },
    "FINANCIAL_REPORTING": {
        "keywords": ["bilanc", "pasqyrë", "audit", "raport financiar", "llogari", "humbje", "fitim", "amortizim"],
        "law": "Ligji për Kontabilitet, Raportim Financiar dhe Auditim dhe SNK",
        "context_note": "Fokus: Standardet Ndërkombëtare të Kontabilitetit (SNK) dhe saktësia e pasqyrave."
    },
    "LABOR_PAYROLL": {
        "keywords": ["punë", "rrogë", "pagë", "kontribute", "trust", "kontratë pune", "largim", "orar", "taksa në paga"],
        "law": "Ligji i Punës dhe Ligji për Kontributet Pensionale",
        "context_note": "Fokus: Kalkulimi i pagave, kontributet pensionale dhe të drejtat e punëtorit."
    },
    "OBLIGATIONS": {
        "keywords": ["kontratë", "borxh", "faturë", "qira", "shitblerje", "marrëveshje", "përmbushje", "furnitor"],
        "law": "Ligji Nr. 04/L-077 për Marrëdhëniet e Detyrimeve (LMD)",
        "context_note": "Fokus: Validiteti i faturave, afatet e pagesës dhe dëmet kontraktuale."
    },
    "ADMINISTRATIVE": {
        "keywords": ["vendim", "licencë", "leje", "inspektorat", "komuna", "ministria", "ankesë"],
        "law": "Ligji për Procedurën e Përgjithshme Administrative",
        "context_note": "Fokus: Përfaqësimi në organe administrative dhe ligjshmëria e vendimeve."
    }
}

def detect_accounting_domain(text: str) -> Dict[str, str]:
    """
    Scans the input text to determine the primary accounting or fiscal domain.
    """
    text_lower = text.lower()
    scores = {key: 0 for key in ACCOUNTING_DOMAINS}
    
    for domain, data in ACCOUNTING_DOMAINS.items():
        for keyword in data["keywords"]:
            if keyword in text_lower:
                scores[domain] += 1
    
    best_match = max(scores, key=lambda k: scores[k])
    
    if scores[best_match] > 0:
        return ACCOUNTING_DOMAINS[best_match]
    
    return {
        "law": "Legjislacioni Fiskal dhe Standardet e Kontabilitetit në Kosovë",
        "context_note": "Fokus: Përputhshmëria e përgjithshme financiare dhe rregullat tatimore."
    }

async def stream_draft_generator(
    db: Database, 
    user_id: str, 
    case_id: Optional[str], 
    draft_type: str, 
    user_prompt: str
) -> AsyncGenerator[str, None]:
    """
    Orchestrates the generation of accounting and financial documents using RAG.
    Note: 'case_id' represents the Client/Business entity.
    """
    logger.info(f"Fiscal Drafting initiated", user=user_id, type=draft_type)
    
    # 1. Dynamic Domain Detection
    domain_context = detect_accounting_domain(user_prompt)
    detected_framework = domain_context["law"]
    context_note = domain_context["context_note"]
    
    # 2. Smart Search Query for Tax/Accounting Library
    search_query = f"{user_prompt} {detected_framework} neni rregullorja udhëzimi"

    # 3. Parallel Retrieval (RAG)
    try:
        tasks = [
            # Retrieve Business Facts (Transactions, Metadata)
            asyncio.to_thread(
                vector_store_service.query_case_knowledge_base, 
                user_id=user_id, 
                query_text=user_prompt, 
                n_results=10, 
                case_context_id=case_id
            ),
            # Retrieve Regulatory Basis (ATK, SNK, Laws)
            asyncio.to_thread(
                vector_store_service.query_global_knowledge_base, 
                query_text=search_query, 
                n_results=12
            )
        ]
        
        results = await asyncio.gather(*tasks)
        business_facts = results[0] or []
        regulatory_articles = results[1] or []

    except Exception as e:
        logger.error(f"Vector Store Retrieval Failed: {e}")
        business_facts, regulatory_articles = [], []

    # Format Retrieved Data
    facts_block = "\n".join([f"- {f.get('text', '')}" for f in business_facts]) if business_facts else "Përdor informacionin nga prompti."
    regs_block = "\n".join([f"- {l.get('text', '')} (Burimi: {l.get('source', 'Rregullore')})" for l in regulatory_articles]) if regulatory_articles else "Bazohu në Standardet e Kontabilitetit në Kosovë."

    # 4. Construct System Mandate
    system_prompt = f"""
    ROLI: Kontabilist i Certifikuar dhe Këshilltar Fiskal në Kosovë.
    DETYRA: Hartimi i dokumentit profesional: "{draft_type.upper()}".
    
    KORNIZA RREGULLATORE E DETEKTUAR:
    - Baza: {detected_framework}
    - Udhëzim: {context_note}
    
    [MATERIALI RREGULLATOR NDITMËS - RAG]:
    {regs_block}
    
    [TË DHËNAT E BIZNESIT DHE TRANSAKSIONET]:
    {facts_block}
    
    UDHËZIME PËR STRUKTURËN (E DETYRUESHME):
    1. HEADER: Emri i Zyrës, Klienti, Data.
    2. LËNDA: [Përmbledhje e shkurtër e qëllimit të dokumentit].
    3. TITULLI: "{draft_type.upper()}" (Bold, i qendërzuar).
    4. BAZA RREGULLATORE: Cito saktë nenet nga "{detected_framework}" ose udhëzimet administrative të ATK-së.
    5. ARSYETIMI FINANCIAR: Shpjegim teknik i shifrave dhe transaksioneve në raport me ligjin.
    6. REKOMANDIMET / KONKLUZIONI: Hapat që duhen ndjekur për përputhshmëri ose optimizim fiskal.
    7. NËNSHKRIMI: Kontabilisti i certifikuar.

    RREGULLA:
    - Përdor terminologji profesionale kontabël.
    - Saktësia në shifra dhe nene është prioriteti #1.
    - Nëse mungojnë shifra specifike, përdor [SHUMA_KËTU] ose [____].
    
    KËRKESA E KLIENTIT:
    {user_prompt}
    """

    # 5. Stream Execution
    full_content = ""
    try:
        # Calls the unified LLM streaming utility
        async for token in llm_service.stream_text_async(system_prompt, "Fillo hartimin e dokumentit profesional tani.", temp=0.1):
            full_content += token
            yield token
            
        # 6. Save Result (Async Fire-and-Forget)
        if full_content.strip() and case_id:
            asyncio.create_task(save_draft_result(db, user_id, case_id, draft_type, full_content))
            
    except Exception as e:
        logger.error(f"LLM Drafting Failed: {e}")
        yield f"\n\n[GABIM SISTEMI]: {str(e)}"

async def save_draft_result(db: Database, user_id: str, case_id: str, draft_type: str, content: str):
    """Saves the generated financial draft asynchronously."""
    try:
        await asyncio.to_thread(
            db.drafting_results.insert_one, 
            {
                "case_id": case_id, 
                "user_id": user_id, 
                "draft_type": draft_type, 
                "result_text": content, 
                "status": "COMPLETED", 
                "created_at": datetime.now(timezone.utc)
            }
        )
    except Exception as e:
        logger.error(f"Failed to save draft result: {e}")