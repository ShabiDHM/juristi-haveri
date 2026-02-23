# FILE: backend/app/services/analysis_service.py
# PHOENIX PROTOCOL - ANALYSIS SERVICE V25.0 (ACCOUNTING TRANSFORMATION)
# 1. REFACTOR: Transformed from "Legal Strategy" to "Audit & Fiscal Compliance".
# 2. SEMANTIC: Updated PDF Report headers for Financial/Audit context.
# 3. ALIGNMENT: Integrated with new Fiscal LLM Personas (ATK Auditor Simulation).
# 4. STATUS: 100% Accounting Aligned.

import asyncio
import structlog
import io
from typing import List, Dict, Any, Tuple
from pymongo.database import Database
from bson import ObjectId
from datetime import datetime
from xml.sax.saxutils import escape 

import app.services.llm_service as llm_service
from . import vector_store_service, report_service, archive_service
from .report_service import _get_text 

logger = structlog.get_logger(__name__)

async def _fetch_rag_context_async(db: Database, case_id: str, user_id: str, include_laws: bool = True) -> str:
    """PHOENIX: Parallelized RAG retrieval for Business context."""
    case = await asyncio.to_thread(db.cases.find_one, {"_id": ObjectId(case_id) if ObjectId.is_valid(case_id) else case_id})
    q = f"{case.get('case_name', '')} {case.get('description', '')}" if case else "Financial audit analysis"
    
    # Run Vector DB queries in parallel
    tasks = [
        asyncio.to_thread(vector_store_service.query_case_knowledge_base, user_id=user_id, query_text=q, case_context_id=case_id, n_results=15)
    ]
    if include_laws:
        tasks.append(asyncio.to_thread(vector_store_service.query_global_knowledge_base, query_text=q, n_results=15))
    
    results = await asyncio.gather(*tasks)
    business_facts = results[0]
    global_regulations = results[1] if include_laws else []

    blocks = ["=== DOKUMENTACIONI I BIZNESIT ==="]
    for f in business_facts:
        blocks.append(f"DOKUMENTI: {f['source']} (Faqja {f['page']})\nTEKSTI: {f['text']}\n")
    
    if include_laws:
        blocks.append("=== BAZA RREGULLATORE FISKALE ===")
        for l in global_regulations:
            blocks.append(f"RREGULLORJA/LIGJI: '{l['source']}'\nNENI/PËRMBAJTJA: {l['text']}\n")
            
    return "\n".join(blocks)

def authorize_case_access(db: Database, case_id: str, user_id: str) -> bool:
    """Verifies access to the client/business profile."""
    try:
        c_oid = ObjectId(case_id) if ObjectId.is_valid(case_id) else case_id
        u_oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
        return db.cases.find_one({"_id": c_oid, "owner_id": u_oid}) is not None
    except: return False

async def verify_business_compliance(db: Database, case_id: str, user_id: str) -> Dict[str, Any]:
    """PHOENIX: High-IQ analysis mapping fiscal regulations to business data."""
    if not authorize_case_access(db, case_id, user_id): return {"error": "Pa autorizim."}
    context = await _fetch_rag_context_async(db, case_id, user_id, include_laws=True)
    
    system_prompt = """
    DETYRA: Analizë e Përputhshmërisë Fiskale dhe Integritetit Financiar.
    MANDATI: Shpjegoni 'NDIKIMIN FISKAL' të çdo rregulloreje për këtë biznes specifik.
    JSON SCHEMA (STRIKT):
    {
      "executive_summary": "...",
      "fiscal_audit": { 
          "audit_risk_assessment": "...", 
          "regulatory_basis": [{"title": "[Emri i Rregullores, Neni](doc://ligji)", "article": "...", "relevance": "..."}] 
      },
      "strategic_recommendation": { "recommendation_text": "...", "risks": [], "action_plan": [], "compliance_score": "XX%", "risk_level": "LOW/MEDIUM/HIGH" },
      "missing_documentation": []
    }
    """
    try:
        # Aligned with updated llm_service method
        raw_res = await asyncio.to_thread(llm_service.analyze_business_integrity, context, custom_prompt=system_prompt)
        audit = raw_res.get("fiscal_audit", {})
        rec = raw_res.get("strategic_recommendation", {})
        return {
            "summary": raw_res.get("executive_summary"),
            "audit_risk": audit.get("audit_risk_assessment"),
            "legal_basis": audit.get("regulatory_basis", []), 
            "strategic_analysis": rec.get("recommendation_text"),
            "weaknesses": rec.get("risks", []),
            "action_plan": rec.get("action_plan", []),
            "missing_evidence": raw_res.get("missing_documentation", []),
            "success_probability": rec.get("compliance_score"),
            "risk_level": rec.get("risk_level", "MEDIUM")
        }
    except Exception as e:
        logger.error(f"Business Analysis Failed: {e}")
        return {"summary": "Dështoi gjenerimi i analizës fiskale."}

