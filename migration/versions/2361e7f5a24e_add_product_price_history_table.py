"""Add product price history table.

Revision ID: 2361e7f5a24e
Revises: 556ff4575155
Create Date: 2014-11-09 03:22:50.249312

"""

# revision identifiers, used by Alembic.
revision = '2361e7f5a24e'
down_revision = '556ff4575155'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'product_price_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('date', sa.DateTime(), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['articulos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('product_price_history')
