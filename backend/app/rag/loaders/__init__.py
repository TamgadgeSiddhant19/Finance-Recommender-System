from app.rag.loaders.base import (
    DocumentLoader,
    clean_text,
    compute_file_hash,
    extract_metadata_from_text,
)
from app.rag.loaders.factory import get_loader_for_file
from app.rag.loaders.html_loader import HTMLLoader
from app.rag.loaders.pdf_loader import PDFLoader
from app.rag.loaders.txt_loader import TextLoader

__all__ = [
    "DocumentLoader",
    "clean_text",
    "compute_file_hash",
    "extract_metadata_from_text",
    "get_loader_for_file",
    "TextLoader",
    "HTMLLoader",
    "PDFLoader",
]
