"""add exam status tracking columns

Revision ID: ae3f5b2c8d1e
Revises: 24dcfe97dd3b
Create Date: 2026-03-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ae3f5b2c8d1e'
down_revision = '24dcfe97dd3b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### Add new columns to exams table ###
    op.add_column('exams', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('exams', sa.Column('failure_reason', sa.Text(), nullable=True))
    
    # ### Update exam_status enum to include new statuses ###
    # Drop the old enum type and create a new one with additional values
    op.execute("ALTER TYPE exam_status ADD VALUE 'generating' BEFORE 'draft'")
    op.execute("ALTER TYPE exam_status ADD VALUE 'ready' AFTER 'generating'")
    op.execute("ALTER TYPE exam_status ADD VALUE 'failed' AFTER 'published'")


def downgrade() -> None:
    # ### Remove columns from exams table ###
    op.drop_column('exams', 'failure_reason')
    op.drop_column('exams', 'updated_at')
    
    # Note: PostgreSQL enums cannot be easily downgraded without recreating the type.
    # The enum values added in upgrade cannot be removed without modifying the enum type.
    # This is a limitation of PostgreSQL and would require manual intervention or recreation
    # of the enum type. For now, we'll skip the enum downgrade.
    # If needed, run: ALTER TYPE exam_status RENAME TO exam_status_old;
    #                CREATE TYPE exam_status AS ENUM ('draft', 'published');
    #                ALTER TABLE exams ALTER COLUMN status DROP DEFAULT;
    #                ALTER TABLE exams ALTER COLUMN status TYPE exam_status USING status::text::exam_status;
    #                DROP TYPE exam_status_old;
