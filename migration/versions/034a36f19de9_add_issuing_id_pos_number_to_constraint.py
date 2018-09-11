"""Add 'issuing_id' column to document, update constraint, migrate data

Revision ID: 034a36f19de9
Revises: 98cc89ef215f
Create Date: 2018-09-11 16:06:09.296594

"""
from alembic import op
import sqlalchemy as sa
from datetime import date


# revision identifiers, used by Alembic.
revision = '034a36f19de9'
down_revision = '98cc89ef215f'
branch_labels = None
depends_on = None

# helper table
dochelper = sa.Table(
    'document',
    sa.MetaData(),
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('issuing_id', sa.Integer),
    sa.Column('issue_date', sa.Date),
    sa.Column('fiscal', sa.String),
    sa.Column('customer_id', sa.Integer),
)

limit_date = date(2010, 3, 12) # special use for custom data


def upgrade():
    op.add_column('document', sa.Column('issuing_id', sa.Integer))

    # migrate data
    stmt1 = dochelper.update().\
            values(issuing_id=dochelper.c.customer_id)
    stmt2 = dochelper.update().\
            where(dochelper.c.fiscal.in_(['+venta', '-venta', None])).\
            where(dochelper.c.issue_date<=limit_date).\
            values(issuing_id=1)
    stmt3 = dochelper.update().\
            where(dochelper.c.fiscal.in_(['+venta', '-venta', None])).\
            where(dochelper.c.issue_date>limit_date).\
            values(issuing_id=2)
    op.execute(stmt1)
    op.execute(stmt2)
    op.execute(stmt3)

    op.alter_column('document', 'issuing_id', nullable=False)

    op.drop_constraint('document_type_key', 'document', type_='unique')
    op.create_unique_constraint('uq_document', 'document',
            ['issuing_id', 'doc_type', 'issue_date', 'pos_number', 'number'])


def downgrade():
    op.drop_constraint('uq_document', 'document', type_='unique')
    op.create_unique_constraint('document_type_key', 'document', ['doc_type', 'issue_date', 'number'])
    op.drop_column('document', 'issuing_id')
