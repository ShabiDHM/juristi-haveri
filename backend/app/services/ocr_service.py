# FILE: backend/app/services/ocr_service.py
# PHOENIX PROTOCOL - OCR ENGINE V6.0 (ACCOUNTING TRANSFORMATION)
# 1. REFACTOR: Transformed Persona to 'Accounting OCR Specialist'.
# 2. FIX: Switched to Absolute Imports to resolve Pylance/Runtime errors.
# 3. ENHANCED: Optimized for Kosovo Fiscal Receipts (TVSH, NUI, Kupon Fiskal).
# 4. STATUS: 100% Accounting Aligned.

import pytesseract
from pytesseract import TesseractError, Output
from PIL import Image, ImageEnhance, ImageFilter
import logging
import cv2
import numpy as np
import re
import os
import io
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Callable, Match

# PHOENIX: Absolute imports for stability
from app.services.llm_service import _call_llm

logger = logging.getLogger(__name__)

# --- PHOENIX: Windows Auto-Configuration ---
if os.name == 'nt':
    possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Users\Shaban\AppData\Local\Tesseract-OCR\tesseract.exe'
    ]
    for path in possible_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            logger.info(f"✅ Tesseract found at: {path}")
            break

# --- KOSOVO ACCOUNTING CONFIGURATION ---
INVOICE_LANGUAGES = ['sqi', 'eng']
FALLBACK_LANGUAGE = 'eng'

# Keywords identifying fiscal importance
INVOICE_KEYWORDS = {
    'sq': ['total', 'shuma', 'data', 'faturë', 'kupon', 'tvsh', 'zbritje', 'pagesë', 'çmimi', 'numri fiskal', 'nui'],
    'en': ['total', 'amount', 'sum', 'vat', 'date', 'invoice', 'receipt', 'tax', 'subtotal', 'fiscal', 'nui'],
}

DATE_PATTERNS = [
    r'\b\d{1,2}\.\d{1,2}\.\d{2,4}\b',
    r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
]

AMOUNT_PATTERNS = [
    r'(?:total|shuma|toti|tota)[:\s]*([\d\.,]+\s*(?:€|eur|lek|n|N))',
    r'([\d\.,]+\s*(?:€|eur|lek|n|N))\s*(?:total|shuma)?',
    r'\b(\d+[\.,]\d{2})\b',
]

KOSOVO_MERCHANTS = [
    'SPAR', 'VIVA Fresh', 'ALBI', 'IPKO', 'VALA', 'Gjirafa',
    'TELEKOM', 'MERIDIAN', 'TEB', 'BKT', 'NLB', 'RAIFFEISEN',
    'MAXI', 'SUPER VIVA', 'GLOBAL', 'EUROPI', 'PRISHTINA',
    'SPARKOSOVA', 'SPAR KOSOVA'
]

FISCAL_PATTERNS = [
    r'(?:NUI|Nr\.\s*Fiskal|NF)[:\-]?\s*(\d{9,13})',
    r'Fiskal\s*[Nn]r[:\s]*(\d{9,13})',
    r'Fiscal\s*[Nn]o[:\s]*(\d{9,13})',
]

class SmartOCRResult:
    """Container for enhanced Accounting OCR results."""
    def __init__(self, text: str, confidence: float = 0.0, metadata: Optional[Dict[str, Any]] = None):
        self.text = text
        self.confidence = confidence
        self.metadata = metadata if metadata is not None else {}
        self.structured_data: Dict[str, Any] = {}
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            'confidence': self.confidence,
            'metadata': self.metadata,
            'structured_data': self.structured_data
        }

def detect_image_type(pil_image: Image.Image) -> str:
    """Detect if image is likely a financial receipt."""
    width, height = pil_image.size
    aspect_ratio = width / height
    return "receipt" if aspect_ratio > 2.0 else "document"

