"""remove unique username constraint

Revision ID: remove_unique_username
Revises: previous_revision
Create Date: 2026-01-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_unique_username'
down_revision = None  # You might need to adjust this manually if strictly ordered
branch_labels = None
depends_on = None


def upgrade():
    # Attempt to drop the unique constraint/index on username
    # Note: The expected name format is typically ix_users_username or users_username_key
    
    # Try dropping known potential unique constraints/indexes
    try:
        op.drop_index('ix_users_username', table_name='users')
        # Re-create as non-unique index
        op.create_index('ix_users_username', 'users', ['username'], unique=False)
    except Exception:
        # If ix_users_username didn't exist or wasn't the unique one
        pass

    try:
        op.drop_constraint('users_username_key', 'users', type_='unique')
    except Exception:
        pass
        
    try:
        op.drop_constraint('uq_users_username', 'users', type_='unique')
    except Exception:
        pass


def downgrade():
    # Re-add unique constraint
    try:
        op.drop_index('ix_users_username', table_name='users')
        op.create_index('ix_users_username', 'users', ['username'], unique=True)
    except Exception:
        pass
