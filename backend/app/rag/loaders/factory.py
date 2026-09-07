from pathlib import Path
from typing import Dict, Type
from app.rag.loaders.base import DocumentLoader
from app.rag.loaders.html_loader import HTMLLoader
from app.rag.loaders.pdf_loader import PDFLoader
from app.rag.loaders.txt_loader import TextLoader

LOADER_MAPPING: Dict[str, Type[DocumentLoader]] = {
    ".txt": TextLoader,
    ".md": TextLoader,
    ".html": HTMLLoader,
    ".htm": HTMLLoader,
    ".pdf": PDFLoader,
}


def get_loader_for_file(file_path: Path) -> DocumentLoader:
    """
    Factory helper to resolve the appropriate DocumentLoader instance for a given file.
    """
    ext = file_path.suffix.lower()
    loader_cls = LOADER_MAPPING.get(ext)
    if not loader_cls:
        raise ValueError(
            f"Unsupported document format '{ext}' for file '{file_path.name}'. "
            f"Supported extensions: {list(LOADER_MAPPING.keys())}"
        )
    return loader_cls()
