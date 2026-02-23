# FILE: backend/app/services/albanian_ner_service.py
# PHOENIX PROTOCOL - NER ENGINE V5.0 (ACCOUNTING TRANSFORMATION)
# 1. REFACTOR: Prompt pivoted to Financial and Accounting document extraction.
# 2. ENHANCED: Added FISCAL_NUMBER (NUI) and INVOICE_NUMBER to entity detection.
# 3. ANONYMIZATION: Updated placeholders for fiscal data protection.
# 4. STATUS: 100% Accounting Aligned.

import os
import httpx
import json
import logging
from typing import List, Tuple, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "deepseek/deepseek-chat"

# Legacy/Local Core
AI_CORE_URL = os.getenv("AI_CORE_URL", "http://ai-core-service:8000")

class AlbanianNERService:
    """
    Service responsible for detecting Named Entities (PII) in financial documents.
    Tier 1: DeepSeek V3 (Cloud) - Optimized for Accounting context.
    Tier 2: Kontabilisti AI Core (Local Spacy)
    """
    def __init__(self):
        self.timeout = 15.0
        
        if DEEPSEEK_API_KEY:
            self.client = OpenAI(
                api_key=DEEPSEEK_API_KEY,
                base_url=OPENROUTER_BASE_URL
            )
        else:
            self.client = None

    def _extract_with_deepseek(self, text: str) -> Optional[List[dict]]:
        """
        Uses DeepSeek to extract accounting-related entities.
        """
        if not self.client: return None

        truncated_text = text[:10000]

        system_prompt = """
        Ti je një ekspert i Nxjerrjes së Entiteteve (NER) për dokumente financiare dhe kontabël shqipe.
        
        DETYRA:
        Identifiko entitetet specifike në tekstin e dhënë dhe ktheji në format JSON.
        
        KATEGORITË:
        - PERSON: Emra njerëzish (p.sh. "Agim Gashi", "Pronari").
        - ORGANIZATION: Biznese, banka, ATK, kompani (p.sh. "Banka Kombëtare", "ABC Sh.p.k").
        - FISCAL_NUMBER: NUI ose Numri Fiskal (9 shifra).
        - INVOICE_NUMBER: Referenca e faturës ose dokumentit.
        - MONEY: Shuma monetare dhe TVSH (p.sh. "500 Euro", "18% TVSH").
        - DATE: Data e lëshimit apo pagesës.
        - LOCATION: Adresa të bizneseve.

        FORMATI:
        [
          {"text": "ABC Sh.p.k", "label": "ORGANIZATION"},
          {"text": "810123456", "label": "FISCAL_NUMBER"}
        ]
        
        Përgjigju VETËM me JSON valid.
        """

        try:
            response = self.client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": truncated_text}
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
                extra_headers={
                    "HTTP-Referer": "https://kontabilisti.tech", 
                    "X-Title": "Kontabilisti AI NER"
                }
            )
            
            content = response.choices[0].message.content
            if not content: return None
            
            data = json.loads(content)
            
            if isinstance(data, dict):
                for key in data:
                    if isinstance(data[key], list): return data[key]
                return []
            elif isinstance(data, list):
                return data
                
        except Exception as e:
            logger.warning(f"⚠️ DeepSeek NER Failed: {e}")
            return None
        return None

    def _extract_with_local_core(self, text: str) -> List[dict]:
        """Fallback to local microservice."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{AI_CORE_URL}/ner/extract",
                    json={"text": text}
                )
                response.raise_for_status()
                data = response.json()
                return data.get("entities", [])
        except Exception as e:
            logger.error(f"❌ Local Core NER Failed: {e}")
            return []

    def extract_entities(self, text: str) -> List[Tuple[str, str, int]]:
        """
        Main entry point for entity extraction.
        Returns: List of (entity_text, entity_label, start_char_index).
        """
        if not text: return []
        
        # 1. Try DeepSeek
        raw_entities = self._extract_with_deepseek(text)
        
        # 2. Fallback to Local
        if raw_entities is None:
            raw_entities = self._extract_with_local_core(text)
            
        if not raw_entities:
            return []

        results = []
        for ent in raw_entities:
            name = ent.get("text", "").strip()
            label = ent.get("label", "UNKNOWN").upper()
            
            if not name: continue
            
            start_index = text.find(name)
            
            # Map common variations to standard fiscal labels
            if label in ["ORG", "BIZNES"]: label = "ORGANIZATION"
            if label in ["PER", "KLIENT"]: label = "PERSON"
            if label in ["NUI", "NR_FISKAL"]: label = "FISCAL_NUMBER"
            if label in ["FATURA", "NR_DOK"]: label = "INVOICE_NUMBER"
            
            if start_index != -1:
                results.append((name, label, start_index))
                
        return results
    
    def get_albanian_placeholder(self, entity_label: str) -> str:
        """ Maps the entity label to a financial/fiscal placeholder. """
        placeholders = {
            "PER": "[EMRI_PERSONI_ANONIMIZUAR]",
            "PERSON": "[EMRI_PERSONI_ANONIMIZUAR]",
            "ORG": "[BIZNES_ANONIMIZUAR]",
            "ORGANIZATION": "[BIZNES_ANONIMIZUAR]",
            "FISCAL_NUMBER": "[NUMRI_FISKAL_ANONIMIZUAR]",
            "INVOICE_NUMBER": "[NUMRI_DOKUMENTIT_ANONIMIZUAR]",
            "DATE": "[DATA_ANONIMIZUAR]",
            "MONEY": "[VLERA_MONETARE_ANONIMIZUAR]",
        }
        return placeholders.get(entity_label.upper(), f"[{entity_label}_ANONIMIZUAR]")
        
# --- Global Instance ---
ALBANIAN_NER_SERVICE = AlbanianNERService()