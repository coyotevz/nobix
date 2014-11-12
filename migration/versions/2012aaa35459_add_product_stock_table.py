"""Add product_stock table

Revision ID: 2012aaa35459
Revises: 51e0057115ec
Create Date: 2014-11-12 13:00:42.249862

"""

# revision identifiers, used by Alembic.
revision = '2012aaa35459'
down_revision = '51e0057115ec'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('product_stock',
        sa.Column('created', sa.DateTime, nullable=True),
        sa.Column('modified', sa.DateTime, nullable=True),
        sa.Column('product_id', sa.Integer, nullable=False),
        sa.Column('branch_id', sa.Integer, nullable=False),
        sa.Column('quantity', sa.Numeric(10, 2), nullable=False),
        sa.Column('logic_quantity', sa.Numeric(10, 2), nullable=True),
        sa.ForeignKeyConstraint(['branch_id'], ['branch.id']),
        sa.ForeignKeyConstraint(['product_id'], ['articulos.id']),
        sa.PrimaryKeyConstraint('product_id', 'branch_id')
    )


def downgrade():
    op.drop_table('product_stock')
