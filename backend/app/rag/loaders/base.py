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
    Extract structured metadata from comment headers or heuristics:
    Example:
    # SEBI Circular: Categorization of Mutual Funds
    # Organization: SEBI
    # Document Type: Circular
    # Topic: mutual_funds
    # Asset Class: equity
    # Publication Date: 2024-01-01
    """
    lines = raw_text.splitlines()
    org = "Regulatory Authority"
    doc_type = "guidelines"
    topic = "general_finance"
    asset_class = "all"
    pub_date: Optional[str] = None
    title = file_path.stem.replace("_", " ").title()

    for line in lines[:20]:
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
        elif lower.startswith("publication date:"):
            pub_date = line_clean.split(":", 1)[1].strip()
        elif lower.startswith("title:") or (not title and len(line_clean) > 5):
            title = line_clean.split(":", 1)[1].strip() if ":" in line_clean else line_clean

    return DocumentMetadata(
        title=title,
        source=file_path.name,
        organization=org,
        document_type=doc_type,
        topic=topic,
        asset_class=asset_class,
        publication_date=pub_date,
    )


class DocumentLoader(ABC):
    """Abstract interface for format-specific document loaders."""

    @abstractmethod
    def load(self, file_path: Path) -> LoadedDocument:
        """Load and extract text and metadata from a file."""
        pass