async def run_deep_audit(db: Database, case_id: str, user_id: str) -> Dict[str, Any]:
    """PHOENIX: Deep Audit Simulation & Anomaly Detection."""
    if not authorize_case_access(db, case_id, user_id): return {"error": "Pa autorizim."}
    
    try:
        full_context_task = _fetch_rag_context_async(db, case_id, user_id, include_laws=True)
        facts_only_task = _fetch_rag_context_async(db, case_id, user_id, include_laws=False)
        
        full_context, facts_only = await asyncio.gather(full_context_task, facts_only_task)

        # Using updated fiscal intelligence methods
        tasks = [
            llm_service.generate_audit_simulation(full_context),
            llm_service.build_financial_history(facts_only), 
            llm_service.detect_accounting_anomalies(full_context)
        ]
        
        adv, chr_res, cnt = await asyncio.gather(*tasks)
        
        return {
            "adversarial_simulation": adv if isinstance(adv, dict) else {},
            "chronology": chr_res.get("timeline", []) if isinstance(chr_res, dict) else [],
            "contradictions": cnt.get("contradictions", []) if isinstance(cnt, dict) else []
        }
    except Exception as e:
        logger.error(f"Deep Audit Failed: {e}")
        return {"error": "Dështoi analiza e thellë e auditimit."}

async def archive_full_strategy_report(db: Database, case_id: str, user_id: str, fiscal_data: Dict[str, Any], audit_data: Dict[str, Any], lang: str = "sq") -> Dict[str, Any]:
    """PHOENIX: Synthesizes Audit data into a Professional PDF."""
    if not authorize_case_access(db, case_id, user_id): return {"error": "Pa autorizim."}
    
    case = await asyncio.to_thread(db.cases.find_one, {"_id": ObjectId(case_id)})
    if not case: return {"error": "Biznesi nuk u gjet."}
        
    case_name = case.get("case_name", "Pa Titull")
    md = "---\n\n" 

    # Section 1: Executive Summary
    md += f"## 1. PËRMBLEDHJA FISKALE\n{fiscal_data.get('summary', '')}\n\n"
    if fiscal_data.get('audit_risk'):
        md += f"**VLERËSIMI I RISKUT TË AUDITIMIT:**\n{fiscal_data.get('audit_risk', '')}\n\n"
    
    # Section 2: Regulatory Basis
    if fiscal_data.get('legal_basis'):
        md += "## 2. BAZA RREGULLATORE & PËRPUTHSHMËRIA\n"
        for lb in fiscal_data.get('legal_basis', []):
            title = lb.get('title', 'Rregullore/Nen')
            md += f"### {title}\n"
            md += f"**Neni:** {lb.get('article', '')}\n\n"
            md += f"**Ndikimi Fiskal:** {lb.get('relevance', '')}\n\n"
        
    # Section 3: Recommendations
    md += "## 3. ANALIZA FINANCIARE & PLANI I VEPRIMIT\n"
    md += f"{fiscal_data.get('strategic_analysis', '')}\n\n"
    if fiscal_data.get('action_plan'):
        md += "### HAPAT E REKOMANDUAR:\n"
        for step in fiscal_data.get('action_plan', []):
            md += f"* {step}\n"
    
    # Section 4: Audit Simulation
    sim = audit_data.get('adversarial_simulation', {})
    md += "\n---\n## 4. SIMULIMI I AUDITIMIT (ATK)\n"
    md += f"### VËREJTJET E INSPEKTORIT\n{sim.get('opponent_strategy', 'Nuk u gjenerua.')}\n\n"
    if sim.get('weakness_attacks'):
        md += "### ANOMALITË E IDENTIFIKUARA\n"
        for w in sim.get('weakness_attacks', []):
            md += f"* {w}\n"

    # Section 5: Transaction History
    if audit_data.get('chronology'):
        md += "\n## 5. HISTORIKU I TRANSAKSIONEVE\n"
        for event in audit_data.get('chronology', []):
            md += f"* **{event.get('date', '')}**: {event.get('event', '')}\n"

    # Section 6: Anomalies
    if audit_data.get('contradictions'):
        md += "\n## 6. ANALIZA E ANOMALIVE\n"
        for c in audit_data.get('contradictions', []):
            severity = c.get('severity', 'LOW')
            md += f"### Anomali: {severity}\n"
            md += f"**Transaksioni:** {c.get('claim', '')}\n"
            md += f"**Dokumenti/Prova:** {c.get('evidence', '')}\n"
            md += f"**Impakti:** {c.get('impact', '')}\n\n"

    # Generate PDF
    try:
        main_report_title = _get_text('analysis_title', lang)
        pdf_buffer = report_service.create_pdf_from_text(
            text=md,
            document_title=main_report_title,
            header_meta_content_html=None 
        )
        pdf_bytes = pdf_buffer.getvalue()
    except Exception as e:
        logger.error(f"Audit PDF generation failed: {e}")
        return {"error": "Dështoi krijimi i raportit PDF."}

    # Persist
    archiver = archive_service.ArchiveService(db)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    archive_item_title = f"{_get_text('analysis_title', lang)}: {case_name}"
    filename = f"Raport_Fiskal_{case_name.replace(' ', '_')}_{timestamp}.pdf"
    
    try:
        archive_item = await archiver.save_generated_file(
            user_id=user_id,
            filename=filename,
            content=pdf_bytes,
            category="CASE_FILE",
            title=archive_item_title,
            case_id=case_id
        )
        return {"status": "success", "item_id": str(archive_item.id)}
    except Exception as e:
        logger.error(f"Audit archiving failed: {e}")
        return {"error": "Dështoi ruajtja e raportit në arkiv."}