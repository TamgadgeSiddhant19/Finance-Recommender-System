from pathlib import Path
from bs4 import BeautifulSoup
from app.rag.loaders.base import (
    DocumentLoader,
    clean_text,
    compute_file_hash,
    extract_metadata_from_text,
)
from app.rag.schemas import LoadedDocument


class HTMLLoader(DocumentLoader):
    """
    Loader for HTML (.html, .htm) documents using BeautifulSoup.
    Strips script, style, and navigation tags while extracting structured text.
    """

    def load(self, file_path: Path) -> LoadedDocument:
        with open(file_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
            raw_html = f.read()

        soup = BeautifulSoup(raw_html, "html.parser")

        # Extract title if present
        title = None
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        # Remove irrelevant non-text tags
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
            tag.decompose()

        # Extract text
        extracted_text = soup.get_text(separator="\n")
        cleaned = clean_text(extracted_text)

        metadata = extract_metadata_from_text(raw_html, file_path)
        if title:
            metadata.title = title

        file_hash = compute_file_hash(file_path)

        return LoadedDocument(
            content=cleaned,
            metadata=metadata,
            file_path=str(file_path),
            file_hash=file_hash,
        )
