# FILE: backend/app/services/albanian_document_processor.py
# PHOENIX PROTOCOL - DOCUMENT PROCESSOR V8.0 (FISCAL AWARE)
# 1. REFACTOR: Transformed from "Legal" to "Accounting/Audit" focus.
# 2. ENHANCED: Structural separators expanded for fiscal reports (Seksioni, Pasqyra).
# 3. ACCURACY: Maintains Page-Aware chunking for precise audit trail citations.
# 4. STATUS: 100% Accounting Aligned.

import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Pydantic Model for Type Safety across the pipeline
class DocumentChunk(BaseModel):
    """Represents a single chunk of fiscal text from a business document."""
    content: str = Field(..., description="The chunked financial or regulatory text.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Fiscal metadata and page tracking.")

class EnhancedDocumentProcessor:
    """
    Advanced processor for splitting Albanian accounting and regulatory text.
    Optimized for Kosovo Tax Law, SNK Standards, and Audit Reports.
    """

    @staticmethod
    def _get_fiscal_regex_separators() -> List[str]:
        """
        Regex Patterns for Kosovo Fiscal and Regulatory Structures.
        Ensures logical breaks at chapters, articles, and financial sections.
        """
        return [
            r"(?=\nKREU\s+[IVX0-9]+)",    # Chapters
            r"(?=\nSEKSIONI\s+\d+)",      # Sections (Accounting reports)
            r"(?=\nPASQYRA\s+)",          # Financial Statements
            r"(?=\nNENI\s+\d+)",          # Articles (Tax Law)
            r"(?=\nNeni\s+\d+)",          # Articles (Casing variation)
            r"(?=\nArtikulli\s+\d+)",     # Articles (Technical variation)
            r"(?=\nDOKUMENTI\s+)",        # Document markers
            r"(?=\n\d+\.)",               # Numbered lists
            r"(?=\n[a-z]\))",             # Lettered points
            r"\n\n",                      # Paragraph breaks
            r"\.\s+",                     # Sentence breaks
        ]

    @classmethod
    def process_document(
        cls,
        text_content: str,
        document_metadata: Dict[str, Any],
        is_albanian: bool,
    ) -> List[DocumentChunk]:
        """
        Splits business text content and enriches chunks with page number tracking.
        """
        if not text_content:
            return []

        # --- PHOENIX V8: PAGE AWARE FISCAL CHUNKING ---
        # 1. Split the document by page markers generated in text_extraction_service
        page_splits = re.split(r'--- \[FAQJA (\d+)\] ---', text_content)
        
        content_by_page = {}
        # Start from index 1: split gives us [pre-text, page_num, content, page_num, content...]
        for i in range(1, len(page_splits), 2):
            try:
                page_number = int(page_splits[i])
                page_content = page_splits[i+1]
                content_by_page[page_number] = page_content
            except (ValueError, IndexError):
                continue
        
        # If no page markers were found, treat the whole document as page 1
        if not content_by_page:
            content_by_page[1] = text_content

        # --- CHUNKING CONFIGURATION ---
        # Albanian fiscal terms are often descriptive; higher chunk size captures more context
        chunk_size = 1500 if is_albanian else 1000
        chunk_overlap = 200
        
        separators = cls._get_fiscal_regex_separators() if is_albanian else ["\n\n", "\n", ". ", " "]
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            is_separator_regex=is_albanian,
            keep_separator=is_albanian,
            length_function=len
        )
        
        enriched_chunks: List[DocumentChunk] = []
        global_chunk_index = 0

        # 2. Process each page individually to maintain citation accuracy
        for page_num, page_text in content_by_page.items():
            if not page_text.strip():
                continue

            raw_chunks = text_splitter.split_text(page_text)
            
            for content in raw_chunks:
                chunk_metadata = document_metadata.copy()

                # Add critical audit-trail metadata
                chunk_metadata.update({
                    "page": page_num,
                    "chunk_index": global_chunk_index,
                    "language": "sq" if is_albanian else "en", 
                    "processor_version": "V8.0-FISCAL_AWARE",
                    "char_count": len(content)
                })

                enriched_chunks.append(
                    DocumentChunk(
                        content=content,
                        metadata=chunk_metadata
                    )
                )
                global_chunk_index += 1

        # Final pass: update total chunk count for context ranking
        total = len(enriched_chunks)
        for chunk in enriched_chunks:
            chunk.metadata["total_chunks"] = total
            
        return enriched_chunks