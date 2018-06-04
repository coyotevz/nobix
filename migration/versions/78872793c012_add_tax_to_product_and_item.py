"""Add tax to product and item

Revision ID: 78872793c012
Revises: c71e7fd6a9b7
Create Date: 2018-06-02 03:54:10.424477

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '78872793c012'
down_revision = 'c71e7fd6a9b7'
branch_labels = None
depends_on = None

producthelper = sa.Table(
    'product',
    sa.MetaData(),
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('tax_code', sa.Unicode())
)

itemhelper = sa.Table(
    'item',
    sa.MetaData(),
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('tax_factor', sa.Unicode())
)


def upgrade():
    op.add_column('product', sa.Column('tax_code', sa.Unicode(), nullable=True))
    op.add_column('item', sa.Column('tax_factor', sa.Unicode(), nullable=True))

    # migrate data
    op.execute(
        producthelper.update().values(
            tax_code='V21',
        )
    )

    op.execute(
        itemhelper.update().values(
            tax_factor='21.00',
        )
    )

    # Fix constraint
    op.alter_column('product', 'tax_code', nullable=False)
    op.alter_column('item', 'tax_factor', nullable=False)


def downgrade():
    op.drop_column('product', 'tax_code')
    op.drop_column('item', 'tax_amount')
