"""Add stock_transaction table

Revision ID: 12da1f0fc75d
Revises: 2012aaa35459
Create Date: 2014-11-12 13:04:45.848748

"""

# revision identifiers, used by Alembic.
revision = '12da1f0fc75d'
down_revision = '2012aaa35459'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('stock_transaction',
        sa.Column('id', sa.Integer, nullable=False),
        sa.Column('date', sa.DateTime, nullable=True),
        sa.Column('product_id', sa.Integer, nullable=False),
        sa.Column('branch_id', sa.Integer, nullable=False),
        sa.Column('stock_cost', sa.Numeric(10, 2), nullable=True),
        sa.Column('quantity', sa.Numeric(10, 2), nullable=False),
        sa.Column('type', sa.UnicodeText, nullable=False),
        sa.ForeignKeyConstraint(['product_id', 'branch_id'],
            ['product_stock.product_id', 'product_stock.branch_id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('stock_transaction')