def enhance_for_kosovo_receipts(image_np: np.ndarray) -> np.ndarray:
    """Preprocessing for Kosovo thermal receipts (fixes low contrast)."""
    if len(image_np.shape) == 3:
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    else:
        gray = image_np
    
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    denoised = cv2.fastNlMeansDenoising(enhanced, h=20)
    
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(denoised, -1, kernel)
    
    return cv2.adaptiveThreshold(
        sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )

def run_tesseract_with_confidence(image: Image.Image, lang: str = 'sqi+eng', psm: int = 6) -> Tuple[str, float]:
    """Run Tesseract with Accounting data validation."""
    try:
        data = pytesseract.image_to_data(image, lang=lang, config=f'--oem 3 --psm {psm}', output_type=Output.DICT)
        confidences = [float(conf) for conf in data['conf'] if conf != '-1']
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        text = ' '.join([word for i, word in enumerate(data['text']) if int(data['conf'][i]) > 60])
        return text, avg_confidence / 100.0
    except Exception as e:
        logger.error(f"Tesseract confidence error: {e}")
        return pytesseract.image_to_string(image, lang=lang, config=f'--oem 3 --psm {psm}'), 0.5

def find_best_psm_for_invoice(image: Image.Image) -> int:
    """Selects the best PSM mode based on financial keyword detection."""
    test_psms = [6, 3, 11, 12, 4]
    best_text = ""
    best_psm = 6
    
    for psm in test_psms:
        try:
            text = pytesseract.image_to_string(image, lang='sqi+eng', config=f'--oem 3 --psm {psm}')
            score = 0
            text_lower = text.lower()
            for lang_keywords in INVOICE_KEYWORDS.values():
                for kw in lang_keywords:
                    if kw in text_lower: score += 1
            
            if score > 0 and len(text) > len(best_text) * 0.8:
                best_text = text
                best_psm = psm
                if score > 10: break
        except: continue
    
    return best_psm

def ai_correct_ocr_text(ocr_text: str, image_type: str = "receipt") -> str:
    """Uses the Financial LLM Persona to correct OCR artifacts in receipts."""
    corrected = rule_based_correction(ocr_text)
    
    correction_prompt = f"""
    Ti je një Kontabilist Ekspert. Korrigjo gabimet e OCR në këtë kupon fiskal të Kosovës.
    SIGUROHU: Totali dhe TVSH-ja të jenë logjike.
    
    TEKSTI OCR:
    {corrected}
    
    Kthe tekstin e pastër dhe të saktësuar.
    """
    
    try:
        llm_corrected = _call_llm(
            "Accounting OCR Correction",
            correction_prompt,
            json_mode=False,
            temp=0.1
        )
        if llm_corrected and len(llm_corrected) > len(corrected) * 0.5:
            return llm_corrected.strip()
    except Exception as e:
        logger.warning(f"AI OCR correction failed: {e}")
    
    return corrected

def rule_based_correction(text: str) -> str:
    """Heuristic correction for common Kosovo thermal printer errors."""
    if not text: return text
    
    # Merchant & Product logic
    text = re.sub(r'SPARKOSOVA', 'SPAR KOSOVA', text, flags=re.IGNORECASE)
    text = re.sub(r'\bKate\b', 'Kafe', text, flags=re.IGNORECASE)
    text = re.sub(r'\bUj\b', 'Ujë', text, flags=re.IGNORECASE)
    
    # Financial symbols
    text = re.sub(r'TOTAL\s+(\d{2})(\d{2})N', r'TOTALI: \1.\2€', text, flags=re.IGNORECASE)
    text = re.sub(r'\bN\b', '€', text)
    
    # Time vs Date smart correction
    def fix_time_smart(match: re.Match) -> str:
        full_text = match.string
        start_pos = match.start()
        if start_pos >= 4:
            lookback = full_text[max(0, start_pos-10):start_pos]
            if re.search(r'\.\d{4}$', lookback): return match.group(0) # It's a year
        
        hours, minutes = match.group(1), match.group(2)
        if int(hours) < 24 and int(minutes) < 60: return f'{hours}:{minutes}'
        return match.group(0)
    
    text = re.sub(r'(?<!\d)(\d{2})(\d{2})\b(?!\d)', fix_time_smart, text)
    
    # Spacing and normalization
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(\d)\s*x\s*(\d)', r'\1 x \2', text)
    
    return text.strip()

