"""Add payment method table

Revision ID: 1fd8093ade93
Revises: 12da1f0fc75d
Create Date: 2014-11-13 03:21:07.821829

"""

# revision identifiers, used by Alembic.
revision = '1fd8093ade93'
down_revision = '12da1f0fc75d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('payment_method',
        sa.Column('id', sa.Integer, nullable=False),
        sa.Column('code', sa.UnicodeText, nullable=True),
        sa.Column('name', sa.UnicodeText, nullable=True),
        sa.Column('method_type', sa.UnicodeText, nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )


def downgrade():
    op.drop_table('payment_method')
