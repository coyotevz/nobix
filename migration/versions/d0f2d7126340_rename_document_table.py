"""Rename document table

Revision ID: d0f2d7126340
Revises: 4418465d2df7
Create Date: 2018-05-27 15:10:46.216698

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd0f2d7126340'
down_revision = '4418465d2df7'
branch_labels = None
depends_on = None


def upgrade():

    op.drop_index('ix_documentos_customer_id', table_name='documentos')
    op.rename_table('documentos', 'document')
    op.create_index(op.f('ix_document_customer_id'), 'document', ['customer_id'], unique=False)

    op.drop_constraint('items_documento_documento_id_fkey', 'items_documento', type_='foreignkey')
    op.create_foreign_key('items_documento_documento_id_fkey', 'items_documento', 'document', ['documento_id'], ['id'])
    op.drop_constraint('tasas_documento_id_fkey', 'tasas', type_='foreignkey')
    op.create_foreign_key('tasas_documento_id_fkey', 'tasas', 'document', ['documento_id'], ['id'])

    # ### commands auto generated by Alembic - please adjust! ###
    # op.create_table('document',
    # sa.Column('id', sa.Integer(), nullable=False),
    # sa.Column('doc_type', sa.Unicode(length=3), nullable=False),
    # sa.Column('issue_date', sa.Date(), nullable=False),
    # sa.Column('issue_time', sa.Time(), nullable=True),
    # sa.Column('number', sa.Integer(), nullable=True),
    # sa.Column('salesman', sa.UnicodeText(length=3), nullable=True),
    # sa.Column('discount', sa.Numeric(precision=10, scale=2), nullable=True),
    # sa.Column('net', sa.Numeric(precision=10, scale=2), nullable=False),
    # sa.Column('fiscal', sa.UnicodeText(length=10), nullable=True),
    # sa.Column('fiscal_period', sa.Date(), nullable=True),
    # sa.Column('customer_id', sa.Integer(), nullable=False),
    # sa.Column('customer_name', sa.UnicodeText(length=35), nullable=True),
    # sa.Column('customer_address', sa.UnicodeText(length=60), nullable=True),
    # sa.Column('customer_cuit', sa.UnicodeText(length=13), nullable=True),
    # sa.ForeignKeyConstraint(['customer_id'], ['clientes.id'], ),
    # sa.PrimaryKeyConstraint('id'),
    # sa.UniqueConstraint('doc_type', 'issue_date', 'number')
    # )
    # op.drop_table('documentos')


    # ### end Alembic commands ###


def downgrade():
    op.drop_index(op.f('ix_document_customer_id'), table_name='document')
    op.rename_table('document', 'documentos')
    op.create_index('ix_documentos_customer_id', 'documentos', ['customer_id'], unique=False)

    op.drop_constraint('tasas_documento_id_fkey', 'tasas', type_='foreignkey')
    op.create_foreign_key('tasas_documento_id_fkey', 'tasas', 'documentos', ['documento_id'], ['id'])
    op.drop_constraint('items_documento_documento_id_fkey', 'items_documento', type_='foreignkey')
    op.create_foreign_key('items_documento_documento_id_fkey', 'items_documento', 'documentos', ['documento_id'], ['id'])
    # ### commands auto generated by Alembic - please adjust! ###
    # op.create_table('documentos',
    # sa.Column('id', sa.INTEGER(), nullable=False),
    # sa.Column('doc_type', sa.VARCHAR(length=3), autoincrement=False, nullable=False),
    # sa.Column('issue_date', sa.DATE(), autoincrement=False, nullable=False),
    # sa.Column('issue_time', postgresql.TIME(), autoincrement=False, nullable=True),
    # sa.Column('number', sa.INTEGER(), autoincrement=False, nullable=True),
    # sa.Column('salesman', sa.TEXT(), autoincrement=False, nullable=True),
    # sa.Column('discount', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=True),
    # sa.Column('net', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=False),
    # sa.Column('fiscal', sa.TEXT(), autoincrement=False, nullable=True),
    # sa.Column('fiscal_period', sa.DATE(), autoincrement=False, nullable=True),
    # sa.Column('customer_id', sa.INTEGER(), autoincrement=False, nullable=False),
    # sa.Column('customer_name', sa.TEXT(), autoincrement=False, nullable=True),
    # sa.Column('customer_address', sa.TEXT(), autoincrement=False, nullable=True),
    # sa.Column('customer_cuit', sa.TEXT(), autoincrement=False, nullable=True),
    # sa.ForeignKeyConstraint(['customer_id'], ['clientes.id'], name='documentos_customer_id_fkey'),
    # sa.PrimaryKeyConstraint('id', name='documentos_pkey'),
    # sa.UniqueConstraint('doc_type', 'issue_date', 'number', name='documentos_doc_type_issue_date_number_key')
    # )
    #op.drop_table('document')
    # ### end Alembic commands ###