def extract_structured_data_from_text(text: str) -> Dict[str, Any]:
    """Parses raw text into an Accounting Data Schema."""
    structured = {
        'total_amount': None,
        'date': None,
        'vat_number': None,
        'fiscal_number': None,
        'merchant': '',
        'items': [],
        'currency': '€'
    }
    
    text_lower = text.lower()
    
    # 1. Total Amount
    for pattern in [r'TOTALI?[:\s]*([\d\.,]+)\s*[€]', r'TOTALI?[:\s]*(\d+[\.\,]\d{2})']:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                structured['total_amount'] = float(match.group(1).replace(',', '.'))
                break
            except: continue
    
    # 2. Date
    date_match = re.search(r'\b(\d{1,2}\.\d{1,2}\.\d{4})\b', text)
    if date_match:
        try:
            d, m, y = date_match.group(1).split('.')
            structured['date'] = f"{y}-{m}-{d}"
        except: structured['date'] = date_match.group(1)
    
    # 3. Fiscal/NUI
    for pattern in FISCAL_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            structured['fiscal_number'] = match.group(1)
            break
    
    # 4. Merchant
    for merchant in KOSOVO_MERCHANTS:
        if merchant.lower() in text_lower:
            structured['merchant'] = merchant
            break
            
    return structured

def multi_strategy_ocr(image: Image.Image) -> SmartOCRResult:
    """Executes thermal-optimized and standard strategies to find the best result."""
    strategies = []
    
    # Standard
    try:
        psm = find_best_psm_for_invoice(image)
        t, c = run_tesseract_with_confidence(image, 'sqi+eng', psm)
        strategies.append({'text': t, 'confidence': c, 'strategy': 'standard'})
    except: pass
    
    # Thermal
    try:
        enhanced = Image.fromarray(enhance_for_kosovo_receipts(np.array(image)))
        t, c = run_tesseract_with_confidence(enhanced, 'sqi+eng', 6)
        strategies.append({'text': t, 'confidence': c, 'strategy': 'thermal'})
    except: pass
    
    if not strategies: return SmartOCRResult("", 0.0, {'error': 'OCR failed'})
    
    best = max(strategies, key=lambda x: x['confidence'])
    corrected = rule_based_correction(best['text'])
    
    res = SmartOCRResult(text=corrected, confidence=best['confidence'], metadata={'market': 'Kosovo'})
    res.structured_data = extract_structured_data_from_text(corrected)
    return res

def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    """Main binary entry point for the Accounting pipeline."""
    try:
        original_image = Image.open(io.BytesIO(image_bytes))
        result = multi_strategy_ocr(original_image)
        logger.info(f"✅ Fiscal OCR Success: {len(result.text)} chars. Total: {result.structured_data.get('total_amount')}€")
        return result.text
    except Exception as e:
        logger.error(f"❌ OCR failed: {e}")
        return ""

def extract_text_from_image(file_path: str) -> str:
    """Disk entry point."""
    if not os.path.exists(file_path): return ""
    try:
        return multi_strategy_ocr(Image.open(file_path)).text
    except: return ""

def extract_expense_data_from_image(image_bytes: bytes) -> Dict[str, Any]:
    """Helper for the Business Center expense tracker."""
    try:
        result = multi_strategy_ocr(Image.open(io.BytesIO(image_bytes)))
        return {
            'success': True,
            'text': result.text,
            'structured_data': result.structured_data,
            'confidence': result.confidence
        }
    except: return {'success': False}

__all__ = [
    'extract_text_from_image_bytes',
    'extract_text_from_image',
    'extract_expense_data_from_image',
    'multi_strategy_ocr',
    'SmartOCRResult',
    'extract_structured_data_from_text',
    'rule_based_correction',
    'ai_correct_ocr_text'
]