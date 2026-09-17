import re
from typing import Any, Dict, List, Optional, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings
from app.rag.schemas import ChunkMetadata, LoadedDocument


class SectionAwareChunker:
    """
    RAG 2.0 Section-Aware Smart Chunker.
    Identifies statutory headings, sections, subsections, and page breaks,
    preserving granular provenance and avoiding mid-clause sentence truncation.
    """

    def __init__(
        self,
        chunk_size: int = settings.RAG_CHUNK_SIZE,
        chunk_overlap: int = settings.RAG_CHUNK_OVERLAP,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", "; ", ", ", " "],
            keep_separator=True,
        )

    def _extract_page_number(self, text: str) -> Optional[int]:
        """Check for page boundary markers like '--- Page 3 ---' or '[Page 3]'."""
        page_match = re.search(r"(?:---|\[)\s*Page\s*(\d+)\s*(?:---|\])", text, re.IGNORECASE)
        if page_match:
            try:
                return int(page_match.group(1))
            except ValueError:
                pass
        return None

    def _parse_sections(self, content: str) -> List[Dict[str, Any]]:
        """
        Split document content into structured section/subsection blocks with hierarchy.
        """
        lines = content.split("\n")
        sections: List[Dict[str, Any]] = []

        current_section = "General Overview"
        current_subsection: Optional[str] = None
        current_page: Optional[int] = 1
        current_paragraphs: List[str] = []
        para_idx = 0

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                if current_paragraphs:
                    current_paragraphs.append("")
                continue

            # Check for page number marker
            detected_page = self._extract_page_number(trimmed)
            if detected_page is not None:
                current_page = detected_page
                continue

            # Check for main Section Heading (e.g. "## Section 1: Executive Summary", "# 1. Overview", "Section 1: ...")
            sec_match = re.match(r"^(?:#{1,2}\s+)?(?:Section\s+\d+:?|\d+\.\s+)(.+)$", trimmed, re.IGNORECASE)
            # Check for Subsection Heading (e.g. "### Subsection 2.1: Large Cap", "a) Large Cap Fund:", "Subsection 1.1:")
            subsec_match = re.match(r"^(?:#{3,4}\s+)?(?:Subsection\s+[\d\.]+:?|[a-z]\)\s+)(.+)$", trimmed, re.IGNORECASE)

            if sec_match and not trimmed.startswith("###"):
                if current_paragraphs:
                    block_text = "\n".join(current_paragraphs).strip()
                    if block_text:
                        sections.append({
                            "section": current_section,
                            "subsection": current_subsection,
                            "page_number": current_page,
                            "paragraph_index": para_idx,
                            "text": block_text,
                        })
                        para_idx += 1
                    current_paragraphs = []
                current_section = sec_match.group(1).strip().strip(":")
                current_subsection = None

            elif subsec_match:
                if current_paragraphs:
                    block_text = "\n".join(current_paragraphs).strip()
                    if block_text:
                        sections.append({
                            "section": current_section,
                            "subsection": current_subsection,
                            "page_number": current_page,
                            "paragraph_index": para_idx,
                            "text": block_text,
                        })
                        para_idx += 1
                    current_paragraphs = []
                current_subsection = subsec_match.group(1).strip().strip(":")

            else:
                current_paragraphs.append(trimmed)

        # Flush final block
        if current_paragraphs:
            block_text = "\n".join(current_paragraphs).strip()
            if block_text:
                sections.append({
                    "section": current_section,
                    "subsection": current_subsection,
                    "page_number": current_page,
                    "paragraph_index": para_idx,
                    "text": block_text,
                })

        return sections

    def chunk_document(self, doc: LoadedDocument) -> List[Dict[str, Any]]:
        """
        Split a LoadedDocument into section-aware chunks with full provenance metadata.
        Returns a list of chunk dicts.
        """
        raw_sections = self._parse_sections(doc.content)
        if not raw_sections:
            # Fallback if no sections detected
            raw_sections = [{
                "section": doc.metadata.title,
                "subsection": None,
                "page_number": 1,
                "paragraph_index": 0,
                "text": doc.content,
            }]

        processed_chunks: List[Dict[str, Any]] = []
        global_chunk_idx = 0

        for sec_block in raw_sections:
            text = sec_block["text"]
            if not text:
                continue

            # Split text within the section boundary
            sub_chunks = self.text_splitter.split_text(text)
            for sub_text in sub_chunks:
                cleaned_text = sub_text.strip()
                if not cleaned_text:
                    continue

                chunk_meta = ChunkMetadata(
                    source=doc.metadata.source,
                    organization=doc.metadata.organization,
                    document_type=doc.metadata.document_type,
                    topic=doc.metadata.topic,
                    asset_class=doc.metadata.asset_class,
                    product_type=doc.metadata.product_type,
                    jurisdiction=doc.metadata.jurisdiction,
                    publication_date=doc.metadata.publication_date,
                    effective_date=doc.metadata.effective_date,
                    source_url=doc.metadata.source_url,
                    version=doc.metadata.version,
                    is_active=doc.metadata.is_active,
                    section=sec_block["section"],
                    subsection=sec_block["subsection"],
                    page_number=sec_block["page_number"],
                    paragraph_index=sec_block["paragraph_index"],
                    chunk_index=global_chunk_idx,
                    char_count=len(cleaned_text),
                )

                processed_chunks.append({
                    "chunk_index": global_chunk_idx,
                    "section": sec_block["section"],
                    "subsection": sec_block["subsection"],
                    "page_number": sec_block["page_number"],
                    "paragraph_index": sec_block["paragraph_index"],
                    "content": cleaned_text,
                    "metadata": chunk_meta.model_dump(),
                })
                global_chunk_idx += 1

        return processed_chunks


# Backward compatibility alias
DocumentChunker = SectionAwareChunker

