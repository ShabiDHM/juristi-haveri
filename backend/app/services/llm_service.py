# FILE: backend/app/services/llm_service.py
# PHOENIX PROTOCOL - CORE INTELLIGENCE V71.0 (ACCOUNTING TRANSFORMATION)
# 1. REFACTOR: Transformed Universal Persona from 'Legal Partner' to 'Senior Certified Accountant & Tax Advisor'.
# 2. REFACTOR: Adversarial Simulation updated to 'ATK Auditor Simulation'.
# 3. REFACTOR: Contradiction Detection updated to 'Financial Anomaly Detection'.
# 4. STATUS: 100% Accounting Aligned. Core intelligence synchronized.

import os, json, logging, re, asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from openai import OpenAI, AsyncOpenAI
from .text_sterilization_service import sterilize_text_for_llm

logger = logging.getLogger(__name__)

# --- UNABRIDGED EXPORT LIST ---
__all__ = [
    "analyze_financial_portfolio", "analyze_business_integrity", "generate_audit_simulation",
    "build_financial_history", "translate_for_client", "detect_accounting_anomalies",
    "extract_deadlines", "perform_audit_verification", "generate_summary",
    "extract_graph_data", "get_embedding", "forensic_interrogation",
    "categorize_document_text", "sterilize_legal_text", "extract_expense_details_from_text",
    "query_global_rag_for_claims", "process_large_document_async", "stream_text_async"
]

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "deepseek/deepseek-chat" 
EMBEDDING_MODEL = "text-embedding-3-small"

# --- PHOENIX: Mandatory Albanian disclaimer for all user‑facing AI text ---
AI_DISCLAIMER = "\n\n---\n*Kjo përgjigje është gjeneruar nga AI për qëllime informative kontabël.*"

_async_client, _api_semaphore = None, None

def get_async_deepseek_client():
    global _async_client
    if not _async_client and DEEPSEEK_API_KEY:
        _async_client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=OPENROUTER_BASE_URL)
    return _async_client

def get_semaphore():
    global _api_semaphore
    if _api_semaphore is None: _api_semaphore = asyncio.Semaphore(10)
    return _api_semaphore

def _parse_json_safely(content: Optional[str]) -> Dict[str, Any]:
    if not content: return {}
    try: return json.loads(content)
    except:
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if match:
            try: return json.loads(match.group(1))
            except: pass
        return {"raw_response": content, "error": "JSON_PARSE_FAILED"}

# --- SENIOR ACCOUNTANT UNIVERSAL PERSONA ---
KOSOVO_FINANCIAL_BRAIN = """
ROLI: Ti je 'Senior Certified Accountant' dhe Këshilltar Fiskal në Kosovë.
MANDATI: Analizo çdo dokument përmes thjerrëzës së përputhshmërisë me ATK-në dhe Standardet e Kontabilitetit.
GJUHA: Çdo përgjigje duhet të jetë VETËM në gjuhën SHQIPE.
DETYRA: Për çdo rregullore ose ligj të cituar, DUHET:
1. Të përdorësh formatin: [Emri i Ligjit/Rregullores, Neni XX](doc://ligji).
2. Të tregosh 'NDIKIMIN FISKAL' – pse ky nen është thelbësor për financat e klientit.
"""

def _call_llm(sys_p: str, user_p: str, json_mode: bool = False, temp: float = 0.1) -> Optional[str]:
    c = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=OPENROUTER_BASE_URL) if DEEPSEEK_API_KEY else None
    if not c: return None
    try:
        messages = [{"role": "system", "content": f"{KOSOVO_FINANCIAL_BRAIN}\n{sys_p}"}, {"role": "user", "content": user_p}]
        kwargs = {"model": OPENROUTER_MODEL, "messages": messages, "temperature": temp}
        if json_mode: kwargs["response_format"] = {"type": "json_object"}
        return c.chat.completions.create(**kwargs).choices[0].message.content
    except Exception as e:
        logger.error(f"LLM Error: {e}")
        return None

