# FILE: backend/app/services/albanian_rag_service.py
# PHOENIX PROTOCOL - RAG SERVICE V57.0 (ACCOUNTING BRAIN TRANSPLANT)
# 1. REFACTOR: Persona transformed from 'Legal Partner' to 'Senior Tax Partner & Auditor'.
# 2. UI: Response structure updated for Financial Audits and Fiscal Compliance.
# 3. LOGIC: Maintained citation linking logic for Tax Laws and ATK Regulations.
# 4. STATUS: Brain transplant complete.

import os
import sys
import asyncio
import logging
import re
from typing import List, Optional, Dict, Any, AsyncGenerator, Tuple
from langchain_openai import ChatOpenAI
from pymongo.database import Database

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY") 
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "deepseek/deepseek-chat" 
LLM_TIMEOUT = 120

AI_DISCLAIMER = "\n\n---\n*Kjo analizë është gjeneruar nga AI për qëllime informative kontabël.*"

PROTOKOLLI_MANDATOR = """
**URDHËRA TË RREPTË FORMATIMI (NDIQINI ME PRECIZION):**
1. Çdo citim i rregulloreve DUHET të përmbajë **EMRIN E PLOTË TË LIGJIT OSE UDHËZIMIT** dhe **NUMRIN ZYRTAR** (p.sh., "Nr. 05/L-037") siç shfaqen në kontekst.  
   **Shembull i saktë:**  
   `Ligji Nr. 05/L-037 për Tatimin mbi Vlerën e Shtuar, Neni 28`  
2. Për çdo rregullore të cituar, DUHET të shtoni rreshtin: **NDIKIMI FISKAL:** [Pse ky nen ndikon në llogaritë e klientit].
3. Përdor TITUJT MARKDOWN (###) për të ndarë seksionet e raportit.
4. MOS përdor blloqe kodi.
"""

