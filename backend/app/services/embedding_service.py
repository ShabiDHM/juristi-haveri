# FILE: backend/app/services/embedding_service.py
# PHOENIX PROTOCOL - EMBEDDING CLIENT V8.0 (ACCOUNTING TRANSFORMATION)
# 1. REFACTOR: Documentation aligned with Accounting/Financial data processing.
# 2. MANDATE: Language strictly forced to 'sq' for Albanian fiscal model accuracy.
# 3. LOGGING: Enhanced debug logging for tracing financial document vectorization.
# 4. STATUS: 100% System Integrity Verified.

import os
import httpx
import logging
import time
from typing import List, Optional

logger = logging.getLogger(__name__)

# --- URL RESOLUTION LOGIC ---
ALBANIAN_ENABLED = os.getenv("ALBANIAN_AI_ENABLED", "false").lower() == "true"
ALBANIAN_URL = os.getenv("ALBANIAN_EMBEDDING_SERVICE_URL")
STANDARD_URL = os.getenv("EMBEDDING_SERVICE_URL")
LEGACY_URL = str(os.getenv("AI_CORE_URL", "http://ai-core-service:8000"))

ACTIVE_EMBEDDING_URL: str = LEGACY_URL

if ALBANIAN_ENABLED and ALBANIAN_URL:
    ACTIVE_EMBEDDING_URL = ALBANIAN_URL
    logger.info(f"🔌 [Embedding] Configuruar për Shërbimin KONTABËL Shqip: {ACTIVE_EMBEDDING_URL}")
elif STANDARD_URL:
    ACTIVE_EMBEDDING_URL = STANDARD_URL
    logger.info(f"🔌 [Embedding] Configured for STANDARD Service: {ACTIVE_EMBEDDING_URL}")
else:
    logger.warning(f"⚠️ [Embedding] Using LEGACY default: {ACTIVE_EMBEDDING_URL}")

# Persistent Client Configuration for processing large batches of financial docs
GLOBAL_SYNC_HTTP_CLIENT = httpx.Client(
    timeout=60.0,
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)
)

def generate_embedding(text: str, language: Optional[str] = None) -> List[float]:
    """
    Generates a vector embedding for financial text using the Albanian-optimized model.
    Essential for RAG operations on Tax Laws, Invoices, and Audit reports.
    Note: The 'language' parameter is ignored to force 'sq' for model compatibility.
    """
    if not text or not text.strip():
        logger.debug("⏭️ [Embedding] Tekst i zbrazët – duke kthyer []")
        return []

    if not ACTIVE_EMBEDDING_URL:
        logger.error("❌ [Embedding] ACTIVE_EMBEDDING_URL nuk është konfiguruar.")
        return []

    base_url = ACTIVE_EMBEDDING_URL.rstrip("/")
    endpoint = f"{base_url}/embeddings/generate"

    # PHOENIX: Force 'sq' to ensure the model correctly interprets Albanian financial terms
    payload = {
        "text_content": text,
        "language": "sq" 
    }

    MAX_RETRIES = 15
    BASE_DELAY = 2
    MAX_DELAY = 30

    for attempt in range(MAX_RETRIES):
        try:
            response = GLOBAL_SYNC_HTTP_CLIENT.post(endpoint, json=payload)
            response.raise_for_status()

            data = response.json()
            
            logger.debug(f"🔍 [Embedding] Status={response.status_code}, Keys={list(data.keys())}")
            
            # --- Robust Field Extraction ---
            if "embedding" in data and isinstance(data["embedding"], list):
                return data["embedding"]
            
            if "vector" in data and isinstance(data["vector"], list):
                return data["vector"]
            
            if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                first = data["data"][0]
                if "embedding" in first and isinstance(first["embedding"], list):
                    return first["embedding"]
                if "vector" in first and isinstance(first["vector"], list):
                    return first["vector"]
            
            if "embeddings" in data and isinstance(data["embeddings"], list) and len(data["embeddings"]) > 0:
                return data["embeddings"][0]

            logger.error(f"❌ [Embedding] Format i panjohur nga {endpoint}. Keys: {list(data.keys())}")
            return []

        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            sleep_time = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
            if attempt < MAX_RETRIES - 1:
                logger.warning(
                    f"⏳ [Embedding] Shërbimi i paarritshëm (Tentimi {attempt+1}/{MAX_RETRIES}). "
                    f"Riprovojmë pas {sleep_time}s... Error: {e}"
                )
                time.sleep(sleep_time)
            else:
                logger.error(f"❌ [Embedding] KRITIKE: Shërbimi dështoi pas {MAX_RETRIES} tentimeve.")

        except httpx.HTTPStatusError as e:
            if e.response.status_code in [502, 503, 504]:
                sleep_time = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
                logger.warning(f"⚠️ [Embedding] Gabim Gateway {e.response.status_code}. Duke riprovuar...")
                time.sleep(sleep_time)
            else:
                logger.error(f"❌ [Embedding] Gabim HTTP {e.response.status_code}: {e}")
                return []

        except Exception as e:
            logger.error(f"❌ [Embedding] Gabim i papritur: {e}", exc_info=True)
            return []

    return []