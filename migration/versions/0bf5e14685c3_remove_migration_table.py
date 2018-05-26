"""Remove migrate version table.

Revision ID: 0bf5e14685c3
Revises:
Create Date: 2018-05-26 17:57:03.941495

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0bf5e14685c3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('migrate_version')


def downgrade():
    op.create_table('migrate_version',
        sa.Column('repository_id', sa.Unicode(length=250),
                  autoincrement=False, nullable=False),
        sa.Column('repository_path', sa.UnicodeText,
                  autoincrement=False, nullable=True),
        sa.Column('version', sa.Integer,
                  autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint('repository_id',
                                name='migrate_version_pkey')
    )
