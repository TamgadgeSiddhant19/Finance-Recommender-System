"""add documents and document_chunks tables

Revision ID: b1ec38fec3ea
Revises: 9726155ffbbf
Create Date: 2026-09-03 11:45:18.603128

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1ec38fec3ea'
down_revision: Union[str, Sequence[str], None] = '9726155ffbbf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('source', sa.String(length=255), nullable=False),
        sa.Column('organization', sa.String(length=100), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('topic', sa.String(length=50), nullable=False),
        sa.Column('asset_class', sa.String(length=50), nullable=False),
        sa.Column('publication_date', sa.String(length=50), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('total_chunks', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_asset_class'), 'documents', ['asset_class'], unique=False)
    op.create_index(op.f('ix_documents_document_type'), 'documents', ['document_type'], unique=False)
    op.create_index(op.f('ix_documents_file_hash'), 'documents', ['file_hash'], unique=False)
    op.create_index(op.f('ix_documents_organization'), 'documents', ['organization'], unique=False)
    op.create_index(op.f('ix_documents_source'), 'documents', ['source'], unique=False)
    op.create_index(op.f('ix_documents_topic'), 'documents', ['topic'], unique=False)

    # 2. Create document_chunks table
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('embedding', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_document_chunks_doc_chunk', 'document_chunks', ['document_id', 'chunk_index'], unique=True)
    op.create_index(op.f('ix_document_chunks_document_id'), 'document_chunks', ['document_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_document_chunks_document_id'), table_name='document_chunks')
    op.drop_index('ix_document_chunks_doc_chunk', table_name='document_chunks')
    op.drop_table('document_chunks')
    op.drop_index(op.f('ix_documents_topic'), table_name='documents')
    op.drop_index(op.f('ix_documents_source'), table_name='documents')
    op.drop_index(op.f('ix_documents_organization'), table_name='documents')
    op.drop_index(op.f('ix_documents_file_hash'), table_name='documents')
    op.drop_index(op.f('ix_documents_document_type'), table_name='documents')
    op.drop_index(op.f('ix_documents_asset_class'), table_name='documents')
    op.drop_table('documents')