class AlbanianRAGService:
    def __init__(self, db: Database):
        self.db = db
        self.citation_map: Dict[Tuple[str, str], str] = {}
        self.law_number_map: Dict[Tuple[str, str], str] = {}
        if DEEPSEEK_API_KEY:
            self.llm = ChatOpenAI(
                model=OPENROUTER_MODEL, 
                base_url=OPENROUTER_BASE_URL, 
                api_key=DEEPSEEK_API_KEY,  # type: ignore
                temperature=0.0, 
                streaming=True,
                timeout=LLM_TIMEOUT
            )
        else:
            self.llm = None

    def _normalize_law_title(self, title: str) -> str:
        return ' '.join(title.strip().split())

    def _extract_law_number(self, text: str) -> Optional[str]:
        match = re.search(r'Nr\.?\s*([\d/L\-]+)', text, re.IGNORECASE)
        return match.group(1) if match else None

    def _build_citation_map(self, global_docs: List[Dict[str, Any]]):
        self.citation_map.clear()
        self.law_number_map.clear()
        for d in global_docs:
            law_title = d.get('law_title')
            article_num = d.get('article_number')
            chunk_id = d.get('chunk_id')
            if law_title and article_num and chunk_id:
                norm_title = self._normalize_law_title(law_title)
                key = (norm_title, str(article_num).strip())
                self.citation_map[key] = chunk_id
                law_number = self._extract_law_number(law_title)
                if law_number:
                    num_key = (law_number, str(article_num).strip())
                    self.law_number_map[num_key] = chunk_id

    def _format_citations(self, text: str) -> str:
        pattern1 = r'(Ligj(i|it)?\s.{0,200}?Nr\.?\s*[\d/L\-]+.{0,200}?,\s*Neni\s+(\d+))'
        pattern2 = r'(Neni\s+(\d+)\s+i\s+Ligj(i|it)?\s.{0,200}?Nr\.?\s*[\d/L\-]+.{0,200}?)'

        def replacer_pattern1(match):
            full_citation = match.group(1).strip()
            article_num = match.group(3).strip()
            law_part = full_citation.split(', Neni')[0]
            return self._make_link(law_part, article_num, full_citation)

        def replacer_pattern2(match):
            full_citation = match.group(1).strip()
            article_num = match.group(2).strip()
            law_part = full_citation.split(f"Neni {article_num} i ")[1]
            return self._make_link(law_part, article_num, full_citation)

        text = re.sub(pattern1, replacer_pattern1, text, flags=re.IGNORECASE)
        text = re.sub(pattern2, replacer_pattern2, text, flags=re.IGNORECASE)
        return text

    def _make_link(self, law_text: str, article_num: str, full_citation: str) -> str:
        law_number = self._extract_law_number(full_citation)
        if law_number:
            num_key = (law_number, article_num)
            chunk_id = self.law_number_map.get(num_key)
            if chunk_id: return f"[{full_citation}](/laws/{chunk_id})"
        
        norm_title = self._normalize_law_title(law_text)
        key = (norm_title, article_num)
        chunk_id = self.citation_map.get(key)
        if chunk_id: return f"[{full_citation}](/laws/{chunk_id})"

        return full_citation

    def _build_context(self, case_docs: List[Dict], global_docs: List[Dict]) -> str:
        context = "\n<<< DOKUMENTACIONI I BIZNESIT (FATURA / PASQYRA) >>>\n"
        for idx, d in enumerate(case_docs):
            snippet = d.get('text', '')[:200]
            logger.info(f"📄 Business doc {idx+1} snippet: {snippet}")
            context += f"[{d.get('source')}, FAQJA: {d.get('page')}]: {d.get('text')}\n\n"

        context += "\n<<< RREGULLORET DHE UDHËZIMET FISKALE >>>\n"
        for d in global_docs:
            law_title = d.get('law_title') or d.get('source') or "Rregullorja përkatëse"
            article_num = d.get('article_number')
            context += f"LIGJI/RREGULLORJA: {law_title}, Neni {article_num}\nPËRMBAJTJA: {d.get('text')}\n\n"
        return context

    async def chat(self, query: str, user_id: str, case_id: Optional[str] = None,
                   document_ids: Optional[List[str]] = None, jurisdiction: str = 'ks') -> AsyncGenerator[str, None]:
        if not self.llm:
            yield "Sistemi AI nuk është aktiv."
            yield AI_DISCLAIMER
            return

        from app.services import vector_store_service

        logger.info(f"🔍 Audit request: user={user_id}, client={case_id}, query='{query[:100]}...'")

        case_docs = vector_store_service.query_case_knowledge_base(
            user_id=user_id, query_text=query, case_context_id=case_id,
            document_ids=document_ids, n_results=15
        )
        
        global_docs = vector_store_service.query_global_knowledge_base(
            query_text=query, n_results=10
        )

        self._build_citation_map(global_docs)
        context_str = self._build_context(case_docs, global_docs)

        prompt = f"""
        Ti je "Senior Tax Partner & Certified Auditor". Detyra jote është të japësh një opinion ekspert mbi financat dhe taksat.
        {PROTOKOLLI_MANDATOR}
        
        **KONTEKSTI I BIZNESIT:**
        {context_str}
        
        **PYETJA E KLIENTIT:** "{query}"

        **UDHËZIM I RËNDËSISHËM:**
        - Analizo faturat dhe transaksionet e ofruara në <<< DOKUMENTACIONI I BIZNESIT >>>.
        - Identifiko përputhshmërinë me ligjet e TVSH-së dhe udhëzimet e ATK-së.
        - Nëse vëren anomali në shifra ose mospërputhje me ligjin, raportoji ato menjëherë.

        **STRUKTURA E RAPORTIT (OBLIGATIVE):**
        ### 1. ANALIZA E TRANSAKSIONEVE
        
        ### 2. PËRPUTHSHMËRIA FISKALE
        
        ### 3. REKOMANDIMET FINANCIARE
        
        Fillo auditimin tani:
        """

        buffer = ""
        try:
            async for chunk in self.llm.astream(prompt):
                if chunk.content:
                    raw = str(chunk.content)
                    buffer += raw
                    if any(p in buffer for p in ['.', '!', '?', '\n']):
                        pos = max(buffer.rfind(p) for p in ['.', '!', '?', '\n'])
                        to_send = buffer[:pos+1]
                        buffer = buffer[pos+1:]
                        yield self._format_citations(to_send)
            
            if buffer.strip():
                yield self._format_citations(buffer)
            yield AI_DISCLAIMER
        except Exception as e:
            logger.error(f"Audit Stream Failure: {e}")
            yield f"\n[Gabim Gjatë Gjenerimit: {str(e)}]"
            yield AI_DISCLAIMER

    async def fast_rag(self, query: str, user_id: str, case_id: Optional[str] = None) -> str:
        if not self.llm:
            return ""
        from app.services import vector_store_service
        l_docs = vector_store_service.query_global_knowledge_base(query_text=query, n_results=5)
        self._build_citation_map(l_docs)
        laws = "\n".join([d.get('text', '') for d in l_docs])
        prompt = f"Përgjigju shkurt si kontabilist duke përdorur citimet: {laws}\n\nPyetja: {query}"
        try:
            res = await self.llm.ainvoke(prompt)
            raw = str(res.content)
            return self._format_citations(raw)
        except Exception:
            return "Gabim teknik."