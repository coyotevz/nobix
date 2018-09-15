"""Add 'barcode' field to product table

Revision ID: 9dd23e3edb81
Revises: 034a36f19de9
Create Date: 2018-09-15 03:05:34.840929

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9dd23e3edb81'
down_revision = '034a36f19de9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('product', sa.Column('barcode', sa.Unicode(), nullable=True, unique=True))


def downgrade():
    op.drop_column('product', 'barcode')
