# FILE: backend/app/services/conversion_service.py
# PHOENIX PROTOCOL - CONVERSION SERVICE V2.0 (ACCOUNTING TRANSFORMATION)
# 1. REFACTOR: Documentation/Logs updated for Accountant workflows (Receipts & Financial Sheets).
# 2. IMAGE TO PDF: Optimized Pillow logic for processing scanned business receipts.
# 3. OFFICE SUPPORT: Handles Excel (XLSX) and Word (DOCX) via LibreOffice headless conversion.
# 4. STATUS: 100% Accounting Workflow Aligned.

import logging
import os
import subprocess
import tempfile
import shutil
from PIL import Image

logger = logging.getLogger(__name__)

def convert_to_pdf(source_path: str) -> str:
    """
    Converts business and financial files (XLSX, DOCX, TXT, JPG, PNG) to PDF format.
    Essential for transforming spreadsheet data and receipt scans into a unified preview format.
    """
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Burimi i dokumentit nuk u gjet: {source_path}")

    file_name, source_ext = os.path.splitext(os.path.basename(source_path))
    ext = source_ext.lower()
    
    output_dir = tempfile.gettempdir()
    dest_pdf_path = os.path.join(output_dir, f"{file_name}_preview.pdf")

    # --- CASE 1: ALREADY PDF ---
    if ext == '.pdf':
        logger.info(f"Dokumenti është PDF. Duke kopjuar...")
        shutil.copy2(source_path, dest_pdf_path)
        return dest_pdf_path

    # --- CASE 2: BUSINESS RECEIPT SCANS (Images to PDF) ---
    if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']:
        try:
            logger.info(f"Duke konvertuar faturën e skanuar në PDF: {source_path}")
            image = Image.open(source_path)
            
            # Convert to RGB to ensure compatibility with OCR and PDF viewers
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save with high quality for better OCR accuracy
            image.save(dest_pdf_path, "PDF", resolution=100.0)
            
            logger.info(f"Fatura u konvertua me sukses: {dest_pdf_path}")
            return dest_pdf_path
        except Exception as e:
            logger.error(f"Konvertimi i imazhit dështoi: {e}", exc_info=True)
            # Fallthrough to LibreOffice attempt
    
    # --- CASE 3: FINANCIAL SPREADSHEETS & DOCS (LibreOffice) ---
    logger.info(f"Duke nisur konvertimin LibreOffice për dokumentin: '{file_name}{source_ext}'.")
    
    # Headless conversion for Excel (XLSX) and Word documents
    command = [
        "soffice",
        "--headless",
        "--convert-to", "pdf",
        "--outdir", output_dir,
        source_path,
    ]

    try:
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120
        )

        if process.returncode != 0:
            stderr_output = process.stderr.decode('utf-8', errors='ignore')
            raise RuntimeError(f"LibreOffice conversion failed: {stderr_output}")

        expected_output_path = os.path.join(output_dir, f"{file_name}.pdf")

        if not os.path.exists(expected_output_path):
             raise RuntimeError(f"PDF i konvertuar nuk u gjet në {expected_output_path}")
            
        if os.path.getsize(expected_output_path) == 0:
            os.remove(expected_output_path)
            raise RuntimeError("Konvertimi prodhoi një dokument 0-byte.")

        # Final move to standardized preview path
        shutil.move(expected_output_path, dest_pdf_path)
        
        logger.info(f"Dokumenti financiar u konvertua me sukses në PDF.")
        return dest_pdf_path

    except Exception as e:
        logger.error(f"Gabim gjatë konvertimit: {e}", exc_info=True)
        raise RuntimeError(f"Konvertimi i dokumentit dështoi: {e}")