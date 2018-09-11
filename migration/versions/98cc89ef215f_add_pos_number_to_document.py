"""Add 'pos_number' column to document, migrate data

Revision ID: 98cc89ef215f
Revises: 78872793c012
Create Date: 2018-09-11 13:34:36.865582

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '98cc89ef215f'
down_revision = '78872793c012'
branch_labels = None
depends_on = None


# helper table
dochelper = sa.Table(
    'document',
    sa.MetaData(),
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('pos_number', sa.Integer)
)


def upgrade():
    op.add_column('document', sa.Column('pos_number', sa.Integer))

    # migrate data
    op.execute(
        dochelper.update().values(
            pos_number=1
        )
    )

    op.alter_column('document', 'pos_number', nullable=False)


def downgrade():
    op.drop_column('document', 'pos_number')
