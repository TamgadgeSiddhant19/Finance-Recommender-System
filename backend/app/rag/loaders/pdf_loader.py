from pathlib import Path
import pypdf
from app.rag.loaders.base import (
    DocumentLoader,
    clean_text,
    compute_file_hash,
    extract_metadata_from_text,
)
from app.rag.schemas import LoadedDocument


class PDFLoader(DocumentLoader):
    """
    Loader for PDF (.pdf) documents using pypdf.
    Extracts text page-by-page.
    """

    def load(self, file_path: Path) -> LoadedDocument:
        reader = pypdf.PdfReader(str(file_path))
        page_texts = []

        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                page_texts.append(extracted)

        raw_combined = "\n\n".join(page_texts)
        cleaned = clean_text(raw_combined)

        metadata = extract_metadata_from_text(cleaned[:2000], file_path)
        file_hash = compute_file_hash(file_path)

        return LoadedDocument(
            content=cleaned,
            metadata=metadata,
            file_path=str(file_path),
            file_hash=file_hash,
        )
