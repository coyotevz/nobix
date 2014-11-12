"""Add branch table

Revision ID: 51e0057115ec
Revises: 3d8d99ffb617
Create Date: 2014-11-12 12:57:11.917512

"""

# revision identifiers, used by Alembic.
revision = '51e0057115ec'
down_revision = '3d8d99ffb617'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('branch',
        sa.Column('id', sa.Integer, nullable=False),
        sa.Column('name', sa.UnicodeText, nullable=False),
        sa.Column('address', sa.UnicodeText, nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('branch')
