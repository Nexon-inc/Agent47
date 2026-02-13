"""add auto_renew field to subscriptions

Revision ID: add_auto_renew_field
Revises: remove_unique_username
Create Date: 2026-02-13 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_auto_renew_field'
down_revision = 'remove_unique_username'
branch_labels = None
depends_on = None


def upgrade():
    # Add auto_renew column to subscriptions table
    # We use server_default='true' to ensure existing rows get a value
    try:
        op.add_column('subscriptions', sa.Column('auto_renew', sa.Boolean(), server_default='true', nullable=True))
    except Exception:
        # Ignore if column already exists (idempotency)
        pass


def downgrade():
    try:
        op.drop_column('subscriptions', 'auto_renew')
    except Exception:
        pass
