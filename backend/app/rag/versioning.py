import logging
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.rag.models import Document

logger = logging.getLogger(__name__)


class DocumentVersionService:
    """
    RAG 2.0 Document Freshness and Versioning Management Service.
    Tracks active statutory circulars, manages superseded document deprecation,
    and guarantees audit preservation.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_documents(self, organization: Optional[str] = None) -> List[Document]:
        """Fetch all actively enforceable documents."""
        stmt = select(Document).where(Document.is_active.is_(True))
        if organization:
            stmt = stmt.where(Document.organization.ilike(f"%{organization.strip()}%"))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def deactivate_document(self, document_id: int, reason: str = "Superseded by newer circular") -> bool:
        """
        Soft-deprecate an outdated document without deleting historical chunks or audit links.
        """
        stmt = (
            update(Document)
            .where(Document.id == document_id)
            .values(is_active=False)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        logger.info(f"Deactivated document id={document_id}. Reason: {reason}")
        return result.rowcount > 0

    async def supersede_document(self, old_doc_id: int, new_doc_id: int) -> bool:
        """Mark an older circular as inactive in favor of a newer statutory version."""
        return await self.deactivate_document(
            old_doc_id,
            reason=f"Superseded by authoritative document id={new_doc_id}"
        )
