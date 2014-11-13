"""Add payment_transaction table

Revision ID: 1eab6f4b7663
Revises: 4f192502753f
Create Date: 2014-11-13 03:24:39.254565

"""

# revision identifiers, used by Alembic.
revision = '1eab6f4b7663'
down_revision = '4f192502753f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('payment_transaction',
        sa.Column('created', sa.DateTime, nullable=True),
        sa.Column('modified', sa.DateTime, nullable=True),
        sa.Column('id', sa.Integer, nullable=False),
        sa.Column('doc_payment_id', sa.Integer, nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('method_id', sa.Integer, nullable=False),
        sa.Column('extra_info', sa.UnicodeText, nullable=True),
        sa.ForeignKeyConstraint(['doc_payment_id'], ['document_payment.id']),
        sa.ForeignKeyConstraint(['method_id'], ['payment_method.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('payment_transaction')
