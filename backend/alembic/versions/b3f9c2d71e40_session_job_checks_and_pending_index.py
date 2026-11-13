"""session_job: enforce the 30-second minimum, fix the pending-jobs index, drop the old capture tables

- The Pi's query filters on status = 'pending', but ix_session_job_pending was built on
  lower(status) = 'pending', so Postgres could never use it. Statuses are now forced to
  lowercase by a check constraint, so the index can use the plain column.
- The team switched from booked capture sessions to the SessionJob queue, so the
  capture_session and capture_settings tables from a8bfeab54ce1 are no longer used.

Revision ID: b3f9c2d71e40
Revises: 0573e69c3b10
Create Date: 2026-11-12 09:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b3f9c2d71e40'
down_revision: Union[str, Sequence[str], None] = '0573e69c3b10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Test jobs made before these rules existed (the old form defaulted to 15 seconds)
    op.execute("UPDATE session_job SET interval_seconds = 30 WHERE interval_seconds < 30")
    op.execute("UPDATE session_job SET status = lower(status)")
    op.execute("UPDATE session_job SET status = 'error' WHERE status NOT IN ('pending', 'running', 'completed', 'error')")

    op.create_check_constraint('ck_session_job_duration', 'session_job', 'duration_seconds > 0')
    op.create_check_constraint('ck_session_job_interval', 'session_job', 'interval_seconds >= 30')
    op.create_check_constraint('ck_session_job_status', 'session_job', "status IN ('pending', 'running', 'completed', 'error')")

    op.execute("DROP INDEX IF EXISTS ix_session_job_pending")
    op.create_index('ix_session_job_pending', 'session_job', ['device_id', 'created_at'], unique=False,
                    postgresql_where=sa.text("status = 'pending'"))

    op.execute("DROP TABLE IF EXISTS capture_session")
    op.execute("DROP TABLE IF EXISTS capture_settings")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table('capture_settings',
    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('interval_s', sa.Integer(), server_default='60', nullable=False),
    sa.Column('updated_by', sa.Integer(), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('id = 1', name='ck_capture_settings_one_row'),
    sa.CheckConstraint('interval_s >= 30', name='ck_capture_settings_interval'),
    sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.execute("INSERT INTO capture_settings (id) VALUES (1)")
    op.create_table('capture_session',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    postgresql.ExcludeConstraint((sa.text('tstzrange(start_at, end_at)'), '&&'), using='gist', name='ex_capture_session_no_overlap'),
    sa.CheckConstraint('end_at > start_at', name='ck_capture_session_end_after_start'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_capture_session_start_at'), 'capture_session', ['start_at'], unique=False)

    # Put back the index exactly as 0dda5dc1730b made it, so its downgrade can drop it
    op.drop_index('ix_session_job_pending', table_name='session_job')
    op.create_index('ix_session_job_pending', 'session_job', ['device_id', 'created_at'], unique=False,
                    postgresql_where=sa.text("lower(status) = 'pending'"))

    op.drop_constraint('ck_session_job_status', 'session_job', type_='check')
    op.drop_constraint('ck_session_job_interval', 'session_job', type_='check')
    op.drop_constraint('ck_session_job_duration', 'session_job', type_='check')
