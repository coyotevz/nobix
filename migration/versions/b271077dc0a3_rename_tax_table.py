"""Rename tax table

Revision ID: b271077dc0a3
Revises: e7211c188fee
Create Date: 2018-05-30 01:58:28.655379

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b271077dc0a3'
down_revision = 'e7211c188fee'
branch_labels = None
depends_on = None


def rename_column(batch_op, old_name, new_name):
    batch_op.alter_column(old_name, new_column_name=new_name)


def upgrade():
    op.rename_table('tasas', 'tax')

    with op.batch_alter_table('tax') as tax:
        rename_column(tax, 'nombre', 'name')
        rename_column(tax, 'monto', 'amount')
        rename_column(tax, 'documento_id', 'document_id')

    op.execute('ALTER SEQUENCE tasas_id_seq RENAME TO tax_id_seq')
    op.execute('ALTER INDEX tasas_pkey RENAME TO tax_pkey')
    op.execute('ALTER INDEX ix_tasas_documento_id RENAME TO ix_tax_document_id')
    op.execute('ALTER TABLE tax RENAME CONSTRAINT tasas_documento_id_fkey TO tax_document_id_fkey')


def downgrade():
    op.rename_table('tax', 'tasas')

    with op.batch_alter_table('tasas') as tax:
        rename_column(tax, 'name', 'nombre')
        rename_column(tax, 'amount', 'monto')
        rename_column(tax, 'document_id', 'documento_id')

    op.execute('ALTER SEQUENCE tax_id_seq RENAME TO tasas_id_seq')
    op.execute('ALTER INDEX tax_pkey RENAME TO tasas_pkey')
    op.execute('ALTER INDEX ix_tax_document_id RENAME TO ix_tasas_documento_id')
    op.execute('ALTER TABLE tasas RENAME CONSTRAINT tax_document_id_fkey TO tasas_documento_id_fkey')
