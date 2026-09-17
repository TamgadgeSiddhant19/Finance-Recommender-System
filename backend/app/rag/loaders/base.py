from abc import ABC, abstractmethod
import hashlib
from pathlib import Path
import re
from typing import Optional
from app.rag.schemas import DocumentMetadata, LoadedDocument


def clean_text(raw_text: str) -> str:
    """
    Clean raw extracted document text:
    - Normalizes unicode whitespace
    - Strips control characters
    - Trims each line and collapses consecutive blank lines
    """
    if not raw_text:
        return ""
    # Normalize carriage returns and tabs
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")
    # Remove control characters except standard whitespace
    text = "".join(ch for ch in text if ch.isprintable() or ch in "\n ")
    # Strip line-by-line whitespace
    lines = [re.sub(r"[ ]+", " ", line).strip() for line in text.split("\n")]
    text = "\n".join(lines)
    # Collapse more than 2 consecutive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file for idempotent change detection."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def extract_metadata_from_text(raw_text: str, file_path: Path) -> DocumentMetadata:
    """
    Extract structured metadata from comment headers, XML/HTML tags, or directory heuristics.
    """
    lines = raw_text.splitlines()
    parent_dir = file_path.parent.name.lower()

    # Directory-based authoritative organization inference
    org_mapping = {
        "sebi": "SEBI",
        "rbi": "RBI",
        "cbdt": "CBDT",
        "pfrda": "PFRDA",
        "amfi": "AMFI",
        "irdai": "IRDAI",
        "financial_education": "Investor Education",
    }
    org = org_mapping.get(parent_dir, "Regulatory Authority")
    doc_type = "guidelines"
    topic = "general_finance"
    asset_class = "all"
    product_type: Optional[str] = None
    jurisdiction = "IN"
    pub_date: Optional[str] = None
    effective_date: Optional[str] = None
    source_url: Optional[str] = None
    version = "1.0"
    last_updated: Optional[str] = None
    is_active = True
    title = file_path.stem.replace("_", " ").title()

    for line in lines[:30]:
        line_clean = line.strip().lstrip("#/*<!--").rstrip("-->*/").strip()
        if not line_clean:
            continue

        lower = line_clean.lower()
        if lower.startswith("organization:"):
            org = line_clean.split(":", 1)[1].strip()
        elif lower.startswith("document type:"):
            doc_type = line_clean.split(":", 1)[1].strip().lower().replace(" ", "_")
        elif lower.startswith("topic:"):
            topic = line_clean.split(":", 1)[1].strip().lower().replace(" ", "_")
        elif lower.startswith("asset class:"):
            asset_class = line_clean.split(":", 1)[1].strip().lower().replace(" ", "_")
        elif lower.startswith("product type:"):
            product_type = line_clean.split(":", 1)[1].strip().lower().replace(" ", "_")
        elif lower.startswith("jurisdiction:"):
            jurisdiction = line_clean.split(":", 1)[1].strip().upper()
        elif lower.startswith("publication date:"):
            pub_date = line_clean.split(":", 1)[1].strip()
        elif lower.startswith("effective date:"):
            effective_date = line_clean.split(":", 1)[1].strip()
        elif lower.startswith("source url:") or lower.startswith("source_url:"):
            source_url = line_clean.split(":", 1)[1].strip()
        elif lower.startswith("version:"):
            version = line_clean.split(":", 1)[1].strip()
        elif lower.startswith("last updated:") or lower.startswith("last_updated:"):
            last_updated = line_clean.split(":", 1)[1].strip()
        elif lower.startswith("is active:") or lower.startswith("is_active:"):
            is_active = line_clean.split(":", 1)[1].strip().lower() in ("true", "1", "yes")
        elif lower.startswith("title:") or (not title and len(line_clean) > 5):
            title = line_clean.split(":", 1)[1].strip() if ":" in line_clean else line_clean

    return DocumentMetadata(
        title=title,
        source=file_path.name,
        organization=org,
        document_type=doc_type,
        topic=topic,
        asset_class=asset_class,
        product_type=product_type,
        jurisdiction=jurisdiction,
        publication_date=pub_date,
        effective_date=effective_date,
        source_url=source_url,
        version=version,
        last_updated=last_updated,
        is_active=is_active,
    )


class DocumentLoader(ABC):
    """Abstract interface for format-specific document loaders."""

    @abstractmethod
    def load(self, file_path: Path) -> LoadedDocument:
        """Load and extract text and metadata from a file."""
        pass