async def _call_llm_async(sys_p: str, user_p: str, json_mode: bool = False, temp: float = 0.1) -> Optional[str]:
    client = get_async_deepseek_client()
    if not client: return None
    async with get_semaphore():
        try:
            kwargs = {"model": OPENROUTER_MODEL, "messages": [{"role": "system", "content": f"{KOSOVO_FINANCIAL_BRAIN}\n{sys_p}"}, {"role": "user", "content": user_p}], "temperature": temp}
            if json_mode: kwargs["response_format"] = {"type": "json_object"}
            res = await client.chat.completions.create(**kwargs)
            return res.choices[0].message.content
        except Exception as e:
            logger.error(f"Async LLM Error: {e}")
            return None

# --- HYDRA PARALLEL PROCESSING ---

async def process_large_document_async(text: str, task_type: str = "SUMMARY") -> str:
    """PHOENIX: Async document summarization + disclaimer."""
    if not text: return "Nuk u gjet tekst." + AI_DISCLAIMER
    map_p = "Analizo këtë segment financiar. Identifiko transaksionet dhe citoni [Rregulloren](doc://ligji). Përgjigju vetëm SHQIP."
    reduce_p = "Sintezo në një raport ekspert kontabël me citime të plota [Ligji Tatimor](doc://ligji). Përgjigju vetëm SHQIP."
    chunks = [text[i:i+5000] for i in range(0, len(text), 5000)]
    tasks = [_call_llm_async(map_p, f"SEGMENTI:\n{c}") for c in chunks]
    results = await asyncio.gather(*tasks)
    combined = "\n---\n".join([r for r in results if r])
    final = await _call_llm_async(reduce_p, f"ANALIZAT:\n{combined}")
    return (final or "Analiza dështoi.") + AI_DISCLAIMER

# --- ASYNC OPTIMIZED ANALYSIS FUNCTIONS (JSON) ---

async def generate_audit_simulation(context: str) -> Dict[str, Any]:
    """PHOENIX: Simulation of a rigorous ATK Tax Audit."""
    sys = (
        "Ti je një Inspektor Tatimor (ATK) jashtëzakonisht rigoroz. Detyra jote është të gjesh çdo gabim në deklarimet e klientit. "
        "MANDATI: Përgjigju vetëm në gjuhën SHQIPE. Gjej mospërputhje në TVSH, TAK dhe kontribute. "
        "Përdor 'doc://ligji' për referencat teknike. "
        "Kthe JSON: {'opponent_strategy':'vërejtjet_e_auditimit', 'weakness_attacks':['anomalitë_e_gjetura'], 'counter_claims':['kërkesat_për_korrigjim']}"
    )
    res = await _call_llm_async(sys, context[:40000], True, 0.4)
    return _parse_json_safely(res)

async def detect_accounting_anomalies(text: str) -> Dict[str, Any]:
    """PHOENIX: Detection of financial discrepancies or tax risks."""
    sys = (
        "Identifiko anomali midis faturave, llogarive bankare dhe deklaratave fiskale. "
        "MANDATI: Përgjigju vetëm në gjuhën SHQIPE. Përdor formatin [Rregullorja](doc://ligji). "
        "Kthe JSON: {'contradictions': [{'severity': 'HIGH/MEDIUM/LOW', 'claim': 'transaksioni_shqip', 'evidence': 'anomalia_e_gjetur', 'impact': 'ndikimi_fiskal'}]}"
    )
    res = await _call_llm_async(sys, text[:40000], True, 0.1)
    return _parse_json_safely(res)

async def build_financial_history(text: str) -> Dict[str, Any]:
    """PHOENIX: Extraction of chronological financial events."""
    sys = (
        "Nxirr një histori precize të transaksioneve dhe veprimeve fiskale nga ky tekst. "
        "MANDATI: Përgjigju vetëm në gjuhën SHQIPE. Përqëndruhu te datat e faturave, pagesat dhe deklarimet. "
        "Përdor formatin JSON: {'timeline': [{'date': 'Data', 'event': 'Veprimi Financiar'}]}"
    )
    res = await _call_llm_async(sys, text[:50000], True, 0.1)
    return _parse_json_safely(res)

# --- LEGACY SUPPORT FUNCTIONS (PLAIN TEXT + DISCLAIMER) ---

