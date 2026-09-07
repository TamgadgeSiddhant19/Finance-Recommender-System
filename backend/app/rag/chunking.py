from typing import Any, Dict, List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings
from app.rag.schemas import ChunkMetadata, LoadedDocument


class DocumentChunker:
    """
    Splits loaded financial documents into coherent semantic chunks while preserving metadata.
    """

    def __init__(
        self,
        chunk_size: int = settings.RAG_CHUNK_SIZE,
        chunk_overlap: int = settings.RAG_CHUNK_OVERLAP,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=True,
        )

    def chunk_document(self, doc: LoadedDocument) -> List[Dict[str, Any]]:
        """
        Split a LoadedDocument into chunks and attach structured metadata.
        Returns a list of dicts with 'chunk_index', 'content', and 'metadata'.
        """
        raw_chunks = self.splitter.split_text(doc.content)
        processed_chunks: List[Dict[str, Any]] = []

        for idx, text_segment in enumerate(raw_chunks):
            cleaned_segment = text_segment.strip()
            if not cleaned_segment:
                continue

            chunk_meta = ChunkMetadata(
                source=doc.metadata.source,
                organization=doc.metadata.organization,
                document_type=doc.metadata.document_type,
                topic=doc.metadata.topic,
                asset_class=doc.metadata.asset_class,
                publication_date=doc.metadata.publication_date,
                chunk_index=idx,
                char_count=len(cleaned_segment),
            )

            processed_chunks.append({
                "chunk_index": idx,
                "content": cleaned_segment,
                "metadata": chunk_meta.model_dump(),
            })

        return processed_chunks
