"""Create session_job table

Revision ID: 0dda5dc1730b
Revises: a8bfeab54ce1
Create Date: 2026-11-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0dda5dc1730b'
down_revision: Union[str, Sequence[str], None] = 'a8bfeab54ce1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'session_job',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.String(), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=False),
        sa.Column('interval_seconds', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), server_default='pending', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_session_job_device_id'), 'session_job', ['device_id'], unique=False)
    op.create_index(op.f('ix_session_job_status'), 'session_job', ['status'], unique=False)
    op.create_index(
        'ix_session_job_pending',
        'session_job',
        ['device_id', 'created_at'],
        unique=False,
        postgresql_where=sa.text("lower(status) = 'pending'"),
    )


def downgrade() -> None:
    op.drop_index('ix_session_job_pending', table_name='session_job')
    op.drop_index(op.f('ix_session_job_status'), table_name='session_job')
    op.drop_index(op.f('ix_session_job_device_id'), table_name='session_job')
    op.drop_table('session_job')