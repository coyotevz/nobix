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
    op.create_index(op.f('ix_document_customer_id'), 'document',
                    ['customer_id'], unique=False)

    op.drop_constraint('items_documento_documento_id_fkey', 'items_documento',
                       type_='foreignkey')
    op.create_foreign_key('items_documento_documento_id_fkey',
                          'items_documento', 'document',
                          ['documento_id'], ['id'])
    op.drop_constraint('tasas_documento_id_fkey', 'tasas', type_='foreignkey')
    op.create_foreign_key('tasas_documento_id_fkey', 'tasas', 'document',
                          ['documento_id'], ['id'])


def downgrade():
    op.drop_index(op.f('ix_document_customer_id'), table_name='document')
    op.rename_table('document', 'documentos')
    op.create_index('ix_documentos_customer_id', 'documentos', ['customer_id'],
                    unique=False)

    op.drop_constraint('tasas_documento_id_fkey', 'tasas', type_='foreignkey')
    op.create_foreign_key('tasas_documento_id_fkey', 'tasas', 'documentos',
                          ['documento_id'], ['id'])
    op.drop_constraint('items_documento_documento_id_fkey', 'items_documento',
                       type_='foreignkey')
    op.create_foreign_key('items_documento_documento_id_fkey',
                          'items_documento', 'documentos',
                          ['documento_id'], ['id'])
