"""Add tax_amount to item document

Revision ID: 3d8d99ffb617
Revises: 2361e7f5a24e
Create Date: 2014-11-09 03:51:31.982081

"""

# revision identifiers, used by Alembic.
revision = '3d8d99ffb617'
down_revision = '2361e7f5a24e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('items_documento',
        sa.Column('tax_amount', sa.Numeric(precision=10, scale=2),
                  nullable=True)
    )


def downgrade():
    op.drop_column('items_documento', 'tax_amount')
