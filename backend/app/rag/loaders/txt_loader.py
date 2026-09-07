from pathlib import Path
from app.rag.loaders.base import (
    DocumentLoader,
    clean_text,
    compute_file_hash,
    extract_metadata_from_text,
)
from app.rag.schemas import LoadedDocument


class TextLoader(DocumentLoader):
    """
    Loader for plain text (.txt) and Markdown (.md) documents.
    """

    def load(self, file_path: Path) -> LoadedDocument:
        with open(file_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
            raw_content = f.read()

        cleaned = clean_text(raw_content)
        metadata = extract_metadata_from_text(raw_content, file_path)
        file_hash = compute_file_hash(file_path)

        return LoadedDocument(
            content=cleaned,
            metadata=metadata,
            file_path=str(file_path),
            file_hash=file_hash,
        )
