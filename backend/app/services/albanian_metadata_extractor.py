# FILE: backend/app/services/albanian_metadata_extractor.py
# PHOENIX PROTOCOL - METADATA EXTRACTOR V6.0 (ACCOUNTING TRANSFORMATION)
# 1. REFACTOR: Transformed from "Legal Specialist" to "Fiscal & Audit Specialist".
# 2. SCHEMA: Optimized to extract NUI (Fiscal Number), Invoice Numbers, and Tax Periods.
# 3. JURISDICTION: Strict focus on Kosovo ATK (Tax Administration) and Banking standards.
# 4. STATUS: 100% Accounting Aligned.

import re
import logging
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from openai import OpenAI

logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "deepseek/deepseek-chat"

class AlbanianMetadataExtractor:
    def __init__(self):
        if DEEPSEEK_API_KEY:
            self.client = OpenAI(
                api_key=DEEPSEEK_API_KEY,
                base_url=OPENROUTER_BASE_URL
            )
        else:
            self.client = None

        # Tier 2: Regex Patterns (Accounting Optimized)
        self.patterns = {
            'fiscal_number': re.compile(r'(NUI|Nr\.\s*Fiskal|NF)[:\-]?\s*(\d{9})', re.IGNORECASE),
            'invoice_ref': re.compile(r'(Fatura|Invoice|Nr\.\s*Dokumentit)[:\-]?\s*([\w\-\/]+)', re.IGNORECASE),
            'date': re.compile(r'(\d{1,2}\s+(Janar|Shkurt|Mars|Prill|Maj|Qershor|Korrik|Gusht|Shtator|Tetor|Nëntor|Dhjetor)\s+\d{4})', re.IGNORECASE),
            'amount': re.compile(r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*(€|EUR|euro)', re.IGNORECASE),
            'business_entity': re.compile(r'(Sh\.p\.k|L\.L\.C|B\.I|O\.P)[:\-]?\s*([\w\s]+)', re.IGNORECASE),
            'institution': re.compile(r'(ATK|Administrata\s+Tatimore|Banka\s+[\w\s]+|Dogana)', re.IGNORECASE),
        }
        
        logger.info("✅ Kosovo Fiscal Metadata Extractor V6.0 Initialized")

    def _extract_with_deepseek(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Tier 1: Semantic Extraction using DeepSeek V3 (Accounting Context).
        """
        if not self.client: return None

        truncated_text = text[:15000] 

        system_prompt = """
        Ti je "Specialist i Analizës Fiskale" për Republikën e Kosovës.
        
        DETYRA:
        Identifiko të dhënat kontabël (Metadata) nga dokumenti financiar.
        
        FUSHAT E KËRKUARA (JSON):
        - business_name: Emri i Biznesit/Klientit (psh. "ABC Sh.p.k").
        - fiscal_number: Numri Fiskal ose NUI (9 shifra).
        - document_number: Numri i faturës ose referenca e deklaratës.
        - entities: Lista e subjekteve të përfshira (Furnitori, Blerësi).
        - document_type: Lloji (Faturë, Deklaratë TVSH, Pasqyrë Bankare, Kontratë Pune).
        - date: Data e lëshimit.
        - total_amount: Vlera totale me TVSH.
        - vat_amount: Shuma e TVSH-së (nëse specifikohet).
        - fiscal_period: Periudha (psh. "TM1 2026" ose "Janar 2026").
        - jurisdiction_check: "KOSOVË" ose "E HUAJ".
        
        RREGULLA:
        - Fokusohu te përputhshmëria me ATK-në.
        - Përgjigju VETËM me JSON valid.
        """

        try:
            response = self.client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"DOKUMENTI FINANCIAR:\n{truncated_text}"}
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
                extra_headers={
                    "HTTP-Referer": "https://kontabilisti.tech", 
                    "X-Title": "Kontabilisti AI Fiscal Metadata"
                }
            )
            
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
                
        except Exception as e:
            logger.warning(f"⚠️ DeepSeek Fiscal Extraction Failed: {e}")
            return None
        return None

    def _extract_with_regex(self, text: str) -> Dict[str, Any]:
        """
        Tier 2: Regex Backup (Accounting focus).
        """
        metadata = {}
        
        match = self.patterns['fiscal_number'].search(text)
        if match: metadata['fiscal_number'] = match.group(2)
        
        match = self.patterns['invoice_ref'].search(text)
        if match: metadata['document_number'] = match.group(2)
        
        match = self.patterns['amount'].search(text)
        if match: metadata['total_amount'] = f"{match.group(1)} {match.group(2)}"
        
        match = self.patterns['institution'].search(text)
        if match: metadata['institution'] = match.group(0)
        
        return metadata

    def extract(self, text: str, document_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Main extraction pipeline for accounting documents.
        """
        if not text:
            return {}
        
        # 1. Semantic Extraction
        metadata = self._extract_with_deepseek(text)
        
        # 2. Fallback
        if not metadata:
            logger.info("Falling back to Regex Fiscal Extraction")
            metadata = self._extract_with_regex(text)
        
        # Standardize Output (Accounting Schema)
        result = {
            "document_id": document_id,
            "extraction_timestamp": datetime.now().isoformat(),
            "business_name": metadata.get("business_name"),
            "fiscal_number": metadata.get("fiscal_number"),
            "document_number": metadata.get("document_number"),
            "entities": metadata.get("entities", []),
            "document_type": metadata.get("document_type"),
            "total_amount": metadata.get("total_amount"),
            "vat_amount": metadata.get("vat_amount"),
            "date": metadata.get("date"),
            "fiscal_period": metadata.get("fiscal_period"),
            "jurisdiction": metadata.get("jurisdiction_check", "UNKNOWN")
        }
        
        return result

# Global Instance
albanian_metadata_extractor = AlbanianMetadataExtractor()