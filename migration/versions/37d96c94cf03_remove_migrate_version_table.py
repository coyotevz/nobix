"""Remove migrate version table.

Revision ID: 37d96c94cf03
Revises: None
Create Date: 2014-11-06 15:51:57.505000

"""

# revision identifiers, used by Alembic.
revision = '37d96c94cf03'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_table('migrate_version')


def downgrade():
    op.create_table('migrate_version',
        sa.Column('repository_id', sa.Unicode(length=250),
                  autoincrement=False, nullable=False),
        sa.Column('repository_path', sa.UnicodeText, autoincrement=False,
                  nullable=True),
        sa.Column('version', sa.Integer, autoincrement=False,
                  nullable=True),
        sa.PrimaryKeyConstraint('repository_id',
                                name=u'migrate_version_pkey'),
    )