def analyze_business_integrity(context: str, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
    sys = custom_prompt or "Analizo përputhshmërinë fiskale dhe integritetin e llogarive. Përgjigju vetëm SHQIP. Kthe JSON."
    return _parse_json_safely(_call_llm(sys, context[:100000], True, 0.1))

def extract_deadlines(text: str) -> Dict[str, Any]:
    return _parse_json_safely(_call_llm("Gjej afatet tatimore dhe të deklarimit në SHQIP. JSON: {'deadlines':[]}", text[:20000], True))

def perform_audit_verification(target: str, context: List[str]) -> Dict[str, Any]:
    return _parse_json_safely(_call_llm(f"Verifiko transaksionin: {target} në SHQIP. JSON.", "\n".join(context)[:40000], True))

def generate_summary(text: str) -> str:
    res = _call_llm("Krijo përmbledhje ekzekutive financiare në 3 pika në SHQIP.", text[:20000])
    return (res or "") + AI_DISCLAIMER

def extract_graph_data(text: str) -> Dict[str, Any]:
    return _parse_json_safely(_call_llm("Nxjerr lidhjet midis subjekteve financiare. Përgjigju SHQIP. JSON: {'nodes':[], 'edges':[]}", text[:30000], True))

def get_embedding(text: str) -> List[float]:
    from openai import OpenAI as OAI
    c = OAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
    if not c: return [0.0] * 1536
    try: return c.embeddings.create(input=[text.replace("\n", " ")], model=EMBEDDING_MODEL).data[0].embedding
    except: return [0.0] * 1536

async def stream_text_async(sys_p: str, user_p: str, temp: float = 0.2) -> AsyncGenerator[str, None]:
    client = get_async_deepseek_client()
    if not client:
        yield "[OFFLINE]"
        yield AI_DISCLAIMER
        return
    async with get_semaphore():
        try:
            stream = await client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=[
                    {"role": "system", "content": f"{KOSOVO_FINANCIAL_BRAIN}\n{sys_p}"},
                    {"role": "user", "content": user_p}
                ],
                temperature=temp,
                stream=True
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            yield AI_DISCLAIMER
        except Exception as e:
            yield f"[Gabim: {str(e)}]"
            yield AI_DISCLAIMER

def forensic_interrogation(q: str, rows: List[str]) -> str:
    res = _call_llm(f"Përgjigju si auditor SHQIP me [Rregulloren](doc://ligji) duke u bazuar në: {' '.join(rows)}", q, temp=0.0)
    return (res or "") + AI_DISCLAIMER

def categorize_document_text(text: str) -> str:
    res = _call_llm("Kategorizo dokumentin (Faturë, Kontratë, Pasqyrë, etj) në SHQIP. JSON {'category': '...'}.", text[:5000], True)
    return _parse_json_safely(res).get("category", "Të tjera")

def sterilize_legal_text(text: str) -> str:
    from .text_sterilization_service import sterilize_text_for_llm
    return sterilize_text_for_llm(text)

def extract_expense_details_from_text(t: str) -> Dict[str, Any]:
    r = _parse_json_safely(_call_llm("Nxirr detajet e shpenzimit në SHQIP (shuma, data, kategoria). JSON.", t[:3000], True))
    return {
        "category": r.get("category", "Shpenzime"),
        "amount": float(r.get("amount", 0.0)),
        "date": r.get("date", datetime.now().strftime("%Y-%m-%d")),
        "description": r.get("merchant", "")
    }

def analyze_financial_portfolio(d: str) -> Dict[str, Any]:
    return _parse_json_safely(_call_llm("Analizo portofolin financiar dhe rreziqet në SHQIP. JSON.", d, True))

def translate_for_client(t: str) -> str:
    res = _call_llm("Përkthe termat financiare në SHQIP të thjeshtë.", t)
    return (res or "") + AI_DISCLAIMER

def query_global_rag_for_claims(r: str, q: str) -> Dict[str, Any]:
    return _parse_json_safely(_call_llm("Gjej bazën rregullatore në SHQIP me [Rregulloren](doc://ligji). JSON.", f"RAG: {r}\nQ: {q}", True))

def generate_adversarial_simulation(context: str) -> Dict[str, Any]:
    """Legacy alias for generate_audit_simulation."""
    import asyncio
    return asyncio.run(generate_audit_simulation(context))

def detect_contradictions(text: str) -> Dict[str, Any]:
    """Legacy alias for detect_accounting_anomalies."""
    import asyncio
    return asyncio.run(detect_accounting_anomalies(text))

def build_case_chronology(text: str) -> Dict[str, Any]:
    """Legacy alias for build_financial_history."""
    import asyncio
    return asyncio.run(build_financial_history(text))