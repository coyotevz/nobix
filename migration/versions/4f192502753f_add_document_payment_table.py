"""Add document_payment table

Revision ID: 4f192502753f
Revises: 1fd8093ade93
Create Date: 2014-11-13 03:23:02.823088

"""

# revision identifiers, used by Alembic.
revision = '4f192502753f'
down_revision = '1fd8093ade93'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('document_payment',
        sa.Column('id', sa.Integer, nullable=False),
        sa.Column('document_id', sa.Integer, nullable=False),
        sa.Column('expiration', sa.DateTime, nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documentos.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('document_payment')
