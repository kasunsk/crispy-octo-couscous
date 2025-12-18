"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import func

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Documents table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('chunks_count', sa.Integer(), default=0),
        sa.Column('status', sa.String(50), default='processing'),
        sa.Column('uploaded_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', postgresql.JSON, nullable=True),
    )

    # Chat sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()')),
    )

    # Chat messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chat_sessions.id'), nullable=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=True),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sources', postgresql.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
    )

    # Document chunks table
    op.create_table(
        'document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('start_char', sa.Integer(), nullable=True),
        sa.Column('end_char', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSON, nullable=True),
    )

    # Indexes
    op.create_index('idx_documents_status', 'documents', ['status'])
    op.create_index('idx_chat_messages_session', 'chat_messages', ['session_id'])
    op.create_index('idx_chat_messages_document', 'chat_messages', ['document_id'])
    op.create_index('idx_document_chunks_document', 'document_chunks', ['document_id'])


def downgrade() -> None:
    op.drop_index('idx_document_chunks_document', 'document_chunks')
    op.drop_index('idx_chat_messages_document', 'chat_messages')
    op.drop_index('idx_chat_messages_session', 'chat_messages')
    op.drop_index('idx_documents_status', 'documents')
    
    op.drop_table('document_chunks')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('documents')

